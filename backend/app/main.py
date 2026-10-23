from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import check_schema
from .tasks import router as tasks_router

check_schema()

app = FastAPI(title="task-flow API")
app.include_router(tasks_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
