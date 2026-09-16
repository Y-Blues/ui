"""Transport: how an adapter reaches an Endpoint. perform_action() is the generic dispatch every
adapter reuses instead of a hand-written callable."""

from typing import Any, Protocol

from ycappuccino.ui.model import Action


class Transport(Protocol):
    async def call(self, service: str, method: str, path: tuple, params: dict, body: Any) -> Any: ...


async def perform_action(action: Action, values: dict, transport: Transport) -> Any:
    endpoint = action.endpoint
    body = dict(endpoint.params)
    body.update(values)
    return await transport.call(endpoint.service, endpoint.method, endpoint.path, {}, body)
