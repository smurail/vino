"""
Django settings for vino.site project.

Generated by 'django-admin startproject' using Django 2.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import dynaconf  # type: ignore
from pathlib import Path
from typing import List

# Use dynaconf explicit mode
# See https://www.dynaconf.com/django/#explicit-mode
settings = dynaconf.LazySettings(
    warn_dynaconf_global_settings=True,
    environments=True,
    lowercase_read=False,
    load_dotenv=True,
    default_settings_paths=dynaconf.constants.DEFAULT_SETTINGS_FILES,
)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.as_posix()
DATA_DIR = Path(BASE_DIR, 'data').as_posix()


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = settings.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = settings.get('DEBUG', True)

ALLOWED_HOSTS: List[str] = settings.get('ALLOWED_HOSTS', [])
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'vino.sharekernel.apps.SharekernelConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_currentuser.middleware.ThreadLocalUserMiddleware',
]

ROOT_URLCONF = 'vino.site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vino.site.wsgi.application'

# This is merged with default logging configuration unless LOGGING_CONFIG = None
# https://docs.djangoproject.com/fr/2.2/topics/logging/#configuring-logging
LOGGING = settings.get('LOGGING', {})


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(DATA_DIR, 'db.sqlite3').as_posix(),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = settings.get('TIME_ZONE', 'UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = Path(DATA_DIR, 'static').as_posix()


# Media files

MEDIA_URL = '/files/'
MEDIA_ROOT = Path(DATA_DIR, 'files').as_posix()
DEFAULT_FILE_STORAGE = 'vino.sharekernel.storage.CustomFileSystemStorage'


# Debug toolbar

if settings.get('DEBUG_TOOLBAR'):
    INSTALLED_APPS[-1:-1] = ['debug_toolbar']

    MIDDLEWARE[0:0] = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        'debug_toolbar_force.middleware.ForceDebugToolbarMiddleware',
    ]

    INTERNAL_IPS = [
        '127.0.0.1',
    ]

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_COLLAPSED': True,
        'SQL_WARNING_THRESHOLD': 100
    }
