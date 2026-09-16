import unittest

from ycappuccino.ui.model import Action, Field, Screen


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

    def test_choice_with_choices_is_accepted(self):
        a_field = Field(name="x", label="X", type="choice", choices=("a", "b"))

        self.assertEqual(a_field.choices, ("a", "b"))


class TestScreen(unittest.TestCase):

    def test_round_trip(self):
        handled = []
        screen = Screen(
            title="Login",
            fields=(Field(name="username", label="Username", required=True),),
            actions=(Action(name="submit", label="Log in", handler=handled.append),),
        )

        self.assertEqual(screen.title, "Login")
        self.assertEqual(len(screen.fields), 1)
        screen.actions[0].handler({"username": "aurelien"})
        self.assertEqual(handled, [{"username": "aurelien"}])

    def test_defaults_are_empty(self):
        screen = Screen(title="Empty")

        self.assertEqual(screen.fields, ())
        self.assertEqual(screen.actions, ())


if __name__ == "__main__":
    unittest.main()
