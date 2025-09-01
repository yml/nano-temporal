import asyncio

from uuid import uuid4
from temporalio.client import Client
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin

from workflows.hello_world_workflow import HelloWorldAgent, HelloWorldWorkflowInput


async def main():
    # Create client connected to server at the given address
    client = await Client.connect(
        "localhost:7233",
        plugins=[
            OpenAIAgentsPlugin(),
        ],
    )

    # Execute a workflow
    result = await client.execute_workflow(
        HelloWorldAgent.run,
        HelloWorldWorkflowInput(prompt="Tell me about windsurfing a blue board."),
        id=f"hello-world-workflow-{uuid4()}",
        task_queue="openai-agents-basic-task-queue-v2",
    )
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
