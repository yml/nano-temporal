from dataclasses import dataclass
from typing import Any

from agents import (
    Agent,
    AgentHooks,
    RunContextWrapper,
    Runner,
    function_tool,
)
from pydantic import BaseModel
from temporalio import workflow

from .registry import WorkflowInfo


class CustomAgentHooks(AgentHooks):
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} started"
        )

    async def on_end(
        self, context: RunContextWrapper, agent: Agent, output: Any
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended with output {output}"
        )

    async def on_handoff(
        self, context: RunContextWrapper, agent: Agent, source: Agent
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {source.name} handed off to {agent.name}"
        )

    async def on_tool_start(
        self, context: RunContextWrapper, agent: Agent, tool
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} started tool {tool.name}"
        )

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool, result: str
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended tool {tool.name} with result {result}"
        )


@function_tool
def random_number(max: int) -> int:
    """Generate a random number up to the provided max."""
    return workflow.random().randint(0, max)


@function_tool
def multiply_by_two(x: int) -> int:
    """Return x times two."""
    return x * 2


@dataclass
class WorkflowInput:
    max_number: int


class FinalResult(BaseModel):
    number: int


@workflow.defn
class AgentLifecycleWorkflow:
    @workflow.run
    async def run(self, workflow_input: WorkflowInput) -> FinalResult:
        multiply_agent = Agent(
            name="Multiply Agent",
            instructions="Multiply the number by 2 and then return the final result.",
            tools=[multiply_by_two],
            output_type=FinalResult,
            hooks=CustomAgentHooks(display_name="Agent"),
        )

        start_agent = Agent(
            name="Start Agent",
            instructions="Generate a random number. If it's even, stop. If it's odd, hand off to the multiplier agent.",
            tools=[random_number],
            output_type=FinalResult,
            handoffs=[multiply_agent],
            hooks=CustomAgentHooks(display_name="Agent"),
        )

        result = await Runner.run(
            start_agent,
            # hooks=hooks,
            input=f"Generate a random number between 0 and {workflow_input.max_number}.",
        )

        print("Done!")
        return result.final_output


agent_lifecycle_workflow_info = WorkflowInfo(
    input=WorkflowInput,
    output=FinalResult,
    workflow=AgentLifecycleWorkflow,
)
