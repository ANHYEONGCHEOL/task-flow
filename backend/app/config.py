import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def db_path() -> Path:
    """DB 파일 위치. 테스트용 DB는 환경변수 TASKFLOW_DB로 지정한다."""
    value = os.environ.get("TASKFLOW_DB")
    return Path(value) if value else BACKEND_DIR / "taskflow.db"


def _read_env_file(name: str) -> str | None:
    path = BACKEND_DIR / ".env"
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == name:
            return value.strip()
    return None


def session_secret() -> str:
    """세션 쿠키 서명 키. 환경변수 또는 backend/.env의 SESSION_SECRET에서 읽는다.

    값이 없으면 API는 시작하지 않는다. 값은 코드와 Git에 넣지 않는다.
    """
    value = os.environ.get("SESSION_SECRET") or _read_env_file("SESSION_SECRET")
    if not value:
        raise RuntimeError(
            "SESSION_SECRET이 비어 있습니다. backend/.env.example을 복사해 "
            "backend/.env를 만들고 값을 채워 주세요."
        )
    return value
