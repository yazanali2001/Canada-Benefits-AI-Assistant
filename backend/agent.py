"""
The core conversational agent: runs the survey question-by-question,
resolving each answer (fixed option or LLM-extracted "Other"), then
holds a real, context-aware follow-up conversation once the survey
is complete — with explainability, confidence scoring, automatic
language matching, re-evaluation on life changes, detailed
professional explanations, and suggested follow-up questions.
"""

import json
import logging
from typing import Any, Optional

from backend.database.db import SessionLocal
from backend.database.models import Conversation
from backend.memory.store import get_memory, save_memory
from backend.memory.questions import get_question_by_field, get_next_question
from backend.memory.change_detection import detect_change
from backend.llm.extraction_llm import extract_other_answer
from backend.eligibility.profile import UserProfile
from backend.eligibility.engine import evaluate_eligibility, diff_eligibility
from backend.vector_db.search import search_benefits
from backend.llm.groq_client import generate_response

logger = logging.getLogger(__name__)

HISTORY_TURNS_LIMIT = 6
MAIN_ANSWER_MAX_TOKENS = 1800
SUGGESTIONS_MAX_TOKENS = 200

SYSTEM_INSTRUCTIONS = """You are a knowledgeable, professional assistant that explains \
Canadian federal public benefits. Only use the ELIGIBLE PROGRAMS and RELATED PROGRAMS \
provided below — do not invent benefit names, dollar amounts, or eligibility rules \
that aren't given to you. Always remind the user to confirm details on the official \
Canada.ca page before applying.

DEPTH AND TONE: Give thorough, professional, well-organized explanations — not short \
one-liners. For each relevant program, briefly cover: (1) what the program is and who \
it's for, (2) why the user specifically qualifies (or doesn't), and (3) a concrete next \
step (e.g. what to prepare, where to apply, roughly how the process works), based only \
on the official URL and information provided — never invent application steps not \
implied by the data given.

FORMATTING — CRITICAL, this text is rendered in a narrow chat bubble, NOT a document:
- Never use Markdown tables (no "|" pipe characters).
- Never use raw HTML tags like <br>. Use a real blank line between paragraphs instead.
- Use short paragraphs and simple "-" bullet points only. Keep each bullet to one line.
- Use plain numbered section headers like "1. Employment Insurance (EI)" on their own \
line, not styled as a Markdown table row.
- If you are covering several programs, keep each program's section concise (a few \
short bullets) rather than exhaustive, so the full answer fits comfortably — prioritize \
covering every eligible program briefly over covering one program exhaustively.

LANGUAGE: Always reply in the SAME language the user's latest message is written in \
(English, Arabic, French, or otherwise) — match them automatically, never ask which \
language to use.

You are in an ONGOING conversation with this user. Read the CONVERSATION HISTORY below \
before replying. Do not repeat the full eligibility summary again if you already gave \
it — instead, directly and specifically answer the user's latest message in the same \
depth, professionalism, and formatting rules described above.

TRANSPARENCY: Briefly ground your answer in the data given — mention that confirmed \
eligibility comes from the rules engine (high confidence), while any general \
suggestions beyond that are informational only and should be verified on the official \
page. Keep this natural, not a rigid disclaimer in every single reply."""


def _get_recent_history(user_id: str, limit: int = HISTORY_TURNS_LIMIT) -> str:
    db = SessionLocal()
    try:
        rows = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()
        lines = []
        for row in rows:
            lines.append(f"User: {row.user_message}")
            lines.append(f"Assistant: {row.assistant_response}")
        return "\n".join(lines) if lines else "(no previous messages)"
    except Exception:
        logger.exception("Failed to load conversation history for user_id=%s", user_id)
        return "(no previous messages)"
    finally:
        db.close()


def _build_prompt(
    profile: UserProfile,
    eligible: list[dict[str, Any]],
    retrieved: list[dict[str, Any]],
    history: str,
    message: str,
    is_first_summary: bool,
    change_note: Optional[str],
) -> str:
    eligible_text = (
        "\n".join(f"- {e['program_name']} [confidence: {e['confidence']}]: {e['reason']}" for e in eligible)
        or "None identified yet."
    )
    retrieved_text = (
        "\n".join(
            f"- {r.get('program_name', 'Unknown')} [confidence: informational]: "
            f"{r.get('description', '')} ({r.get('official_url', '')})"
            for r in retrieved
        )
        or "None found."
    )

    task_instruction = (
        "This is the FIRST message after completing the survey — give a clear, "
        "complete, and DETAILED summary of what the user is eligible for and why, "
        "following the DEPTH AND TONE and FORMATTING instructions above."
        if is_first_summary
        else "This is a FOLLOW-UP message in an ongoing conversation — answer the "
        "user's specific question directly and thoroughly. Do not re-list everything "
        "again unless they explicitly ask for the full summary again."
    )

    change_block = f"\nIMPORTANT UPDATE: {change_note}\n" if change_note else ""

    return f"""{SYSTEM_INSTRUCTIONS}

USER PROFILE:
- Employment: {profile.employment_status}
- Marital status: {profile.marital_status}
- Province: {profile.province}
- Residency status: {profile.residency_status}
- Student: {profile.student}
- Children: {profile.children}
- Income: {profile.income}
- Disability: {profile.disability}
- Senior: {profile.senior}
- Veteran: {profile.veteran_status}
- Indigenous: {profile.indigenous_status}
- Housing problem: {profile.housing_problem}

ELIGIBLE PROGRAMS (confirmed by rules engine):
{eligible_text}

RELATED PROGRAMS (from search, informational only):
{retrieved_text}
{change_block}
CONVERSATION HISTORY:
{history}

TASK: {task_instruction}

LATEST USER MESSAGE:
{message}

Respond in the same language as the user's message."""


