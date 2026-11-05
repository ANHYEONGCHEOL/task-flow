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

1. Supabase 프로젝트를 만들고 앱 전용 역할을 만든다. (SQL Editor, 비밀번호는 영문·숫자로 길고 무작위로 직접 정한다. `@ # / :` 같은 특수문자는 접속 주소가 깨지니 쓰지 않는다)

       create role tf_app with login password '<긴 무작위 비밀번호>';
       grant usage, create on schema public to tf_app;

   프로젝트를 만들 때 Data API는 꺼도 된다(앱은 DB에 직접 연결한다). 켠다면 「Automatically expose new tables」는 끈다.
2. 테이블을 만든다. 마이그레이션은 **Session pooler(포트 5432) 주소**로 한 번만 실행한다. 사용자 이름은 `tf_app.<프로젝트ID>`다. 실DB를 바꾸는 명령이라 사람이 직접 한다.

       cd backend
       $env:DATABASE_URL = "<Session pooler 주소>"
       uv run alembic upgrade head

   Direct connection(5432)은 IPv6라서 집 인터넷에서는 연결되지 않을 수 있다. 그래서 Session pooler를 쓴다.
   alembic이 만드는 `alembic_version` 테이블은 마이그레이션이 RLS를 켜지 못한다. SQL Editor에서 직접 켠다. 프로젝트를 만들 때 「Enable automatic RLS」를 켰다면 `rls_auto_enable()` 함수의 실행 권한도 거둔다. (둘 다 Supabase는 관리자 소유라 SQL Editor에서 한다)

       ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY;
       REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;

   Supabase 대시보드 → Advisors → Security Advisor에 「RLS Disabled in Public」 경고가 없어야 한다. 「RLS Enabled No Policy」 안내는 규칙을 만들지 않은 것이라 정상이다.
3. Vercel에 로그인하고 프로젝트를 연결한다. Windows에서는 **개발자 모드**(설정 → 시스템 → 개발자용)가 켜져 있어야 `vercel link`가 된다.

       vercel login
       vercel link --yes --project task-flow

   환경 변수를 넣는다. 앱이 쓰는 `DATABASE_URL`은 **Transaction pooler(포트 6543) 주소**다. 값은 모두 Secret으로 넣는다.

       vercel env add DATABASE_URL production
       vercel env add SESSION_SECRET production
       vercel env add ANTHROPIC_API_KEY production   # AI 기능을 쓸 때만. 아래 「요금」을 먼저 읽는다

   값을 화면에 보이지 않게 넣으려면 파이프로 전달한다.

       node -e "process.stdout.write(require('crypto').randomBytes(32).toString('hex'))" | vercel env add SESSION_SECRET production --sensitive

   **환경 변수를 넣거나 바꾼 뒤에는 다시 배포해야 반영된다.**
4. 배포하고 확인한다.

       vercel deploy --prod --yes
       curl.exe -s <운영 주소>/api/health

`requirements.txt`는 `backend`의 잠금 파일에서 만든다. 패키지를 바꾸면 다시 만든다.

    cd backend
    uv export --no-hashes --no-dev --no-emit-project -o ../requirements.txt

### 배포에 비밀 파일이 올라가지 않게

- **`.vercelignore`가 있으면 Vercel은 `.gitignore`를 쓰지 않는다.** 올리면 안 되는 파일은 `.vercelignore`에도 적는다. `.env`만 적으면 `.env.local`(Vercel 토큰 파일)은 막지 못해서 `.env.*`로 적는다.
- 로그인 쿠키를 저장하는 `ck.txt`(`curl -c ck.txt`)도 올리거나 커밋하면 안 된다. `.gitignore`와 `.vercelignore`에 적어 두었다.
- 배포하기 전에 올라갈 파일에 비밀값이 없는지 확인한다. 배포 로그의 「Downloading N deployment files」 개수가 예상보다 많으면 멈춘다.
- 환경 변수는 파일이 아니라 Vercel에 암호화되어 보관된다. 화면과 코드에 출력하지 않는다.

### 운영 점검

`vercel project ls`에 나오는 Latest Production URL이 운영 주소다. 이 주소는 누구나 열 수 있다. (배포마다 붙는 긴 주소는 Vercel 로그인 보호가 걸려 있다)

    vercel project ls
    curl.exe -s <운영 주소>/api/health                              # {"status":"ok"}
    curl.exe -s -o NUL -w "%{http_code}" <운영 주소>/               # 200
    curl.exe -s -o NUL -w "%{http_code}" <운영 주소>/api/tasks      # 401 (로그인 없이는 막힘)

### 안 될 때

    vercel ls                                                      # 맨 위 줄이 가장 최근 배포
    vercel logs --deployment <맨 위 배포 주소> --since 30m

로그에서 원인 줄을 찾는다. 뒤따라 나오는 줄(`cannot import name ...`)은 원인이 아니다.

| 로그나 증상 | 원인과 해결 |
|---|---|
| `SESSION_SECRET이 비어 있습니다` | 환경 변수가 없다. `vercel env ls`로 확인하고 넣은 뒤 다시 배포한다. |
| `DATABASE_URL이 비어 있습니다` | 위와 같다. |
| `DB가 아직 이전되지 않았습니다` | 이 DB에 `alembic upgrade head`를 하지 않았다. 2단계를 한다. |
| `vercel link`에서 `EPERM ... symlink` | Windows 개발자 모드가 꺼져 있다. 켠다. |
| 배포가 커밋 작성자 때문에 막힘 | 최근 커밋 작성자 이메일이 Vercel 가입 이메일과 다르다. `git log -1 --format="%h %ae"`로 확인하고, 필요할 때만 가입 이메일로 빈 커밋을 만든다. |
| 터미널에서 `/api/health`가 `C:/Program Files/Git/...`로 바뀜 | Git Bash가 경로로 바꾼 것이다. PowerShell에서 실행한다. |

### 처음부터 다시 (초기화)

조에서 배포한 사람의 PC에서 한 번만 한다. **프로젝트를 지우면 배포 기록, 운영 주소, 환경 변수가 함께 없어진다.** 지운 뒤에는 3단계부터 다시 한다.

    vercel project rm <프로젝트 이름> --confirm-name <프로젝트 이름>
    vercel project ls
    Remove-Item -Recurse -Force .vercel
    Remove-Item -Force .env.local -ErrorAction SilentlyContinue

`.vercel`은 이 폴더가 어느 프로젝트인지 적어 둔 곳이고, `.env.local`은 vercel이 내려받은 임시 토큰 파일이다. 둘 다 Git에 올리지 않는다.

### 요금과 공개 범위

- Vercel Hobby와 Supabase Free는 무료다. 카드를 등록하지 않으면 한도를 넘어도 청구되지 않고 기능이 제한된다.
- 운영 주소는 공개이고 회원가입은 누구나 할 수 있다. 실제 개인정보나 중요한 비밀번호를 넣지 않는다.
- `ANTHROPIC_API_KEY`를 넣으면 AI 기능을 쓸 때마다 요금이 든다. 가입한 누구나 AI 기능을 부를 수 있으므로, **키를 넣기 전에 Anthropic 콘솔에서 월 사용 한도를 낮게 정한다.**

## 테스트 (backend 폴더에서)

`backend/.env`의 `TASKFLOW_TEST_DATABASE_URL`(DB 이름이 `_test`로 끝나야 한다)의 테스트용 DB로만 확인한다. 이 DB의 테이블은 테스트할 때마다 지우고 다시 만든다. 실제 DB는 건드리지 않는다.

    uv run python -m unittest discover -s tests -t .
