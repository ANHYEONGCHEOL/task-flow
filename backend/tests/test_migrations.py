"""단위 1: PostgreSQL 기준 스키마 확인 (D-020).

실서비스 DB는 건드리지 않는다. TASKFLOW_TEST_DATABASE_URL의 테스트용 DB만 쓰고,
확인할 때마다 비우고 다시 만든다.
"""

import os
import subprocess
import sys
import unittest

import psycopg

from .support import BACKEND_DIR, reset_database, test_database_url


def alembic(url: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DATABASE_URL": url, "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.url = test_database_url()
        reset_database(self.url)

    def query(self, sql, params=()):
        with psycopg.connect(self.url) as conn:
            cur = conn.execute(sql, params)
            return cur.fetchall() if cur.description else []

    def upgrade(self):
        result = alembic(self.url, "upgrade", "head")
        self.assertEqual(result.returncode, 0, result.stderr)

    def add_user(self, email="a@test.com") -> int:
        return self.query(
            "INSERT INTO users (email, password_hash) VALUES (%s, 'x') RETURNING id", (email,)
        )[0][0]

    def test_새_DB에서_끝까지_이전된다(self):
        self.upgrade()
        tables = {
            r[0]
            for r in self.query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
        }
        self.assertTrue({"users", "sessions", "tasks", "alembic_version"} <= tables)
        self.assertEqual(self.query("SELECT version_num FROM alembic_version"), [("0001",)])
        self.assertEqual(self.query("SELECT COUNT(*) FROM tasks"), [(0,)])
        # 새 DB에는 이전용 계정을 만들지 않는다.
        self.assertEqual(self.query("SELECT COUNT(*) FROM users"), [(0,)])

    def test_다시_실행해도_데이터가_바뀌지_않는다(self):
        self.upgrade()
        uid = self.add_user()
        self.query("INSERT INTO tasks (title, owner_id) VALUES ('가', %s)", (uid,))
        before = self.query("SELECT id, title, owner_id FROM tasks ORDER BY id")
        self.upgrade()
        self.assertEqual(self.query("SELECT id, title, owner_id FROM tasks ORDER BY id"), before)
        self.assertEqual(self.query("SELECT COUNT(*) FROM users"), [(1,)])

    def test_다운그레이드는_지원하지_않는다(self):
        self.upgrade()
        result = alembic(self.url, "downgrade", "-1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.query("SELECT version_num FROM alembic_version"), [("0001",)])

    def test_owner_id는_NOT_NULL이고_없는_사용자는_저장소가_막는다(self):
        self.upgrade()
        with self.assertRaises(psycopg.errors.NotNullViolation):
            self.query("INSERT INTO tasks (title, owner_id) VALUES ('x', NULL)")
        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            self.query("INSERT INTO tasks (title, owner_id) VALUES ('x', 999)")

    def test_기본값은_TODO_NORMAL_마감일_없음이다(self):
        self.upgrade()
        uid = self.add_user()
        self.query("INSERT INTO tasks (title, owner_id) VALUES ('기본', %s)", (uid,))
        self.assertEqual(
            self.query("SELECT description, status, priority, due_date FROM tasks"),
            [("", "TODO", "NORMAL", None)],
        )

    def test_status와_priority는_정해진_값만_저장소가_받는다(self):
        self.upgrade()
        uid = self.add_user()
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.query("INSERT INTO tasks (title, owner_id, priority) VALUES ('x', %s, 'URGENT')", (uid,))
        with self.assertRaises(psycopg.errors.NotNullViolation):
            self.query("INSERT INTO tasks (title, owner_id, priority) VALUES ('x', %s, NULL)", (uid,))
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.query("INSERT INTO tasks (title, owner_id, status) VALUES ('x', %s, '없는값')", (uid,))

    def test_이메일은_중복될_수_없고_사용자를_지우면_세션도_지워진다(self):
        self.upgrade()
        uid = self.add_user("dup@test.com")
        with self.assertRaises(psycopg.errors.UniqueViolation):
            self.add_user("dup@test.com")
        self.query(
            "INSERT INTO sessions (id, user_id, expires_at) VALUES ('s1', %s, '2999-01-01T00:00:00+00:00')",
            (uid,),
        )
        self.query("DELETE FROM users WHERE id = %s", (uid,))
        self.assertEqual(self.query("SELECT COUNT(*) FROM sessions"), [(0,)])

    def test_세_테이블_모두_RLS가_켜져_있다(self):
        self.upgrade()
        rows = self.query(
            "SELECT relname, relrowsecurity FROM pg_class "
            "WHERE relnamespace = 'public'::regnamespace AND relname IN ('users', 'sessions', 'tasks') "
            "ORDER BY relname"
        )
        self.assertEqual(rows, [("sessions", True), ("tasks", True), ("users", True)])

    def test_삭제한_번호는_다시_쓰지_않는다(self):
        self.upgrade()
        uid = self.add_user()
        first = self.query("INSERT INTO tasks (title, owner_id) VALUES ('가', %s) RETURNING id", (uid,))[0][0]
        self.query("DELETE FROM tasks WHERE id = %s", (first,))
        second = self.query("INSERT INTO tasks (title, owner_id) VALUES ('나', %s) RETURNING id", (uid,))[0][0]
        self.assertGreater(second, first)


if __name__ == "__main__":
    unittest.main()
