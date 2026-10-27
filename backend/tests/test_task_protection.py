"""단위 3: Task API 보호 확인. 로그인 없이 401, 남의 Task는 404, 소유자는 서버가 정한다."""

import unittest

from .support import Client, TestServer


class TaskProtectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TestServer()
        cls.server.start()
        cls.alice = Client(cls.server.base)
        cls.bob = Client(cls.server.base)
        for c, email in ((cls.alice, "alice@test.com"), (cls.bob, "bob@test.com")):
            c.post("/auth/register", {"email": email, "password": "password123"})
            c.post("/auth/login", {"email": email, "password": "password123"})
        cls.anonymous = Client(cls.server.base)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def new_task(self, client, title="내 카드", description=""):
        r = client.post("/tasks", {"title": title, "description": description})
        self.assertEqual(r.status, 201, r.raw)
        return r.json

    # ---- 로그인하지 않으면 모두 401 ----
    def test_로그인하지_않으면_Task_API_다섯_개가_모두_401이다(self):
        task = self.new_task(self.alice)
        a = self.anonymous
        self.assertEqual(a.get("/tasks").status, 401)
        self.assertEqual(a.post("/tasks", {"title": "x", "description": ""}).status, 401)
        self.assertEqual(a.patch(f"/tasks/{task['id']}", {"title": "x", "description": ""}).status, 401)
        self.assertEqual(a.patch(f"/tasks/{task['id']}/status", {"status": "DONE"}).status, 401)
        self.assertEqual(a.delete(f"/tasks/{task['id']}").status, 401)
        # 401이 먼저다. 잘못된 입력이어도, 없는 번호여도 401이다.
        self.assertEqual(a.post("/tasks", {"title": "   "}).status, 401)
        self.assertEqual(a.delete("/tasks/999999").status, 401)

    def test_로그아웃한_뒤에는_Task_API가_401이다(self):
        c = Client(self.server.base)
        c.post("/auth/register", {"email": "carol@test.com", "password": "password123"})
        c.post("/auth/login", {"email": "carol@test.com", "password": "password123"})
        self.assertEqual(c.get("/tasks").status, 200)
        c.post("/auth/logout")
        self.assertEqual(c.get("/tasks").status, 401)

    def test_위조한_쿠키로는_Task를_볼_수_없다(self):
        task = self.new_task(self.alice)
        session_id = self.alice.cookies["session"].rpartition(".")[0]
        forged = {"session": f"{session_id}.{'f' * 64}"}
        self.assertEqual(self.anonymous.get("/tasks", cookies=forged).status, 401)

    # ---- 자기 Task만 본다 ----
    def test_목록에는_내_Task만_나온다(self):
        mine = self.new_task(self.alice, "앨리스만")
        theirs = self.new_task(self.bob, "밥만")
        alice_titles = [t["title"] for t in self.alice.get("/tasks").json]
        bob_titles = [t["title"] for t in self.bob.get("/tasks").json]
        self.assertIn("앨리스만", alice_titles)
        self.assertNotIn("밥만", alice_titles)
        self.assertIn("밥만", bob_titles)
        self.assertNotIn("앨리스만", bob_titles)
        self.assertNotEqual(mine["id"], theirs["id"])

    def test_응답에는_소유자가_들어_있지_않다(self):
        task = self.new_task(self.alice)
        self.assertEqual(
            set(task),
            {"id", "title", "description", "status", "priority", "due_date", "is_overdue"},
        )
        for t in self.alice.get("/tasks").json:
            self.assertEqual(
                set(t),
                {"id", "title", "description", "status", "priority", "due_date", "is_overdue"},
            )

    # ---- 남의 Task는 404 ----
    def test_남의_Task를_수정_상태변경_삭제하면_404다(self):
        task = self.new_task(self.alice, "앨리스의 카드", "설명")
        tid = task["id"]
        self.assertEqual(self.bob.patch(f"/tasks/{tid}", {"title": "해킹", "description": ""}).status, 404)
        self.assertEqual(self.bob.patch(f"/tasks/{tid}/status", {"status": "DONE"}).status, 404)
        self.assertEqual(self.bob.delete(f"/tasks/{tid}").status, 404)
        # 바뀐 것이 없다.
        mine = [t for t in self.alice.get("/tasks").json if t["id"] == tid][0]
        self.assertEqual(
            mine,
            {
                "id": tid, "title": "앨리스의 카드", "description": "설명", "status": "TODO",
                "priority": "NORMAL", "due_date": None, "is_overdue": False,
            },
        )

    def test_남의_Task와_없는_Task는_같은_404와_같은_응답이다(self):
        task = self.new_task(self.alice)
        theirs = self.bob.delete(f"/tasks/{task['id']}")
        missing = self.bob.delete("/tasks/999999")
        self.assertEqual(theirs.status, 404)
        self.assertEqual(missing.status, 404)
        self.assertEqual(theirs.json, missing.json)
        a = self.bob.patch(f"/tasks/{task['id']}/status", {"status": "DONE"})
        b = self.bob.patch("/tasks/999999/status", {"status": "DONE"})
        self.assertEqual((a.status, a.json), (b.status, b.json))

    def test_자기_Task는_수정_상태변경_삭제가_된다(self):
        tid = self.new_task(self.alice, "고칠 카드")["id"]
        r = self.alice.patch(f"/tasks/{tid}", {"title": "고친 카드", "description": "새 설명"})
        self.assertEqual((r.status, r.json["title"]), (200, "고친 카드"))
        r = self.alice.patch(f"/tasks/{tid}/status", {"status": "DONE"})
        self.assertEqual((r.status, r.json["status"]), (200, "DONE"))
        self.assertEqual(self.alice.delete(f"/tasks/{tid}").status, 204)
        self.assertEqual(self.alice.delete(f"/tasks/{tid}").status, 404)

    # ---- 소유자는 서버가 정한다 ----
    def test_요청에_owner_id가_들어_있어도_무시하고_로그인한_사용자가_주인이다(self):
        bob_id = self.bob.get("/auth/me").json["id"]
        r = self.alice.post("/tasks", {"title": "가로채기", "description": "", "owner_id": bob_id})
        self.assertEqual(r.status, 201)
        owner = self.server.sql("SELECT owner_id FROM tasks WHERE id = ?", (r.json["id"],))[0][0]
        alice_id = self.alice.get("/auth/me").json["id"]
        self.assertEqual(owner, alice_id)
        self.assertNotIn("가로채기", [t["title"] for t in self.bob.get("/tasks").json])

    def test_기존_규칙은_그대로다_빈_제목은_422_잘못된_상태는_422(self):
        self.assertEqual(self.alice.post("/tasks", {"title": "   ", "description": ""}).status, 422)
        tid = self.new_task(self.alice)["id"]
        self.assertEqual(self.alice.patch(f"/tasks/{tid}/status", {"status": "없는값"}).status, 422)
        self.assertEqual(self.alice.patch(f"/tasks/{tid}", {"title": "", "description": ""}).status, 422)

    # ---- 이전용 계정과 기존 Task ----
    def test_이전한_기존_Task는_이전용_계정으로_가입한_사람에게만_보인다(self):
        migrated_id = self.server.sql("SELECT id FROM users WHERE email = 'migrated@test.com'")[0][0]
        self.server.sql(
            "INSERT INTO tasks (title, description, status, owner_id) VALUES ('옛 카드', '', 'DONE', ?)",
            (migrated_id,),
        )
        self.assertNotIn("옛 카드", [t["title"] for t in self.alice.get("/tasks").json])
        owner = Client(self.server.base)
        self.assertEqual(owner.post("/auth/register", {"email": "migrated@test.com", "password": "claimed-pass-1"}).status, 201)
        owner.post("/auth/login", {"email": "migrated@test.com", "password": "claimed-pass-1"})
        titles = [t["title"] for t in owner.get("/tasks").json]
        self.assertIn("옛 카드", titles)


if __name__ == "__main__":
    unittest.main()
