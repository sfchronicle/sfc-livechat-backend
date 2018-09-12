# chat/settings.py

import os

# Setting Up directory paths
SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.join(
    os.path.abspath(
        os.path.join(SETTINGS_DIR, os.path.pardir),
    ),
)
BASE_DIR = ROOT_DIR

# Importing the secret key from the .env file
SECRET_KEY = os.getenv("secret_key")

# Setting up working variables.
# These can be manually switched or imported from the .env file if you have multiple working environments.
DEBUG = True
DEBUG_TOOLBAR = True

DEVELOPMENT = True
PRODUCTION = False

# Setting up host URLs that will be able to serve our app
ALLOWED_HOSTS = ["0.0.0.0"]

# It's ok Django, we don't need to scream about field length limits
SILENCED_SYSTEM_CHECKS = ['mysql.E001']

# Adding ngrok to hosts in DEVELOPMENT (more on ngrok later)
if DEVELOPMENT:
    ALLOWED_HOSTS += '*.ngrok.io'

# Django Boilerplate
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'livechat',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_WHITELIST = (
    'sfchronicle.com',
    'projects.sfchronicle.com',
    'localhost:3000',
    '0.0.0.0:3000'
)

ROOT_URLCONF = 'livechat.urls'

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

# SQLite Database (Django Boilerplate)
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db',
        'USER': os.getenv("db_user"),
        'PASSWORD': os.getenv("db_pass"), 
        'HOST': os.getenv("db_host"),
        'PORT': '',
    }
}

# Password validation (Django Boilerplate)
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
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


# Internationalization (Django Boilerplate)
# https://docs.djangoproject.com/en/1.11/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

# Adding our API keys from our .env file
SLACK_APP_TOKEN = os.getenv("slack_app_token")
SLACK_BOT_TOKEN = os.getenv("slack_bot_token")
SLACK_VERIFICATION_TOKEN = os.getenv("slack_verification_token")