import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.database import get_db
from werkzeug.security import check_password_hash


class RegistrationTests(unittest.TestCase):

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

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_register_success(self):
        response = self.client.post(
            "/api/register",
            json={
                "username": "alice",
                "password": "LabPass1234!",
            },
        )

        self.assertEqual(response.status_code, 201)

    def test_duplicate_username(self):
        payload = {
            "username": "alice",
            "password": "LabPass1234!",
        }

        self.client.post("/api/register", json=payload)

        response = self.client.post(
            "/api/register",
            json=payload,
        )

        self.assertEqual(response.status_code, 409)

    def test_short_password_rejected(self):
        response = self.client.post(
            "/api/register",
            json={
                "username": "bob",
                "password": "123",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_username_rejected(self):
        response = self.client.post(
            "/api/register",
            json={
                "username": "alice;admin",
                "password": "LabPass123!",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_password_is_hashed(self):
        self.client.post(
            "/api/register",
            json={
                "username": "alice",
                "password": "LabPass1234!",
            },
        )

        with self.app.app_context():
            user = get_db().execute(
                "SELECT * FROM users WHERE username = ?",
                ("alice",),
            ).fetchone()

            self.assertNotEqual(
                user["password_hash"],
                "LabPass1234!",
            )

            self.assertTrue(
                check_password_hash(
                    user["password_hash"],
                    "LabPass1234!",
                )
            )

    def test_client_cannot_choose_admin_role(self):
        response = self.client.post(
            "/api/register",
            json={
                "username": "alice",
                "password": "LabPass1234!",
                "role": "admin",
            },
        )

        self.assertEqual(response.status_code, 201)

        with self.app.app_context():
            user = get_db().execute(
                "SELECT role FROM users WHERE username = ?",
                ("alice",),
            ).fetchone()

            self.assertEqual(user["role"], "user")


if __name__ == "__main__":
    unittest.main()