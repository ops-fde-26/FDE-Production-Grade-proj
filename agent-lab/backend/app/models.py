from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class Agent(Base):
    __tablename__ = "agent"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    instruction = Column(Text, default="You are a helpful assistant.")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),)



class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String,default="new chat")
    agent_id = Column(Integer, ForeignKey("agent.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("conversation.id"), nullable=False, index=True
    )
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
