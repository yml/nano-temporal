from .registry import Registry
from .hello_world_workflow import hello_world_workflow_info
from .lifecycle_workflow import lifecycle_workflow_info


def get_registry() -> Registry:
    registry = Registry()
    registry.register(hello_world_workflow_info)
    registry.register(lifecycle_workflow_info)
    registry.freeze()
    return registry