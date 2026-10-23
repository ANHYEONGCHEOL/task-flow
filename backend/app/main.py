from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import router as auth_router
from .config import session_secret
from .db import check_schema
from .tasks import router as tasks_router

check_schema()
session_secret()  # SESSION_SECRET이 비어 있으면 시작하지 않는다.

app = FastAPI(title="task-flow API")
app.include_router(auth_router)
app.include_router(tasks_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
