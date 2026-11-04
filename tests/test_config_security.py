import unittest

from app import create_app


class ConfigSecurityTests(unittest.TestCase):

    def test_debug_disabled(self):
        app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
        })

        self.assertFalse(app.config["DEBUG"])

    def test_http_only_enabled(self):
        app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
        })

        self.assertTrue(
            app.config["SESSION_COOKIE_HTTPONLY"]
        )

    def test_cookie_samesite(self):
        app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
        })

        self.assertEqual(
            app.config["SESSION_COOKIE_SAMESITE"],
            "Lax"
        )

    def test_cookie_secure_configurable(self):
        app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "SESSION_COOKIE_SECURE": True,
        })

        self.assertTrue(
            app.config["SESSION_COOKIE_SECURE"]
        )


if __name__ == "__main__":
    unittest.main()