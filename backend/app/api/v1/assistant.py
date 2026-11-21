"""
API v1 AI Financial Assistant Router
Grounded natural language interface for financial intelligence queries.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.db import get_db
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.services.ai_assistant import AIAssistantService

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Natural language question about user's financial mandates")

class ChatResponse(BaseModel):
    query: str
    intent: str
    answer: str
    structured_data: Dict[str, Any]
    citations: List[str]

@router.get("/suggested-prompts")
def get_suggested_prompts():
    """
    Returns curated one-click questions for the AI Financial Assistant chat interface.
    """
    return {
        "prompts": [
            "How much do I spend on subscriptions?",
            "What payments are due next month?",
            "Which subscriptions have increased in price?",
            "Show all recurring payments above ₹500",
            "Which subscriptions might I have forgotten?",
            "Identify potentially duplicate payments",
            "How do I cancel Netflix?"
        ]
    }

@router.post("/chat", response_model=ChatResponse)
def assistant_chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a user query to the AI Assistant. Answers are strictly grounded in verified ledger data.
    """
    result = AIAssistantService.process_query(
        query=payload.message,
        user_id=user.id,
        db=db
    )
    return {
        "query": payload.message,
        "intent": result["intent"],
        "answer": result["answer"],
        "structured_data": result["structured_data"],
        "citations": result["citations"]
    }

