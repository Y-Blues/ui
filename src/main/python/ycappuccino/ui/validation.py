"""
validate_screen: field validation shared by every adapter, so validation rules are declared once
on a Screen (required + an optional per-field callable) and never reimplemented per renderer.
"""

from typing import Any

from ycappuccino.ui.model import Screen


def validate_screen(screen: Screen, values: dict[str, Any]) -> dict[str, str]:
    errors = {}
    for a_field in screen.fields:
        value = values.get(a_field.name, a_field.default)
        if a_field.required and _is_empty(value):
            errors[a_field.name] = f"{a_field.label} is required"
            continue
        if a_field.validate is not None and not _is_empty(value):
            message = a_field.validate(value)
            if message:
                errors[a_field.name] = message
    return errors


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == []
