import unittest

from ycappuccino.ui.model import Field, Screen
from ycappuccino.ui.validation import validate_screen


class TestValidateScreen(unittest.TestCase):

    def test_required_field_missing_is_an_error(self):
        screen = Screen(title="s", fields=(Field(name="username", label="Username", required=True),))

        errors = validate_screen(screen, {})

        self.assertIn("username", errors)

    def test_required_field_present_has_no_error(self):
        screen = Screen(title="s", fields=(Field(name="username", label="Username", required=True),))

        errors = validate_screen(screen, {"username": "aurelien"})

        self.assertEqual(errors, {})

    def test_custom_validate_callable_runs(self):
        def not_admin(value):
            return "reserved name" if value == "admin" else None

        screen = Screen(title="s", fields=(Field(name="username", label="Username", validate=not_admin),))

        errors = validate_screen(screen, {"username": "admin"})

        self.assertEqual(errors["username"], "reserved name")

    def test_custom_validate_is_skipped_when_empty_and_not_required(self):
        calls = []

        def track(value):
            calls.append(value)
            return None

        screen = Screen(title="s", fields=(Field(name="nickname", label="Nickname", validate=track),))

        errors = validate_screen(screen, {})

        self.assertEqual(errors, {})
        self.assertEqual(calls, [])

    def test_default_value_satisfies_required_when_missing_from_values(self):
        screen = Screen(
            title="s",
            fields=(Field(name="count", label="Count", type="number", required=True, default=0),),
        )

        errors = validate_screen(screen, {})

        self.assertEqual(errors, {})


if __name__ == "__main__":
    unittest.main()
