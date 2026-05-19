import pytest
from unittest.mock import patch


async def _auth(client):
    await client.post("/auth/register", json={
        "name": "Dev", "email": "dev@example.com", "password": "pass123"
    })
    token = (await client.post("/auth/login", json={
        "email": "dev@example.com", "password": "pass123"
    })).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_trigger_run_creates_run(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish"):
        response = await client.post("/runs/trigger", json={
            "workflow_id": wf["id"],
            "trigger_payload": {"source": "linear", "ticket_id": "ABC-1"}
        }, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["workflow_id"] == wf["id"]
    assert data["status"] == "running"
    assert "id" in data


@pytest.mark.asyncio
async def test_trigger_run_draft_workflow_fails(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()

    response = await client.post("/runs/trigger", json={
        "workflow_id": wf["id"], "trigger_payload": {}
    }, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_run(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish"):
        run = (await client.post("/runs/trigger", json={
            "workflow_id": wf["id"], "trigger_payload": {}
        }, headers=headers)).json()

    response = await client.get(f"/runs/{run['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == run["id"]


@pytest.mark.asyncio
async def test_trigger_publishes_to_kafka_when_stage_exists(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/stages", json={
        "name": "Planning", "order": 1, "executor_type": "agent", "config": {}
    }, headers=headers)
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish") as mock_pub:
        await client.post("/runs/trigger", json={
            "workflow_id": wf["id"], "trigger_payload": {"ticket": "ABC-1"}
        }, headers=headers)
        assert mock_pub.called
        assert mock_pub.call_args_list[0][0][0] == "agent.tasks"
