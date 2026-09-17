"""
Application: the layout of a whole console -- its login screen, its menu, and the screens each menu entry
chains -- described once (usually YAML) and rendered the same way by every adapter (ui_shell, ui_web).

    title: Administration
    login: {screen: login, transport: login}
    menu:
      - label: Créer un utilisateur
        steps:
          - {screen: create_login, transport: services}
          - {screen: account, transport: crud, prefill: {login: values.login}}
          - {screen: role_account, transport: crud, prefill: {account: result._id}}

`screen` and `transport` are names the application resolves (a screen loader, a dict of Transports). A
step's `prefill` fills its fields from the previous step: `values.<field>` what was typed there,
`result.<key>` what its action returned. Once the last step succeeds, the adapter shows `saved` with a
`back` button to the menu; the menu ends with `sign_out`.
"""

import dataclasses
from dataclasses import dataclass, field
from typing import Any

import yaml

from ycappuccino.ui.model import Screen

_PREFILL_SOURCES = ("values", "result")


@dataclass(frozen=True)
class Step:
    screen: str
    transport: str
    prefill: dict = field(default_factory=dict)


@dataclass(frozen=True)
class MenuEntry:
    label: str
    steps: tuple[Step, ...]


@dataclass(frozen=True)
class Application:
    title: str
    login: Step
    menu: tuple[MenuEntry, ...]
    sign_out: str = "Se déconnecter"
    saved: str = "Enregistré."
    back: str = "Retour au menu"


def load_application(data: dict) -> Application:
    labels = {key: data[key] for key in ("sign_out", "saved", "back") if key in data}
    return Application(
        title=data["title"],
        login=_load_step(data["login"]),
        menu=tuple(
            MenuEntry(label=entry["label"], steps=tuple(_load_step(step) for step in entry["steps"]))
            for entry in data.get("menu", ())
        ),
        **labels,
    )


def load_application_yaml(text: str) -> Application:
    return load_application(yaml.safe_load(text))


def _load_step(data: dict) -> Step:
    prefill = dict(data.get("prefill") or {})
    for field_name, source in prefill.items():
        if source.split(".", 1)[0] not in _PREFILL_SOURCES or "." not in source:
            raise ValueError(f"prefill of {field_name!r}: {source!r} is neither values.<field> nor result.<key>")
    return Step(screen=data["screen"], transport=data["transport"], prefill=prefill)


def prefill_values(step: Step, previous_values: dict, previous_result: Any) -> dict:
    """the field values the step's prefill takes from the previous step; a missing source fills nothing"""
    sources = {"values": previous_values or {}, "result": previous_result if isinstance(previous_result, dict) else {}}
    values = {}
    for field_name, source in step.prefill.items():
        kind, key = source.split(".", 1)
        if key in sources[kind]:
            values[field_name] = sources[kind][key]
    return values


def with_defaults(screen: Screen, **values: Any) -> Screen:
    """the screen with these fields prefilled"""
    unknown = set(values) - {a_field.name for a_field in screen.fields}
    if unknown:
        raise ValueError(f"screen {screen.title!r} has no field {sorted(unknown)}")
    fields = tuple(
        dataclasses.replace(a_field, default=values[a_field.name]) if a_field.name in values else a_field
        for a_field in screen.fields
    )
    return dataclasses.replace(screen, fields=fields)
