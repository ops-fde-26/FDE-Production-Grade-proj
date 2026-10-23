from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime

from app.database import Base


class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="new chat")
    created_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
    )