from flask import Blueprint, jsonify

from .auth import require_roles
from .database import get_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/api/admin/stats")
@require_roles("admin")
def admin_stats():
    db = get_db()

    user_count = db.execute(
        "SELECT COUNT(*) AS total FROM users"
    ).fetchone()["total"]

    document_count = db.execute(
        "SELECT COUNT(*) AS total FROM documents"
    ).fetchone()["total"]

    return jsonify({
        "users": user_count,
        "documents": document_count,
    })