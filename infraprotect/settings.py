"""
Django settings for infraprotect project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-uirslahosm*_udwemotzje2fvpi0+ss7e=irj&q$i_b%hp#z#-"
# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = False # True：デプロイ時はFalseとする

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "infra.apps.InfraConfig",
    'storages',
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

ROOT_URLCONF = "infraprotect.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = "infraprotect.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "ja"

TIME_ZONE = "Asia/Tokyo"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# STATIC_URL = "infra/static/"# infra/static/以降のファイルパスをviews.pyで指定
STATIC_URL = "/static/"

if DEBUG:
    STATICFILES_DIRS = ( # 同じくinfra/static/
        os.path.join(BASE_DIR, "/static/"), #「C:\work\django\myproject\myvenv\infraprotect\infra\static\」と同じ
    )

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #「C:\work\django\myproject\myvenv\infraprotect\」と同じ
"""
MEDIA_URL   = "/media/"
if DEBUG:
    MEDIA_ROOT  = os.path.join(BASE_DIR, "media")
else:
    PROJECT_NAME    = os.path.basename(BASE_DIR)
    #↓は一般的なLinuxサーバーにデプロイする場合のパス。クラウドにデプロイする場合、下記は要修正。
    MEDIA_ROOT      = "/var/www/{}/media".format(PROJECT_NAME)
"""
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media') # 「C:\work\django\myproject\myvenv\infraprotect\media」

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = 'list-article'#'index'
LOGOUT_REDIRECT_URL = '/'

DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 10  # 10 MBの例

AUTH_USER_MODEL = 'accounts.CustomUser'

BASE_DIR = Path(__file__).resolve().parent.parent
"""
if not DEBUG: # 27行目のDEBUGがFalseになっていることを確認

    #INSTALLED_APPSにcloudinaryの追加
    INSTALLED_APPS.append('cloudinary')
    INSTALLED_APPS.append('cloudinary_storage')

    # ALLOWED_HOSTSに( Herokuのアプリのドメイン名 )を入力
    # os.environ は環境変数。後で、Herokuの設定に追加をする。
    ALLOWED_HOSTS = [ os.environ["HOST"] ]

    # CSRFトークンの生成、ハッシュ化に使われる。
    SECRET_KEY = os.environ["SECRETKEY"]
    
    # 静的ファイル配信ミドルウェア、whitenoiseを使用。※ 順番不一致だと動かないため下記をそのままコピーする。
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

    # STATICファイルの場所指定
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
    # STATIC_ROOT = BASE_DIR / 'static'
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    
    # DBの設定(HerokuPostgres は PostgreSQLなので、)
    # Heroku＞Heroku Postgres＞Settings＞View Credentials
    # 参考サイト：https://noauto-nolife.com/post/django-deploy-heroku/
    DATABASES = { 
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME'    : os.environ["DB_NAME"],
                'USER'    : os.environ["DB_USER"],
                'PASSWORD': os.environ["DB_PASSWORD"],
                'HOST'    : os.environ["DB_HOST"],
                'PORT': '5432',
                }
            }

    #DBのアクセス設定
    import dj_database_url

    db_from_env = dj_database_url.config(conn_max_age=600, ssl_require=True)
    DATABASES['default'].update(db_from_env)
    

    #cloudinaryの設定
    CLOUDINARY_STORAGE = { 
            'CLOUD_NAME': os.environ["CLOUD_NAME"], 
            'API_KEY'   : os.environ["API_KEY"], 
            'API_SECRET': os.environ["API_SECRET"],
            "SECURE"    : True,
            }
    
    # cloudinary://435863325477269:N337D13Yjy6-J0K8K7d_IgFU_-Y@hslrqdyny
    # cloudinary://[API_KEY]      :[API_SECRET]               @[CLOUD_NAME]
    #これは画像だけ(上限20MB)
    #DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

    #これは動画だけ(上限100MB)
    #DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.VideoMediaCloudinaryStorage'

    #これで全てのファイルがアップロード可能(上限20MB。ビュー側でアップロードファイル制限するなら基本これでいい)
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.RawMediaCloudinaryStorage'
"""
DEFAULT_AUTO_FIELD='django.db.models.AutoField'

if not DEBUG:

    # Herokuデプロイ時に必要になるライブラリのインポート
    import django_heroku
    import dj_database_url

    # ALLOWED_HOSTSにホスト名)を入力
    # ALLOWED_HOSTS = [os.environ.get("HOST", "127.0.0.1")]
    ALLOWED_HOSTS = ['infraprotect-fe1819f27e30.herokuapp.com']
    
    # 静的ファイル配信ミドルウェア、whitenoiseを使用。※順番不一致だと動かないため下記をそのままコピーする。
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
    
    
    # Herokuデータベースを使用
    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME'    : os.environ["DB_NAME"],
                'USER'    : os.environ["DB_USER"],
                'PASSWORD': os.environ["DB_PASSWORD"],
                'HOST'    : os.environ["DB_HOST"],
                'PORT': '5432',
                }
            }
    db_from_env = dj_database_url.config(conn_max_age=600, ssl_require=True)
    DATABASES['default'].update(db_from_env)
    
    # 静的ファイル(static)の存在場所を指定する。
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

    #ストレージ設定。
    AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
    AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    S3_URL = 'http://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
    MEDIA_URL = S3_URL

    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None