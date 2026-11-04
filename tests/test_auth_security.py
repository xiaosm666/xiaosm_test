import unittest

from tests.helpers import SecureAppTestCase


class AuthSecurityTests(SecureAppTestCase):

    def test_me_requires_login(self):
        response = self.client.get("/api/me")

        self.assertEqual(response.status_code, 401)

    def test_wrong_password_rejected(self):
        self.client.post(
            "/api/register",
            json={
                "username": "alice",
                "password": "LabPass123!",
            },
        )

        response = self.client.post(
            "/api/login",
            json={
                "username": "alice",
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_login_and_me(self):
        reg=self.client.post(
            "/api/register",
            json={
                "username": "alice",
                "password": "LabPass1234!",
            },
        )
        print("注册状态码：", reg.status_code, "注册返回：", reg.data.decode("utf-8"))
        
        login = self.client.post(
            "/api/login",
            json={
                "username": "alice",
                "password": "LabPass1234!",
            },
        )
        print("登录状态码：", login.status_code, "登录返回：", login.data.decode("utf-8"))
        self.assertEqual(login.status_code, 200)

        me = self.client.get("/api/me")

        self.assertEqual(me.status_code, 200)

    def test_logout_revokes_session(self):
        self.client.post(
            "/api/register",
            json={
                "username": "alice",
                "password": "LabPass123!",
            },
        )

        self.client.post(
            "/api/login",
            json={
                "username": "alice",
                "password": "LabPass123!",
            },
        )

        logout = self.client.post("/api/logout")

        self.assertEqual(logout.status_code, 200)

        me = self.client.get("/api/me")

        self.assertEqual(me.status_code, 401)


if __name__ == "__main__":
    unittest.main()