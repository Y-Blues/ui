import io
import json
import unittest
import urllib.error

from ycappuccino.ui.http_transport import (
    Forbidden,
    HttpTransport,
    InvalidRequest,
    NotAuthenticated,
    NotFoundError,
    TransportError,
)


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, status=200, payload=None):
        self.status = status
        self.payload = payload if payload is not None else {"status": 200, "meta": {}, "data": {}}
        self.requests = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        if self.status >= 400:
            raise urllib.error.HTTPError(
                request.full_url, self.status, "error", None,
                io.BytesIO(json.dumps(self.payload).encode()),
            )
        return FakeResponse(self.status, self.payload)


class TestHttpTransport(unittest.IsolatedAsyncioTestCase):

    async def test_builds_the_service_url_and_forwards_the_body(self):
        opener = FakeOpener(payload={"status": 200, "meta": {}, "data": {"token": "abc"}})
        transport = HttpTransport("http://localhost:8080", opener=opener)

        result = await transport.call("login", "POST", (), {}, {"login": "aurelien", "password": "x"})

        self.assertEqual(result, {"token": "abc"})
        request = opener.requests[0]
        self.assertEqual(request.full_url, "http://localhost:8080/api/services/login")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data), {"login": "aurelien", "password": "x"})

    async def test_forwards_extra_path_and_query_params(self):
        opener = FakeOpener()
        transport = HttpTransport("http://localhost:8080", opener=opener)

        await transport.call("scripts", "GET", ("run",), {"limit": "5"}, None)

        request = opener.requests[0]
        self.assertEqual(request.full_url, "http://localhost:8080/api/services/scripts/run?limit=5")
        self.assertIsNone(request.data)

    async def test_token_is_sent_as_a_bearer_header_once_set(self):
        opener = FakeOpener()
        transport = HttpTransport("http://localhost:8080", opener=opener)
        transport.set_token("a-token")

        await transport.call("change_password", "POST", (), {}, {})

        self.assertEqual(opener.requests[0].get_header("Authorization"), "Bearer a-token")
        self.assertEqual(transport.get_token(), "a-token")

    async def test_no_authorization_header_before_a_token_is_set(self):
        opener = FakeOpener()
        transport = HttpTransport("http://localhost:8080", opener=opener)

        await transport.call("login", "POST", (), {}, {})

        self.assertIsNone(opener.requests[0].get_header("Authorization"))

    async def test_clear_token_removes_it(self):
        transport = HttpTransport("http://localhost:8080", opener=FakeOpener())
        transport.set_token("a-token")

        transport.clear_token()

        self.assertIsNone(transport.get_token())

    async def test_401_becomes_not_authenticated(self):
        opener = FakeOpener(status=401, payload={"status": 401, "meta": {}, "data": {"error": "no"}})
        transport = HttpTransport("http://localhost:8080", opener=opener)

        with self.assertRaises(NotAuthenticated):
            await transport.call("change_password", "POST", (), {}, {})

    async def test_403_becomes_forbidden(self):
        opener = FakeOpener(status=403, payload={"status": 403, "meta": {}, "data": {"error": "no"}})
        transport = HttpTransport("http://localhost:8080", opener=opener)

        with self.assertRaises(Forbidden):
            await transport.call("change_password", "POST", (), {}, {})

    async def test_404_becomes_not_found(self):
        opener = FakeOpener(status=404, payload={"status": 404, "meta": {}, "data": {"error": "no"}})
        transport = HttpTransport("http://localhost:8080", opener=opener)

        with self.assertRaises(NotFoundError):
            await transport.call("bogus", "POST", (), {}, {})

    async def test_400_becomes_invalid_request(self):
        opener = FakeOpener(status=400, payload={"status": 400, "meta": {}, "data": {"error": "bad"}})
        transport = HttpTransport("http://localhost:8080", opener=opener)

        with self.assertRaises(InvalidRequest):
            await transport.call("login", "POST", (), {}, {})

    async def test_500_becomes_a_generic_transport_error(self):
        opener = FakeOpener(status=500, payload={"status": 500, "meta": {}, "data": {"error": "boom"}})
        transport = HttpTransport("http://localhost:8080", opener=opener)

        with self.assertRaises(TransportError):
            await transport.call("login", "POST", (), {}, {})


if __name__ == "__main__":
    unittest.main()
