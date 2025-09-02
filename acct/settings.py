from pathlib import Path

import dj_database_url
from decouple import Csv, config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="not-so-secret")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default=".acct, acct", cast=Csv())


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

DB_CONN_MAX_AGE = config("DB_CONN_MAX_AGE", default=0, cast=int)
DB_SSL_REQUIRE = config("DB_SSL_REQUIRE", default=False, cast=bool)
DB_URL = config("DB_URL", default="postgres://postgres:password@localhost:5432/acct")

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

CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="django-db")
