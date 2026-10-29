"""
Django settings for SmartMed AI project.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if present
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "smartmed-ai-insecure-dev-key-change-in-prod-2026")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

allowed_hosts_raw = os.environ.get("ALLOWED_HOSTS", "*")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_raw.split(",") if h.strip()]
if "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("*")

# Application definition
INSTALLED_APPS = [
    "daphne",  # ASGI Daphne must be before django.contrib.staticfiles
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "channels",

    # SmartMed AI core apps
    "apps.authentication",
    "apps.dashboard",
    "apps.uploads",
    "apps.review",
    "apps.colorization",
    "apps.lung_analysis",
    "apps.brain_tumor",
    "apps.analysis",
    "apps.reports",
    "apps.evaluations",
    "apps.devices",
    "apps.audit",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.authentication.middleware.MongoUserMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.dashboard.context_processors.smartmed_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Django Channels layer (InMemory for fast local deployment)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# SQLite is used strictly for internal Django session table; all medical and application data resides in MongoDB
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Custom Authentication Backends
AUTHENTICATION_BACKENDS = [
    "apps.authentication.backends.MongoAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (Medical Scans, Colorized Outputs, Grad-CAM, Reports)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom Application Constants
def _resolve_server_host():
    """Auto-detect the LAN IP address so QR codes always encode the correct URL."""
    env_host = os.environ.get("SERVER_HOST", "").strip()
    if env_host and env_host.lower() != "auto":
        return env_host
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

SERVER_HOST = _resolve_server_host()
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8000"))
UPLOAD_MAX_MB = int(os.environ.get("UPLOAD_MAX_MB", "25"))
QR_SESSION_EXPIRE_MINUTES = int(os.environ.get("QR_SESSION_EXPIRE_MINUTES", "30"))

# Login URLs
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/auth/login/"

# CORS Configuration for mobile uploads and external device APIs
CORS_ALLOW_ALL_ORIGINS = True

# Build CSRF trusted origins dynamically to cover the detected LAN IP
_csrf_origins = [
    f"http://{SERVER_HOST}:{SERVER_PORT}",
    f"http://localhost:{SERVER_PORT}",
    f"http://127.0.0.1:{SERVER_PORT}",
    f"http://{SERVER_HOST}",
    "https://*.loca.lt",
    "https://*.ngrok-free.app",
    "https://*.trycloudflare.com",
]
# Add common LAN subnets for mobile phone access
for _subnet_prefix in ["10.", "172.", "192.168."]:
    if SERVER_HOST.startswith(_subnet_prefix):
        # Add the specific IP with and without port
        _csrf_origins.append(f"http://{SERVER_HOST}:{SERVER_PORT}")
        break
CSRF_TRUSTED_ORIGINS = _csrf_origins

# Allow any host to connect (mobile phones on LAN)
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
