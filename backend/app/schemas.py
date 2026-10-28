import re
from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, model_validator


class Status(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Priority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


def _require_title(value: str) -> str:
    # 공백만 있는 제목은 비어 있는 제목으로 본다. (D-012)
    value = value.strip()
    if not value:
        raise ValueError("제목을 입력해 주세요.")
    return value


Title = Annotated[str, AfterValidator(_require_title)]

_DATE_FORMAT = re.compile(r"\d{4}-\d{2}-\d{2}")


def _check_due_date(value: str | None) -> str | None:
    # 날짜만 받는다. YYYY-MM-DD가 아니거나 없는 날짜(2월 30일 등)는 거절한다. (BR-02)
    if value is None:
        return None
    if not _DATE_FORMAT.fullmatch(value):
        raise ValueError("마감일은 YYYY-MM-DD 형식이어야 합니다.")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError("존재하지 않는 날짜입니다.") from None
    return value


DueDate = Annotated[str | None, AfterValidator(_check_due_date)]


class TaskCreate(BaseModel):
    title: Title
    description: str = ""
    priority: Priority = Priority.NORMAL  # 고르지 않으면 NORMAL이다. null은 거절한다. (BR-01)
    due_date: DueDate = None


class TaskBulkCreate(BaseModel):
    """미리본 할일을 한꺼번에 저장한다. 하나라도 값이 틀리면 전부 저장하지 않는다."""

    items: Annotated[list[TaskCreate], Field(min_length=1, max_length=10)]


class TaskUpdate(BaseModel):
    """보낸 필드만 바꾼다. 상태는 받지 않는다. (결정 F, N-15)

    due_date는 null을 보내면 지운다. 나머지는 null을 보내면 거절한다.
    """

    title: Title | None = None
    description: str | None = None
    priority: Priority | None = None
    due_date: DueDate = None

    @model_validator(mode="after")
    def _no_null_except_due_date(self):
        for name in ("title", "description", "priority"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name}은(는) 비울 수 없습니다.")
        return self


class StatusChange(BaseModel):
    status: Status  # 세 값이 아니면 422로 거부된다. (D-004)


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: Status
    priority: Priority
    due_date: str | None
    is_overdue: bool  # 저장하지 않고 목록을 줄 때 계산한다. (BR-03)
