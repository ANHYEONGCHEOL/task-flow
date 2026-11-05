"""테스트용 서버와 HTTP 클라이언트. 실제 DB는 쓰지 않고 임시 폴더의 테스트용 DB만 쓴다."""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import psycopg

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_SECRET = "test-secret-not-a-real-one"


def test_database_url() -> str:
    """테스트용 PostgreSQL 주소. 환경변수 또는 backend/.env의 TASKFLOW_TEST_DATABASE_URL.

    테스트는 이 DB의 테이블을 모두 지우고 다시 만든다. 그래서 DB 이름이 _test로 끝나지
    않으면 멈춘다. (실서비스 DB를 지우지 않기 위한 안전장치)
    """
    url = os.environ.get("TASKFLOW_TEST_DATABASE_URL")
    if not url:
        env_file = BACKEND_DIR / ".env"
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                key, _, value = line.strip().partition("=")
                if key == "TASKFLOW_TEST_DATABASE_URL":
                    url = value.strip()
    if not url:
        raise RuntimeError(
            "TASKFLOW_TEST_DATABASE_URL이 비어 있습니다. backend/.env에 테스트용 DB 주소를 넣어 주세요."
        )
    name = url.split("?")[0].rsplit("/", 1)[-1]
    if not name.endswith("_test"):
        raise RuntimeError(f"테스트용 DB 이름은 _test로 끝나야 합니다. (지금: {name})")
    return url


def reset_database(url: str) -> None:
    """테스트용 DB를 빈 상태로 되돌린다."""
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestServer:
    """alembic으로 이전한 테스트용 DB로 API를 띄운다."""

    def __init__(self, secret: str | None = TEST_SECRET, extra_env: dict | None = None):
        self.db_url = test_database_url()
        self.env = {
            **os.environ,
            "DATABASE_URL": self.db_url,
            "PYTHONUTF8": "1",
            "SESSION_SECRET": secret or "",
            **(extra_env or {}),
        }
        self.port = _free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        reset_database(self.db_url)
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=BACKEND_DIR, env=self.env, check=True, capture_output=True,
        )
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(self.port)],
            cwd=BACKEND_DIR, env=self.env,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        for _ in range(80):
            try:
                urllib.request.urlopen(f"{self.base}/health", timeout=1).read()
                return
            except Exception:
                if self.proc.poll() is not None:
                    raise RuntimeError(self.proc.stderr.read().decode("utf-8", "replace"))
                time.sleep(0.25)
        raise RuntimeError("테스트 서버가 시작되지 않았습니다.")

    def stop(self) -> None:
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=10)
            if self.proc.stderr:
                self.proc.stderr.close()

    def sql(self, query: str, params=()):
        # 자리표시자는 %s다. SELECT가 아닌 문장은 결과 없이 빈 목록을 돌려준다.
        with psycopg.connect(self.db_url) as conn:
            cur = conn.execute(query, params)
            return cur.fetchall() if cur.description else []


    def seed_migrated_user(self) -> int:
        """이전용 계정(D-018)을 비밀번호 없는 상태로 만든다. 새 DB에는 기본으로 없다."""
        return self.sql("INSERT INTO users (email, password_hash) VALUES ('migrated@test.com', NULL) ON CONFLICT (email) DO UPDATE SET password_hash = NULL RETURNING id")[0][0]


class Response:
    def __init__(self, status: int, headers, raw: bytes):
        self.status = status
        self.headers = headers
        self.raw = raw

    @property
    def json(self):
        return json.loads(self.raw) if self.raw else None

    def set_cookie_header(self) -> str | None:
        return self.headers.get("Set-Cookie")


class Client:
    """브라우저처럼 쿠키를 들고 다니는 클라이언트."""

    def __init__(self, base: str):
        self.base = base
        self.cookies: dict[str, str] = {}

    def request(self, method: str, path: str, body=None, cookies=None) -> Response:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(f"{self.base}{path}", data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        jar = self.cookies if cookies is None else cookies
        if jar:
            req.add_header("Cookie", "; ".join(f"{k}={v}" for k, v in jar.items()))
        try:
            res = urllib.request.urlopen(req, timeout=10)
        except urllib.error.HTTPError as e:
            res = e
        raw = res.read()
        out = Response(res.status if hasattr(res, "status") else res.code, res.headers, raw)
        if cookies is None:
            self._store(out)
        return out

    def _store(self, response: Response) -> None:
        for header in response.headers.get_all("Set-Cookie") or []:
            first, *attrs = [part.strip() for part in header.split(";")]
            name, _, value = first.partition("=")
            lowered = [a.lower() for a in attrs]
            if value == '""' or value == "" or "max-age=0" in lowered:
                self.cookies.pop(name, None)
            else:
                self.cookies[name] = value

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.request("POST", path, body, **kw)

    def patch(self, path, body=None, **kw):
        return self.request("PATCH", path, body, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)
