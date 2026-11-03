from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
from .security import security_bp
from flask import Flask, jsonify
from . import database
from .auth import auth_bp
from .documents import documents_bp
from .admin import admin_bp
from .uploads import uploads_bp
from .audit import configure_audit_logging
import os
def create_app(test_config=None):
    app = Flask(__name__)

    BASE_DIR = Path(__file__).resolve().parent.parent

    app.config["DATABASE"] = str(
        BASE_DIR / "instance" / "app.db"
    )

    app.config["STORAGE_DIR"] = str(
        BASE_DIR / "storage"
    )

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    environment = os.environ.get(
        "APP_ENV",
        "development"
    )

    if environment == "production":
        from .config import ProductionConfig

        ProductionConfig.validate()
        app.config.from_object(ProductionConfig)

    elif environment == "development":
        from .config import DevelopmentConfig

        app.config.from_object(DevelopmentConfig)

    else:
        raise RuntimeError(
            f"不支持的 APP_ENV：{environment}"
        )

    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "缺少 SECRET_KEY，请设置环境变量"
        )

    Path(app.config["DATABASE"]).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    Path(app.config["STORAGE_DIR"]).mkdir(
        parents=True,
        exist_ok=True
    )

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "application": "Secure Document Manager",
        })

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Frame-Options"] = "DENY"
        return response
    database.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(uploads_bp)
    configure_audit_logging(app)
    return app