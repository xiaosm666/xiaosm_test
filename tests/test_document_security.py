import unittest

from tests.helpers import SecureAppTestCase


class DocumentSecurityTests(SecureAppTestCase):

    def test_document_api_requires_login(self):
        response = self.client.get("/api/documents")

        self.assertEqual(response.status_code, 401)

    def test_document_creation_requires_login(self):
        response = self.client.post(
            "/api/documents",
            json={
                "title": "Test document",
                "content": "Hello",
            },
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()