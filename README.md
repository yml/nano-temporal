# nano-temporal

A Django web application that integrates with Temporal workflows for AI agent orchestration using OpenAI Agents.

The temporal workflows heavily borrow from [temporal samples python GH repo](https://github.com/temporalio/samples-python). Temporal is the [recommended way to run long running or human in the loop](https://github.com/openai/openai-agents-python?tab=readme-ov-file#long-running-agents--human-in-the-loop) in the official `openai-agents-python.

## Features

- **Web API**: RESTful endpoints for managing workflow runs
- **Temporal Integration**: Execute AI agent workflows using Temporal
- **OpenAI Agents**: AI-powered workflows with customizable agents
- **Admin Interface**: Django admin for managing workflow runs
- **Testing Suite**: Comprehensive test coverage with async support

## Tech Stack

- **Backend**: Django (via nanodjango)
- **Workflow Engine**: Temporal
- **AI Framework**: OpenAI Agents
- **Database**: SQLite
- **Testing**: pytest with async support

## Quick Start

### Prerequisites

- Python 3.11.9+
- Temporal server running on `localhost:7233`

### Installation

```bash
# Install dependencies
uv sync

# Start temporal dev server
temporal server start-dev --db-filename=test_temporal.db

# Set OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"
```

### Running the Application

You have two options to run the application:

#### Option 1: All-in-One (Recommended)

Run both the web server and temporal worker together:

```bash
# Run both web server and temporal worker
python run_servers.py

# With custom host/port
python run_servers.py --host=0.0.0.0:8080

# See all options
python run_servers.py --help
```

#### Option 2: Individual Servers

**Important**: Choose either Option 1 OR Option 2, not both simultaneously.

```bash
# Terminal 1: Start web server only
nanodjango run web.py

# Terminal 2: Start temporal worker only  
python run_worker.py
```

### Usage

#### Start a workflow run:
```bash
curl -X POST -s http://127.0.0.1:8000/api/workflow_runs \
  -H 'Content-Type: application/json' \
  -d '{"workflow_path":"workflows.lifecycle_workflow","payload":{"max_number": 10}}'

curl -X POST -s http://127.0.0.1:8000/api/workflow_runs \
  -H 'Content-Type: application/json' \
  -d '{"workflow_path":"workflows.hello_world_workflow","payload":{"prompt": "tell me something about horses"}}'
```

#### List workflow runs:
```bash
curl http://localhost:8000/api/workflow_runs
```

#### Get workflow run details:
```bash
curl http://localhost:8000/api/workflow_runs/{id}
```

## API Endpoints

- `GET /` - Home page
- `GET /api/workflow_runs` - List all workflow runs
- `POST /api/workflow_runs` - Create a new workflow run
- `GET /api/workflow_runs/{id}` - Get workflow run details
- `/wall-garden/` - Django admin interface

## Available Workflows

- **HelloWorldAgent**: Simple haiku-generating agent
- **ToolsWorkflow**: Workflow with various tool integrations
- **AgentLifecycleWorkflow**: Agent lifecycle management
- **DynamicSystemPromptWorkflow**: Dynamic prompt handling
- **ImageWorkflows**: Local and remote image processing
- **LifecycleWorkflow**: General workflow lifecycle management

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_api.py::test_create_workflow_run

# Run with verbose output
pytest -v
```

## Development

The project uses:
- **nanodjango** for rapid Django development
- **Temporal** for durable workflow execution
- **OpenAI Agents** for AI-powered workflows
- **pytest** for testing with async support

## Environment Variables

- `TEMPORAL_TARGET`: Temporal server address (default: `localhost:7233`)
- `TEMPORAL_TASK_QUEUE`: Task queue name (default: `openai-agents-basic-task-queue`)
- `POLL_INTERVAL_SECONDS`: Polling interval (default: `30`)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.