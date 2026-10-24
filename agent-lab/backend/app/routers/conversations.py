from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str = "new chat"
    agent_id: int | None = None


class ConversationOut(BaseModel):
    id: int
    title: str
    agent_id: int | None = None

    class Config:
        from_attributes = True


@router.post("", response_model=ConversationOut)
def create_conversation(body: ConversationCreate, db: Session = Depends(get_db)):
    row = Conversation(title=body.title, agent_id=body.agent_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.id.desc()).all()
