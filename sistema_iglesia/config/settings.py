"""
Configuración de Django para el Sistema de Gestión de la Iglesia.

Los valores sensibles y los que cambian entre desarrollo y producción se leen
de variables de entorno (ver deploy/.env.example). En desarrollo, sin variables,
todo sigue funcionando como antes: DEBUG activo, MySQL local y 127.0.0.1 como
host permitido.

Para producción basta con definir DJANGO_DEBUG=0, DJANGO_SECRET_KEY,
DJANGO_ALLOWED_HOSTS y DJANGO_CSRF_TRUSTED_ORIGINS en el archivo .env que lee
systemd (ver deploy/README.md).
"""

from pathlib import Path
import os
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def _env_booleano(nombre, por_defecto=False):
    """Lee un booleano de entorno: 1/true/si/yes son verdaderos."""
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ("1", "true", "si", "sí", "yes", "on")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# En producción DJANGO_SECRET_KEY es obligatorio: el fallback solo sirve en dev.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-me")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_booleano("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver"
    ).split(",")
    if host.strip()
]

# Orígenes de confianza para el CSRF cuando el sitio va detrás de Nginx/HTTPS.
CSRF_TRUSTED_ORIGINS = [
    origen.strip()
    for origen in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origen.strip()
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps del sistema (Semana 4)
    "miembros",
    "inventario",
    "eventos",
    "reportes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sirve los estáticos (admin incluido) sin depender de Nginx.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Control de acceso del sistema: sesión obligatoria y permisos por rol.
    "config.middleware.LoginObligatorioMiddleware",
    "config.middleware.PermisosPorRolMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.permisos",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database: MySQL via PyMySQL (ver config/__init__.py). Credenciales por entorno.
# BD dev: cursor_demo | BD prod: iglesia_db.
# Al correr 'manage.py test' se usa SQLite en memoria: el usuario MySQL solo
# tiene permisos sobre cursor_demo y no puede crear la BD de pruebas test_*.
if "test" in sys.argv:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_test.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("MYSQL_DB", "cursor_demo"),
            "USER": os.environ.get("MYSQL_USER", "Nuclearblast"),
            "PASSWORD": os.environ.get("MYSQL_PASS", ""),
            "HOST": os.environ.get("MYSQL_HOST", "127.0.0.1"),
            "PORT": os.environ.get("MYSQL_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
            # Reutiliza la conexión entre peticiones (producción con Gunicorn).
            "CONN_MAX_AGE": int(os.environ.get("MYSQL_CONN_MAX_AGE", "60")),
            "CONN_HEALTH_CHECKS": True,
        }
    }


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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


# Sesiones y acceso

LOGIN_URL = "/cuentas/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/cuentas/login/"

# Sin sesión no se ve nada, salvo la pantalla de login y el chequeo de salud.
# La suite de pruebas de las semanas 5-9 no simula sesiones, así que se apaga
# durante `manage.py test`; tests/test_permisos.py lo vuelve a encender con
# override_settings para verificar el control de acceso.
REQUIERE_LOGIN = _env_booleano("DJANGO_REQUIERE_LOGIN", True)
if "test" in sys.argv:
    REQUIERE_LOGIN = False

SESSION_COOKIE_AGE = int(os.environ.get("DJANGO_SESSION_HORAS", "12")) * 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # el formulario necesita leer la cookie en plantillas
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = "es"

TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "America/El_Salvador")

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

# Las tablas existentes usan INT AUTO_INCREMENT (ver modelo_iglesia.sql)
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # Comprime y firma los estáticos con hash para cachearlos para siempre.
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Seguridad para producción (solo se activa cuando DEBUG=0)

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    SECURE_SSL_REDIRECT = _env_booleano("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SEGUNDOS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"


# Registro de eventos y errores

LOG_DIR = Path(os.environ.get("DJANGO_LOG_DIR", BASE_DIR / "logs"))
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except OSError:  # si el usuario no puede crear el directorio, solo consola
    pass

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "archivo": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "iglesia.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "simple",
        },
    },
    "root": {"handlers": ["console", "archivo"], "level": "INFO"},
    "loggers": {
        "django.request": {
            "handlers": ["console", "archivo"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# Email (en producción se puede cambiar a SMTP por entorno)
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    "default": {
        "BACKEND": os.environ.get(
            "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
        ),
    },
}
