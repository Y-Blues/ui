"""Transport speaking the {"status", "meta", "data"} envelope over plain HTTP. Standalone (no
ycappuccino.api dependency, see README). Runs in a worker thread so it never blocks the UI."""

import asyncio
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Optional


class TransportError(Exception):
    pass


class NotAuthenticated(TransportError):
    pass


class Forbidden(TransportError):
    pass


class NotFoundError(TransportError):
    pass


class InvalidRequest(TransportError):
    pass


class HttpTransport:

    def __init__(self, base_url: str, opener: Callable | None = None, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._opener = opener if opener is not None else urllib.request.urlopen
        self._timeout = timeout
        self._token: Optional[str] = None

    def set_token(self, token: str) -> None:
        self._token = token

    def get_token(self) -> Optional[str]:
        return self._token

    def clear_token(self) -> None:
        self._token = None

    async def call(self, service: str, method: str, path: tuple, params: dict, body: Any) -> Any:
        request = self._build_request(service, method, path, params, body)
        return await asyncio.to_thread(self._perform, request)

    def _build_request(
        self, service: str, method: str, path: tuple, params: dict, body: Any
    ) -> urllib.request.Request:
        url = f"{self._base_url}/api/services/{service}"
        if path:
            url += "/" + "/".join(path)
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}
        if self._token is not None:
            headers["Authorization"] = f"Bearer {self._token}"
        return urllib.request.Request(url, data=data, method=method, headers=headers)

    def _perform(self, request: urllib.request.Request) -> Any:
        try:
            response = self._opener(request, timeout=self._timeout)
        except urllib.error.HTTPError as error:
            with error:
                return _translate(error.code, json.loads(error.read()))
        with response:
            return _translate(response.status, json.loads(response.read()))


def _translate(status: int, payload: dict) -> Any:
    data = payload.get("data")
    message = data.get("error", "call failed") if isinstance(data, dict) else "call failed"
    if status == 401:
        raise NotAuthenticated(message)
    if status == 403:
        raise Forbidden(message)
    if status == 404:
        raise NotFoundError(message)
    if status == 400:
        raise InvalidRequest(message)
    if status >= 400:
        raise TransportError(message)
    return data
