from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio.client import Client
from temporalio.contrib.openai_agents import ModelActivityParameters, OpenAIAgentsPlugin


from activities.get_weather_activity import get_weather
from activities.image_activities import read_image_as_base64
from activities.math_activities import (
    multiply_by_two,
    random_number,
)
from workflows.agent_lifecycle_workflow import (
    AgentLifecycleWorkflow,
)
from workflows.dynamic_system_prompt_workflow import (
    DynamicSystemPromptWorkflow,
)
from workflows.hello_world_workflow import HelloWorldAgent
from workflows.lifecycle_workflow import LifecycleWorkflow
from workflows.local_image_workflow import LocalImageWorkflow
from workflows.non_strict_output_workflow import (
    NonStrictOutputWorkflow,
)
from workflows.previous_response_id_workflow import (
    PreviousResponseIdWorkflow,
)
from workflows.remote_image_workflow import RemoteImageWorkflow
from workflows.tools_workflow import ToolsWorkflow
from temporalio.worker import Worker, UnsandboxedWorkflowRunner


async def temporal_worker():
    # Create client connected to server at the given address
    client = await Client.connect(
        "localhost:7233",
        plugins=[
            OpenAIAgentsPlugin(
                model_params=ModelActivityParameters(
                    start_to_close_timeout=timedelta(seconds=30)
                )
            ),
        ],
    )

    worker = Worker(
        client,
        task_queue="openai-agents-basic-task-queue-v2",
        workflows=[
            HelloWorldAgent,
            ToolsWorkflow,
            AgentLifecycleWorkflow,
            DynamicSystemPromptWorkflow,
            NonStrictOutputWorkflow,
            LocalImageWorkflow,
            RemoteImageWorkflow,
            LifecycleWorkflow,
            PreviousResponseIdWorkflow,
        ],
        activities=[
            get_weather,
            multiply_by_two,
            random_number,
            read_image_as_base64,
        ],
        # workflow_runner=UnsandboxedWorkflowRunner(),
        debug_mode=False,
    )
    await worker.run()


if __name__ == "__main__":
    print("Starting temporal worker...")
    asyncio.run(temporal_worker())
