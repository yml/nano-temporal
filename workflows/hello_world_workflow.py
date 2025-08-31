import asyncio
from agents import Agent, Runner
from temporalio import workflow


@workflow.defn
class HelloWorldAgent:
    @workflow.run
    async def run(self, prompt: str) -> str:
        await asyncio.sleep(60)
        agent = Agent(
            name="Assistant",
            instructions="You only respond in haikus.",
        )

        result = await Runner.run(agent, input=prompt)
        return result.final_output
