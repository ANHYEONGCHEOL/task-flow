"""단위 2: 인증 API(가입 · 로그인 · 로그아웃 · 현재 사용자) 확인. 테스트용 DB만 쓴다."""

import unittest
from datetime import UTC, datetime, timedelta

from .support import Client, TestServer


class AuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TestServer()
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def client(self) -> Client:
        return Client(self.server.base)

    def register(self, c, email, password="password123"):
        return c.post("/auth/register", {"email": email, "password": password})

    def login(self, c, email, password="password123"):
        return c.post("/auth/login", {"email": email, "password": password})

    # ---- 가입 ----
    def test_가입하면_201이고_응답에는_id와_email만_있다(self):
        c = self.client()
        r = self.register(c, "a1@test.com")
        self.assertEqual(r.status, 201)
        self.assertEqual(set(r.json), {"id", "email"})
        self.assertEqual(r.json["email"], "a1@test.com")
        self.assertNotIn("password", r.raw.decode("utf-8").lower())

    def test_가입해도_자동으로_로그인하지_않는다(self):
        c = self.client()
        self.register(c, "a2@test.com")
        self.assertEqual(c.get("/auth/me").status, 401)

    def test_이메일은_앞뒤_공백을_지우고_소문자로_저장한다(self):
        c = self.client()
        r = self.register(c, "  A3@Test.COM  ")
        self.assertEqual(r.json["email"], "a3@test.com")
        self.assertEqual(self.login(c, "a3@test.com").status, 200)

    def test_이미_쓰는_이메일은_409다(self):
        c = self.client()
        self.assertEqual(self.register(c, "a4@test.com").status, 201)
        self.assertEqual(self.register(c, "a4@test.com").status, 409)
        self.assertEqual(self.register(c, "A4@TEST.com").status, 409)

    def test_규칙에_맞지_않는_입력은_422다(self):
        c = self.client()
        self.assertEqual(self.register(c, "no-at-sign").status, 422)
        self.assertEqual(self.register(c, "x" * 250 + "@a.com").status, 422)
        self.assertEqual(self.register(c, "a5@test.com", "short").status, 422)
        self.assertEqual(self.register(c, "a5@test.com", "p" * 129).status, 422)
        self.assertEqual(self.register(c, "a5@test.com", "p" * 128).status, 201)

    def test_비밀번호는_원문이_아니라_Argon2_해시로만_저장한다(self):
        c = self.client()
        self.register(c, "a6@test.com", "my-secret-pass")
        stored = self.server.sql("SELECT password_hash FROM users WHERE email = ?", ("a6@test.com",))[0][0]
        self.assertTrue(stored.startswith("$argon2"), stored[:10])
        self.assertNotIn("my-secret-pass", stored)

    # ---- 로그인 ----
    def test_로그인하면_세션_쿠키가_속성과_함께_온다(self):
        c = self.client()
        self.register(c, "b1@test.com")
        r = self.login(c, "b1@test.com")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.json["email"], "b1@test.com")
        header = r.set_cookie_header().lower()
        self.assertIn("session=", header)
        self.assertIn("httponly", header)
        self.assertIn("samesite=lax", header)
        self.assertIn("max-age=1800", header)
        self.assertIn("path=/", header)
        self.assertNotIn("secure", header)  # 로컬 http에서는 붙이지 않는다.

    def test_세션_쿠키_값은_비밀번호가_아니라_서명한_무작위_번호다(self):
        c = self.client()
        self.register(c, "b2@test.com", "password-b2")
        self.login(c, "b2@test.com", "password-b2")
        value = c.cookies["session"]
        self.assertNotIn("password-b2", value)
        session_id, _, signature = value.rpartition(".")
        self.assertGreaterEqual(len(session_id), 32)
        self.assertEqual(len(signature), 64)
        stored = self.server.sql("SELECT id FROM sessions")
        self.assertIn((session_id,), stored)

    def test_틀린_비밀번호와_없는_이메일은_같은_401이다(self):
        c = self.client()
        self.register(c, "b3@test.com")
        wrong = self.login(c, "b3@test.com", "wrong-password")
        missing = self.login(c, "nobody@test.com")
        self.assertEqual(wrong.status, 401)
        self.assertEqual(missing.status, 401)
        self.assertEqual(wrong.json, missing.json)
        self.assertIsNone(wrong.set_cookie_header())
        self.assertEqual(c.get("/auth/me").status, 401)

    def test_로그인하면_me가_현재_사용자를_돌려준다(self):
        c = self.client()
        self.register(c, "b4@test.com")
        self.login(c, "b4@test.com")
        r = c.get("/auth/me")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.json["email"], "b4@test.com")
        self.assertEqual(set(r.json), {"id", "email"})

    def test_로그인하지_않으면_me는_401이다(self):
        self.assertEqual(self.client().get("/auth/me").status, 401)

    # ---- 로그아웃 ----
    def test_로그아웃하면_204이고_세션이_사라져_다음_요청은_401이다(self):
        c = self.client()
        self.register(c, "c1@test.com")
        self.login(c, "c1@test.com")
        old_cookie = dict(c.cookies)
        r = c.post("/auth/logout")
        self.assertEqual(r.status, 204)
        self.assertEqual(c.get("/auth/me").status, 401)
        # 로그아웃 전에 가졌던 쿠키를 다시 보내도 서버가 세션을 지워서 401이다.
        self.assertEqual(c.get("/auth/me", cookies=old_cookie).status, 401)
        session_id = old_cookie["session"].rpartition(".")[0]
        self.assertEqual(self.server.sql("SELECT id FROM sessions WHERE id = ?", (session_id,)), [])

    def test_로그인하지_않은_상태의_로그아웃은_401이다(self):
        self.assertEqual(self.client().post("/auth/logout").status, 401)

    def test_로그아웃은_현재_세션만_끝낸다(self):
        a, b = self.client(), self.client()
        self.register(a, "c2@test.com")
        self.login(a, "c2@test.com")
        self.login(b, "c2@test.com")
        a.post("/auth/logout")
        self.assertEqual(a.get("/auth/me").status, 401)
        self.assertEqual(b.get("/auth/me").status, 200)

    # ---- 세션 만료와 쿠키 위조 ----
    def test_서명이_맞지_않는_쿠키는_세션이_있어도_401이다(self):
        c = self.client()
        self.register(c, "d1@test.com")
        self.login(c, "d1@test.com")
        session_id = c.cookies["session"].rpartition(".")[0]
        self.assertEqual(c.get("/auth/me", cookies={"session": f"{session_id}.{'0' * 64}"}).status, 401)
        self.assertEqual(c.get("/auth/me", cookies={"session": session_id}).status, 401)
        self.assertEqual(c.get("/auth/me", cookies={"session": "garbage"}).status, 401)
        self.assertEqual(c.get("/auth/me").status, 200)

    def test_30분이_지난_세션은_401이다(self):
        c = self.client()
        self.register(c, "d2@test.com")
        self.login(c, "d2@test.com")
        session_id = c.cookies["session"].rpartition(".")[0]
        row = self.server.sql("SELECT expires_at FROM sessions WHERE id = ?", (session_id,))[0][0]
        remaining = datetime.fromisoformat(row) - datetime.now(UTC)
        self.assertTrue(timedelta(minutes=29) < remaining <= timedelta(minutes=30), remaining)
        past = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
        self.server.sql("UPDATE sessions SET expires_at = ? WHERE id = ?", (past, session_id))
        self.assertEqual(c.get("/auth/me").status, 401)

    def test_요청해도_세션_시간이_연장되지_않는다(self):
        c = self.client()
        self.register(c, "d3@test.com")
        self.login(c, "d3@test.com")
        session_id = c.cookies["session"].rpartition(".")[0]
        before = self.server.sql("SELECT expires_at FROM sessions WHERE id = ?", (session_id,))
        c.get("/auth/me")
        c.get("/auth/me")
        self.assertEqual(self.server.sql("SELECT expires_at FROM sessions WHERE id = ?", (session_id,)), before)

    def test_로그인할_때_만료된_세션을_지운다(self):
        c = self.client()
        self.register(c, "d4@test.com")
        self.login(c, "d4@test.com")
        stale = c.cookies["session"].rpartition(".")[0]
        self.server.sql("UPDATE sessions SET expires_at = ? WHERE id = ?", ("2000-01-01T00:00:00+00:00", stale))
        self.login(self.client(), "d4@test.com")
        self.assertEqual(self.server.sql("SELECT id FROM sessions WHERE id = ?", (stale,)), [])

    # ---- 이전용 계정 ----
    def test_이전용_계정은_가입하기_전에는_로그인할_수_없다(self):
        r = self.login(self.client(), "migrated@test.com", "anything-1234")
        self.assertEqual(r.status, 401)

    def test_이전용_이메일로_처음_가입하는_사람이_비밀번호를_정해_계정을_받는다(self):
        c = self.client()
        r = self.register(c, "migrated@test.com", "claimed-pass-1")
        self.assertEqual(r.status, 201)
        users = self.server.sql("SELECT id FROM users WHERE email = 'migrated@test.com'")
        self.assertEqual(len(users), 1)
        self.assertEqual(r.json["id"], users[0][0])
        self.assertEqual(self.login(c, "migrated@test.com", "claimed-pass-1").status, 200)
        # 이미 받은 뒤의 가입 요청은 새 사용자를 만들지 않고 409다.
        self.assertEqual(self.register(self.client(), "migrated@test.com", "another-pass-2").status, 409)
        self.assertEqual(self.login(self.client(), "migrated@test.com", "another-pass-2").status, 401)


class SecretTest(unittest.TestCase):
    def test_SESSION_SECRET이_비어_있으면_API는_시작하지_않는다(self):
        server = TestServer(secret="")
        # 값을 읽을 수 있는 .env가 없는 환경을 만든다.
        server.env["TASKFLOW_ENV_FILE"] = str(server.db.parent / "no-such.env")
        try:
            with self.assertRaises(RuntimeError) as ctx:
                server.start()
            self.assertIn("SESSION_SECRET", str(ctx.exception))
        finally:
            server.stop()

    def test_env_파일에_값이_있으면_그_값으로_시작한다(self):
        server = TestServer(secret="")
        env_file = server.db.parent / "test.env"
        env_file.write_text("# 주석" + chr(10) + "SESSION_SECRET=from-env-file" + chr(10), encoding="utf-8")
        server.env["TASKFLOW_ENV_FILE"] = str(env_file)
        try:
            server.start()
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
