import unittest

from ycappuccino.ui.ycappuccino_transport import ComponentTransport, CrudTransport, ServiceEndpointTransport


class FakeCrud:

    def __init__(self, result=None):
        self.result = result
        self.calls = []

    async def get_one(self, item_id, id, params=None, subject=None):
        self.calls.append(("get_one", item_id, id, params, subject))
        return self.result

    async def get_many(self, item_id, params=None, subject=None):
        self.calls.append(("get_many", item_id, params, subject))
        return self.result

    async def create(self, item_id, fields, subject=None):
        self.calls.append(("create", item_id, fields, subject))
        return self.result

    async def update(self, item_id, id, fields, subject=None):
        self.calls.append(("update", item_id, id, fields, subject))
        return self.result

    async def delete(self, item_id, id, subject=None):
        self.calls.append(("delete", item_id, id, subject))


class TestCrudTransport(unittest.IsolatedAsyncioTestCase):

    async def test_post_without_path_creates(self):
        crud = FakeCrud(result={"_id": "acme"})
        transport = CrudTransport(crud, subject={"sub": "admin"})

        result = await transport.call("organization", "POST", (), {}, {"name": "Acme"})

        self.assertEqual(result, {"_id": "acme"})
        self.assertEqual(crud.calls, [("create", "organization", {"name": "Acme"}, {"sub": "admin"})])

    async def test_get_without_path_lists(self):
        crud = FakeCrud(result={"items": [], "total": 0})
        transport = CrudTransport(crud)

        await transport.call("role", "GET", (), {"limit": "10"}, None)

        self.assertEqual(crud.calls, [("get_many", "role", {"limit": "10"}, None)])

    async def test_get_with_path_reads_one(self):
        crud = FakeCrud(result={"_id": "admin"})
        transport = CrudTransport(crud)

        await transport.call("role", "GET", ("admin",), {}, None)

        self.assertEqual(crud.calls, [("get_one", "role", "admin", {}, None)])

    async def test_put_updates(self):
        crud = FakeCrud(result={"_id": "admin"})
        transport = CrudTransport(crud)

        await transport.call("role", "PUT", ("admin",), {}, {"name": "Admin"})

        self.assertEqual(crud.calls, [("update", "role", "admin", {"name": "Admin"}, None)])

    async def test_delete(self):
        crud = FakeCrud()
        transport = CrudTransport(crud)

        result = await transport.call("role", "DELETE", ("admin",), {}, None)

        self.assertIsNone(result)
        self.assertEqual(crud.calls, [("delete", "role", "admin", None)])

    async def test_subject_can_be_set_after_construction(self):
        crud = FakeCrud(result={})
        transport = CrudTransport(crud)

        transport.subject = {"sub": "admin"}
        await transport.call("organization", "POST", (), {}, {})

        self.assertEqual(crud.calls[0][3], {"sub": "admin"})


class FakeResult:
    def __init__(self, body):
        self.body = body


class FakeServiceEndpoint:

    def __init__(self, result=None):
        self.result = result
        self.calls = []

    async def call(self, name, method, extra_path, params, body, subject):
        self.calls.append((name, method, extra_path, params, body, subject))
        return FakeResult(self.result)


class TestServiceEndpointTransport(unittest.IsolatedAsyncioTestCase):

    async def test_calls_the_service_endpoint_directly_no_subject_by_default(self):
        endpoint = FakeServiceEndpoint(result={"token": "abc"})
        transport = ServiceEndpointTransport(endpoint)

        result = await transport.call("login", "POST", (), {}, {"login": "aurelien", "password": "x"})

        self.assertEqual(result, {"token": "abc"})
        self.assertEqual(
            endpoint.calls,
            [("login", "POST", [], {}, {"login": "aurelien", "password": "x"}, None)],
        )

    async def test_subject_given_at_construction_is_forwarded(self):
        endpoint = FakeServiceEndpoint(result={})
        transport = ServiceEndpointTransport(endpoint, subject={"sub": "acc-1"})

        await transport.call("change_password", "POST", (), {}, {})

        self.assertEqual(endpoint.calls[0][5], {"sub": "acc-1"})

    async def test_subject_can_be_set_after_construction(self):
        endpoint = FakeServiceEndpoint(result={})
        transport = ServiceEndpointTransport(endpoint)

        transport.subject = {"sub": "acc-1"}
        await transport.call("change_password", "POST", (), {}, {})

        self.assertEqual(endpoint.calls[0][5], {"sub": "acc-1"})

    async def test_extra_path_is_forwarded_as_a_list(self):
        endpoint = FakeServiceEndpoint(result={})
        transport = ServiceEndpointTransport(endpoint)

        await transport.call("scripts", "POST", ("run",), {}, {})

        self.assertEqual(endpoint.calls[0][2], ["run"])



class FakeLogin:

    def __init__(self):
        self.calls = []

    async def login(self, login, password):
        self.calls.append((login, password))
        return "token"

    async def whoami(self, subject=None):
        return subject


class TestComponentTransport(unittest.IsolatedAsyncioTestCase):

    async def test_calls_the_named_method_of_the_named_component_with_the_body_as_arguments(self):
        login = FakeLogin()
        transport = ComponentTransport({"login": login})

        result = await transport.call("login", "login", (), {}, {"login": "alice", "password": "secret"})

        self.assertEqual((result, login.calls), ("token", [("alice", "secret")]))

    async def test_the_subject_is_passed_to_a_method_declaring_one(self):
        transport = ComponentTransport({"me": FakeLogin()}, subject={"sub": "alice"})

        self.assertEqual(await transport.call("me", "whoami", (), {}, None), {"sub": "alice"})

    async def test_an_unknown_component_or_a_private_method_is_refused(self):
        transport = ComponentTransport({"login": FakeLogin()})

        for service, method in (("nobody", "login"), ("login", "_private"), ("login", "missing")):
            with self.subTest(service=service, method=method):
                with self.assertRaises(ValueError):
                    await transport.call(service, method, (), {}, {})


if __name__ == "__main__":
    unittest.main()
