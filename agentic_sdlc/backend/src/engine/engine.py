import uuid
from sqlalchemy.orm import Session
from src.models.run import WorkflowRun, StageExecution, RunStatus, ExecutionStatus
from src.models.workflow import Workflow, Stage, WorkflowStatus
from src.kafka.producer import publish
from src.kafka import topics

def trigger_run(db: Session, workflow_id: str, trigger_payload: dict) -> WorkflowRun:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow or workflow.status != WorkflowStatus.active:
        raise ValueError("Workflow not found or not active")

    run = WorkflowRun(
        id=uuid.uuid4(),
        workflow_id=workflow_id,
        trigger_payload=trigger_payload,
        status=RunStatus.running,
    )
    db.add(run)
    db.flush()

    first_stage = (
        db.query(Stage)
        .filter(Stage.workflow_id == workflow_id)
        .order_by(Stage.order)
        .first()
    )

    if first_stage:
        _dispatch_stage(db, run, first_stage, trigger_payload)

    db.commit()
    db.refresh(run)
    return run

def _dispatch_stage(db: Session, run: WorkflowRun, stage: Stage, payload: dict):
    run.current_stage_id = stage.id

    execution = StageExecution(
        id=uuid.uuid4(),
        run_id=run.id,
        stage_id=stage.id,
        executor_type=stage.executor_type,
        status=ExecutionStatus.running,
    )
    db.add(execution)
    db.flush()

    event = {
        "run_id": str(run.id),
        "workflow_id": str(run.workflow_id),
        "stage_id": str(stage.id),
        "stage_execution_id": str(execution.id),
        "executor_type": str(stage.executor_type),
        "payload": payload,
    }

    if str(stage.executor_type) in ("agent", "ExecutorType.agent"):
        publish(topics.AGENT_TASKS, event, key=str(run.id))
    else:
        publish(topics.HUMAN_TASKS, event, key=str(run.id))

    publish(topics.PIPELINE_STATE, {**event, "event": "stage_started"}, key=str(run.id))

def get_run(db: Session, run_id: str) -> WorkflowRun | None:
    return db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()

def list_runs(db: Session, workflow_id: str) -> list[WorkflowRun]:
    return db.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).all()
