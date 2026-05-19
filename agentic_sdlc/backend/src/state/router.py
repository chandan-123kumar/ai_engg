from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.state import service

router = APIRouter()

@router.get("/runs")
def list_runs(workflow_id: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    runs = service.list_runs(db, workflow_id)
    return [
        {"id": str(r.id), "workflow_id": str(r.workflow_id),
         "status": r.status, "trigger_payload": r.trigger_payload}
        for r in runs
    ]

@router.get("/runs/{run_id}/stages")
def list_run_stages(run_id: str, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    execs = service.list_stage_executions(db, run_id)
    return [
        {"id": str(e.id), "stage_id": str(e.stage_id),
         "executor_type": e.executor_type, "status": e.status}
        for e in execs
    ]
