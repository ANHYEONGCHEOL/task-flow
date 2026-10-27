"""단위 4: 우선순위 · 마감일 · 기한 초과 · 정렬 (#21, R-009~R-012, BR-01~BR-05)."""

import unittest
from datetime import date, timedelta

from .support import Client, TestServer

TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
TOMORROW = (TODAY + timedelta(days=1)).isoformat()
TODAY_S = TODAY.isoformat()


class PriorityDueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TestServer()
        cls.server.start()
        cls.n = 0

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        # 테스트마다 새 사용자라서 목록이 서로 섞이지 않는다.
        type(self).n += 1
        self.c = Client(self.server.base)
        email = f"u{self.n}@test.com"
        self.c.post("/auth/register", {"email": email, "password": "password123"})
        self.c.post("/auth/login", {"email": email, "password": "password123"})

    def make(self, title="t", **extra):
        r = self.c.post("/tasks", {"title": title, **extra})
        self.assertEqual(r.status, 201, r.raw)
        return r.json

    # ---- BR-01 우선순위 ----
    def test_우선순위를_안_고르면_NORMAL이고_마감일은_없다(self):
        t = self.make()
        self.assertEqual((t["priority"], t["due_date"], t["is_overdue"]), ("NORMAL", None, False))

    def test_우선순위와_마감일을_골라_만든다(self):
        t = self.make(priority="HIGH", due_date="2030-01-31")
        self.assertEqual((t["priority"], t["due_date"]), ("HIGH", "2030-01-31"))
        self.assertEqual(self.c.get("/tasks").json[0]["priority"], "HIGH")

    def test_없는_우선순위와_null은_422이고_저장되지_않는다(self):
        for bad in ("URGENT", "high", "", None, 1):
            r = self.c.post("/tasks", {"title": "x", "priority": bad})
            self.assertEqual(r.status, 422, bad)
        self.assertEqual(self.c.get("/tasks").json, [])

    # ---- BR-02 마감일 ----
    def test_잘못된_마감일은_422이다(self):
        for bad in ("2026-02-30", "2026/01/01", "26-01-01", "2026-1-1", "2026-01-01T00:00:00", "내일", "", 20260101):
            r = self.c.post("/tasks", {"title": "x", "due_date": bad})
            self.assertEqual(r.status, 422, bad)
        self.assertEqual(self.c.get("/tasks").json, [])

    def test_지난_날짜도_마감일로_쓸_수_있다(self):
        self.assertEqual(self.make(due_date="2000-01-01")["due_date"], "2000-01-01")

    # ---- BR-03 기한 초과 판정표 8행 ----
    def test_기한_초과_판정표(self):
        cases = [
            (YESTERDAY, "TODO", True),
            (YESTERDAY, "IN_PROGRESS", True),
            (YESTERDAY, "DONE", False),
            (TODAY_S, "TODO", False),
            (TODAY_S, "DONE", False),
            (TOMORROW, "TODO", False),
            (TOMORROW, "DONE", False),
            (None, "TODO", False),
            (None, "DONE", False),
        ]
        for due, state, expected in cases:
            t = self.make(due_date=due)
            if state != "TODO":
                t = self.c.patch(f"/tasks/{t['id']}/status", {"status": state}).json
            self.assertEqual(t["is_overdue"], expected, (due, state))
            listed = next(x for x in self.c.get("/tasks").json if x["id"] == t["id"])
            self.assertEqual(listed["is_overdue"], expected, (due, state))

    # ---- BR-05 기한 초과는 상태를 바꾸지 않는다 ----
    def test_기한_초과여도_상태는_그대로이다(self):
        t = self.make(due_date=YESTERDAY)
        for _ in range(2):
            self.c.get("/tasks")
        self.assertEqual(self.c.get("/tasks").json[0]["status"], "TODO")
        self.assertEqual(t["status"], "TODO")

    def test_상태_변경은_우선순위와_마감일을_바꾸지_않는다(self):
        t = self.make(priority="HIGH", due_date="2030-01-31")
        r = self.c.patch(f"/tasks/{t['id']}/status", {"status": "DONE"}).json
        self.assertEqual((r["priority"], r["due_date"], r["status"]), ("HIGH", "2030-01-31", "DONE"))

    # ---- 수정 ----
    def test_기존_형식의_수정은_우선순위와_마감일을_지우지_않는다(self):
        t = self.make(priority="LOW", due_date="2030-01-31")
        r = self.c.patch(f"/tasks/{t['id']}", {"title": "새 제목", "description": "새 설명"})
        self.assertEqual(r.status, 200, r.raw)
        self.assertEqual(
            (r.json["title"], r.json["description"], r.json["priority"], r.json["due_date"]),
            ("새 제목", "새 설명", "LOW", "2030-01-31"),
        )

    def test_보낸_필드만_바뀌고_나머지는_그대로이다(self):
        t = self.make("원래", description="설명", priority="LOW", due_date="2030-01-31")
        r = self.c.patch(f"/tasks/{t['id']}", {"priority": "HIGH"}).json
        self.assertEqual(
            (r["title"], r["description"], r["priority"], r["due_date"], r["status"]),
            ("원래", "설명", "HIGH", "2030-01-31", "TODO"),
        )

    def test_마감일_null은_지우고_새_날짜는_바꾼다(self):
        t = self.make(due_date="2030-01-31")
        r = self.c.patch(f"/tasks/{t['id']}", {"due_date": "2031-02-01"}).json
        self.assertEqual(r["due_date"], "2031-02-01")
        r = self.c.patch(f"/tasks/{t['id']}", {"due_date": None}).json
        self.assertIsNone(r["due_date"])

    def test_우선순위_null과_허용_밖의_값은_422이고_바뀌지_않는다(self):
        t = self.make(priority="HIGH", due_date="2030-01-31")
        for body in (
            {"priority": None},
            {"priority": "URGENT"},
            {"due_date": "2026-02-30"},
            {"title": None},
            {"description": None},
            {"title": "   "},
            {"title": ""},
        ):
            self.assertEqual(self.c.patch(f"/tasks/{t['id']}", body).status, 422, body)
        after = self.c.get("/tasks").json[0]
        self.assertEqual((after["title"], after["priority"], after["due_date"]), ("t", "HIGH", "2030-01-31"))

    # ---- BR-04 정렬 ----
    def test_정렬_기한_초과_우선순위_마감일_ID_순이다(self):
        # 일부러 뒤섞인 순서로 만든다.
        a = self.make("a 보통 마감없음")
        b = self.make("b 낮음 내일", priority="LOW", due_date=TOMORROW)
        c = self.make("c 높음 마감없음", priority="HIGH")
        d = self.make("d 높음 내일", priority="HIGH", due_date=TOMORROW)
        e = self.make("e 높음 모레", priority="HIGH", due_date=(TODAY + timedelta(days=2)).isoformat())
        f = self.make("f 낮음 기한초과", priority="LOW", due_date=YESTERDAY)
        g = self.make("g 높음 기한초과 오래됨", priority="HIGH", due_date="2000-01-01")
        h = self.make("h 높음 기한초과 어제", priority="HIGH", due_date=YESTERDAY)
        i = self.make("i 보통 내일", due_date=TOMORROW)
        j = self.make("j 보통 마감없음")
        k = self.make("k 높음 기한초과지만 완료", priority="HIGH", due_date=YESTERDAY)
        self.c.patch(f"/tasks/{k['id']}/status", {"status": "DONE"})

        listed = self.c.get("/tasks").json
        # 기한 초과: g, h(높음, 이른 마감일 먼저), f(낮음). 그 뒤 높음: k(완료라 기한 초과 아님, 마감일 어제),
        # d, e, c(마감일 없음은 뒤). 보통: i, a, j. 낮음: b.
        expected = [g, h, f, k, d, e, c, i, a, j, b]
        self.assertEqual(
            [t["id"] for t in listed], [t["id"] for t in expected], [t["title"][0] for t in listed]
        )

    def test_마감일이_없는_Task는_같은_우선순위에서_뒤이고_ID_순이다(self):
        a = self.make("a")
        b = self.make("b", due_date=TOMORROW)
        c = self.make("c")
        ids = [t["id"] for t in self.c.get("/tasks").json]
        self.assertEqual(ids, [b["id"], a["id"], c["id"]])

    def test_상태를_바꾸면_정렬_위치가_규칙을_따른다(self):
        a = self.make("a", due_date=YESTERDAY)
        b = self.make("b", priority="HIGH")
        # a는 기한 초과라 우선순위가 낮아도 먼저다.
        self.assertEqual([t["id"] for t in self.c.get("/tasks").json], [a["id"], b["id"]])
        self.c.patch(f"/tasks/{a['id']}/status", {"status": "DONE"})
        # 완료가 되면 기한 초과가 풀려 높음인 b가 먼저다.
        self.assertEqual([t["id"] for t in self.c.get("/tasks").json], [b["id"], a["id"]])

    # ---- 사용자 분리, 기존 규칙 ----
    def test_남의_Task의_우선순위는_바꿀_수_없고_정렬에도_섞이지_않는다(self):
        mine = self.make("내것", priority="LOW")
        other = Client(self.server.base)
        other.post("/auth/register", {"email": "other-p@test.com", "password": "password123"})
        other.post("/auth/login", {"email": "other-p@test.com", "password": "password123"})
        theirs = other.post("/tasks", {"title": "남의것", "priority": "HIGH", "due_date": YESTERDAY}).json
        self.assertEqual([t["id"] for t in self.c.get("/tasks").json], [mine["id"]])
        r = self.c.patch(f"/tasks/{theirs['id']}", {"priority": "LOW"})
        self.assertEqual(r.status, 404)
        self.assertEqual(other.get("/tasks").json[0]["priority"], "HIGH")

    def test_빈_제목은_여전히_422이고_삭제는_204이다(self):
        self.assertEqual(self.c.post("/tasks", {"title": "   "}).status, 422)
        t = self.make()
        self.assertEqual(self.c.delete(f"/tasks/{t['id']}").status, 204)
        self.assertEqual(self.c.patch(f"/tasks/{t['id']}", {"title": "x"}).status, 404)

    def test_로그인하지_않으면_401이다(self):
        anon = Client(self.server.base)
        self.assertEqual(anon.get("/tasks").status, 401)
        self.assertEqual(anon.post("/tasks", {"title": "x", "priority": "HIGH"}).status, 401)
        self.assertEqual(anon.patch("/tasks/1", {"priority": "HIGH"}).status, 401)


if __name__ == "__main__":
    unittest.main()
