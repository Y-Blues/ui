import unittest

from ycappuccino.ui.application import (
    Application,
    MenuEntry,
    Step,
    load_application,
    load_application_yaml,
    prefill_values,
    with_defaults,
)
from ycappuccino.ui.model import Field, Screen

APPLICATION_YAML = """
title: Administration
login: {screen: login, transport: login}
menu:
  - label: Créer un rôle
    steps:
      - {screen: role, transport: crud}
  - label: Créer un utilisateur
    steps:
      - {screen: create_login, transport: services}
      - {screen: account, transport: crud, prefill: {login: values.login}}
      - {screen: role_account, transport: crud, prefill: {account: result._id}}
"""


class TestLoadApplication(unittest.TestCase):

    def test_loads_the_login_the_menu_and_the_steps(self):
        application = load_application_yaml(APPLICATION_YAML)

        self.assertEqual(
            application,
            Application(
                title="Administration",
                login=Step(screen="login", transport="login"),
                menu=(
                    MenuEntry(label="Créer un rôle", steps=(Step(screen="role", transport="crud"),)),
                    MenuEntry(
                        label="Créer un utilisateur",
                        steps=(
                            Step(screen="create_login", transport="services"),
                            Step(screen="account", transport="crud", prefill={"login": "values.login"}),
                            Step(screen="role_account", transport="crud", prefill={"account": "result._id"}),
                        ),
                    ),
                ),
            ),
        )

    def test_the_labels_have_defaults_and_can_be_overridden(self):
        application = load_application({"title": "t", "login": {"screen": "l", "transport": "l"}, "menu": [],
                                         "back": "Menu"})

        self.assertEqual((application.sign_out, application.saved, application.back),
                         ("Se déconnecter", "Enregistré.", "Menu"))

    def test_a_prefill_reads_the_values_or_the_result_of_the_previous_step_only(self):
        with self.assertRaises(ValueError):
            load_application({"title": "t", "login": {"screen": "l", "transport": "l"},
                               "menu": [{"label": "x", "steps": [{"screen": "s", "transport": "t",
                                                                   "prefill": {"a": "session.user"}}]}]})


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
