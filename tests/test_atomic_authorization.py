import sqlite3
import unittest

from app.documents import (
    update_document_for_user,
    delete_document_for_user,
)


class AtomicAuthorizationTests(unittest.TestCase):

    def setUp(self):
        self.db = sqlite3.connect(":memory:")

        self.db.execute("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                owner_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)

        self.db.execute("""
            INSERT INTO documents
            (id, owner_id, title, content)
            VALUES
            (1, 1, 'Alice document', 'Alice content'),
            (2, 2, 'Bob document', 'Bob content')
        """)

        self.db.commit()

        self.alice = {"id": 1, "role": "user"}
        self.bob = {"id": 2, "role": "user"}
        self.admin = {"id": 3, "role": "admin"}

    def tearDown(self):
        self.db.close()

    def test_owner_can_update(self):
        result = update_document_for_user(
            self.db, self.alice, 1,
            "New title", "New content"
        )
        self.assertTrue(result)

    def test_other_user_cannot_update(self):
        result = update_document_for_user(
            self.db, self.alice, 2,
            "Hacked title", "Hacked content"
        )
        self.assertFalse(result)

        title = self.db.execute(
            "SELECT title FROM documents WHERE id=2"
        ).fetchone()[0]

        self.assertEqual(title, "Bob document")

    def test_other_user_cannot_delete(self):
        result = delete_document_for_user(
            self.db, self.alice, 2
        )
        self.assertFalse(result)

        count = self.db.execute(
            "SELECT COUNT(*) FROM documents WHERE id=2"
        ).fetchone()[0]

        self.assertEqual(count, 1)

    def test_admin_can_update(self):
        result = update_document_for_user(
            self.db, self.admin, 2,
            "Admin title", "Admin content"
        )
        self.assertTrue(result)

    def test_admin_can_delete(self):
        result = delete_document_for_user(
            self.db, self.admin, 2
        )
        self.assertTrue(result)

    def test_unknown_role_denied(self):
        unknown = {"id": 4, "role": "unknown"}

        result = delete_document_for_user(
            self.db, unknown, 1
        )

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()