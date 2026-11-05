# task-flow

혼자 쓰는 Task 관리 웹 앱. 화면 React · Vite, API FastAPI, 저장소 PostgreSQL(배포는 Supabase · Vercel). (D-020)
로그인한 사람은 자기 Task만 본다. (R-008)

## 실행

PostgreSQL이 필요하다. 로컬에 개발용 DB를 하나 만들어 둔다. (테스트용 DB와는 따로 쓴다)

    psql -U postgres -h localhost -c "CREATE DATABASE taskflow"

처음 한 번, 세션 비밀값을 만들고 DB 주소를 적는다. `backend/.env`는 Git에 올라가지 않는다.

    cd backend
    cp .env.example .env
    uv run python -c "import secrets; print(secrets.token_hex(32))"

출력된 긴 값을 `.env`의 `SESSION_SECRET=` 뒤에 붙여 넣고, `DATABASE_URL=` 뒤에 DB 주소를 적고 저장한다.

    DATABASE_URL=postgresql://postgres:<비밀번호>@localhost:5432/taskflow

값이 비어 있으면 API는 시작하지 않는다. 앱은 시작할 때 DB를 바꾸지 않으므로, 테이블은 직접 만든다.

    cd backend
    uv run alembic upgrade head

API (backend 폴더에서):

    uv run python -m uvicorn app.main:app --port 8000

### AI 제안 (선택)

`POST /tasks/suggest`는 Task의 제목과 설명으로 우선순위와 마감일을 제안한다. 제안만 돌려주고 DB는 바꾸지 않는다.
API를 켜는 터미널에 환경 변수 `ANTHROPIC_API_KEY`를 설정해야 한다. `.env` 파일은 읽지 않는다. 키 값은 Git에 넣지 않는다.
키가 없어도 앱은 시작하고, 이 API만 503 「AI 기능 꺼짐」으로 답한다.

화면 (frontend 폴더에서, Node.js 필요):

    npm install
    npm run dev

## 배포 (Supabase + Vercel)

화면과 API를 Vercel 한 곳에 올리고, DB는 Supabase를 쓴다. `api/index.py`가 진입점이고, 배포할 때 `vercel.json`의 명령으로 화면을 빌드한다.
기존 SQLite 데이터는 옮기지 않고 새 DB로 시작한다. (D-020)

1. Supabase 프로젝트를 만들고 앱 전용 역할을 만든다. (SQL Editor, 비밀번호는 길고 무작위로 직접 정한다)

       create role tf_app with login password '<긴 무작위 비밀번호>';
       grant usage, create on schema public to tf_app;

2. 테이블을 만든다. **직접 연결(포트 5432) 주소**로 한 번만 실행한다. 실DB를 바꾸는 명령이라 사람이 직접 한다.

       cd backend
       $env:DATABASE_URL = "<직접 연결 주소>"
       uv run alembic upgrade head

   Supabase 대시보드 → Advisors → Security Advisor에 「RLS Disabled in Public」 경고가 없어야 한다.
3. Vercel에 로그인하고 환경 변수를 넣는다. 앱이 쓰는 `DATABASE_URL`은 **Transaction pooler(포트 6543) 주소**다.

       vercel login
       vercel env add DATABASE_URL production
       vercel env add SESSION_SECRET production
       vercel env add ANTHROPIC_API_KEY production

4. 배포하고 확인한다.

       vercel deploy --prod --yes
       curl.exe -s <운영 주소>/api/health

`requirements.txt`는 `backend`의 잠금 파일에서 만든다. 패키지를 바꾸면 다시 만든다.

    cd backend
    uv export --no-hashes --no-dev --no-emit-project -o ../requirements.txt

## 테스트 (backend 폴더에서)

`backend/.env`의 `TASKFLOW_TEST_DATABASE_URL`(DB 이름이 `_test`로 끝나야 한다)의 테스트용 DB로만 확인한다. 이 DB의 테이블은 테스트할 때마다 지우고 다시 만든다. 실제 DB는 건드리지 않는다.

    uv run python -m unittest discover -s tests -t .
