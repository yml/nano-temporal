from datetime import datetime
import logging
import os
import sys
from typing import List, Optional

from django.db import models
from django.http import HttpResponse
from nanodjango import Django
from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin

from workflows.hello_world_workflow import hello_world_workflow_info
from workflows import get_registry

# Set up logging for async diagnostics
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)


# --- Temporal client  ---------------------------------
TEMPORAL_TARGET = os.getenv("TEMPORAL_TARGET", "localhost:7233")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "openai-agents-basic-task-queue-v2")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))


async def get_temporal_client() -> Client:
    return await Client.connect(TEMPORAL_TARGET, plugins=[OpenAIAgentsPlugin()])


# --- Django app setup -----------------------------------------------------------

app = Django(
    ADMIN_URL="wall-garden/",
    ALLOWED_HOSTS=["*"],
    DEBUG=True,
    NINJA_DEFAULT_THROTTLE_RATES={"anon": "5/minute"},
)

# initialize the workflow registry
registry = get_registry()


@app.admin(
    list_display=("workflow_path", "handle_id", "created_at"),
    list_filter=("workflow_path", "handle_id"),
)
class WorkflowRun(models.Model):
    workflow_path = models.CharField(max_length=255, db_index=True)
    handle_id = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("workflow_path", "handle_id")]


class WorkflowRunInput(app.ninja.Schema):
    workflow_path: str
    payload: dict


class WorkflowRunOutput(app.ninja.Schema):
    id: int
    workflow_path: str
    handle_id: str
    created_at: datetime


class WorkflowRunDescribeOutput(app.ninja.Schema):
    workflow_path: str
    handle_id: str
    run_id: str
    status: str
    result_payload: Optional[dict]
    created_at: datetime


@app.route("/")
async def index(request):
    return app.render(request, "index.html", {"title": "Home"})


@app.api.get(
    "/workflow_runs", response=List[WorkflowRunOutput], url_name="workflow_runs"
)
def get_workflow_runs(request):
    return WorkflowRun.objects.all()


@app.api.post("/workflow_runs", url_name="create_workflow_run")
async def create_workflow_run(request, workflow_run: WorkflowRunInput):
    client = await get_temporal_client()
    workflow_info = registry.get_by_import_path(workflow_run.workflow_path)
    workflow_input = workflow_info.input(**workflow_run.payload)
    handle = await client.start_workflow(
        workflow_info.workflow.run,
        workflow_input,
        id=f"{workflow_run.workflow_path}-{datetime.utcnow().isoformat()}",
        task_queue=TASK_QUEUE,
    )
    rec_workflow_run = await WorkflowRun.objects.acreate(
        workflow_path=workflow_run.workflow_path,
        handle_id=handle.id,
    )
    return WorkflowRunOutput.from_orm(rec_workflow_run)


@app.api.get("/workflow_runs/{id}", url_name="describe_workflow_run")
async def describe_workflow_run(request, id: str):
    try:
        workflow_run = await WorkflowRun.objects.aget(id=id)
    except WorkflowRun.DoesNotExist:
        return HttpResponse("Not Found", status=404)
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_run.handle_id)
    desc = await handle.describe()

    if desc.status == WorkflowExecutionStatus.COMPLETED:
        result_payload = await handle.result()
    else:
        result_payload = None
    return WorkflowRunDescribeOutput(
        handle_id=desc.id,
        workflow_path=workflow_run.workflow_path,
        run_id=desc.run_id,
        status=desc.status.name,
        result_payload=result_payload,
        created_at=desc.start_time,
    )
