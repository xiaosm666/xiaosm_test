import time

from flask import Blueprint, jsonify, request
from .audit import audit_event
from .database import get_db
from .sessions import get_current_user
from .security import require_csrf
documents_bp = Blueprint("documents", __name__)

def update_document_for_user(
    db,
    user,
    document_id,
    title,
    content
):
    if user["role"] == "admin":
        cursor = db.execute(
            """
            UPDATE documents
            SET title = ?, content = ?
            WHERE id = ?
            """,
            (title, content, document_id)
        )

    elif user["role"] == "user":
        cursor = db.execute(
            """
            UPDATE documents
            SET title = ?, content = ?
            WHERE id = ? AND owner_id = ?
            """,
            (title, content, document_id, user["id"])
        )

    else:
        return False

    return cursor.rowcount == 1

def delete_document_for_user(db, user, document_id):
    if user["role"] == "admin":
        cursor = db.execute(
            """
            DELETE FROM documents
            WHERE id = ?
            """,
            (document_id,)
        )

    elif user["role"] == "user":
        cursor = db.execute(
            """
            DELETE FROM documents
            WHERE id = ? AND owner_id = ?
            """,
            (document_id, user["id"])
        )

    else:
        return False

    return cursor.rowcount == 1

def can_access_document(user, document, action="read"):
    if user is None or document is None:
        audit_event(
            "document_access_denied",
            user_id=user["id"],
            resource_type="document",
            resource_id=document["id"],
            result="denied"
        )
        return False

    # 管理员可以管理所有文档
    if user["role"] == "admin":
        return action in ("read", "update", "delete")

    # 普通用户只能访问自己的文档
    if user["role"] == "user":
        if document["owner_id"] != user["id"]:
            return False

        return action in ("read", "update", "delete")

    # 未知角色默认拒绝
    return False


def get_document(document_id):
    return get_db().execute(
        """
        SELECT id, owner_id, title, content, created_at
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    ).fetchone()


def validate_document(data):
    if not isinstance(data, dict):
        return None

    title = data.get("title")
    content = data.get("content")

    if not isinstance(title, str):
        return None

    if not isinstance(content, str):
        return None

    title = title.strip()

    if not title or len(title) > 100:
        return None

    if len(content) > 10000:
        return None

    return title, content


@documents_bp.post("/api/documents")
@require_csrf
def create_document():
    user = get_current_user()

    if user is None:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True)
    validated = validate_document(data)

    if validated is None:
        return jsonify({"error": "invalid_document"}), 400

    title, content = validated

    db = get_db()

    cursor = db.execute(
        """
        INSERT INTO documents (
            owner_id,
            title,
            content,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user["id"],
            title,
            content,
            int(time.time()),
        ),
    )

    db.commit()

    return jsonify({
        "id": cursor.lastrowid,
        "title": title,
        "message": "document_created",
    }), 201


@documents_bp.get("/api/documents")
def list_documents():
    user = get_current_user()

    if user is None:
        return jsonify({"error": "unauthorized"}), 401

    if user["role"] == "admin":
        rows = get_db().execute(
            """
            SELECT id, owner_id, title, created_at
            FROM documents
            ORDER BY id
            """
        ).fetchall()

    elif user["role"] == "user":
        rows = get_db().execute(
            """
            SELECT id, owner_id, title, created_at
            FROM documents
            WHERE owner_id = ?
            ORDER BY id
            """,
            (user["id"],),
        ).fetchall()

    else:
        return jsonify({"error": "forbidden"}), 403

    return jsonify({
        "documents": [dict(row) for row in rows]
    })


@documents_bp.get("/api/documents/<int:document_id>")
def read_document(document_id):
    user = get_current_user()

    if user is None:
        return jsonify({"error": "unauthorized"}), 401

    document = get_document(document_id)

    if document is None:
        return jsonify({"error": "not_found"}), 404

    if not can_access_document(user, document, "read"):
        return jsonify({"error": "not_found"}), 404

    return jsonify(dict(document))


@documents_bp.patch("/api/documents/<int:document_id>")
@require_csrf
def update_document(document_id):
    user = get_current_user()

    if user is None:
        return jsonify({"error": "unauthorized"}), 401

    document = get_document(document_id)

    if document is None:
        return jsonify({"error": "not_found"}), 404

    if not can_access_document(user, document, "update"):
        return jsonify({"error": "not_found"}), 404

    data = request.get_json(silent=True)
    validated = validate_document(data)

    if validated is None:
        return jsonify({"error": "invalid_document"}), 400

    title, content = validated

    db = get_db()

    success = update_document_for_user(
    db,
    user,
    document_id,
    data["title"],
    data["content"]
    )

    if not success:
        db.rollback()
        return jsonify({"error": "Document not found"}), 404

    db.commit()

    return jsonify({"status": "updated"})


@documents_bp.delete("/api/documents/<int:document_id>")
@require_csrf
def delete_document(document_id):
    user = get_current_user()

    if user is None:
        return jsonify({"error": "unauthorized"}), 401

    document = get_document(document_id)

    if document is None:
        return jsonify({"error": "not_found"}), 404

    if not can_access_document(user, document, "delete"):
        return jsonify({"error": "not_found"}), 404

    db = get_db()

    success = delete_document_for_user(
    db,
    user,
    document_id
    )

    if not success:
        db.rollback()
        return jsonify({"error": "Document not found"}), 404

    db.commit()

    return jsonify({"status": "deleted"})