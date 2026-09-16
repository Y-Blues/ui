"""every code block below reproduces one from README.md verbatim -- if this test fails, fix the
code (or the README to match it, whichever is wrong), the test is the source of truth."""

import unittest

from ycappuccino.ui.loader import load_screen_yaml
from ycappuccino.ui.model import Action, Endpoint, Field, Screen
from ycappuccino.ui.transport import perform_action
from ycappuccino.ui.validation import validate_screen

SCREEN_YAML = """
title: Connexion
fields:
  - name: username
    label: Nom d'utilisateur
    required: true
actions:
  - name: submit
    label: Se connecter
    endpoint:
      service: login
      method: POST
"""


class TestReadme(unittest.IsolatedAsyncioTestCase):

    def test_load_screen_yaml(self):
        screen = load_screen_yaml(SCREEN_YAML)

        self.assertEqual(screen.title, "Connexion")
        self.assertEqual(screen.fields[0].name, "username")
        self.assertEqual(screen.actions[0].endpoint.service, "login")

    def test_describe_a_screen_directly_in_python(self):
        screen = Screen(
            title="Connexion",
            fields=(
                Field(name="username", label="Nom d'utilisateur", required=True),
                Field(name="remember_me", label="Se souvenir de moi", type="boolean", default=False),
            ),
            actions=(Action(name="submit", label="Se connecter", endpoint=Endpoint(service="login")),),
        )

        self.assertEqual(screen.title, "Connexion")

    def test_validate(self):
        screen = Screen(title="s", fields=(Field(name="username", label="Nom d'utilisateur", required=True),))

        errors = validate_screen(screen, {"username": ""})

        self.assertEqual(errors, {"username": "Nom d'utilisateur is required"})

    async def test_perform_action(self):
        screen = Screen(
            title="Connexion",
            fields=(Field(name="username", label="Nom d'utilisateur", required=True),),
            actions=(Action(name="submit", label="Se connecter", endpoint=Endpoint(service="login")),),
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


if __name__ == "__main__":
    unittest.main()
