from sqlalchemy.orm import Session
from src.models.run import WorkflowRun, StageExecution
from src.kafka.consumer import BaseConsumer
from src.kafka import topics
from src.database import SessionLocal


def list_runs(db: Session, workflow_id: str) -> list[WorkflowRun]:
    return db.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).all()


def list_stage_executions(db: Session, run_id: str) -> list[StageExecution]:
    return db.query(StageExecution).filter(StageExecution.run_id == run_id).all()


class PipelineStateConsumer(BaseConsumer):
    topic = topics.PIPELINE_STATE

    def handle(self, message: dict):
        from src.websocket.manager import manager

        db = SessionLocal()
        try:
            run_id = message.get("run_id")
            if not run_id:
                return

            if message.get("event") == "stage_completed":
                run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
                if run:
                    run.status = message.get("run_status", run.status)
                    db.commit()

            manager.broadcast_from_thread({
                "event": message.get("event"),
                "run_id": run_id,
                "stage_id": message.get("stage_id"),
                "stage_execution_id": message.get("stage_execution_id"),
                "executor_type": message.get("executor_type"),
                "run_status": message.get("run_status"),
            })
        finally:
            db.close()
