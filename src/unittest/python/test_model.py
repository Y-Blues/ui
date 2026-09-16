import unittest

from ycappuccino.ui.model import Action, Endpoint, Field, Screen


class TestField(unittest.TestCase):

    def test_defaults(self):
        a_field = Field(name="username", label="Username")

        self.assertEqual(a_field.type, "text")
        self.assertFalse(a_field.required)
        self.assertIsNone(a_field.default)

    def test_unknown_type_is_rejected(self):
        with self.assertRaises(ValueError):
            Field(name="x", label="X", type="bogus")

    def test_choice_without_choices_is_rejected(self):
        with self.assertRaises(ValueError):
            Field(name="x", label="X", type="choice")

    def test_password_type_is_accepted(self):
        a_field = Field(name="password", label="Password", type="password")

        self.assertEqual(a_field.type, "password")

    def test_choice_with_choices_is_accepted(self):
        a_field = Field(name="x", label="X", type="choice", choices=("a", "b"))

        self.assertEqual(a_field.choices, ("a", "b"))


class TestEndpoint(unittest.TestCase):

    def test_defaults(self):
        endpoint = Endpoint(service="login")

        self.assertEqual(endpoint.method, "POST")
        self.assertEqual(endpoint.path, ())
        self.assertEqual(endpoint.params, {})


class TestScreen(unittest.TestCase):

    def test_round_trip(self):
        screen = Screen(
            title="Login",
            fields=(Field(name="username", label="Username", required=True),),
            actions=(Action(name="submit", label="Log in", endpoint=Endpoint(service="login")),),
        )

        self.assertEqual(screen.title, "Login")
        self.assertEqual(len(screen.fields), 1)
        self.assertEqual(screen.actions[0].endpoint.service, "login")

    def test_defaults_are_empty(self):
        screen = Screen(title="Empty")

        self.assertEqual(screen.fields, ())
        self.assertEqual(screen.actions, ())


if __name__ == "__main__":
    unittest.main()
