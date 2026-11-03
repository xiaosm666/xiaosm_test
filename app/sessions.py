import hashlib
import secrets
import time

from flask import current_app, jsonify, request, make_response

from .database import get_db

SESSION_COOKIE = "lab_session"
SESSION_TTL = 30 * 60


def hash_session_id(session_id):
    return hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()


def create_session(user_id):
    session_id = secrets.token_urlsafe(32)
    id_hash = hash_session_id(session_id)
    csrf_token = secrets.token_urlsafe(32)
    now = int(time.time())
    expires_at = now + SESSION_TTL

    db = get_db()

    db.execute(
        """
        INSERT INTO sessions (
            id_hash,
            user_id,
            expires_at,
            revoked,
            csrf_token
        )
        VALUES (?, ?, ?, 0, ?)
        """,
        (id_hash, user_id, expires_at, csrf_token),
    )

    db.commit()

    return session_id


def revoke_session(session_id):
    if not session_id:
        return

    db = get_db()

    db.execute(
        """
        UPDATE sessions
        SET revoked = 1
        WHERE id_hash = ?
        """,
        (hash_session_id(session_id),),
    )

    db.commit()


def get_current_user():
    session_id = request.cookies.get(SESSION_COOKIE)

    if not session_id:
        return None

    id_hash = hash_session_id(session_id)

    now = int(time.time())

    user = get_db().execute(
        """
        SELECT
            users.id,
            users.username,
            users.role
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.id_hash = ?
          AND sessions.revoked = 0
          AND sessions.expires_at > ?
        """,
        (id_hash, now),
    ).fetchone()

    return user


def set_session_cookie(response, session_id):
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        httponly=True,
        secure=current_app.config["SESSION_COOKIE_SECURE"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
        max_age=SESSION_TTL,
        path="/",
    )

    return response


def clear_session_cookie(response):
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=current_app.config["SESSION_COOKIE_SECURE"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
    )

    return response
def get_current_session_record():
    session_id = request.cookies.get(SESSION_COOKIE)

    if not session_id:
        return None

    return get_db().execute(
        """
        SELECT
            sessions.id_hash,
            sessions.csrf_token,
            sessions.expires_at,
            users.id,
            users.username,
            users.role
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.id_hash = ?
          AND sessions.revoked = 0
          AND sessions.expires_at > ?
        """,
        (
            hash_session_id(session_id),
            int(time.time()),
        ),
    ).fetchone()