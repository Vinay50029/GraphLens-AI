import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(BASE_DIR := Path(__file__).resolve().parent.parent / '.env')

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production-please')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# No database needed — stateless API
DATABASES = {}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True

STATIC_URL = '/static/'

# ─── CORS ───────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',   # Vite dev server
    'http://127.0.0.1:5173',
]
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Allow all in dev for convenience

# ─── DRF ────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}


# ─── File Upload ─────────────────────────────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024   # 200 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024   # 200 MB

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
