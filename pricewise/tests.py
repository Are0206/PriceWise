import os
import subprocess
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from pricewise.env import env_bool, get_env, parse_bool, read_env_file, validate_production

BASE_DIR = Path(__file__).resolve().parent.parent
NO_ENV_FILE = BASE_DIR / "does-not-exist.env"
STRONG_KEY = "k" * 60


class EnvHelperTests(SimpleTestCase):
    def test_true_and_false_spellings(self):
        for raw in ("1", "true", "TRUE", "Yes", " on "):
            self.assertIs(parse_bool("X", raw), True)
        for raw in ("0", "false", "False", "NO", "off"):
            self.assertIs(parse_bool("X", raw), False)

    def test_invalid_boolean_is_rejected(self):
        for raw in ("Fasle", "2", "debug", "y"):
            with self.assertRaises(ImproperlyConfigured):
                parse_bool("X", raw)

    def test_missing_required_boolean_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            env_bool("X", environ={}, env_file=NO_ENV_FILE)

    def test_missing_optional_boolean_uses_default(self):
        self.assertIs(env_bool("X", True, environ={}, env_file=NO_ENV_FILE), True)

    def test_environment_wins_over_env_file(self):
        env_file = BASE_DIR / "pricewise" / "test-tmp.env"
        env_file.write_text('# comment\nA="from file"\nB=only-file\n')
        try:
            self.assertEqual(read_env_file(env_file), {"A": "from file", "B": "only-file"})
            self.assertEqual(get_env("A", environ={"A": "from env"}, env_file=env_file), "from env")
            self.assertEqual(get_env("B", environ={}, env_file=env_file), "only-file")
        finally:
            env_file.unlink()


class ProductionValidationTests(SimpleTestCase):
    def test_valid_production_config(self):
        self.assertEqual(validate_production(False, STRONG_KEY, ["pricewise.example.com"]), [])

    def test_debug_must_be_false(self):
        self.assertEqual(len(validate_production(True, STRONG_KEY, ["a.com"])), 1)

    def test_secret_key_rules(self):
        for key in ("", "short", "django-insecure-" + "x" * 60):
            self.assertEqual(len(validate_production(False, key, ["a.com"])), 1, key)

    def test_allowed_hosts_rules(self):
        for hosts in ([], ["*"], ["a.com", "*"]):
            self.assertEqual(len(validate_production(False, STRONG_KEY, hosts)), 1, hosts)


def load_settings(**env):
    """Import settings in a clean process so the developer's own variables don't leak in."""
    clean = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    clean.update(env)
    return subprocess.run(
        [sys.executable, "-c", "import pricewise.settings as s; print(s.DEBUG, s.ALLOWED_HOSTS, s.SESSION_COOKIE_SECURE if hasattr(s, 'SESSION_COOKIE_SECURE') else None)"],
        cwd=BASE_DIR, env=clean, capture_output=True, text=True,
    )


class SettingsProfileTests(SimpleTestCase):
    def test_development_is_the_default(self):
        result = load_settings()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("True", result.stdout)

    def test_debug_string_false_turns_debug_off(self):
        result = load_settings(DJANGO_DEBUG="False")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("False"))

    def test_production_without_secret_key_refuses_to_start(self):
        result = load_settings(DJANGO_ENV="production", DJANGO_DEBUG="false", DJANGO_ALLOWED_HOSTS="a.com")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_production_with_insecure_key_refuses_to_start(self):
        result = load_settings(DJANGO_ENV="production", DJANGO_DEBUG="false", DJANGO_ALLOWED_HOSTS="a.com",
                               DJANGO_SECRET_KEY="django-insecure-" + "x" * 60)
        self.assertNotEqual(result.returncode, 0)

    def test_production_with_wildcard_host_refuses_to_start(self):
        result = load_settings(DJANGO_ENV="production", DJANGO_DEBUG="false", DJANGO_ALLOWED_HOSTS="*",
                               DJANGO_SECRET_KEY=STRONG_KEY)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", result.stderr)

    def test_production_requires_debug_to_be_declared(self):
        result = load_settings(DJANGO_ENV="production", DJANGO_ALLOWED_HOSTS="a.com", DJANGO_SECRET_KEY=STRONG_KEY)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_DEBUG", result.stderr)

    def test_valid_production_turns_on_secure_cookies(self):
        result = load_settings(DJANGO_ENV="production", DJANGO_DEBUG="false", DJANGO_ALLOWED_HOSTS="a.com",
                               DJANGO_SECRET_KEY=STRONG_KEY)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False ['a.com'] True")

    def test_unknown_profile_is_rejected(self):
        result = load_settings(DJANGO_ENV="prod")
        self.assertNotEqual(result.returncode, 0)

    def test_deploy_check_only_reports_the_accepted_hsts_warnings(self):
        # W005 (HSTS on subdomains) and W021 (HSTS preload) are opt-in on purpose:
        # both are hard to undo, so they stay off until HTTPS is proven on every host.
        clean = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
        clean.update(DJANGO_ENV="production", DJANGO_DEBUG="false", DJANGO_ALLOWED_HOSTS="a.com",
                     DJANGO_SECRET_KEY=STRONG_KEY + "!@#$%^&*()")
        result = subprocess.run([sys.executable, "manage.py", "check", "--deploy"],
                                cwd=BASE_DIR, env=clean, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = result.stdout + result.stderr
        reported = {word.strip("():") for word in output.split() if word.startswith("(security.W")}
        self.assertEqual(reported, {"security.W005", "security.W021"}, output)


class ErrorPageTests(SimpleTestCase):
    def test_500_template_renders_without_context(self):
        from django.template.loader import render_to_string
        html = render_to_string('500.html')
        self.assertIn('Algo salió mal', html)
