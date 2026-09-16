"""
Screen: a backend-agnostic, declarative description of a form-like screen (fields + actions), built
either directly in Python (see this module) or loaded from a YAML/JSON template
(ycappuccino.ui.loader.load_screen) -- the template is the normal way to describe a screen; the
Python model exists so a loaded template and a hand-built Screen are the exact same object, and so
adapters never special-case "where the Screen came from".

An Action never carries a hand-written Python callable: it names an Endpoint (service, method,
path, static params) that a generic ycappuccino.ui.transport.Transport dispatches at runtime (see
that module) -- the whole point of describing a screen in a template is that no per-screen Python
code is needed to wire it up. No adapter (Qt/textual/browser) is imported here, and none of
Screen/Field/Action/Endpoint depends on any of them either: a Screen must be constructible and
testable in plain CPython with none of the rendering toolkits installed. See ycappuccino-ui-shell
(and future ui-qt/ui-web) for renderers.
"""

from dataclasses import dataclass, field as dataclass_field
from typing import Any, Callable, Optional

FIELD_TYPES = ("text", "password", "number", "boolean", "choice", "date")


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
class Endpoint:
    """what an Action calls: the same (service, method, path) shape IExposedService/RemoteCall
    already use across the framework (ycappuccino.api.endpoints_service), so a template's endpoint
    maps directly onto an existing route without inventing a second addressing scheme."""

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
