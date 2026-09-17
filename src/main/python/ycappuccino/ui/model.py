"""Backend-agnostic description of a form-like screen (fields + actions), usually loaded from a
YAML/JSON template (see loader.py). An Action names an Endpoint, never a Python callable -- see
transport.py for the generic dispatch. No adapter dependency here."""

from dataclasses import dataclass, field as dataclass_field
from typing import Any, Callable, Optional

FIELD_TYPES = ("text", "password", "number", "boolean", "choice", "date", "list")


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    type: str = "text"
    required: bool = False
    default: Any = None
    choices: Optional[tuple[str, ...]] = None
    validate: Optional[Callable[[Any], Optional[str]]] = None

    def __post_init__(self) -> None:
        if self.type not in FIELD_TYPES:
            raise ValueError(f"field {self.name!r}: unknown type {self.type!r}, expected one of {FIELD_TYPES}")
        if self.type == "choice" and not self.choices:
            raise ValueError(f"field {self.name!r}: type='choice' requires a non-empty choices tuple")


@dataclass(frozen=True)
class Endpoint:
    service: str
    method: str = "POST"
    path: tuple[str, ...] = ()
    params: dict = dataclass_field(default_factory=dict)


@dataclass(frozen=True)
class Action:
    name: str
    label: str
    endpoint: Endpoint


@dataclass(frozen=True)
class Screen:
    title: str
    fields: tuple[Field, ...] = ()
    actions: tuple[Action, ...] = ()
