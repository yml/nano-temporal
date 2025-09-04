from unittest.mock import Mock, patch
import uuid
from typing import Type

import pytest
from temporalio.client import Client
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin,TestModelProvider

from workflows.hello_world_workflow import (
    HelloWorldAgent,
    HelloWorldWorkflowInput,
    HelloWorldWorkflowOutput,
)
from temporalio.worker import UnsandboxedWorkflowRunner, Worker
from tests.openai_helper import StaticFakeModel, ResponseBuilders




class FakeHelloModel(StaticFakeModel):
    responses = [ResponseBuilders.output_message("llm expected output")]

def new_openai_temporal_client(temporal_client: Client, test_model_class: Type[StaticFakeModel]) -> Client:
    """Create a new Temporal client with OpenAIAgentsPlugin using the provided test model class.
    """
    new_config = temporal_client.config()
    new_config["plugins"] = [
        OpenAIAgentsPlugin(model_provider=TestModelProvider(test_model_class()))
    ]
    return Client(**new_config)


class TestWithLocalWorkflow:
    @pytest.mark.asyncio
    async def test_workflow_execution(self, temporal_client):
        client = new_openai_temporal_client(temporal_client, FakeHelloModel)
        task_queue = str(uuid.uuid4())

        async with Worker(
            client,
            task_queue=task_queue,
            workflows=[HelloWorldAgent],
            workflow_runner=UnsandboxedWorkflowRunner(),
            debug_mode=True,
        ):
            result = await temporal_client.execute_workflow(
                HelloWorldAgent,
                HelloWorldWorkflowInput(prompt="Test"),
                id=f"hello-world-{uuid.uuid4()}",
                task_queue=task_queue,
            )
        assert result == HelloWorldWorkflowOutput(response="llm expected output")



class TestHelloWorldAgent:
    @pytest.mark.asyncio
    async def test_error_handling(self):
        with (
            patch("agents.Agent") as mock_agent_class,
            patch("agents.Runner.run") as mock_runner_run,
        ):
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            # Test Runner.run raising an exception
            mock_runner_run.side_effect = Exception("Agent execution failed")

            agent = HelloWorldAgent()
            workflow_input = HelloWorldWorkflowInput(prompt="Test")

            with pytest.raises(Exception, match="Agent execution failed"):
                await agent.run(workflow_input)


