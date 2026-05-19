from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.workflows import service
from src.workflows.schemas import (
    WorkflowCreate, WorkflowResponse,
    StageCreate, StageResponse,
    SubStepCreate, SubStepResponse,
)

router = APIRouter()

@router.post("/workflows", status_code=201, response_model=WorkflowResponse)
def create_workflow(body: WorkflowCreate, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    wf = service.create_workflow(db, str(user.id), body.name, body.trigger)
    return {**wf.__dict__, "trigger": wf.config.get("trigger", {})}

@router.get("/workflows", response_model=list[WorkflowResponse])
def list_workflows(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wfs = service.list_workflows(db, str(user.id))
    return [{**w.__dict__, "trigger": w.config.get("trigger", {})} for w in wfs]

@router.post("/workflows/{workflow_id}/publish", response_model=WorkflowResponse)
def publish_workflow(workflow_id: str, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    wf = service.publish_workflow(db, workflow_id, str(user.id))
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {**wf.__dict__, "trigger": wf.config.get("trigger", {})}

@router.post("/workflows/{workflow_id}/stages", status_code=201, response_model=StageResponse)
def add_stage(workflow_id: str, body: StageCreate, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    wf = service.get_workflow(db, workflow_id, str(user.id))
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return service.add_stage(db, workflow_id, body.name, body.order,
                              body.executor_type, body.gate_type, body.config)

@router.get("/workflows/{workflow_id}/stages", response_model=list[StageResponse])
def list_stages(workflow_id: str, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    return service.get_stages(db, workflow_id)

@router.post("/stages/{stage_id}/substeps", status_code=201, response_model=SubStepResponse)
def add_sub_step(stage_id: str, body: SubStepCreate, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    return service.add_sub_step(
        db, stage_id, body.name, body.order, body.executor_type,
        body.agent_conversation_config, body.on_complete, body.on_reject,
    )

@router.get("/stages/{stage_id}/substeps", response_model=list[SubStepResponse])
def list_sub_steps(stage_id: str, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return service.get_sub_steps(db, stage_id)
