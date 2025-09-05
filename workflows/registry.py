from dataclasses import dataclass
from typing import Any, Dict, Type


@dataclass
class WorkflowInfo:
    input: Type[Any]
    output: Type[Any]
    workflow: Type[Any]


class Registry:
    def __init__(self) -> None:
        self._by_path: Dict[str, WorkflowInfo] = {}
        self._frozen = False

    @staticmethod
    def import_path_of(cls: Type) -> str:
        return f"{cls.__module__}"

    def register(
        self, workflow_info: WorkflowInfo, *, key: str | None = None
    ) -> WorkflowInfo:
        if self._frozen:
            raise RuntimeError("Registry is frozen; cannot register new workflows.")
        k = key or self.import_path_of(workflow_info.workflow)
        self._by_path[k] = workflow_info
        return workflow_info

    def freeze(self) -> None:
        self._frozen = True

    def get_by_import_path(self, path: str) -> WorkflowInfo:
        workflow_info = self._by_path.get(path)
        if workflow_info is not None:
            return workflow_info
        else:
            raise KeyError(f"{path!r} is not registered")
