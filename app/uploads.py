import secrets
from datetime import datetime, timezone
from .database import get_db
from pathlib import Path
from .audit import audit_event
from flask import send_file, abort
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    send_file,
)
from werkzeug.utils import secure_filename

from .sessions import get_current_user
from .security import require_csrf


uploads_bp = Blueprint("uploads", __name__)

MAX_FILE_SIZE = 1024 * 1024
ALLOWED_EXTENSIONS = {".txt"}


def validate_upload(uploaded_file):
    if uploaded_file is None:
        return None, "Missing file"

    original_name = secure_filename(
        uploaded_file.filename or ""
    )

    if not original_name:
        return None, "Invalid filename"

    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return None, "Unsupported file type"

    content = uploaded_file.stream.read(
        MAX_FILE_SIZE + 1
    )

    if not content:
        return None, "Empty file"

    if len(content) > MAX_FILE_SIZE:
        return None, "File too large"

    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return None, "Invalid UTF-8 content"

    return content, None


@uploads_bp.post("/api/uploads")
@require_csrf
def upload_file():
    user = get_current_user()

    if user is None:
        return jsonify({
            "error": "Authentication required"
        }), 401

    uploaded_file = request.files.get("file")

    content, error = validate_upload(uploaded_file)

    if error:
        return jsonify({"error": error}), 400

    storage_dir = Path(
        current_app.config["STORAGE_DIR"]
    ) / "uploads"

    storage_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    file_id = secrets.token_hex(16)
    storage_name = f"{file_id}.txt"

    file_path = storage_dir / storage_name

    try:
        with file_path.open("xb") as output:
            output.write(content)
    except FileExistsError:
        return jsonify({
            "error": "Storage collision"
        }), 500
    db = get_db()

    try:
        db.execute(
            """
            INSERT INTO uploads (
                id,
                owner_id,
                original_name,
                storage_name,
                size,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                file_id,
                user["id"],
                secure_filename(uploaded_file.filename),
                storage_name,
                len(content),
                datetime.now(timezone.utc).isoformat(),
            )
        )

        db.commit()

    except Exception:
        db.rollback()

        file_path.unlink(missing_ok=True)

        raise
    audit_event(
    "file_upload",
    user_id=user["id"],
    resource_type="upload",
    resource_id=file_id,
    result="success"
    )
    return jsonify({
        "status": "uploaded",
        "file_id": file_id
    }), 201


@uploads_bp.get("/api/uploads/<file_id>")
def download_file(file_id):
    user = get_current_user()

    if user is None:
        return jsonify({
            "error": "Authentication required"
        }), 401

    # 只允许32位十六进制文件ID
    if (
        len(file_id) != 32
        or any(c not in "0123456789abcdef" for c in file_id)
    ):
        return jsonify({
            "error": "File not found"
        }), 404

    db = get_db()

    upload = db.execute(
        """
        SELECT *
        FROM uploads
        WHERE id = ?
        """,
        (file_id,)
    ).fetchone()

    if upload is None:
        return jsonify({
            "error": "File not found"
        }), 404

    # 管理员可以下载所有文件，普通用户只能下载自己的
    if (
        user["role"] != "admin"
        and upload["owner_id"] != user["id"]
    ):
        return jsonify({
            "error": "File not found"
        }), 404

    storage_dir = (
        Path(current_app.config["STORAGE_DIR"])
        / "uploads"
    ).resolve()

    file_path = (
        storage_dir / upload["storage_name"]
    ).resolve()

    # 确认最终路径仍然在上传目录内
    if not file_path.is_relative_to(storage_dir):
        return jsonify({
            "error": "File not found"
        }), 404

    if not file_path.is_file():
        return jsonify({
            "error": "File not found"
        }), 404

    response = send_file(
        file_path,
        as_attachment=True,
        download_name=upload["original_name"],
        mimetype="text/plain"
    )

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"

    return response


@uploads_bp.delete("/api/uploads/<file_id>")
@require_csrf
def delete_upload(file_id):
    user = get_current_user()

    if user is None:
        return jsonify({
            "error": "Authentication required"
        }), 401

    if (
        len(file_id) != 32
        or any(c not in "0123456789abcdef" for c in file_id)
    ):
        return jsonify({
            "error": "File not found"
        }), 404

    db = get_db()

    upload = db.execute(
        """
        SELECT *
        FROM uploads
        WHERE id = ?
        """,
        (file_id,)
    ).fetchone()

    if upload is None:
        return jsonify({
            "error": "File not found"
        }), 404

    if (
        user["role"] != "admin"
        and (
            user["role"] != "user"
            or upload["owner_id"] != user["id"]
        )
    ):
        return jsonify({
            "error": "File not found"
        }), 404

    storage_dir = (
        Path(current_app.config["STORAGE_DIR"])
        / "uploads"
    ).resolve()

    file_path = (
        storage_dir / upload["storage_name"]
    ).resolve()

    if not file_path.is_relative_to(storage_dir):
        return jsonify({
            "error": "File not found"
        }), 404

    try:
        # 先删除磁盘文件
        file_path.unlink(missing_ok=True)

        # 再删除数据库记录
        if user["role"] == "admin":
            cursor = db.execute(
                "DELETE FROM uploads WHERE id = ?",
                (file_id,)
            )
        else:
            cursor = db.execute(
                """
                DELETE FROM uploads
                WHERE id = ? AND owner_id = ?
                """,
                (file_id, user["id"])
            )

        if cursor.rowcount != 1:
            db.rollback()
            return jsonify({
                "error": "File not found"
            }), 404

        db.commit()

    except OSError:
        db.rollback()

        current_app.logger.exception(
            "Failed to remove uploaded file"
        )

        return jsonify({
            "error": "File deletion failed"
        }), 500
    audit_event(
    "file_delete",
    user_id=user["id"],
    resource_type="upload",
    resource_id=file_id,
    result="success"
    )
    return jsonify({
        "status": "deleted"
    }), 200