import uuid
from datetime import timedelta
from typing import Type
from unittest.mock import Mock, patch

import pytest
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.contrib.openai_agents import (
    ModelActivityParameters,
    OpenAIAgentsPlugin,
    TestModelProvider,
)
from temporalio.worker import UnsandboxedWorkflowRunner, Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner

from tests.openai_helper import ResponseBuilders, StaticFakeModel
from workflows import get_registry

registry = get_registry()
lifecycle_workflow_info = registry.get_by_import_path("workflows.lifecycle_workflow")
agent_lifecycle_workflow_info = registry.get_by_import_path(
    "workflows.agent_lifecycle_workflow"
)


class FakeLifecycleModel(StaticFakeModel):
    responses = [
        ResponseBuilders.tool_call('{"number": 2}', "random_number"),
        ResponseBuilders.output_message('{"number":4}'),
    ]


def new_openai_temporal_client(
    temporal_client: Client, test_model_class: Type[StaticFakeModel]
) -> Client:
    """Create a new Temporal client with OpenAIAgentsPlugin using the provided test model class."""
    new_config = temporal_client.config()
    new_config["plugins"] = [
        OpenAIAgentsPlugin(
            model_provider=TestModelProvider(test_model_class()),
            model_params=ModelActivityParameters(
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            ),
        )
    ]
    return Client(**new_config)


class TestWithLocalWorkflow:
    @pytest.mark.parametrize(
        "workflow_info", [lifecycle_workflow_info, agent_lifecycle_workflow_info]
    )
    @pytest.mark.asyncio
    async def test_workflow_execution(self, temporal_client, workflow_info):
        client = new_openai_temporal_client(temporal_client, FakeLifecycleModel)
        task_queue = str(uuid.uuid4())

        async with Worker(
            client,
            task_queue=task_queue,
            workflows=[workflow_info.workflow],
            workflow_runner=SandboxedWorkflowRunner(),
            unsandboxed_workflow_runner=UnsandboxedWorkflowRunner(),
            debug_mode=True,
        ):
            result = await temporal_client.execute_workflow(
                workflow_info.workflow,
                workflow_info.input(max_number=1),
                id=f"lifecycle-workflow-{uuid.uuid4()}",
                task_queue=task_queue,
            )
        assert result == workflow_info.output(**{"number": 4})


class TestHelloWorldAgent:
    @pytest.mark.parametrize(
        "workflow_info", [lifecycle_workflow_info, agent_lifecycle_workflow_info]
    )
    @pytest.mark.asyncio
    async def test_error_handling(self, workflow_info):
        with (
            patch("agents.Agent") as mock_agent_class,
            patch("agents.Runner.run") as mock_runner_run,
        ):
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            # Test Runner.run raising an exception
            mock_runner_run.side_effect = Exception("Agent execution failed")

            workflow = workflow_info.workflow()
            workflow_input = workflow_info.input(max_number=5)

            with pytest.raises(Exception, match="Agent execution failed"):
                await workflow.run(workflow_input)
