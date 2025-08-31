
import pytest


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Temporal" in response.text

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_create_workflow_run(async_client):
    response = await async_client.post(
        "/api/workflow_runs",
        {
            "workflow_type": "hello_world",
            "payload": {"prompt": "Hello, world!"}
        },
        content_type="application/json")
    assert response.status_code == 200
    assert "id" in response.json()