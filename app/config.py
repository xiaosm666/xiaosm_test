import os
from datetime import timedelta


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    MAX_CONTENT_LENGTH = 1024 * 1024

    DATABASE = os.environ.get("DATABASE_PATH")
    STORAGE_DIR = os.environ.get("STORAGE_DIR")

    TRUSTED_ORIGIN = os.environ.get(
        "TRUSTED_ORIGIN",
        "http://127.0.0.1:8121"
    )


class DevelopmentConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    TRUSTED_ORIGIN = os.environ.get("TRUSTED_ORIGIN")

    @classmethod
    def validate(cls):
        required = [
            "SECRET_KEY",
            "TRUSTED_ORIGIN",
        ]

        missing = [
            name for name in required
            if not os.environ.get(name)
        ]

        if missing:
            raise RuntimeError(
                "缺少生产环境配置：" + ", ".join(missing)
            )

        if not cls.TRUSTED_ORIGIN.startswith("https://"):
            raise RuntimeError(
                "生产环境 TRUSTED_ORIGIN 必须使用 HTTPS"
            )