import unittest

from ycappuccino.ui.loader import fetch_screen, load_screen, load_screen_json, load_screen_yaml

SCREEN_DICT = {
    "title": "Connexion",
    "fields": [
        {"name": "username", "label": "Nom d'utilisateur", "required": True},
        {"name": "role", "label": "Role", "type": "choice", "choices": ["admin", "user"]},
    ],
    "actions": [
        {
            "name": "submit",
            "label": "Se connecter",
            "endpoint": {"service": "login", "method": "POST"},
        },
    ],
}


class TestLoadScreen(unittest.TestCase):

    def test_loads_fields_and_actions_from_a_dict(self):
        screen = load_screen(SCREEN_DICT)

        self.assertEqual(screen.title, "Connexion")
        self.assertEqual(len(screen.fields), 2)
        self.assertEqual(screen.fields[0].name, "username")
        self.assertTrue(screen.fields[0].required)
        self.assertEqual(screen.fields[1].choices, ("admin", "user"))
        self.assertEqual(screen.actions[0].endpoint.service, "login")

    def test_field_defaults_when_omitted(self):
        screen = load_screen({"title": "s", "fields": [{"name": "x", "label": "X"}]})

        self.assertEqual(screen.fields[0].type, "text")
        self.assertFalse(screen.fields[0].required)

    def test_loads_from_yaml_text(self):
        text = """
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
        """

        screen = load_screen_yaml(text)

        self.assertEqual(screen.title, "Connexion")
        self.assertEqual(screen.fields[0].name, "username")

    def test_loads_from_json_text(self):
        import json

        screen = load_screen_json(json.dumps(SCREEN_DICT))

        self.assertEqual(screen.title, "Connexion")
        self.assertEqual(len(screen.actions), 1)


class FakeTransport:

    def __init__(self, screen_dict):
        self.screen_dict = screen_dict
        self.calls = []

    async def call(self, service, method, path, params, body):
        self.calls.append((service, method, path, params, body))
        return self.screen_dict


class TestFetchScreen(unittest.IsolatedAsyncioTestCase):

    async def test_fetches_the_template_operation_and_parses_it(self):
        transport = FakeTransport(SCREEN_DICT)

        screen = await fetch_screen(transport, "login")

        self.assertEqual(screen.title, "Connexion")
        self.assertEqual(transport.calls, [("login", "GET", ("$template",), {}, None)])


if __name__ == "__main__":
    unittest.main()
