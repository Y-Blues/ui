"""
Transport: the one thing every adapter must supply to make a Screen's Action callable -- how to
actually reach an Endpoint. Same shape as ycappuccino.client.transport.HttpTransport /
IHttpFetcher: a Protocol, so tests inject a fake and no adapter (shell/Qt/web) is forced to share
an implementation -- a shell app in the same process as the backend might call an IServiceEndpoint
directly, a browser adapter would go through ycappuccino-client's HttpTransport, a desktop Qt app
might call plain HTTP.

perform_action() is the "generic dispatch" every adapter reuses: build the call from the Screen's
declared Endpoint plus the current field values, call the Transport, return its result. No adapter
re-implements this -- it is the reason Action never carries a hand-written Python callable.
"""

from typing import Any, Protocol

from ycappuccino.ui.model import Action


class Transport(Protocol):
    async def call(self, service: str, method: str, path: tuple, params: dict, body: Any) -> Any: ...


async def perform_action(action: Action, values: dict, transport: Transport) -> Any:
    endpoint = action.endpoint
    body = dict(endpoint.params)
    body.update(values)
    return await transport.call(endpoint.service, endpoint.method, endpoint.path, {}, body)
