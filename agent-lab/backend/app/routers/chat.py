from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agent, Conversation, Message
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

    system_prompt = "you are helpful assistant. Use tools to get the information you need."

    if conversation.agent_id:
        agent = db.query(Agent).filter(Agent.id == conversation.agent_id).first()
        if agent:
            system_prompt = agent.instruction

    prior = (
        db.query(Message)
        .filter(Message.conversation_id == body.conversation_id)
        .order_by(Message.id)
        .all()
    )

    db.add(
        Message(
            conversation_id=body.conversation_id,
            role="user",
            content=body.message,
        )
    )

    history = [{"role": m.role, "content": m.content} for m in prior]
    history.append({"role": "user", "content": body.message})

    try:
        reply = get_chat_reply(history, system_prompt=system_prompt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}") from e

    db.add(
        Message(
            conversation_id=body.conversation_id,
            role="assistant",
            content=reply,
        )
    )
    db.commit()

    return ChatResponse(
        conversation_id=body.conversation_id,
        user_message=body.message,
        assistant_message=reply,
    )
