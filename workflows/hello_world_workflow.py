from dataclasses import dataclass

from agents import Agent, Runner, RunConfig
from agents.models.openai_provider import OpenAIProvider
from temporalio import workflow
from agents.models.interface import ModelProvider

from workflows.registry import WorkflowInfo


@dataclass
class HelloWorldWorkflowInput:
    prompt: str


@dataclass
class HelloWorldWorkflowOutput:
    response: str


@workflow.defn
class HelloWorldAgent:
    @staticmethod
    async def get_model_provider() -> ModelProvider:
        print("Getting model provider")
        return OpenAIProvider()

    @workflow.run
    async def run(
        self, workflow_input: HelloWorldWorkflowInput
    ) -> HelloWorldWorkflowOutput:
        agent = Agent(
            name="Assistant",
            instructions="You only respond in haikus.",
        )
        model_provider = await HelloWorldAgent.get_model_provider()
        run_config = RunConfig(model_provider=model_provider)
        result = await Runner.run(
            agent, input=workflow_input.prompt, run_config=run_config
        )
        return HelloWorldWorkflowOutput(response=result.final_output)


hello_world_workflow_info = WorkflowInfo(
    input=HelloWorldWorkflowInput,
    output=HelloWorldWorkflowOutput,
    workflow=HelloWorldAgent,
)
