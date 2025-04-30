import dj_database_url
from pathlib import Path
from decouple import config, Csv
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="not-so-secret")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default=".acc, acc", cast=Csv())


# Application definition

SHARED_APPS = [
    "django_tenants",  # 3rd party
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party apps
    "rest_framework",
    "tenant_users.permissions",
    "tenant_users.tenants",
    "django_celery_results",
    "drf_spectacular",
    # internal apps
    "apps.user",
    "apps.organisation",
]

TENANT_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "tenant_users.permissions",
    # internal apps
    "apps.department",
    "apps.inventory.item",
    "apps.tax",
    "apps.accounting",
    "apps.address",
    "apps.sales.client",
    "apps.sales.invoice",
    "apps.purchase.vendor",
    "apps.purchase.bill",
    "apps.purchase.expense",
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
PUBLIC_SCHEMA_URLCONF = "core.urls_public"

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

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases


DATABASES = {
    "default": dj_database_url.parse(
        config("DATABASE_URL", default="postgres://postgres:password@localhost:5432/acc"),
        engine="django_tenants.postgresql_backend",
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=config("SSL_REQUIRE", default=False, cast=bool),
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

# Multinants settings
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)
TENANT_USERS_DOMAIN = config("APP_DOMAIN_NAME", default="acc")
TENANT_MODEL = "organisation.Tenant"
TENANT_DOMAIN_MODEL = "organisation.Domain"
BASE_TENANT_SLUG = config("BASE_TENANT_SLUG", default="acme")
BASE_TENANT_OWNER_EMAIL = config("BASE_TENANT_OWNER_EMAIL", default="meta@localhost")

AUTHENTICATION_BACKENDS = ("tenant_users.permissions.backend.UserBackend",)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "core.permissions.BelongsToOrganisation",
        "core.permissions.BaseModelPermissions",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "COERCE_DECIMAL_TO_STRING": False,
    "SEARCH_PARAM": "q",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "acc",
    "DESCRIPTION": "Double-entry accounting REST API.",
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

PERMISSION_CATEGORIES = {
    "organisation": ["user", "department", "organisation"],
    "accounting": ["tax", "account", "account sub type"],
    "sales": [
        "invoice",
        "client",
        "payment received",
    ],
    "purchase": [
        "bill",
        "vendor",
        "payment made",
        "expense",
    ],
}

CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="django-db")
