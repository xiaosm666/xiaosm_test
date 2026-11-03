import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.database import get_db


class SessionTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-123456",
            "DATABASE": str(
                Path(self.temp_dir.name) / "test.db"
            ),
            "STORAGE_DIR": str(
                Path(self.temp_dir.name) / "storage"
            ),
        })

        self.client = self.app.test_client()

        self.client.post(
            "/api/register",
            json={
                "username": "alice",
                "password": "LabPass1234!",
            },
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def login(self):
        return self.client.post(
            "/api/login",
            json={
                "username": "alice",
                "password": "LabPass1234!",
            },
        )

    def test_login_success(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertIn("lab_session", response.headers.get("Set-Cookie", ""))

    def test_wrong_password_rejected(self):
        response = self.client.post(
            "/api/login",
            json={
                "username": "alice",
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_me_requires_login(self):
        response = self.client.get("/api/me")

        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_access_me(self):
        self.login()

        response = self.client.get("/api/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["username"], "alice")

    def test_logout_revokes_session(self):
        self.login()

        cookie = self.client.get_cookie("lab_session")
        old_session_id = cookie.value

        self.client.post("/api/logout")

        response = self.client.get("/api/me")
        self.assertEqual(response.status_code, 401)

        from app.sessions import hash_session_id

        with self.app.app_context():
            row = get_db().execute(
                """
                SELECT revoked
                FROM sessions
                WHERE id_hash = ?
                """,
                (hash_session_id(old_session_id),),
            ).fetchone()

            self.assertEqual(row["revoked"], 1)


if __name__ == "__main__":
    unittest.main()