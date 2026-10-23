# task-flow

혼자 쓰는 Task 관리 웹 앱. 화면 React · Vite, API FastAPI, 저장소 SQLite.
로그인한 사람은 자기 Task만 본다. (R-008)

## 실행

처음 한 번, 세션 비밀값을 만든다. `backend/.env`는 Git에 올라가지 않는다.

    cd backend
    cp .env.example .env
    uv run python -c "import secrets; print(secrets.token_hex(32))"

출력된 긴 값을 `.env`의 `SESSION_SECRET=` 뒤에 붙여 넣고 저장한다. 값이 비어 있으면 API는 시작하지 않는다.

API (backend 폴더에서):

    uv run python -m uvicorn app.main:app --port 8000

화면 (frontend 폴더에서, Node.js 필요):

    npm install
    npm run dev

## 기존 DB 이전

로그인을 넣기 전의 DB(Task만 있고 주인이 없는 `backend/taskflow.db`)는 이전해야 쓸 수 있다.
이전되지 않은 DB이면 API가 시작하지 않는다. 이전은 **백업한 뒤 사람이 직접** 실행한다.
(앱은 시작할 때 DB를 바꾸지 않는다. 이전 도구는 alembic이고 절차 파일은 `backend/migrations/versions`에 있다.)

1. 이전 전 수량을 적어 둔다: 전체 Task 수, 상태별 수, 표본 Task 세 개의 제목 · 설명 · 상태.
2. API를 멈추고 DB 파일을 백업한다.

       cp backend/taskflow.db backend/before-auth-taskflow.db

3. 이전을 실행한다. `Running upgrade` 줄이 네 번(0001 ~ 0004) 보이면 끝까지 적용된 것이다.

       cd backend
       uv run alembic upgrade head

4. 같은 질문으로 수량을 다시 확인하고 이전 전과 맞춘다: 전체 Task 수 · 상태별 수 · 표본 세 개가 같고, 주인 없는 Task가 0개이고, `users`에 `migrated@test.com` 한 명만 있어야 한다.
5. 하나라도 다르면 API를 멈추고 백업 파일로 되돌린다.

       cp backend/before-auth-taskflow.db backend/taskflow.db

   되돌리는 명령은 늘 백업 파일로 한다. 다운그레이드는 지원하지 않는다(사용자와 Task를 잃을 수 있어서).
6. 기존 Task는 이전용 계정 `migrated@test.com`이 갖는다. 이 계정은 비밀번호가 없어서 처음에는 로그인할 수 없다.
   앱에서 **이 이메일로 처음 가입하는 사람**이 비밀번호를 정해 계정과 기존 Task를 받는다.
   다른 사람이 먼저 이 이메일로 가입하면 그 사람이 기존 Task를 받으니, 이전한 직후에 가입한다.

## 테스트 (backend 폴더에서)

임시 폴더의 테스트용 DB로만 확인하고 실제 DB는 건드리지 않는다.

    uv run python -m unittest discover -s tests -t .
