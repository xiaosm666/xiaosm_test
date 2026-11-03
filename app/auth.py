import re
import time
import sqlite3
from functools import wraps
from .sessions import get_current_user
from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from .audit import audit_event
from .database import get_db
from .sessions import (
    create_session,
    get_current_user,
    revoke_session,
    set_session_cookie,
    clear_session_cookie,
    SESSION_COOKIE,
)
auth_bp = Blueprint("auth", __name__)

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")

def require_roles(*allowed_roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped(*args, **kwargs):
            user = get_current_user()

            if user is None:
                return jsonify({"error": "Authentication required"}), 401

            if user["role"] not in allowed_roles:
                return jsonify({"error": "Forbidden"}), 403

            return view_function(*args, **kwargs)

        return wrapped

    return decorator

def validate_registration(data):
    if not isinstance(data, dict):
        return "invalid_json"

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str):
        return "invalid_username"

    if not USERNAME_PATTERN.fullmatch(username):
        return "invalid_username"

    if not isinstance(password, str):
        return "invalid_password"

    if len(password) < 12 or len(password) > 128:
        return "invalid_password"

    if "\x00" in password:
        return "invalid_password"

    return None


@auth_bp.post("/api/register")
def register():
    if not request.is_json:
        return jsonify({"error": "json_required"}), 400

    data = request.get_json(silent=True)

    error = validate_registration(data)

    if error:
        return jsonify({"error": error}), 400

    username = data["username"]
    password = data["password"]

    password_hash = generate_password_hash(password)

    db = get_db()

    try:
        cursor = db.execute(
            """
            INSERT INTO users (
                username,
                password_hash,
                role,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                password_hash,
                "user",
                int(time.time()),
            ),
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "username_unavailable"}), 409

    return jsonify({
        "message": "registration_successful",
        "user_id": cursor.lastrowid,
    }), 201

@auth_bp.post("/api/login")
def login():
    if not request.is_json:
        return jsonify({"error": "json_required"}), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "invalid_request"}), 400

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str):
        return jsonify({"error": "invalid_credentials"}), 401

    if not isinstance(password, str):
        audit_event(
            "login_failed",
            resource_type="user",
            result="failure"
        )
        return jsonify({"error": "invalid_credentials"}), 401

    if len(username) > 30 or len(password) > 128:
        return jsonify({"error": "invalid_credentials"}), 401

    user = get_db().execute(
        """
        SELECT id, username, password_hash, role
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    if user is None or not check_password_hash(
        user["password_hash"],
        password,
    ):
        return jsonify({"error": "invalid_credentials"}), 401

    # 如果浏览器已经持有旧 Session，先撤销
    old_session = request.cookies.get(SESSION_COOKIE)

    if old_session:
        revoke_session(old_session)

    # 创建全新的 Session
    session_id = create_session(user["id"])

    response = jsonify({
        "message": "login_successful",
        "username": user["username"],
        "role": user["role"],
    })
    audit_event(
    "login_success",
    user_id=user["id"],
    resource_type="user"
    )
    return set_session_cookie(response, session_id)


@auth_bp.get("/api/me")
def me():
    user = get_current_user()

    if user is None:
        return jsonify({"error": "unauthorized"}), 401

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    })


@auth_bp.post("/api/logout")
def logout():
    session_id = request.cookies.get(SESSION_COOKIE)

    if session_id:
        revoke_session(session_id)

    response = jsonify({
        "message": "logout_successful"
    })

    return clear_session_cookie(response)