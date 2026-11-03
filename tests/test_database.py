import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import create_app


class DatabaseTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        database_path = str(
            Path(self.temp_dir.name) / "test.db"
        )

        self.app = create_app({
            "TESTING": True,
            "DATABASE": database_path,
            "STORAGE_DIR": str(
                Path(self.temp_dir.name) / "storage"
            ),
        })

        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tables_exist(self):
        with self.app.app_context():
            from app.database import get_db

            db = get_db()

            rows = db.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
            """).fetchall()

            names = {row["name"] for row in rows}

            self.assertTrue({
                "users",
                "sessions",
                "documents",
            }.issubset(names))

    def test_foreign_keys_enabled(self):
        with self.app.app_context():
            from app.database import get_db

            result = get_db().execute(
                "PRAGMA foreign_keys"
            ).fetchone()

            self.assertEqual(result[0], 1)


if __name__ == "__main__":
    unittest.main()