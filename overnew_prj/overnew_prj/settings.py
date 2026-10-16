import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "account",
    "users",
    "discussion",
    "recommend",
    "feed",
    "archive",
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

ROOT_URLCONF = "overnew_prj.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "overnew_prj.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH") or BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = 'users.User'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# 비밀번호 유효성 검사 설정
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # 사용자 속성 유사성 검사
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # 최소 비밀번호 길이 설정
        'OPTIONS': {
            'min_length': 8,  # 최소 8자
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # 일반적인 비밀번호 방지
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # 숫자만 비밀번호 방지
    },
]

# 국제화 설정
LANGUAGE_CODE = 'ko-kr'  # 언어 설정 (한국어)
TIME_ZONE = 'Asia/Seoul'  # 시간대 설정
USE_I18N = True  # 국제화 사용
USE_TZ = True  # 시간대 사용

# 기본 Primary Key 필드 설정
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 이메일 설정
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 이메일 백엔드 설정
EMAIL_HOST = 'smtp.gmail.com'  # SMTP 서버 주소
EMAIL_PORT = 587  # SMTP 포트
EMAIL_USE_TLS = True  # TLS 사용
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

LOGIN_URL = 'account:login'

# 이메일 인증하는거 개발 중엔 번거로우니 꺼놓은거
EMAIL_VERIFICATION_REQUIRED = False  # 개발 중엔 False, 배포할 때 True로 변경