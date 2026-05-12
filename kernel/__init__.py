"""Public exports for the kernel package."""

from kernel.contracts import Cell, Contract, Event, State, Workflow, World
from kernel.types import (
    CellInput,
    CellOutput,
    ExecutionContext,
    ExecutionResult,
    WorkflowEdge,
    WorkflowNode,
)

__all__ = [
    "Contract",
    "World",
    "State",
    "Cell",
    "Workflow",
    "Event",
    "CellInput",
    "CellOutput",
    "WorkflowNode",
    "WorkflowEdge",
    "ExecutionContext",
    "ExecutionResult",
]

try:
    from kernel.kernel import Pipeline, WorldKernel

    __all__.extend(["WorldKernel", "Pipeline"])
except ModuleNotFoundError:
    pass
