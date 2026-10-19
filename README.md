# task-flow

혼자 쓰는 Task 관리 웹 앱. 화면 React · Vite, API FastAPI, 저장소 SQLite.
현재 M0: 프로젝트 기본 구조만 있다. (Task 기능, DB, 로그인 없음)

## 실행

API (backend 폴더에서):

    uv run uvicorn app.main:app --port 8000

화면 (frontend 폴더에서, Node.js 필요):

    npm install
    npm run dev
