import pytest


async def _auth(client):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_register_agent(client, setup_db):
    headers = await _auth(client)
    response = await client.post("/agents/registry", json={
        "agent_type": "coder",
        "name": "Code Generator",
        "description": "Writes code based on spec",
        "input_schema": {"spec": "string"},
        "output_schema": {"code": "string"},
        "provider": "claude_api",
        "provider_config": {"model": "claude-sonnet-4-6"}
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["agent_type"] == "coder"
    assert data["provider"] == "claude_api"


@pytest.mark.asyncio
async def test_list_agents(client, setup_db):
    headers = await _auth(client)
    await client.post("/agents/registry", json={
        "agent_type": "coder", "name": "Coder", "input_schema": {},
        "output_schema": {}, "provider": "claude_cli", "provider_config": {}
    }, headers=headers)
    await client.post("/agents/registry", json={
        "agent_type": "reviewer", "name": "Reviewer", "input_schema": {},
        "output_schema": {}, "provider": "claude_api", "provider_config": {}
    }, headers=headers)
    response = await client.get("/agents/registry", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_agent_by_type(client, setup_db):
    headers = await _auth(client)
    await client.post("/agents/registry", json={
        "agent_type": "planner", "name": "Planner", "input_schema": {},
        "output_schema": {}, "provider": "claude_api",
        "provider_config": {"model": "claude-sonnet-4-6"}
    }, headers=headers)
    response = await client.get("/agents/registry/planner", headers=headers)
    assert response.status_code == 200
    assert response.json()["agent_type"] == "planner"


@pytest.mark.asyncio
async def test_update_agent_provider(client, setup_db):
    headers = await _auth(client)
    await client.post("/agents/registry", json={
        "agent_type": "coder", "name": "Coder", "input_schema": {},
        "output_schema": {}, "provider": "claude_cli", "provider_config": {}
    }, headers=headers)
    response = await client.patch("/agents/registry/coder", json={
        "provider": "claude_api",
        "provider_config": {"model": "claude-opus-4-7", "api_key": "sk-test"}
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["provider"] == "claude_api"


@pytest.mark.asyncio
async def test_duplicate_agent_type_fails(client, setup_db):
    headers = await _auth(client)
    payload = {"agent_type": "coder", "name": "Coder", "input_schema": {},
               "output_schema": {}, "provider": "claude_cli", "provider_config": {}}
    await client.post("/agents/registry", json=payload, headers=headers)
    response = await client.post("/agents/registry", json=payload, headers=headers)
    assert response.status_code == 409
