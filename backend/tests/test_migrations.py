"""단위 1: 구조 · 이전 절차 확인.

실제 DB(backend/taskflow.db)는 건드리지 않는다. 모든 확인은 임시 폴더의 테스트용 DB로 한다.
"""

import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

OLD_TASKS = """
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'TODO'
        CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE'))
)
"""


def alembic(db: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "TASKFLOW_DB": str(db), "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def make_old_db(path: Path) -> None:
    """옛 구조(owner_id 없음)의 DB. 지운 번호가 있어 AUTOINCREMENT 번호가 id보다 크다."""
    conn = sqlite3.connect(path)
    conn.execute(OLD_TASKS)
    conn.executemany(
        "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
        [("가", "설명1", "TODO"), ("나", "", "IN_PROGRESS"), ("다", "설명3", "DONE"), ("지울것", "", "TODO")],
    )
    conn.execute("DELETE FROM tasks WHERE title = '지울것'")
    conn.commit()
    conn.close()


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"

    def tearDown(self):
        self.tmp.cleanup()

    def query(self, sql, params=()):
        conn = sqlite3.connect(self.db)
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def test_옛_DB를_이전하면_Task가_그대로이고_주인은_이전용_계정이다(self):
        make_old_db(self.db)
        before = self.query("SELECT id, title, description, status FROM tasks ORDER BY id")
        seq_before = self.query("SELECT seq FROM sqlite_sequence WHERE name = 'tasks'")

        result = alembic(self.db, "upgrade", "head")
        self.assertEqual(result.returncode, 0, result.stderr)

        after = self.query("SELECT id, title, description, status FROM tasks ORDER BY id")
        self.assertEqual(after, before)
        self.assertEqual(len(after), 3)
        users = self.query("SELECT id, email, password_hash FROM users")
        self.assertEqual([(u[1], u[2]) for u in users], [("migrated@test.com", None)])
        owners = {row[0] for row in self.query("SELECT owner_id FROM tasks")}
        self.assertEqual(owners, {users[0][0]})
        self.assertEqual(self.query("SELECT version_num FROM alembic_version"), [("0005",)])
        # 지운 번호 뒤에서 이어서 번호가 붙는다.
        self.assertEqual(self.query("SELECT seq FROM sqlite_sequence WHERE name = 'tasks'"), seq_before)

    def test_owner_id는_NOT_NULL이고_없는_사용자는_저장소가_막는다(self):
        make_old_db(self.db)
        self.assertEqual(alembic(self.db, "upgrade", "head").returncode, 0)

        conn = sqlite3.connect(self.db)
        conn.execute("PRAGMA foreign_keys = ON")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO tasks (title, owner_id) VALUES ('x', NULL)")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO tasks (title, owner_id) VALUES ('x', 999)")
        self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        conn.close()

    def test_새_DB에서도_끝까지_이전된다(self):
        result = alembic(self.db, "upgrade", "head")
        self.assertEqual(result.returncode, 0, result.stderr)
        tables = {r[0] for r in self.query("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertTrue({"users", "sessions", "tasks", "alembic_version"} <= tables)
        self.assertEqual(self.query("SELECT COUNT(*) FROM tasks"), [(0,)])

    def test_다시_실행해도_Task가_바뀌지_않는다(self):
        make_old_db(self.db)
        self.assertEqual(alembic(self.db, "upgrade", "head").returncode, 0)
        before = self.query("SELECT id, title, description, status, owner_id FROM tasks ORDER BY id")
        again = alembic(self.db, "upgrade", "head")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(
            self.query("SELECT id, title, description, status, owner_id FROM tasks ORDER BY id"),
            before,
        )
        self.assertEqual(self.query("SELECT COUNT(*) FROM users"), [(1,)])

    def test_users가_비어_있지_않으면_이전용_계정을_만들지_않고_멈추며_변경이_취소된다(self):
        make_old_db(self.db)
        self.assertEqual(alembic(self.db, "upgrade", "0001").returncode, 0)
        conn = sqlite3.connect(self.db)
        conn.execute("INSERT INTO users (email, password_hash) VALUES ('other@test.com', 'x')")
        conn.commit()
        conn.close()

        result = alembic(self.db, "upgrade", "head")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("users가 비어 있지 않습니다", result.stderr)
        # 0002에서 멈췄으므로 0001까지만 적용되어 있고, 사용자는 그대로다.
        self.assertEqual(self.query("SELECT version_num FROM alembic_version"), [("0001",)])
        self.assertEqual(self.query("SELECT email FROM users"), [("other@test.com",)])
        self.assertEqual(self.query("SELECT COUNT(*) FROM tasks WHERE owner_id IS NOT NULL"), [(0,)])

    def test_다운그레이드는_지원하지_않는다(self):
        make_old_db(self.db)
        self.assertEqual(alembic(self.db, "upgrade", "head").returncode, 0)
        result = alembic(self.db, "downgrade", "-1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.query("SELECT version_num FROM alembic_version"), [("0005",)])
        self.assertEqual(self.query("SELECT COUNT(*) FROM tasks"), [(3,)])

    def test_이전하면_기존_Task는_NORMAL이고_마감일이_없다(self):
        make_old_db(self.db)
        self.assertEqual(alembic(self.db, "upgrade", "head").returncode, 0)
        self.assertEqual(
            self.query("SELECT priority, due_date FROM tasks ORDER BY id"),
            [("NORMAL", None)] * 3,
        )

    def test_priority는_세_값만_저장소가_받고_due_date는_비울_수_있다(self):
        self.assertEqual(alembic(self.db, "upgrade", "head").returncode, 0)
        conn = sqlite3.connect(self.db)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("INSERT INTO users (email, password_hash) VALUES ('a@test.com', 'x')")
        uid = conn.execute("SELECT id FROM users WHERE email = 'a@test.com'").fetchone()[0]
        conn.execute("INSERT INTO tasks (title, owner_id) VALUES ('기본', ?)", (uid,))
        self.assertEqual(conn.execute("SELECT priority, due_date FROM tasks").fetchall(), [("NORMAL", None)])
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO tasks (title, owner_id, priority) VALUES ('x', ?, 'URGENT')", (uid,))
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO tasks (title, owner_id, priority) VALUES ('x', ?, NULL)", (uid,))
        conn.close()

    def test_새_리비전도_owner_id_제약과_번호_이어가기를_유지한다(self):
        make_old_db(self.db)
        seq_before = self.query("SELECT seq FROM sqlite_sequence WHERE name = 'tasks'")
        self.assertEqual(alembic(self.db, "upgrade", "head").returncode, 0)
        self.assertEqual(self.query("SELECT seq FROM sqlite_sequence WHERE name = 'tasks'"), seq_before)
        conn = sqlite3.connect(self.db)
        conn.execute("PRAGMA foreign_keys = ON")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO tasks (title, owner_id) VALUES ('x', NULL)")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO tasks (title, owner_id) VALUES ('x', 999)")
        conn.close()


if __name__ == "__main__":
    unittest.main()