def _generate_suggested_questions(
    answer_text: str, eligible: list[dict[str, Any]], language_hint: str
) -> list[str]:
    """
    Ask the LLM for 3 short, natural follow-up questions the user might
    want to ask next, based on the answer just given.
    """
    program_names = ", ".join(e["program_name"] for e in eligible) or "general benefits"

    prompt = f"""Based on this assistant answer about Canadian benefits, suggest exactly \
3 short, natural follow-up questions a user might reasonably ask next. Keep each under \
12 words. Write them in the SAME language as this text: "{language_hint}".

Relevant programs: {program_names}

Assistant's last answer:
\"\"\"{answer_text}\"\"\"

Respond with ONLY a JSON object, no other text, in this exact shape:
{{"questions": ["...", "...", "..."]}}"""

    raw = generate_response(prompt, temperature=0.3, max_tokens=SUGGESTIONS_MAX_TOKENS)

    try:
        cleaned = (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        parsed = json.loads(cleaned)
        questions = parsed.get("questions", [])
        return [q for q in questions if isinstance(q, str)][:3]
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Could not parse suggested questions output: %r", raw)
        return []


def _log_conversation(user_id: str, message: str, response: str) -> None:
    db = SessionLocal()
    try:
        db.add(Conversation(user_id=user_id, user_message=message, assistant_response=response))
        db.commit()
    except Exception:
        logger.exception("Failed to log conversation for user_id=%s", user_id)
        db.rollback()
    finally:
        db.close()


def _apply_answer(
    memory: dict[str, Any],
    field: str,
    selected_option: Optional[str],
    free_text: Optional[str],
) -> None:
    question_def = get_question_by_field(field)
    value_map = question_def["value_map"] if question_def else {}

    if selected_option and selected_option in value_map:
        value = value_map[selected_option]
    else:
        text = free_text or selected_option or ""
        value = extract_other_answer(field, text)

    if value is not None:
        memory[field] = {"value": value, "asked": True}
    else:
        logger.warning("Could not resolve a value for field=%s from input.", field)


def ask_agent(
    user_id: str,
    message: Optional[str] = None,
    selected_option: Optional[str] = None,
) -> dict[str, Any]:
    memory = get_memory(user_id)
    pending_field = memory.get("current_question")

    if pending_field:
        _apply_answer(memory, pending_field, selected_option, message)
        save_memory(user_id, memory)

    next_question = get_next_question(memory)

    if next_question:
        memory["current_question"] = next_question["field"]
        save_memory(user_id, memory)
        if message != "start":
            _log_conversation(user_id, message or selected_option or "", next_question["question"])
        
        return {
            "type": "question",
            "text": next_question["question"],
            "options": next_question["options"],
            "suggestions": [],
        }

    is_first_summary = not memory.get("eligibility_summary_given", False)
    memory["current_question"] = None
    memory["eligibility_summary_given"] = True

    change_note = None
    if message and not is_first_summary:
        change_update = detect_change(message, memory)
        if change_update:
            before = memory.get("last_known_eligibility", [])
            for field, value in change_update.items():
                memory[field] = {"value": value, "asked": True}

            profile_after = UserProfile.from_memory_dict(memory)
            after = evaluate_eligibility(profile_after)
            diff = diff_eligibility(before, after)

            if diff["gained"] or diff["lost"]:
                parts = []
                if diff["gained"]:
                    parts.append(f"newly eligible for: {', '.join(diff['gained'])}")
                if diff["lost"]:
                    parts.append(f"no longer eligible for: {', '.join(diff['lost'])}")
                change_note = "The user just reported a change in circumstances. Based on this, they are " + "; ".join(parts) + ". Clearly highlight this change to them."

    profile = UserProfile.from_memory_dict(memory)
    eligible = evaluate_eligibility(profile)
    memory["last_known_eligibility"] = eligible
    save_memory(user_id, memory)

    history = _get_recent_history(user_id)
    user_message = message or "Please summarize what benefits I qualify for."
    retrieved = search_benefits(user_message)

    prompt = _build_prompt(
        profile, eligible, retrieved, history, user_message, is_first_summary, change_note
    )
    answer = generate_response(prompt, temperature=0.5, max_tokens=MAIN_ANSWER_MAX_TOKENS)

    suggestions = _generate_suggested_questions(answer, eligible, language_hint=user_message)

    _log_conversation(user_id, user_message, answer)
    return {"type": "answer", "text": answer, "options": None, "suggestions": suggestions}