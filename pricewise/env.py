"""Environment helpers shared by settings.py and management commands.

Values come from the process environment first and then from the project's
.env file, so secrets never live in the code.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}

# Marks a setting that has no default and must be declared.
REQUIRED = object()


def read_env_file(path=ENV_FILE):
    """Parse a simple KEY=value .env file. Missing file means no values."""
    values = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def get_env(name, default=None, environ=None, env_file=ENV_FILE):
    """The process environment wins over the .env file."""
    environ = os.environ if environ is None else environ
    if name in environ:
        return environ[name]
    return read_env_file(env_file).get(name, default)


def parse_bool(name, raw):
    """Strict boolean parsing: "False" must never turn into True."""
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ImproperlyConfigured(
        f"{name} must be one of {sorted(TRUE_VALUES | FALSE_VALUES)}, got {raw!r}."
    )


def env_bool(name, default=REQUIRED, **kwargs):
    raw = get_env(name, **kwargs)
    if raw is None or raw.strip() == "":
        if default is REQUIRED:
            raise ImproperlyConfigured(f"{name} must be set explicitly.")
        return default
    return parse_bool(name, raw)


def env_list(name, default="", **kwargs):
    raw = get_env(name, default, **kwargs)
    return [item.strip() for item in raw.split(",") if item.strip()]


def validate_production(debug, secret_key, allowed_hosts):
    """Return the list of problems that make a production config unsafe."""
    problems = []
    if debug is not False:
        problems.append("DJANGO_DEBUG must be false in production.")
    if not secret_key or len(secret_key) < 50 or secret_key.startswith("django-insecure"):
        problems.append(
            "DJANGO_SECRET_KEY must be set, at least 50 characters long and not a django-insecure key."
        )
    if not allowed_hosts or "*" in allowed_hosts:
        problems.append("DJANGO_ALLOWED_HOSTS must list the real hosts, without '*'.")
    return problems
