"""
load_screen: parse a Screen from a plain dict (as produced by yaml.safe_load/json.loads), or fetch
one dynamically from a backend via a Transport -- inspired by SData 2.0's $template/$schema
resource discovery (https://sage.github.io/SData-2.0/, entity/$template returns a default/empty
instance of a resource, entity/$schema describes it): a service can describe its own screen instead
of every client hand-authoring one. Only that idea is borrowed, not SData's own wire format -- the
template vocabulary here stays plain (name/label/type/required), not SData's Atom/XML shape.
"""

import json

import yaml

from ycappuccino.ui.model import Action, Endpoint, Field, Screen
from ycappuccino.ui.transport import Transport

TEMPLATE_OPERATION = "$template"


def load_screen(data: dict) -> Screen:
    return Screen(
        title=data["title"],
        fields=tuple(_load_field(item) for item in data.get("fields", ())),
        actions=tuple(_load_action(item) for item in data.get("actions", ())),
    )


def load_screen_yaml(text: str) -> Screen:
    return load_screen(yaml.safe_load(text))


def load_screen_json(text: str) -> Screen:
    return load_screen(json.loads(text))


async def fetch_screen(transport: Transport, service: str) -> Screen:
    """asks the service itself for its screen, at the reserved "$template" operation
    (mirroring SData's entity/$template), instead of only ever loading one from a local file."""
    data = await transport.call(service, "GET", (TEMPLATE_OPERATION,), {}, None)
    return load_screen(data)


def _load_field(item: dict) -> Field:
    choices = item.get("choices")
    return Field(
        name=item["name"],
        label=item["label"],
        type=item.get("type", "text"),
        required=item.get("required", False),
        default=item.get("default"),
        choices=tuple(choices) if choices else None,
    )


def _load_action(item: dict) -> Action:
    endpoint_data = item["endpoint"]
    endpoint = Endpoint(
        service=endpoint_data["service"],
        method=endpoint_data.get("method", "POST"),
        path=tuple(endpoint_data.get("path", ())),
        params=endpoint_data.get("params", {}),
    )
    return Action(name=item["name"], label=item["label"], endpoint=endpoint)
