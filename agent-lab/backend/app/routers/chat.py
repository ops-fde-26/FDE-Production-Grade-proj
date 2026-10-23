from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation, Message
from app.services.llm import get_chat_reply

router = APIRouter(prefix="/api/chat", tags=["chats"])


class ChatRequest(BaseModel):
    conversation_id: int
    message: str


class ChatResponse(BaseModel):
    conversation_id: int
    user_message: str
    assistant_message: str


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_db)):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == body.conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, 
        detail="Conversation not found")

    user_message = Message(
        conversation_id=body.conversation_id,
        role="user",
        content=body.message,
    )
    db.add(user_message)

    try:
        reply = get_chat_reply(body.message)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}") from e

    assistant_message = Message(
        conversation_id=body.conversation_id,
        role="assistant",
        content=reply,
    )
    db.add(assistant_message)
    db.commit()

    return ChatResponse(
        conversation_id=body.conversation_id,
        user_message=body.message,
        assistant_message=reply,
    )

   