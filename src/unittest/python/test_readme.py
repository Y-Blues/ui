"""every code block below reproduces one from README.md verbatim -- if this test fails, fix the
code (or the README to match it, whichever is wrong), the test is the source of truth."""

import unittest

from ycappuccino.ui.loader import load_screen_yaml
from ycappuccino.ui.model import Action, Endpoint, Field, Screen
from ycappuccino.ui.transport import perform_action
from ycappuccino.ui.validation import validate_screen
from ycappuccino.ui.ycappuccino_transport import CrudTransport

SCREEN_YAML = """
title: Sign in
fields:
  - name: username
    label: Username
    required: true
actions:
  - name: submit
    label: Sign in
    endpoint:
      service: login
      method: POST
"""


class TestReadme(unittest.IsolatedAsyncioTestCase):

    def test_load_screen_yaml(self):
        screen = load_screen_yaml(SCREEN_YAML)

        self.assertEqual(screen.title, "Sign in")
        self.assertEqual(screen.fields[0].name, "username")
        self.assertEqual(screen.actions[0].endpoint.service, "login")

    def test_describe_a_screen_directly_in_python(self):
        screen = Screen(
            title="Sign in",
            fields=(
                Field(name="username", label="Username", required=True),
                Field(name="remember_me", label="Se souvenir de moi", type="boolean", default=False),
            ),
            actions=(Action(name="submit", label="Sign in", endpoint=Endpoint(service="login")),),
        )

        self.assertEqual(screen.title, "Sign in")

    def test_validate(self):
        screen = Screen(title="s", fields=(Field(name="username", label="Username", required=True),))

        errors = validate_screen(screen, {"username": ""})

        self.assertEqual(errors, {"username": "Username is required"})

    async def test_perform_action(self):
        screen = Screen(
            title="Sign in",
            fields=(Field(name="username", label="Username", required=True),),
            actions=(Action(name="submit", label="Sign in", endpoint=Endpoint(service="login")),),
        )

        class ExampleTransport:
            async def call(self, service, method, path, params, body):
                return {"received": {"service": service, "method": method, "path": path, "body": body}}

        async def main():
            result = await perform_action(screen.actions[0], {"username": "aurelien"}, ExampleTransport())
            return result

        result = await main()

        self.assertEqual(result["received"]["service"], "login")
        self.assertEqual(result["received"]["body"], {"username": "aurelien"})

    def test_crud_transport_constructs(self):
        transport = CrudTransport(object(), subject={"sub": "admin"})

        self.assertEqual(transport.subject, {"sub": "admin"})


if __name__ == "__main__":
    unittest.main()
