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
async def test_create_workflow(client, setup_db):
    headers = await _auth(client)
    response = await client.post("/workflows", json={
        "name": "Full SDLC",
        "trigger": {"source": "linear", "event": "status.tb_ready"}
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Full SDLC"
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_workflows(client, setup_db):
    headers = await _auth(client)
    await client.post("/workflows", json={"name": "WF1", "trigger": {}}, headers=headers)
    await client.post("/workflows", json={"name": "WF2", "trigger": {}}, headers=headers)
    response = await client.get("/workflows", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_add_stage_to_workflow(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    response = await client.post(f"/workflows/{wf['id']}/stages", json={
        "name": "Planning", "order": 1, "executor_type": "agent", "config": {}
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Planning"


@pytest.mark.asyncio
async def test_add_substep_to_stage(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    stage = (await client.post(f"/workflows/{wf['id']}/stages", json={
        "name": "Code Gen", "order": 1, "executor_type": "agent", "config": {}
    }, headers=headers)).json()
    response = await client.post(f"/stages/{stage['id']}/substeps", json={
        "name": "Generate code",
        "order": 1,
        "executor_type": "agent",
        "agent_conversation_config": {
            "participants": ["coder", "reviewer"],
            "initiator": "coder",
            "termination": {"condition": "reviewer_approves", "max_turns": 5}
        }
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Generate code"


@pytest.mark.asyncio
async def test_publish_workflow(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    response = await client.post(f"/workflows/{wf['id']}/publish", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "active"
