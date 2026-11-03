import unittest


def can_delete_upload(user, upload):
    if user is None:
        return False

    if user["role"] == "admin":
        return True

    if user["role"] == "user":
        return upload["owner_id"] == user["id"]

    return False


class UploadDeletionTests(unittest.TestCase):

    def setUp(self):
        self.alice = {"id": 1, "role": "user"}
        self.bob = {"id": 2, "role": "user"}
        self.admin = {"id": 3, "role": "admin"}

        self.upload = {
            "id": "aabbcc",
            "owner_id": 1
        }

    def test_owner_can_delete(self):
        self.assertTrue(
            can_delete_upload(self.alice, self.upload)
        )

    def test_other_user_cannot_delete(self):
        self.assertFalse(
            can_delete_upload(self.bob, self.upload)
        )

    def test_admin_can_delete(self):
        self.assertTrue(
            can_delete_upload(self.admin, self.upload)
        )

    def test_unauthenticated_cannot_delete(self):
        self.assertFalse(
            can_delete_upload(None, self.upload)
        )

    def test_unknown_role_denied(self):
        unknown = {"id": 4, "role": "unknown"}

        self.assertFalse(
            can_delete_upload(unknown, self.upload)
        )


if __name__ == "__main__":
    unittest.main()