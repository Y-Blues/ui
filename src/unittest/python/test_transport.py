import unittest

from ycappuccino.ui.model import Action, Endpoint
from ycappuccino.ui.transport import perform_action


class FakeTransport:

    def __init__(self, result=None):
        self.result = result
        self.calls = []

    async def call(self, service, method, path, params, body):
        self.calls.append((service, method, path, params, body))
        return self.result


class TestPerformAction(unittest.IsolatedAsyncioTestCase):

    async def test_calls_the_endpoint_with_the_field_values_as_body(self):
        transport = FakeTransport(result={"token": "abc"})
        action = Action(name="submit", label="Log in", endpoint=Endpoint(service="login", method="POST"))

        result = await perform_action(action, {"username": "aurelien"}, transport)

        self.assertEqual(result, {"token": "abc"})
        self.assertEqual(transport.calls, [("login", "POST", (), {}, {"username": "aurelien"})])

    async def test_endpoint_params_are_merged_under_the_field_values(self):
        transport = FakeTransport()
        endpoint = Endpoint(service="scripts", method="POST", path=("run",), params={"scriptId": "hello"})
        action = Action(name="run", label="Run", endpoint=endpoint)

        await perform_action(action, {"scriptId": "override"}, transport)

        self.assertEqual(transport.calls[0][2], ("run",))
        self.assertEqual(transport.calls[0][4], {"scriptId": "override"})


if __name__ == "__main__":
    unittest.main()
