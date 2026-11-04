import os
import tempfile
import unittest

from app import create_app


class SecureAppTestCase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        base = self.temp_dir.name

        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "DATABASE": os.path.join(base, "test.db"),
            "STORAGE_DIR": os.path.join(base, "storage"),
            "SESSION_COOKIE_SECURE": False,
            "TRUSTED_ORIGIN": "http://localhost",
        })

        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()