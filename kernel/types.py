"""Shared type definitions for the kernel layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping, TypeAlias

if TYPE_CHECKING:
    from kernel.contracts import Event, State, World


CellInput: TypeAlias = Mapping[str, Any] | Any
"""Canonical cell input payload type."""

CellOutput: TypeAlias = Mapping[str, Any] | Any
"""Canonical cell output payload type."""

WorkflowNode: TypeAlias = str
"""Workflow node identifier type."""

WorkflowEdge: TypeAlias = tuple[WorkflowNode, WorkflowNode]
"""Workflow edge type represented as ``(from_node, to_node)``."""


@dataclass(slots=True)
class ExecutionContext:
    """Execution context passed to runtime operations.

    Attributes:
        world: Active world container.
        state: Active state abstraction.
        metadata: Optional immutable-friendly context metadata.
    """

    world: World
    state: State
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionResult:
    """Normalized execution result payload.

    Attributes:
        success: Indicates whether execution completed successfully.
        output: Optional execution output payload.
        events: Ordered events emitted during execution.
        error: Optional error message when ``success`` is ``False``.
    """

    success: bool
    output: CellOutput | None = None
    events: tuple[Event, ...] = field(default_factory=tuple)
    error: str | None = None
