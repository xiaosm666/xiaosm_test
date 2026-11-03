import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.database import get_db


class DocumentTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.app = create_app({
            "TESTING": True,
            "DATABASE": str(
                Path(self.temp_dir.name) / "test.db"
            ),
            "STORAGE_DIR": str(
                Path(self.temp_dir.name) / "storage"
            ),
        })

        self.client = self.app.test_client()

        self.create_user("alice", "AlicePass123!")
        self.create_user("bob", "BobPass123456!")

        self.alice_client = self.app.test_client()
        self.bob_client = self.app.test_client()

        self.login(self.alice_client, "alice", "AlicePass123!")
        self.login(self.bob_client, "bob", "BobPass123456!")

        with self.app.app_context():
            db = get_db()

            db.execute(
                """
                INSERT INTO documents
                (owner_id, title, content, created_at)
                VALUES (1, 'Alice Document', 'Alice Content', 1)
                """
            )

            db.execute(
                """
                INSERT INTO documents
                (owner_id, title, content, created_at)
                VALUES (2, 'Bob Document', 'Bob Content', 1)
                """
            )

            db.commit()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_user(self, username, password):
        response = self.client.post(
            "/api/register",
            json={
                "username": username,
                "password": password,
            },
        )

        self.assertEqual(response.status_code, 201)

    def login(self, client, username, password):
        response = client.post(
            "/api/login",
            json={
                "username": username,
                "password": password,
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_alice_can_read_own_document(self):
        response = self.alice_client.get(
            "/api/documents/1"
        )

        self.assertEqual(response.status_code, 200)

    def test_alice_cannot_read_bob_document(self):
        response = self.alice_client.get(
            "/api/documents/2"
        )

        self.assertEqual(response.status_code, 404)

    def test_bob_can_read_own_document(self):
        response = self.bob_client.get(
            "/api/documents/2"
        )

        self.assertEqual(response.status_code, 200)

    def test_bob_cannot_read_alice_document(self):
        response = self.bob_client.get(
            "/api/documents/1"
        )

        self.assertEqual(response.status_code, 404)

    def test_list_only_returns_own_documents(self):
        response = self.alice_client.get(
            "/api/documents"
        )

        self.assertEqual(response.status_code, 200)

        documents = response.json["documents"]

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["owner_id"], 1)

    def test_unauthenticated_user_rejected(self):
        response = self.client.get(
            "/api/documents/1"
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()