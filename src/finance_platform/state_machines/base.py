from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, Type, TypeVar

from finance_platform.errors.exceptions import StateMachineError
from finance_platform.models.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class StateTransitionError(StateMachineError):
    def __init__(
        self,
        current_state: str,
        target_state: str,
        entity_type: str = "entity",
        reason: Optional[str] = None,
    ) -> None:
        msg = f"Cannot transition {entity_type} from '{current_state}' to '{target_state}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.current_state = current_state
        self.target_state = target_state
        self.entity_type = entity_type
        self.transition_reason = reason


TransitionMap = Dict[str, Set[str]]


class StateMachine(ABC, Generic[T]):
    entity_type: str = "entity"

    def __init__(self, entity: Optional[T] = None) -> None:
        self._entity = entity

    @property
    @abstractmethod
    def state_field(self) -> str:
        ...

    @property
    @abstractmethod
    def transitions(self) -> TransitionMap:
        ...

    def _get_state(self, entity: Optional[T] = None) -> str:
        target = entity or self._entity
        if target is None:
            raise StateMachineError("No entity bound to state machine")
        return str(getattr(target, self.state_field))

    def _set_state(self, new_state: str, entity: Optional[T] = None) -> None:
        target = entity or self._entity
        if target is None:
            raise StateMachineError("No entity bound to state machine")
        setattr(target, self.state_field, new_state)

    def can_transition(
        self, target_state: str, entity: Optional[T] = None, raise_on_error: bool = False
    ) -> bool:
        current = self._get_state(entity)
        allowed = self.transitions.get(current, set())
        if target_state in allowed:
            return True
        if raise_on_error:
            raise StateTransitionError(current, target_state, self.entity_type)
        return False

    def transition(
        self,
        target_state: str,
        entity: Optional[T] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> T:
        target = entity or self._entity
        if target is None:
            raise StateMachineError("No entity bound to state machine")
        current = self._get_state(target)
        self.can_transition(target_state, target, raise_on_error=True)
        self._on_before_transition(current, target_state, target, context)
        self._set_state(target_state, target)
        self._on_after_transition(current, target_state, target, context)
        return target

    def _on_before_transition(
        self,
        from_state: str,
        to_state: str,
        entity: T,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ...

    def _on_after_transition(
        self,
        from_state: str,
        to_state: str,
        entity: T,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        if hasattr(entity, "touch"):
            entity.touch()

    @property
    def current_state(self) -> str:
        return self._get_state()

    @property
    def allowed_transitions(self) -> Set[str]:
        return self.transitions.get(self.current_state, set())

    @property
    def is_terminal(self) -> bool:
        return len(self.allowed_transitions) == 0

    def states(self) -> Set[str]:
        result: Set[str] = set()
        for src, targets in self.transitions.items():
            result.add(src)
            result.update(targets)
        return result

    def transition_path(self, from_state: str, to_state: str) -> List[str]:
        visited: Set[str] = set()
        parent: Dict[str, Optional[str]] = {}
        queue: List[str] = [from_state]
        visited.add(from_state)
        parent[from_state] = None
        while queue:
            current = queue.pop(0)
            if current == to_state:
                path: List[str] = []
                while current is not None:
                    path.append(current)
                    current = parent[current]
                path.reverse()
                return path
            for nxt in self.transitions.get(current, set()):
                if nxt not in visited:
                    visited.add(nxt)
                    parent[nxt] = current
                    queue.append(nxt)
        return []


class StateMachineRegistry:
    _machines: Dict[str, Type[StateMachine]] = {}

    @classmethod
    def register(cls, machine_cls: Type[StateMachine]) -> Type[StateMachine]:
        key = machine_cls.entity_type
        cls._machines[key] = machine_cls
        return machine_cls

    @classmethod
    def get(cls, entity_type: str) -> Type[StateMachine]:
        if entity_type not in cls._machines:
            raise KeyError(f"No state machine registered for entity type '{entity_type}'")
        return cls._machines[entity_type]

    @classmethod
    def create(cls, entity_type: str, entity: Optional[BaseModel] = None) -> StateMachine:
        machine_cls = cls.get(entity_type)
        return machine_cls(entity)

    @classmethod
    def registered_types(cls) -> List[str]:
        return list(cls._machines.keys())
