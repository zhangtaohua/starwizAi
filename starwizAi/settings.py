"""
Django settings for starwizAi project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
import platform
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(".") / ".env"

load_dotenv(dotenv_path=env_path)


# 判断当前操作系统
current_os = platform.system()

if current_os == "Windows":
    os.environ["PROJ_LIB"] = r"C:\Python312\Lib\site-packages\pyproj\proj_dir\share\proj"
# elif current_os == "Linux":
#     os.environ["PROJ_LIB"] = r"/usr/local/lib/python3.12/site-packages/pyproj/proj_dir/share/proj"
# elif current_os == "Darwin":
#     os.environ["PROJ_LIB"] = r"/usr/local/lib/python3.12/site-packages/pyproj/proj_dir/share/proj"


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = "#uk62v_xzund$4!2iyk9#800fmurj9d861RJxkrisinigueh2qe^f*mtohvh^z="
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "#uk62v_xzund$4!2iyk9#800fmurj9d861RJxkrisinigueh2qe^f*mtohvh^z=")

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = False
DEBUG = bool(os.environ.get("DJANGO_DEBUG", True))

ALLOWED_HOSTS = []
# ALLOWED_HOSTS = ["*"]
ALLOWED_HOSTS_STR = os.getenv("DJANGO_ALLOWED_HOSTS")
if ALLOWED_HOSTS_STR:
    ALLOWED_HOSTS = ALLOWED_HOSTS_STR.split(" ")

# Application definition

INSTALLED_APPS = [
    "ais.apps.AisConfig",
    "django_q",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # 'django.middleware.csrf.CsrfViewMiddleware',
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "starwizAi.urls"

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

WSGI_APPLICATION = "starwizAi.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
    "postgres": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "aidb",  # 数据库名称
        "USER": "postgres",  # 登录数据库用户名
        "PASSWORD": "123456",  # 登录数据库密码
        "HOST": "192.168.3.237",  # 数据库服务器的主机地址
        "PORT": "54327",  # 数据库服务的端口号
    },
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
STATIC_URL = "static/"

STATICFILES_DIRS = [
    # ...
    # ("assets", "D:/Work/project/Python/starwizAi/assets"),
    ("assets", os.path.join(BASE_DIR, "assets")),
]

# 或者在生产环境中使用
# STATIC_ROOT = os.path.join(BASE_DIR, "assets")

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django Q2
Q_CLUSTER = {
    "name": "starwiz_ai_project",
    "workers": 8,
    "recycle": 500,
    "timeout": 6000,
    "retry": 7000,
    "compress": True,
    "save_limit": 250,
    "queue_limit": 500,
    "cpu_affinity": 1,
    "label": "Django Q2",
    "redis": {
        "host": "192.168.3.247",
        "port": 56379,
        "db": 1,
    },
    "ALT_CLUSTERS": {
        "long": {
            "timeout": 6000,
            "retry": 7000,
            "max_attempts": 3,
        },
        "short": {
            "timeout": 5000,
            "retry": 6000,
            "max_attempts": 1,
        },
    },
}

# CUSTOM VAR
PRODUCT_ASSETS_BASE_URL = "http://192.168.3.246"
PRODUCT_ASSETS_BASE_DIR = "/mnt/nas246/public/DataWiz/ais"

DOWNLOAD_TIFF_URL = "/assets/ai/downloads/tiff/"
AI_RESULTS_URL = "/assets/ai/results/"

DOWNLOAD_TIFF_PATH = BASE_DIR / "assets/ai/downloads/tiff/"
AI_RESULTS_PATH = BASE_DIR / "assets/ai/results/"

MAX_TRY_DOWNLOADS_TIMES = 5
MAX_TRY_AI_PROCESS_TIMES = 5
