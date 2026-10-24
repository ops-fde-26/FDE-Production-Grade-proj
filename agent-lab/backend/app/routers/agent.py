from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agent

router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentCreate(BaseModel):
    name: str
    instruction: str = "you are helpful assistant"


class AgentOut(BaseModel):
    id: int
    name: str
    instruction: str

    class Config:
        from_attributes = True


@router.post("", response_model=AgentOut)
def create_agent(body: AgentCreate, db: Session = Depends(get_db)):
    row = Agent(name=body.name, instruction=body.instruction)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[AgentOut])
def list_agents(db: Session = Depends(get_db)):
    return db.query(Agent).order_by(Agent.id.desc()).all()
