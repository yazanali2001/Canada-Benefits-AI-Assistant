"""
Thin wrapper around the Groq API.
All Groq-specific code lives here — nowhere else in the app should
import the `groq` package directly.
"""

import logging
from groq import Groq, GroqError

from backend.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

_client = Groq(api_key=GROQ_API_KEY)

FALLBACK_MESSAGE = (
    "Sorry, I'm having trouble reaching the AI service right now. "
    "Please try again in a moment."
)

DEFAULT_MAX_TOKENS = 1800  # raised from 800 so detailed, multi-program
                            # explanations don't get cut off mid-answer


def generate_response(
    prompt: str, temperature: float = 0.3, max_tokens: int = DEFAULT_MAX_TOKENS
) -> str:
    """
    Send a prompt to Groq's chat completion endpoint and return the
    generated text.

    Args:
        prompt: The full prompt (system + context + user message).
        temperature: Lower = more deterministic/factual answers.
        max_tokens: Hard cap on the reply length. Kept generous by
            default for detailed eligibility explanations that may
            cover multiple programs — a short structured-extraction
            call (see extraction_llm.py) can pass a much smaller
            value instead.

    Returns:
        The model's reply, or a safe fallback message on failure —
        this function never raises, so the agent can always
        return *something* to the user.
    """
    try:
        completion = _client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content

    except GroqError:
        logger.exception("Groq API returned an error.")
        return FALLBACK_MESSAGE
    except Exception:
        logger.exception("Unexpected error calling Groq.")
        return FALLBACK_MESSAGE