"""
Bridges the real backend interfaces (ycappuccino.api.endpoints_storage.ICrud,
ycappuccino.api.endpoints_service.IServiceEndpoint, or any interface through ComponentTransport) to
ycappuccino.ui.transport.Transport, so a
Screen's Endpoint(service, method, path, params) works uniformly whether it addresses a named
service or a CRUD item -- the YAML never says which, only the deployment's Transport choice does.

Deliberately the only module in this package importing ycappuccino.api: model.py/transport.py/
validation.py/loader.py stay dependency-free (see README), so an adapter that needs neither
CrudTransport nor ServiceEndpointTransport never pays for ycappuccino.api being importable.

Application code never constructs these explicitly to pick "local vs HTTP vs whatever": it always
depends on ICrud/IServiceEndpoint through normal component injection (a native component's
constructor, e.g. def __init__(self, crud: ICrud)), and whatever concrete implementation the
framework wires in - the real ycappuccino.storage-backed one, or ycappuccino.client's
Pyodide-in-browser RemoteCrud/RemoteServiceEndpoint proxying over HTTP - is exactly as invisible
here as it already is to that constructor. CrudTransport/ServiceEndpointTransport only translate
the SHAPE of the call (Transport.call(...) vs ICrud's distinct methods / IServiceEndpoint.call),
never the question of where the implementation lives or how it talks to it.
"""

import inspect
from typing import Any

from ycappuccino.api.endpoints_service import IServiceEndpoint
from ycappuccino.api.endpoints_storage import ICrud


class CrudTransport:
    """Transport wrapping an ICrud: `service` is an item_id, `path` is empty or a single
    document id."""

    def __init__(self, crud: ICrud, subject: dict | None = None) -> None:
        self._crud = crud
        self.subject = subject

    async def call(self, service: str, method: str, path: tuple, params: dict, body: Any) -> Any:
        if method == "GET" and not path:
            return await self._crud.get_many(service, params, self.subject)
        if method == "GET":
            return await self._crud.get_one(service, path[0], params, self.subject)
        if method == "POST":
            return await self._crud.create(service, body, self.subject)
        if method == "PUT":
            return await self._crud.update(service, path[0], body, self.subject)
        if method == "DELETE":
            await self._crud.delete(service, path[0], self.subject)
            return None
        raise ValueError(f"CrudTransport: unsupported method {method!r}")


class ServiceEndpointTransport:
    """Transport wrapping an IServiceEndpoint: `service` is the named service."""

    def __init__(self, endpoint: IServiceEndpoint, subject: dict | None = None) -> None:
        self._endpoint = endpoint
        self.subject = subject

    async def call(self, service: str, method: str, path: tuple, params: dict, body: Any) -> Any:
        result = await self._endpoint.call(service, method, list(path), params, body, self.subject)
        return result.body


class ComponentTransport:
    """Transport calling a component through its interface: `service` names one of the components
    (e.g. {"login": an ILoginService}), `method` is the method to call, the body its arguments."""

    def __init__(self, components: dict[str, Any], subject: dict | None = None) -> None:
        self._components = components
        self.subject = subject

    async def call(self, service: str, method: str, path: tuple, params: dict, body: Any) -> Any:
        component = self._components.get(service)
        target = None if component is None or method.startswith("_") else getattr(component, method, None)
        if not callable(target):
            raise ValueError(f"ComponentTransport: no method {method!r} on component {service!r}")
        kwargs = dict(body or {})
        if "subject" in inspect.signature(target).parameters:
            kwargs["subject"] = self.subject
        return await target(**kwargs)
