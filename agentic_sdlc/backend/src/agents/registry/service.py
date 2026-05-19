import uuid
from sqlalchemy.orm import Session
from src.models.agent_registry import AgentRegistry


def create_agent(db: Session, agent_type: str, name: str, description: str | None,
                 input_schema: dict, output_schema: dict, endpoint: str | None,
                 provider: str, provider_config: dict) -> AgentRegistry:
    agent = AgentRegistry(
        id=uuid.uuid4(), agent_type=agent_type, name=name,
        description=description, input_schema=input_schema,
        output_schema=output_schema, endpoint=endpoint,
        provider=provider, provider_config=provider_config,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def list_agents(db: Session) -> list[AgentRegistry]:
    return db.query(AgentRegistry).all()


def get_agent(db: Session, agent_type: str) -> AgentRegistry | None:
    return db.query(AgentRegistry).filter(AgentRegistry.agent_type == agent_type).first()


def update_agent(db: Session, agent_type: str, **kwargs) -> AgentRegistry | None:
    agent = get_agent(db, agent_type)
    if not agent:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(agent, key, value)
    db.commit()
    db.refresh(agent)
    return agent
