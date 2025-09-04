import pytest
from uuid import UUID
from unittest.mock import patch, AsyncMock

from run_hello_world_workflow import main
from workflows.hello_world_workflow import (
    HelloWorldWorkflowInput,
    HelloWorldWorkflowOutput,
)


class TestMainFunction:
    @pytest.mark.asyncio
    async def test_main_client_connection(self):
        with patch("temporalio.client.Client.connect") as mock_connect:
            mock_client = AsyncMock()
            mock_client.execute_workflow.return_value = HelloWorldWorkflowOutput(
                response="A gentle breeze flows,\nWindsurfing blue board so free,\nOcean meets the sky."
            )
            mock_connect.return_value = mock_client

            await main()

            # Verify client connection
            mock_connect.assert_called_once()
            args, kwargs = mock_connect.call_args
            assert args[0] == "localhost:7233"
            assert "plugins" in kwargs
            assert len(kwargs["plugins"]) == 1

    @pytest.mark.asyncio
    async def test_main_workflow_execution(self):
        with patch("temporalio.client.Client.connect") as mock_connect:
            mock_client = AsyncMock()
            expected_result = HelloWorldWorkflowOutput(
                response="Windsurfing board blue,\nDancing with ocean's rhythm,\nFreedom on the waves."
            )
            mock_client.execute_workflow.return_value = expected_result
            mock_connect.return_value = mock_client

            await main()

            # Verify workflow execution
            mock_client.execute_workflow.assert_called_once()
            args, kwargs = mock_client.execute_workflow.call_args

            # Check workflow function
            from workflows.hello_world_workflow import HelloWorldAgent

            assert args[0] == HelloWorldAgent.run

            # Check workflow input
            workflow_input = args[1]
            assert isinstance(workflow_input, HelloWorldWorkflowInput)
            assert workflow_input.prompt == "Tell me about windsurfing a blue board."

            # Check workflow ID format
            workflow_id = kwargs["id"]
            assert workflow_id.startswith("hello-world-workflow-")
            # Verify UUID part is valid
            uuid_part = workflow_id.replace("hello-world-workflow-", "")
            UUID(uuid_part)  # This will raise ValueError if not a valid UUID

            # Check task queue
            assert kwargs["task_queue"] == "openai-agents-basic-task-queue-v2"

    @pytest.mark.asyncio
    async def test_main_result_output(self, capsys):
        with patch("temporalio.client.Client.connect") as mock_connect:
            mock_client = AsyncMock()
            expected_result = HelloWorldWorkflowOutput(
                response="Blue board cuts waves,\nWind whispers secrets of sea,\nSpirit soars on high."
            )
            mock_client.execute_workflow.return_value = expected_result
            mock_connect.return_value = mock_client

            await main()

            # Capture printed output
            captured = capsys.readouterr()
            assert f"Result: {expected_result}" in captured.out

    @pytest.mark.asyncio
    async def test_main_openai_agents_plugin(self):
        with patch("temporalio.client.Client.connect") as mock_connect:
            mock_client = AsyncMock()
            mock_client.execute_workflow.return_value = HelloWorldWorkflowOutput(
                response="Test response"
            )
            mock_connect.return_value = mock_client

            await main()

            # Check OpenAIAgentsPlugin configuration
            args, kwargs = mock_connect.call_args
            plugin = kwargs["plugins"][0]

            from temporalio.contrib.openai_agents import OpenAIAgentsPlugin

            assert isinstance(plugin, OpenAIAgentsPlugin)

    @pytest.mark.asyncio
    async def test_main_with_connection_error(self):
        with patch("temporalio.client.Client.connect") as mock_connect:
            mock_connect.side_effect = ConnectionError(
                "Failed to connect to Temporal server"
            )

            with pytest.raises(ConnectionError):
                await main()

    @pytest.mark.asyncio
    async def test_main_with_workflow_execution_error(self):
        with patch("temporalio.client.Client.connect") as mock_connect:
            mock_client = AsyncMock()
            mock_client.execute_workflow.side_effect = Exception(
                "Workflow execution failed"
            )
            mock_connect.return_value = mock_client

            with pytest.raises(Exception, match="Workflow execution failed"):
                await main()


class TestWorkflowInput:
    def test_workflow_input_creation(self):
        workflow_input = HelloWorldWorkflowInput(
            prompt="Tell me about windsurfing a blue board."
        )

        assert workflow_input.prompt == "Tell me about windsurfing a blue board."
        assert isinstance(workflow_input, HelloWorldWorkflowInput)

    def test_workflow_input_validation(self):
        # Test that the input matches what's used in main()
        expected_prompt = "Tell me about windsurfing a blue board."
        workflow_input = HelloWorldWorkflowInput(prompt=expected_prompt)

        assert workflow_input.prompt == expected_prompt


class TestImports:
    def test_required_imports(self):
        # Test that all required modules can be imported
        import asyncio
        from uuid import uuid4
        from temporalio.client import Client
        from temporalio.contrib.openai_agents import OpenAIAgentsPlugin
        from workflows.hello_world_workflow import (
            HelloWorldAgent,
            HelloWorldWorkflowInput,
        )

        assert asyncio is not None
        assert uuid4 is not None
        assert Client is not None
        assert OpenAIAgentsPlugin is not None
        assert HelloWorldAgent is not None
        assert HelloWorldWorkflowInput is not None

    def test_hello_world_workflow_import(self):
        from workflows.hello_world_workflow import (
            HelloWorldAgent,
            HelloWorldWorkflowInput,
        )

        assert hasattr(HelloWorldAgent, "run")
        assert HelloWorldWorkflowInput is not None

    def test_temporal_client_import(self):
        from temporalio.client import Client

        assert hasattr(Client, "connect")
        assert hasattr(Client, "execute_workflow")




class TestUUIDGeneration:
    def test_uuid_generation_uniqueness(self):
        from uuid import uuid4

        # Generate multiple UUIDs to ensure uniqueness
        uuids = [str(uuid4()) for _ in range(10)]
        assert len(set(uuids)) == 10  # All should be unique

    def test_workflow_id_format(self):
        from uuid import uuid4

        # Test the workflow ID format used in main()
        uuid_str = str(uuid4())
        workflow_id = f"hello-world-workflow-{uuid_str}"

        assert workflow_id.startswith("hello-world-workflow-")
        assert len(workflow_id) > len("hello-world-workflow-")

        # Verify UUID part is extractable and valid
        uuid_part = workflow_id.replace("hello-world-workflow-", "")
        UUID(uuid_part)  # Should not raise


class TestConfiguration:
    def test_temporal_server_address(self):
        # Verify the server address matches other configurations
        server_address = "localhost:7233"

        # This should match the configuration in other files
        from web import TEMPORAL_TARGET

        assert TEMPORAL_TARGET == server_address

    def test_task_queue_name(self):
        # Verify the task queue name matches other configurations
        task_queue = "openai-agents-basic-task-queue-v2"

        # This should match the TASK_QUEUE in web.py
        from web import TASK_QUEUE

        assert TASK_QUEUE == task_queue

    def test_workflow_prompt_content(self):
        # Test that the prompt used is appropriate and matches expectations
        prompt = "Tell me about windsurfing a blue board."

        assert "windsurfing" in prompt
        assert "blue board" in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 0
