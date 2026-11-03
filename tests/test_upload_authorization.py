import unittest


def can_download(user, upload):
    if user is None:
        return False

    if user["role"] == "admin":
        return True

    if user["role"] == "user":
        return upload["owner_id"] == user["id"]

    return False


class UploadAuthorizationTests(unittest.TestCase):

    def setUp(self):
        self.alice = {"id": 1, "role": "user"}
        self.bob = {"id": 2, "role": "user"}
        self.admin = {"id": 3, "role": "admin"}

        self.alice_file = {
            "id": "aabbcc",
            "owner_id": 1
        }

    def test_owner_can_download(self):
        self.assertTrue(
            can_download(self.alice, self.alice_file)
        )

    def test_other_user_cannot_download(self):
        self.assertFalse(
            can_download(self.bob, self.alice_file)
        )

    def test_admin_can_download(self):
        self.assertTrue(
            can_download(self.admin, self.alice_file)
        )

    def test_unauthenticated_cannot_download(self):
        self.assertFalse(
            can_download(None, self.alice_file)
        )

    def test_unknown_role_denied(self):
        unknown = {"id": 4, "role": "unknown"}

        self.assertFalse(
            can_download(unknown, self.alice_file)
        )


if __name__ == "__main__":
    unittest.main()