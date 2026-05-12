# Kernel Layer

The `kernel` package defines foundational **contracts only** for World-Platform.
This layer sets system boundaries and shared abstractions used by higher-level
runtime modules.

## Scope and Boundaries

- Defines abstract interfaces and shared types.
- Must not contain concrete runtime behavior.
- Must not include infrastructure details (transport, storage, UI).
- Concrete implementations belong in runtime/application layers.

## Contracts (`kernel/contracts.py`)

- `Contract`: Base marker interface for kernel contracts.
- `World`: Abstract world context container.
- `State`: Abstract world state representation.
- `Cell`: Abstract executable cell/node contract.
- `Workflow`: Abstract workflow definition and orchestration contract.
- `Event`: Abstract normalized event structure.

## Types (`kernel/types.py`)

- `CellInput`, `CellOutput`: Canonical input/output payload aliases.
- `WorkflowNode`, `WorkflowEdge`: Workflow graph type aliases.
- `ExecutionContext`: Dataclass containing world, state, and metadata.
- `ExecutionResult`: Dataclass for normalized execution outcomes.

## Expected Usage Pattern

1. Runtime modules implement `World`, `State`, `Cell`, `Workflow`, and `Event`.
2. Shared orchestration code accepts these contracts instead of concrete classes.
3. Execution pipelines exchange `ExecutionContext` and `ExecutionResult` values.

## Public API Surface

Import from `kernel` package root:

```python
from kernel import (
    Contract,
    World,
    State,
    Cell,
    Workflow,
    Event,
    CellInput,
    CellOutput,
    WorkflowNode,
    WorkflowEdge,
    ExecutionContext,
    ExecutionResult,
)
```
