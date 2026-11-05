import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _read_env_file(name: str) -> str | None:
    # 테스트에서는 TASKFLOW_ENV_FILE로 다른 위치를 가리킬 수 있다.
    path = Path(os.environ.get("TASKFLOW_ENV_FILE") or BACKEND_DIR / ".env")
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


def database_url() -> str:
    """PostgreSQL 연결 주소. 환경변수 또는 backend/.env의 DATABASE_URL에서 읽는다. (D-020)

    Supabase는 Transaction pooler(포트 6543) 주소를 쓴다. 값은 코드와 Git에 넣지 않는다.
    """
    value = os.environ.get("DATABASE_URL") or _read_env_file("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "DATABASE_URL이 비어 있습니다. backend/.env.example을 복사해 "
            "backend/.env를 만들고 값을 채워 주세요."
        )
    return value
