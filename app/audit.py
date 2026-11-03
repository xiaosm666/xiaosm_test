import json
import logging
import re
from datetime import datetime, timezone
from flask import current_app, request, g
from logging.handlers import RotatingFileHandler

def safe_log_value(value, max_length=128):
    if value is None:
        return None

    value = str(value)

    value = value.replace("\r", "\\r")
    value = value.replace("\n", "\\n")

    return value[:max_length]

def configure_audit_logging(app):
    logger = logging.getLogger("security_audit")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    # 如果是测试环境，不创建文件日志，直接返回，避免找logs文件夹
    if app.config.get("TESTING"):
        # 测试环境：不写文件，直接放一个logger进去，避免KeyError
        app.extensions["security_audit_logger"] = logger
        return
    if not logger.handlers:
        log_path = (
            app.root_path + "/../logs/security.log"
        )

        handler = RotatingFileHandler(
            log_path,
            maxBytes=1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )

        handler.setFormatter(
            logging.Formatter("%(message)s")
        )

        logger.addHandler(handler)

    app.extensions["security_audit_logger"] = logger


def audit_event(
    event_type,
    user_id=None,
    resource_type=None,
    resource_id=None,
    result="success",
):
    logger = current_app.extensions[
        "security_audit_logger"
    ]

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "event_type": safe_log_value(
            event_type, 64
        ),

        "user_id": user_id,

        "resource_type": safe_log_value(
            resource_type, 64
        ),

        "resource_id": safe_log_value(
            resource_id, 128
        ),

        "result": safe_log_value(
            result, 32
        ),
    }

    logger.info(
        json.dumps(event, ensure_ascii=False)
    )