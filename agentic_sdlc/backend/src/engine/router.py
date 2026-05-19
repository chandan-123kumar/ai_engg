from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.engine import engine
from src.engine.engine import serialize_run

router = APIRouter()

class TriggerRequest(BaseModel):
    workflow_id: str
    trigger_payload: dict = {}

class RunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    trigger_payload: dict

@router.post("/runs/trigger", status_code=201, response_model=RunResponse)
def trigger_run(body: TriggerRequest, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    try:
        run = engine.trigger_run(db, body.workflow_id, body.trigger_payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_run(run)

@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    run = engine.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return serialize_run(run)
