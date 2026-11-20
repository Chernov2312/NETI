from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent


env = environ.Env()
env.read_env(BASE_DIR.parent / '.env')

SECRET_KEY = env.str('DJANGO_SECRET_KEY')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list(
    'DJANGO_ALLOWED_HOSTS',
    default=['localhost', '127.0.0.1'],
)
AUTH_USER_MODEL = 'user.User'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authentication.apps.AuthenticationConfig',
    'core.apps.CoreConfig',
    'feedback.apps.FeedbackConfig',
    'home.apps.HomeConfig',
    'project.apps.ProjectConfig',
    'user.apps.UserConfig',
    'sorl.thumbnail',
    'django_cleanup.apps.CleanupConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    INSTALLED_APPS.insert(-1, 'debug_toolbar')
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
    INTERNAL_IPS = ['127.0.0.1']

ROOT_URLCONF = 'neti.urls'

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

WSGI_APPLICATION = 'neti.wsgi.application'

database_engine = env.str('DJANGO_DB_ENGINE', default='postgresql')
if database_engine == 'postgresql':
    database = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': env.str('POSTGRES_HOST', default='127.0.0.1'),
        'PORT': env.int('POSTGRES_PORT', default=5432),
        'NAME': env.str('POSTGRES_DB'),
        'USER': env.str('POSTGRES_USER'),
        'PASSWORD': env.str('POSTGRES_PASSWORD'),
    }
elif database_engine == 'sqlite':
    database = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': env.str(
            'DJANGO_SQLITE_PATH',
            default=str(BASE_DIR / 'db.sqlite3'),
        ),
    }
else:
    raise ImproperlyConfigured(
        'DJANGO_DB_ENGINE должен быть postgresql или sqlite.',
    )

DATABASES = {'default': database}
TEST_RUNNER = 'neti.test_runner.ProjectDiscoverRunner'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation'
        '.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
        '.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
        '.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
        '.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'ru-RU'
USE_I18N = True

USE_TZ = True
TIME_ZONE = 'UTC'

LANGUAGES = [
    ('ru', _('Русский')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
STATIC_ROOT = BASE_DIR / 'collect_static'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static_dev',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR.parent / env.str(
    'DJANGO_MEDIA_ROOT',
    default='neti/media',
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'authentication:login'

EMAIL_BACKEND = (
    'django.core.mail.backends.console.EmailBackend'
    if DEBUG
    else 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = env.str('DJANGO_EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('DJANGO_EMAIL_PORT', default=25)
EMAIL_HOST_USER = env.str('DJANGO_EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('DJANGO_EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('DJANGO_EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = env.bool('DJANGO_EMAIL_USE_SSL', default=False)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env.str(
    'DJANGO_DEFAULT_FROM_EMAIL',
    default='webmaster@localhost',
)
