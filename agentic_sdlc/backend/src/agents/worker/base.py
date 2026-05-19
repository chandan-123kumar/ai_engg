from src.kafka.consumer import BaseConsumer
from src.kafka.producer import publish
from src.kafka import topics
from src.database import SessionLocal
from src.models.agent_registry import AgentRegistry
from src.agents.worker.claude_cli import ClaudeCliProvider
from src.agents.worker.claude_api import ClaudeApiProvider


class AgentWorker(BaseConsumer):
    topic = topics.AGENT_TASKS

    def _get_provider(self, agent: AgentRegistry):
        cfg = agent.provider_config or {}
        if agent.provider == "claude_cli":
            return ClaudeCliProvider(
                cli_path=cfg.get("cli_path", "claude"),
                model=cfg.get("model", "claude-sonnet-4-6"),
            )
        if agent.provider == "claude_api":
            return ClaudeApiProvider(
                api_key=cfg.get("api_key", ""),
                model=cfg.get("model", "claude-sonnet-4-6"),
            )
        raise ValueError(f"Unknown provider: {agent.provider}")

    def handle(self, message: dict):
        db = SessionLocal()
        try:
            agent_type = message.get("agent_type")
            run_id = message.get("run_id")
            stage_execution_id = message.get("stage_execution_id")
            payload = message.get("payload", {})

            agent = db.query(AgentRegistry).filter(
                AgentRegistry.agent_type == agent_type
            ).first()
            if not agent:
                self._publish_failure(run_id, stage_execution_id, f"Unknown agent type: {agent_type}")
                return

            provider = self._get_provider(agent)
            system_prompt = payload.get("system_prompt", f"You are a {agent_type} agent.")
            user_message = payload.get("user_message", "")

            output = provider.call(system_prompt=system_prompt, user_message=user_message)

            publish(topics.AGENT_RESULTS, {
                "run_id": run_id,
                "stage_execution_id": stage_execution_id,
                "agent_type": agent_type,
                "output": output,
                "status": "done",
            }, key=run_id)

        except Exception as e:
            self._publish_failure(run_id, stage_execution_id, str(e))
        finally:
            db.close()

    def _publish_failure(self, run_id: str, stage_execution_id: str, error: str):
        publish(topics.AGENT_RESULTS, {
            "run_id": run_id,
            "stage_execution_id": stage_execution_id,
            "status": "failed",
            "error": error,
        }, key=run_id)
