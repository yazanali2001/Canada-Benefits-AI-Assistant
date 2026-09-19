"""
FastAPI application exposing the Canada Benefits AI agent as an HTTP API.
"""

import logging
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.agent import ask_agent
from backend.database.db import SessionLocal
from backend.database.models import User, Conversation
from backend.memory.store import get_memory, save_memory
from backend.memory.questions import QUESTIONS, get_question_by_field
from backend.llm.extraction_llm import extract_other_answer
from backend.auth.schemas import SignupRequest, LoginRequest, TokenResponse
from backend.auth.security import hash_password, verify_password, create_access_token
from backend.auth.dependencies import get_current_username
from backend.pdf_export import build_summary_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Canada Benefits AI", version="1.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: Optional[str] = None
    selected_option: Optional[str] = None


class ChatResponse(BaseModel):
    type: str
    text: str
    options: Optional[list[str]] = None
    suggestions: Optional[list[str]] = None


class HistoryItem(BaseModel):
    user_message: str
    assistant_response: str
    created_at: str


class ProfileFieldUpdate(BaseModel):
    field: str
    new_option: str
    free_text: Optional[str] = None


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    current_username: str = Depends(get_current_username),
) -> ChatResponse:
    if not req.message and not req.selected_option:
        raise HTTPException(status_code=400, detail="Provide 'message' or 'selected_option'.")
    try:
        result = ask_agent(
            current_username, message=req.message, selected_option=req.selected_option
        )
        return ChatResponse(**result)
    except Exception:
        logger.exception("Unhandled error processing chat for user=%s", current_username)
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")


@app.get("/history", response_model=list[HistoryItem])
def get_history(current_username: str = Depends(get_current_username)) -> list[HistoryItem]:
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(Conversation)
            .filter(Conversation.user_id == current_username)
            .order_by(Conversation.created_at.asc())
            .all()
        )
        return [
            HistoryItem(
                user_message=row.user_message,
                assistant_response=row.assistant_response,
                created_at=row.created_at.isoformat(),
            )
            for row in rows
        ]
    except Exception:
        logger.exception("Failed to fetch history for user=%s", current_username)
        raise HTTPException(status_code=500, detail="Could not load history.")
    finally:
        db.close()


@app.get("/profile")
def get_profile(current_username: str = Depends(get_current_username)) -> dict[str, Any]:
    memory = get_memory(current_username)
    fields = []
    for q in QUESTIONS:
        current_value = memory.get(q["field"], {}).get("value")
        fields.append({
            "field": q["field"],
            "question": q["question"],
            "options": q["options"],
            "current_value": current_value,
        })
    return {"fields": fields}


@app.post("/profile/update")
def update_profile(
    req: ProfileFieldUpdate,
    current_username: str = Depends(get_current_username),
) -> dict[str, str]:
    question_def = get_question_by_field(req.field)
    if question_def is None:
        raise HTTPException(status_code=400, detail=f"Unknown field: {req.field}")

    value_map = question_def["value_map"]
    if req.new_option in value_map:
        value = value_map[req.new_option]
    else:
        value = extract_other_answer(req.field, req.free_text or req.new_option)

    if value is None:
        raise HTTPException(status_code=400, detail="Could not interpret the new answer.")

    memory = get_memory(current_username)
    memory[req.field] = {"value": value, "asked": True}
    save_memory(current_username, memory)

    return {"status": "updated"}


@app.get("/export/pdf")
def export_pdf(current_username: str = Depends(get_current_username)) -> Response:
    db: Session = SessionLocal()
    try:
        last = (
            db.query(Conversation)
            .filter(Conversation.user_id == current_username)
            .order_by(Conversation.created_at.desc())
            .first()
        )
        if not last:
            raise HTTPException(status_code=404, detail="No conversation found yet.")

        pdf_bytes = build_summary_pdf(current_username, last.assistant_response)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=benefits_summary.pdf"},
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("PDF export failed for user=%s", current_username)
        raise HTTPException(status_code=500, detail="Could not generate PDF.")
    finally:
        db.close()


@app.post("/auth/signup", response_model=TokenResponse, status_code=201)
def signup(req: SignupRequest) -> TokenResponse:
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == req.username).first()
        if existing:
            raise HTTPException(status_code=409, detail="Username already taken.")

        user = User(username=req.username, hashed_password=hash_password(req.password))
        db.add(user)
        db.commit()

        token = create_access_token(username=req.username)
        return TokenResponse(access_token=token)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Signup failed for username=%s", req.username)
        db.rollback()
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.")
    finally:
        db.close()


@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest) -> TokenResponse:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == req.username).first()
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect username or password.")

        token = create_access_token(username=req.username)
        return TokenResponse(access_token=token)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Login failed for username=%s", req.username)
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")
    finally:
        db.close()