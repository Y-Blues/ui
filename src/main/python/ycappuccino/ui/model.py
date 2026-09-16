"""
Screen: a backend-agnostic, declarative description of a form-like screen (fields + actions).

No adapter (Qt/textual/browser) is imported here, and none of Screen/Field/Action depends on any
of them either: a Screen must be constructible and testable in plain CPython with none of the
rendering toolkits installed. See ycappuccino-ui-shell (and future ui-qt/ui-web) for renderers.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

FIELD_TYPES = ("text", "number", "boolean", "choice", "date")


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    type: str = "text"
    required: bool = False
    default: Any = None
    choices: Optional[tuple[str, ...]] = None
    validate: Optional[Callable[[Any], Optional[str]]] = None

    def __post_init__(self):
        if self.type not in FIELD_TYPES:
            raise ValueError(f"field {self.name!r}: unknown type {self.type!r}, expected one of {FIELD_TYPES}")
        if self.type == "choice" and not self.choices:
            raise ValueError(f"field {self.name!r}: type='choice' requires a non-empty choices tuple")


@dataclass(frozen=True)
class Action:
    name: str
    label: str
    handler: Callable[[dict], Any]


@dataclass(frozen=True)
class Screen:
    title: str
    fields: tuple[Field, ...] = ()
    actions: tuple[Action, ...] = ()
