from dataclasses import dataclass

from agents import Agent, Runner
from temporalio import workflow


@dataclass
class HelloWorldWorkflowInput:
    prompt: str

@dataclass
class HelloWorldWorkflowOutput:
    response: str


@workflow.defn
class HelloWorldAgent:
    @workflow.run
    async def run(self, workflow_input: HelloWorldWorkflowInput) -> HelloWorldWorkflowOutput:
        agent = Agent(
            name="Assistant",
            instructions="You only respond in haikus.",
        )

        result = await Runner.run(agent, input=workflow_input.prompt)
        return HelloWorldWorkflowOutput(response=result.final_output)
