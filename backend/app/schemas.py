from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel


class Status(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


def _require_title(value: str) -> str:
    # 공백만 있는 제목은 비어 있는 제목으로 본다. (D-012)
    value = value.strip()
    if not value:
        raise ValueError("제목을 입력해 주세요.")
    return value


Title = Annotated[str, AfterValidator(_require_title)]


class TaskCreate(BaseModel):
    title: Title
    description: str = ""


class TaskUpdate(TaskCreate):
    """제목과 설명을 통째로 보낸다. 상태는 받지 않는다."""


class StatusChange(BaseModel):
    status: Status  # 세 값이 아니면 422로 거부된다. (D-004)


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: Status
