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
async def test_list_runs_empty(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    response = await client.get(f"/runs?workflow_id={wf['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_runs_after_trigger(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish"):
        await client.post("/runs/trigger", json={
            "workflow_id": wf["id"], "trigger_payload": {}
        }, headers=headers)

    response = await client.get(f"/runs?workflow_id={wf['id']}", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "running"


@pytest.mark.asyncio
async def test_get_run_stages(client, setup_db):
    headers = await _auth(client)
    wf = (await client.post("/workflows", json={"name": "SDLC", "trigger": {}}, headers=headers)).json()
    await client.post(f"/workflows/{wf['id']}/stages", json={
        "name": "Planning", "order": 1, "executor_type": "agent", "config": {}
    }, headers=headers)
    await client.post(f"/workflows/{wf['id']}/publish", headers=headers)

    with patch("src.engine.engine.publish"):
        run = (await client.post("/runs/trigger", json={
            "workflow_id": wf["id"], "trigger_payload": {}
        }, headers=headers)).json()

    response = await client.get(f"/runs/{run['id']}/stages", headers=headers)
    assert response.status_code == 200
    stages = response.json()
    assert len(stages) == 1
    assert stages[0]["status"] == "running"
