import hmac
from urllib.parse import urlsplit
from functools import wraps
from flask import Blueprint, jsonify, request, current_app

from .sessions import get_current_session_record

security_bp = Blueprint("security", __name__)



def require_csrf(view_function):
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        session_record = get_current_session_record()

        if session_record is None:
            return jsonify({
                "error": "Authentication required"
            }), 401

        origin = request.headers.get("Origin")

        if not is_trusted_origin(origin):
            return jsonify({
                "error": "Untrusted origin"
            }), 403

        supplied_token = request.headers.get(
            "X-CSRF-Token", ""
        )

        expected_token = session_record["csrf_token"]

        if not validate_csrf_token(
            expected_token,
            supplied_token
        ):
            return jsonify({
                "error": "Invalid CSRF token"
            }), 403

        return view_function(*args, **kwargs)

    return wrapped
def validate_csrf_token():
    record = get_current_session_record()

    if record is None:
        return False

    expected = record["csrf_token"]
    supplied = request.headers.get("X-CSRF-Token")

    if not isinstance(expected, str):
        return False

    if not isinstance(supplied, str):
        return False

    return hmac.compare_digest(expected, supplied)


def is_trusted_origin(origin):
    if not isinstance(origin, str):
        return False

    try:
        parsed = urlsplit(origin)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.netloc:
            return False

        if parsed.username or parsed.password:
            return False

        if parsed.path or parsed.query or parsed.fragment:
            return False

        return origin == current_origin()

    except ValueError:
        return False


def current_origin():
    from flask import current_app

    return current_app.config["TRUSTED_ORIGIN"]


@security_bp.get("/api/csrf")
def csrf_token():
    record = get_current_session_record()

    if record is None:
        return jsonify({"error": "unauthorized"}), 401

    response = jsonify({
        "csrf_token": record["csrf_token"]
    })

    response.headers["Cache-Control"] = "no-store"

    return response
@security_bp.post("/api/security-demo")
def security_demo():
    record = get_current_session_record()

    if record is None:
        return jsonify({"error": "unauthorized"}), 401

    origin = request.headers.get("Origin")

    if not is_trusted_origin(origin):
        return jsonify({"error": "untrusted_origin"}), 403

    if not validate_csrf_token():
        return jsonify({"error": "invalid_csrf_token"}), 403

    return jsonify({
        "message": "request_accepted"
    })