import uuid
from sqlalchemy.orm import Session
from src.models.workflow import Workflow, Stage, SubStep, WorkflowStatus

def create_workflow(db: Session, user_id: str, name: str, trigger: dict) -> Workflow:
    wf = Workflow(id=uuid.uuid4(), user_id=user_id, name=name, config={"trigger": trigger})
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return wf

def list_workflows(db: Session, user_id: str) -> list[Workflow]:
    return db.query(Workflow).filter(Workflow.user_id == user_id).all()

def get_workflow(db: Session, workflow_id: str, user_id: str) -> Workflow | None:
    return db.query(Workflow).filter(
        Workflow.id == workflow_id, Workflow.user_id == user_id
    ).first()

def publish_workflow(db: Session, workflow_id: str, user_id: str) -> Workflow | None:
    wf = get_workflow(db, workflow_id, user_id)
    if not wf:
        return None
    wf.status = WorkflowStatus.active
    db.commit()
    db.refresh(wf)
    return wf

def add_stage(db: Session, workflow_id: str, name: str, order: int,
              executor_type: str, gate_type: str | None, config: dict) -> Stage:
    stage = Stage(
        id=uuid.uuid4(), workflow_id=workflow_id,
        name=name, order=order, executor_type=executor_type,
        gate_type=gate_type, config=config,
    )
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage

def get_stages(db: Session, workflow_id: str) -> list[Stage]:
    return db.query(Stage).filter(Stage.workflow_id == workflow_id).order_by(Stage.order).all()

def add_sub_step(db: Session, stage_id: str, name: str, order: int, executor_type: str,
                 agent_conversation_config: dict | None, on_complete: str | None,
                 on_reject: str | None) -> SubStep:
    ss = SubStep(
        id=uuid.uuid4(), stage_id=stage_id, name=name, order=order,
        executor_type=executor_type,
        agent_conversation_config=agent_conversation_config,
        on_complete=on_complete, on_reject=on_reject,
    )
    db.add(ss)
    db.commit()
    db.refresh(ss)
    return ss

def get_sub_steps(db: Session, stage_id: str) -> list[SubStep]:
    return db.query(SubStep).filter(SubStep.stage_id == stage_id).order_by(SubStep.order).all()
