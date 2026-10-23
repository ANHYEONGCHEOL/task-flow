import hashlib
import hmac
import re
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from pydantic import BaseModel, field_validator

from .config import session_secret
from .db import connect

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "session"
SESSION_MINUTES = 30  # 로그인한 때부터 센다. 요청마다 연장하지 않는다. (D-019)
MIGRATED_EMAIL = "migrated@test.com"  # 기존 Task를 가진 이전용 계정 (D-018)

# 비밀번호는 Argon2 같은 전용 해시로만 저장한다. 원문은 어디에도 남기지 않는다.
hasher = PasswordHash.recommended()
# 없는 이메일로 로그인해도 해시 계산을 한 번 하게 해서 응답 시간으로 가입 여부가 드러나지 않게 한다.
DUMMY_HASH = hasher.hash("not-a-real-password")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NOT_LOGGED_IN = "로그인이 필요합니다."
LOGIN_FAILED = "이메일이나 비밀번호가 맞지 않습니다."


def _normalize_email(value: str) -> str:
    return value.strip().lower()


class Register(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        value = _normalize_email(value)
        if len(value) > 254 or not EMAIL_PATTERN.match(value):
            raise ValueError("이메일 형식이 맞지 않습니다.")
        return value

    @field_validator("password")
    @classmethod
    def _password(cls, value: str) -> str:
        if not 8 <= len(value) <= 128:
            raise ValueError("비밀번호는 8자 이상 128자 이하여야 합니다.")
        return value


class Login(BaseModel):
    # 로그인에서는 규칙 위반을 따로 알리지 않는다. 틀리면 모두 같은 401이다.
    email: str
    password: str


class User(BaseModel):
    """응답에는 id와 email만 담는다. 비밀번호와 해시는 담지 않는다."""

    id: int
    email: str


def _sign(session_id: str) -> str:
    return hmac.new(
        session_secret().encode("utf-8"), session_id.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _session_id_from_cookie(value: str | None) -> str | None:
    """`세션ID.서명` 쿠키에서 서명이 맞을 때만 세션 구분값을 돌려준다."""
    if not value:
        return None
    session_id, _, signature = value.rpartition(".")
    if not session_id or not hmac.compare_digest(signature, _sign(session_id)):
        return None
    return session_id


def _now() -> datetime:
    return datetime.now(UTC)


def current_user(request: Request) -> User:
    """로그인한 사용자. 없거나 만료되었으면 401이다."""
    session_id = _session_id_from_cookie(request.cookies.get(COOKIE_NAME))
    if session_id:
        with connect() as conn:
            row = conn.execute(
                "SELECT u.id, u.email, s.expires_at FROM sessions s "
                "JOIN users u ON u.id = s.user_id WHERE s.id = ?",
                (session_id,),
            ).fetchone()
        if row and datetime.fromisoformat(row["expires_at"]) > _now():
            return User(id=row["id"], email=row["email"])
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, NOT_LOGGED_IN)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: Register) -> User:
    hashed = hasher.hash(body.password)
    try:
        with connect() as conn:
            row = conn.execute(
                "SELECT id, password_hash FROM users WHERE email = ?", (body.email,)
            ).fetchone()
            if row is None:
                cur = conn.execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    (body.email, hashed),
                )
                user_id = cur.lastrowid
            elif body.email == MIGRATED_EMAIL and row["password_hash"] is None:
                # 이전용 계정은 처음 가입하는 사람이 비밀번호를 정해 기존 Task와 함께 받는다. (D-018)
                cur = conn.execute(
                    "UPDATE users SET password_hash = ? "
                    "WHERE id = ? AND password_hash IS NULL",
                    (hashed, row["id"]),
                )
                if cur.rowcount == 0:
                    raise sqlite3.IntegrityError("already claimed")
                user_id = row["id"]
            else:
                raise sqlite3.IntegrityError("duplicate email")
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 쓰고 있는 이메일입니다.")
    return User(id=user_id, email=body.email)


@router.post("/login")
def login(body: Login, response: Response) -> User:
    email = _normalize_email(body.email)
    with connect() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    stored = row["password_hash"] if row else None
    verified = hasher.verify(body.password, stored or DUMMY_HASH)
    # 비밀번호가 없는 계정(아직 가입으로 받지 않은 이전용 계정)은 로그인할 수 없다.
    if row is None or stored is None or not verified:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, LOGIN_FAILED)

    session_id = secrets.token_urlsafe(32)
    expires_at = _now() + timedelta(minutes=SESSION_MINUTES)
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (_now().isoformat(),))
        conn.execute(
            "INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)",
            (session_id, row["id"], expires_at.isoformat()),
        )
    response.set_cookie(
        COOKIE_NAME,
        f"{session_id}.{_sign(session_id)}",
        max_age=SESSION_MINUTES * 60,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return User(id=row["id"], email=row["email"])


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request, response: Response, user: User = Depends(current_user)
) -> None:
    session_id = _session_id_from_cookie(request.cookies.get(COOKIE_NAME))
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me")
def me(user: User = Depends(current_user)) -> User:
    return user
