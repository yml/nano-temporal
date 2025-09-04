import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from temporalio.client import WorkflowExecutionStatus

from web import WorkflowRun, get_temporal_client, WorkflowRunInput, WorkflowRunOutput


class TestWebApp:
    def test_index(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "Temporal" in response.text

    @pytest.mark.django_db
    def test_get_workflow_runs_empty(self, client):
        response = client.get("/api/workflow_runs")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.django_db
    def test_get_workflow_runs_with_data(self, client):
        WorkflowRun.objects.create(
            workflow_type="test_workflow", handle_id="test-handle-123"
        )
        response = client.get("/api/workflow_runs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["workflow_type"] == "test_workflow"
        assert data[0]["handle_id"] == "test-handle-123"

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_create_workflow_run_success(self, async_client):
        mock_handle = Mock()
        mock_handle.id = "workflow-handle-123"
        mock_desc = Mock()
        mock_desc.workflow_type = "HelloWorldAgent"
        mock_handle.describe = AsyncMock(return_value=mock_desc)

        with patch("web.get_temporal_client") as mock_client:
            mock_temporal_client = AsyncMock()
            mock_temporal_client.start_workflow.return_value = mock_handle
            mock_client.return_value = mock_temporal_client

            response = await async_client.post(
                "/api/workflow_runs",
                {
                    "workflow_type": "hello_world",
                    "payload": {"prompt": "Hello, world!"},
                },
                content_type="application/json",
            )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["workflow_type"] == "HelloWorldAgent"
        assert data["handle_id"] == "workflow-handle-123"

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_create_workflow_run_invalid_payload(self, async_client):
        response = await async_client.post(
            "/api/workflow_runs",
            {
                "workflow_type": "hello_world"
                # Missing required payload
            },
            content_type="application/json",
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_describe_workflow_run_success(self, async_client):
        workflow_run = await WorkflowRun.objects.acreate(
            workflow_type="test_workflow_success", handle_id="test-handle-success-123"
        )

        mock_handle = Mock()
        mock_desc = Mock()
        mock_desc.id = "test-handle-success-123"
        mock_desc.workflow_type = "TestWorkflow"
        mock_desc.run_id = "run-123"
        mock_desc.status = WorkflowExecutionStatus.COMPLETED
        mock_desc.start_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_handle.describe = AsyncMock(return_value=mock_desc)
        mock_handle.result = AsyncMock(return_value={"result": "success"})

        with patch("web.get_temporal_client") as mock_client:
            mock_temporal_client = AsyncMock()
            mock_temporal_client.get_workflow_handle = Mock(return_value=mock_handle)
            mock_client.return_value = mock_temporal_client

            response = await async_client.get(f"/api/workflow_runs/{workflow_run.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["handle_id"] == "test-handle-success-123"
        assert data["workflow_type"] == "TestWorkflow"
        assert data["status"] == "COMPLETED"
        assert data["result_payload"] == {"result": "success"}

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_describe_workflow_run_running(self, async_client):
        workflow_run = await WorkflowRun.objects.acreate(
            workflow_type="test_workflow_running", handle_id="test-handle-running-456"
        )

        mock_handle = Mock()
        mock_desc = Mock()
        mock_desc.id = "test-handle-running-456"
        mock_desc.workflow_type = "TestWorkflow"
        mock_desc.run_id = "run-456"
        mock_desc.status = WorkflowExecutionStatus.RUNNING
        mock_desc.start_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_handle.describe = AsyncMock(return_value=mock_desc)

        with patch("web.get_temporal_client") as mock_client:
            mock_temporal_client = AsyncMock()
            mock_temporal_client.get_workflow_handle = Mock(return_value=mock_handle)
            mock_client.return_value = mock_temporal_client

            response = await async_client.get(f"/api/workflow_runs/{workflow_run.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"
        assert data["result_payload"] is None

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_describe_workflow_run_not_found(self, async_client):
        response = await async_client.get("/api/workflow_runs/999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_temporal_client(self):
        with patch("temporalio.client.Client.connect") as mock_connect:
            mock_client = AsyncMock()
            mock_connect.return_value = mock_client

            client = await get_temporal_client()

            mock_connect.assert_called_once()
            assert client == mock_client


class TestWorkflowRunModel:
    @pytest.mark.django_db
    def test_workflow_run_creation(self):
        workflow_run = WorkflowRun.objects.create(
            workflow_type="test_workflow_model", handle_id="test-handle-model-789"
        )
        assert workflow_run.workflow_type == "test_workflow_model"
        assert workflow_run.handle_id == "test-handle-model-789"
        assert workflow_run.created_at is not None

    @pytest.mark.django_db
    def test_workflow_run_unique_constraint(self):
        WorkflowRun.objects.create(
            workflow_type="test_workflow_unique", handle_id="test-handle-unique-999"
        )

        with pytest.raises(Exception):  # Django IntegrityError
            WorkflowRun.objects.create(
                workflow_type="test_workflow_unique", handle_id="test-handle-unique-999"
            )

    @pytest.mark.django_db
    def test_workflow_run_different_types_same_handle(self):
        WorkflowRun.objects.create(
            workflow_type="workflow_a", handle_id="test-handle-123"
        )

        # This should work - different workflow_type
        workflow_run = WorkflowRun.objects.create(
            workflow_type="workflow_b", handle_id="test-handle-123"
        )
        assert workflow_run.workflow_type == "workflow_b"


class TestSchemas:
    def test_workflow_run_input_validation(self):
        valid_input = WorkflowRunInput(
            workflow_type="hello_world", payload={"prompt": "test"}
        )
        assert valid_input.workflow_type == "hello_world"
        assert valid_input.payload == {"prompt": "test"}

    def test_workflow_run_output_creation(self):
        output = WorkflowRunOutput(
            id=1,
            workflow_type="test_workflow",
            handle_id="handle-123",
            created_at=datetime(2023, 1, 1, 12, 0, 0),
        )
        assert output.id == 1
        assert output.workflow_type == "test_workflow"
