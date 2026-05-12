"""Abstract contracts for the kernel layer.

This module defines the foundational interfaces for the World-Platform system.
All classes here are abstract contracts and intentionally contain no concrete
runtime behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence


class Contract(ABC):
    """Base marker interface for all kernel-level contracts.

    System-level rule:
    Implementations of kernel contracts should only define domain behavior and
    should avoid infrastructure concerns such as transport, persistence, and UI.
    """


class State(Contract):
    """Abstract representation of world state.

    Responsibility:
    Provide structured read/write access to state values and expose a
    serialization-friendly snapshot of the entire state.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Return the value stored for ``key``.

        Args:
            key: State key to read.
            default: Value returned when ``key`` is not present.
        """
        raise NotImplementedError("State.get must be implemented by subclasses")

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Persist a value under ``key`` in the state model.

        Args:
            key: State key to write.
            value: Value to persist.
        """
        raise NotImplementedError("State.set must be implemented by subclasses")

    @abstractmethod
    def snapshot(self) -> Mapping[str, Any]:
        """Return a serialization-safe snapshot of the full state."""
        raise NotImplementedError("State.snapshot must be implemented by subclasses")


class World(Contract):
    """Abstract world context container.

    Responsibility:
    Aggregate state, events, and world-scoped metadata required for execution.
    """

    @property
    @abstractmethod
    def state(self) -> State:
        """Return the active ``State`` instance for this world."""
        raise NotImplementedError("World.state must be implemented by subclasses")

    @abstractmethod
    def publish(self, event: "Event") -> None:
        """Publish an event into the world event stream.

        Args:
            event: Event to publish.
        """
        raise NotImplementedError("World.publish must be implemented by subclasses")

    @abstractmethod
    def context(self) -> Mapping[str, Any]:
        """Return immutable world-level context metadata for execution."""
        raise NotImplementedError("World.context must be implemented by subclasses")


class Event(Contract):
    """Abstract event contract.

    Responsibility:
    Define normalized event metadata used to communicate lifecycle changes,
    observations, and outcomes between kernel components.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the canonical event name."""
        raise NotImplementedError("Event.name must be implemented by subclasses")

    @property
    @abstractmethod
    def payload(self) -> Mapping[str, Any]:
        """Return structured event payload data."""
        raise NotImplementedError("Event.payload must be implemented by subclasses")

    @abstractmethod
    def to_dict(self) -> Mapping[str, Any]:
        """Return a serialized dictionary representation of the event."""
        raise NotImplementedError("Event.to_dict must be implemented by subclasses")


class Cell(Contract):
    """Abstract cell/node contract.

    Responsibility:
    Represent a single executable unit that transforms input data into output
    under a world execution context.
    """

    @property
    @abstractmethod
    def cell_id(self) -> str:
        """Return the stable identifier for the cell."""
        raise NotImplementedError("Cell.cell_id must be implemented by subclasses")

    @abstractmethod
    def execute(self, data: Any, world: World) -> Any:
        """Execute the cell with input data in a given world context.

        Args:
            data: Cell input payload.
            world: Active world context.
        """
        raise NotImplementedError("Cell.execute must be implemented by subclasses")


class Workflow(Contract):
    """Abstract workflow definition.

    Responsibility:
    Describe and orchestrate a set of cells and their execution edges while
    enforcing workflow-level sequencing and coordination rules.
    """

    @property
    @abstractmethod
    def nodes(self) -> Sequence[Cell]:
        """Return the ordered collection of workflow nodes."""
        raise NotImplementedError("Workflow.nodes must be implemented by subclasses")

    @abstractmethod
    def run(self, data: Any, world: World) -> Any:
        """Run the workflow using the provided input and world context.

        Args:
            data: Workflow input payload.
            world: Active world context.
        """
        raise NotImplementedError("Workflow.run must be implemented by subclasses")
