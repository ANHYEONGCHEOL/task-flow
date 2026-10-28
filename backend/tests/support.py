"""테스트용 서버와 HTTP 클라이언트. 실제 DB는 쓰지 않고 임시 폴더의 테스트용 DB만 쓴다."""

import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_SECRET = "test-secret-not-a-real-one"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestServer:
    """alembic으로 이전한 테스트용 DB로 API를 띄운다."""

    def __init__(self, secret: str | None = TEST_SECRET, extra_env: dict | None = None):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        self.env = {
            **os.environ,
            "TASKFLOW_DB": str(self.db),
            "PYTHONUTF8": "1",
            "SESSION_SECRET": secret or "",
            **(extra_env or {}),
        }
        self.port = _free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
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
        self.tmp.cleanup()

    def sql(self, query: str, params=()):
        conn = sqlite3.connect(self.db)
        try:
            rows = conn.execute(query, params).fetchall()
            conn.commit()
            return rows
        finally:
            conn.close()


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
