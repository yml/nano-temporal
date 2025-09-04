from typing import AsyncGenerator
import logging

import pytest_asyncio
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment


from web import app


def pytest_configure():
    """
    Load nanodjango project and make sure the ninja routes are mounted.
    """
    # Suppress openai.agents warnings
    logging.getLogger("openai.agents").setLevel(logging.ERROR)
    app._prepare(is_prod=False)


def pytest_addoption(parser):
    parser.addoption(
        "--workflow-environment",
        default="local",
        help="Which workflow environment to use ('local', 'time-skipping', or target to existing server)",
    )


@pytest_asyncio.fixture(scope="session")
async def workflow_env(request) -> AsyncGenerator[WorkflowEnvironment, None]:
    env_type = request.config.getoption("--workflow-environment")
    if env_type == "local":
        env = await WorkflowEnvironment.start_local(
            dev_server_extra_args=[
                "--dynamic-config-value",
                "frontend.enableExecuteMultiOperation=true",
            ]
        )
    elif env_type == "time-skipping":
        env = await WorkflowEnvironment.start_time_skipping()
    else:
        env = WorkflowEnvironment.from_client(await Client.connect(env_type))
    yield env
    await env.shutdown()


@pytest_asyncio.fixture
async def temporal_client(workflow_env: WorkflowEnvironment) -> Client:
    return workflow_env.client