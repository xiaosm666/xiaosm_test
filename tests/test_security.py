import tempfile
import unittest
from pathlib import Path

from app import create_app


class SecurityTests(unittest.TestCase):

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
            "TRUSTED_ORIGIN": "http://127.0.0.1:8121",
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

    def get_token(self):
        return self.client.get(
            "/api/csrf"
        ).json["csrf_token"]

    def test_token_requires_login(self):
        response = self.client.get("/api/csrf")
        self.assertEqual(response.status_code, 401)

    def test_missing_token_rejected(self):
        self.login()

        response = self.client.post(
            "/api/security-demo",
            headers={
                "Origin": "http://127.0.0.1:8121",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_wrong_token_rejected(self):
        self.login()

        response = self.client.post(
            "/api/security-demo",
            headers={
                "Origin": "http://127.0.0.1:8121",
                "X-CSRF-Token": "wrong-token",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_wrong_origin_rejected(self):
        self.login()
        token = self.get_token()

        response = self.client.post(
            "/api/security-demo",
            headers={
                "Origin": "http://evil.example",
                "X-CSRF-Token": token,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_valid_request_accepted(self):
        self.login()
        token = self.get_token()

        response = self.client.post(
            "/api/security-demo",
            headers={
                "Origin": "http://127.0.0.1:8121",
                "X-CSRF-Token": token,
            },
        )

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()