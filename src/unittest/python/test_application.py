import unittest

from ycappuccino.ui.application import (
    Application,
    MenuEntry,
    MenuGroup,
    Step,
    load_application,
    load_application_yaml,
    prefill_values,
    with_defaults,
)
from ycappuccino.ui.model import Field, Screen

APPLICATION_YAML = """
title: Administration
login: {screen: login, transport: login, user: login}
menu:
  - label: Roles
    entries:
      - label: Create a role
        steps:
          - {screen: role, transport: crud}
  - label: Users
    entries:
      - label: Create a user
        steps:
          - {screen: create_login, transport: services}
          - {screen: account, transport: crud, prefill: {login: values.login}}
          - {screen: role_account, transport: crud, prefill: {account: result._id}}
"""


class TestLoadApplication(unittest.TestCase):

    def test_loads_the_login_and_the_menu_sections_with_their_entries(self):
        application = load_application_yaml(APPLICATION_YAML)

        self.assertEqual(
            application,
            Application(
                title="Administration",
                login=Step(screen="login", transport="login"),
                user_field="login",
                menu=(
                    MenuGroup(
                        label="Roles",
                        entries=(MenuEntry(label="Create a role", steps=(Step(screen="role", transport="crud"),)),),
                    ),
                    MenuGroup(
                        label="Users",
                        entries=(
                            MenuEntry(
                                label="Create a user",
                                steps=(
                                    Step(screen="create_login", transport="services"),
                                    Step(screen="account", transport="crud", prefill={"login": "values.login"}),
                                    Step(screen="role_account", transport="crud", prefill={"account": "result._id"}),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

    def test_the_texts_have_defaults_and_can_be_overridden(self):
        application = load_application({"title": "t", "login": {"screen": "l", "transport": "l"}, "menu": [],
                                         "saved": "OK"})

        self.assertEqual(
            (application.sign_out, application.saved, application.welcome, application.user_field),
            ("Sign out", "OK", "Welcome, {user}.", None),
        )

    def test_the_welcome_names_the_signed_in_user(self):
        application = load_application({"title": "t", "login": {"screen": "l", "transport": "l"}, "menu": []})

        self.assertEqual(application.welcome_text("admin"), "Welcome, admin.")

    def test_a_prefill_reads_the_values_or_the_result_of_the_previous_step_only(self):
        with self.assertRaises(ValueError):
            load_application({"title": "t", "login": {"screen": "l", "transport": "l"},
                              "menu": [{"label": "g", "entries": [{"label": "x", "steps": [
                                  {"screen": "s", "transport": "t", "prefill": {"a": "session.user"}}]}]}]})


class TestPrefill(unittest.TestCase):

    def test_values_and_result_of_the_previous_step(self):
        step = Step(screen="s", transport="t", prefill={"login": "values.login", "account": "result._id"})

        self.assertEqual(
            prefill_values(step, {"login": "bob", "password": "x"}, {"_id": "42"}),
            {"login": "bob", "account": "42"},
        )

    def test_a_missing_source_prefills_nothing(self):
        step = Step(screen="s", transport="t", prefill={"account": "result._id"})

        self.assertEqual(prefill_values(step, {}, None), {})


class TestWithDefaults(unittest.TestCase):

    def setUp(self):
        self.screen = Screen(title="t", fields=(Field(name="a", label="A"), Field(name="b", label="B")))

    def test_prefills_the_named_fields_only(self):
        screen = with_defaults(self.screen, a="x")

        self.assertEqual([a_field.default for a_field in screen.fields], ["x", None])
        self.assertIsNone(self.screen.fields[0].default)

    def test_an_unknown_field_is_refused(self):
        with self.assertRaises(ValueError):
            with_defaults(self.screen, nope="x")


if __name__ == "__main__":
    unittest.main()
