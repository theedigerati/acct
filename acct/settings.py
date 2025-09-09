import os
import warnings
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from django.core.management.utils import get_random_secret_key
from django.core.validators import URLValidator

from acct.core.languages import LANGUAGES as CORE_LANGUAGES


def get_list(text):
    return [item.strip() for item in text.split(",") if item]


def get_bool_from_env(name, default_value):
    """Retrieve and convert an environment variable to a boolean object.

    Accepted values are `true` (case-insensitive) and `1`, any other value resolves to `False`.
    """
    value = os.environ.get(name)
    if value is None:
        return default_value
    return value.lower() in ("true", "1")


def get_url_from_env(name, *, schemes=None) -> str | None:
    if name in os.environ:
        value = os.environ[name]
        message = f"{value} is an invalid value for {name}"
        URLValidator(schemes=schemes, message=message)(value)
        return value
    return None


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = get_bool_from_env("DEBUG", True)

ALLOWED_HOSTS = get_list(os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1"))

if not SECRET_KEY and DEBUG:
    warnings.warn(
        "SECRET_KEY not configured, using a random temporary key.", stacklevel=1
    )
    SECRET_KEY = get_random_secret_key()

RSA_PRIVATE_KEY = os.environ.get("RSA_PRIVATE_KEY", None)
RSA_PRIVATE_PASSWORD = os.environ.get("RSA_PRIVATE_PASSWORD", None)
JWT_MANAGER_PATH = os.environ.get(
    "JWT_MANAGER_PATH", "acct.core.auth.manager.JWTManager"
)

ENABLE_SSL: bool = get_bool_from_env("ENABLE_SSL", False)

# URL on which Acct is hosted (e.g., https://api.example.com/).
# This has precedence over ENABLE_SSL.
PUBLIC_URL: str | None = get_url_from_env("PUBLIC_URL", schemes=["http", "https"])
if PUBLIC_URL:
    if os.environ.get("ENABLE_SSL") is not None:
        warnings.warn(
            "ENABLE_SSL is ignored on URL generation if PUBLIC_URL is set.",
            stacklevel=1,
        )
    ENABLE_SSL = urlparse(PUBLIC_URL).scheme.lower() == "https"

if ENABLE_SSL:
    SECURE_SSL_REDIRECT = not DEBUG


INSTALLED_APPS = [
    # External apps that need to go before django's
    # "storages",
    # Django modules
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django_celery_beat",
    # Local apps
    "acct.core",
    "acct.people",
    # External apps
    "django_measurement",
    "mptt",
    "django_countries",
    "django_filters",
    "phonenumber_field",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "acct.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "acct.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DB_CONN_MAX_AGE = int(os.environ.get("DB_CONN_MAX_AGE", 0))
DB_SSL_REQUIRE = get_bool_from_env("DB_SSL_REQUIRE", False)
DB_URL = os.environ.get("DB_URL", "postgres://postgres:password@localhost:5432/acct")

DATABASES = {
    "default": dj_database_url.parse(
        DB_URL,
        conn_max_age=DB_CONN_MAX_AGE,
        conn_health_checks=True,
        ssl_require=DB_SSL_REQUIRE,
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"
LANGUAGES: list[tuple[str, str]] = CORE_LANGUAGES

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "user.User"

ADMIN_USER_RESTRICTIONS = [
    "delete_organisation",
]

MANAGER_USER_RESTRICTIONS = [
    *ADMIN_USER_RESTRICTIONS,
    "add_organisation",
    "view_all_organisations",
]


AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "django-db")
