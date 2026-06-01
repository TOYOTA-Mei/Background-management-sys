"""
Django settings for QianHoufenli project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# 加载.env环境变量文件
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Build paths inside the project like this: BASE_DIR / 'subdir'.

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-test-key-keep-it-safe')

# 🔥 正常开启调试，绝对不破坏配置
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '*').split(',')]

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user',
    'role',
    'menu',
    'rest_framework',
    'rest_framework_jwt',
    # 跨域组件
    'corsheaders',
    # API文档
    'drf_yasg',
]

MIDDLEWARE = [
    # 跨域中间件（必须第一行）
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'user.middleware.JwtAuthenticationMiddleware',
]

# 🔥 核心路由配置（你丢失的就是这个）
ROOT_URLCONF = 'QianHoufenli.urls'

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'QianHoufenli.wsgi.application'

# Database
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.mysql')

if DB_ENGINE == 'django.db.backends.mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'db_admin'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': int(os.getenv('DB_PORT', 3306)),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.getenv('DB_NAME', 'db.sqlite3'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 跨域完全放开
CORS_ALLOW_ALL_ORIGINS = True

MEDIA_ROOT = BASE_DIR / os.getenv('MEDIA_ROOT', 'media')
MEDIA_URL = os.getenv('MEDIA_URL', 'media/')

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': int(os.getenv('CACHE_TIMEOUT', 3600)),  # 默认1小时
    }
}
