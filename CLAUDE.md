# prepkit

면접 질문 관리 앱. FastAPI 백엔드 + Next.js 프론트엔드.

## 스택

**백엔드** (`backend/`)
- **FastAPI** + **SQLModel** + **MySQL** (pymysql)
- **JWT** 인증 (pyjwt + pwdlib argon2/bcrypt)
- **Alembic** 마이그레이션

**프론트엔드** (`frontend/`)
- **Next.js 16** (App Router) + **TypeScript** + **Tailwind CSS**
- Next.js rewrites로 `/api/*` → FastAPI 프록시 (CORS 불필요)

## 개발 환경

```bash
# Docker로 전체 스택 기동 (MySQL + FastAPI)
docker compose up -d

# 백엔드 로컬 실행
source backend/.venv/bin/activate   # .venv는 backend/ 안에 위치
cd backend
make dev          # fastapi dev app/main.py

# 마이그레이션
cd backend
make migrate                      # alembic upgrade head
make makemigration m="설명"        # autogenerate 후 파일 생성

# 프론트엔드 실행 (백엔드가 :8000에서 실행 중이어야 함)
cd frontend
npm run dev       # http://localhost:3000
```

API 문서: `http://localhost:8000/docs`

## 프로젝트 구조

```
backend/
├── app/
│   ├── models.py          # User · Tag · Question · QuestionTagLink · ReviewSchedule
│   ├── crud.py            # CRUD 함수 + SM-2 알고리즘 (_sm2_update)
│   ├── main.py            # FastAPI 앱 진입점
│   ├── core/
│   │   ├── config.py      # pydantic-settings (MYSQL_*, SECRET_KEY 등)
│   │   ├── security.py    # JWT 생성/검증, 패스워드 해싱
│   │   └── db.py          # engine, init_db (superuser 생성)
│   └── api/
│       ├── deps.py        # SessionDep · CurrentUser (JWT → uuid.UUID 변환)
│       └── routes/
│           ├── login.py   # POST /login/access-token
│           ├── users.py   # /users/*
│           ├── questions.py  # /questions/*
│           ├── tags.py       # /tags/*
│           └── reviews.py    # /reviews/due · /{q_id}/submit
├── alembic.ini
├── Makefile
└── Dockerfile

frontend/
├── app/
│   ├── login/page.tsx     # 로그인
│   ├── questions/page.tsx # 질문 목록·생성·삭제
│   ├── reviews/page.tsx   # SM-2 복습 세션
│   ├── layout.tsx         # 루트 레이아웃 (Nav 포함)
│   └── page.tsx           # /questions로 리다이렉트
├── components/
│   └── Nav.tsx            # 네비게이션 바
├── lib/
│   ├── api.ts             # FastAPI 클라이언트 (fetch 래퍼)
│   └── types.ts           # TypeScript 타입 (백엔드 모델 대응)
└── next.config.ts         # /api/* → http://localhost:8000 rewrite
```

## 프론트엔드 API 연결 구조

- `next.config.ts`의 rewrites: `/api/:path*` → `BACKEND_URL/api/:path*`
- `frontend/lib/api.ts`: 인증 토큰(`localStorage`)을 자동으로 `Authorization` 헤더에 첨부
- `frontend/.env.local`: `BACKEND_URL=http://localhost:8000`
- 인증: JWT를 `localStorage['access_token']`에 저장, 페이지 진입 시 토큰 없으면 `/login`으로 리다이렉트

## API 엔드포인트

모든 엔드포인트는 `/api/v1` 접두사. 인증은 `Authorization: Bearer <token>`.

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/login/access-token` | 로그인 (form-data) |
| GET | `/users/me` | 내 정보 |
| POST | `/users/signup` | 회원가입 |
| GET/POST | `/questions/` | 질문 목록·생성 (`?tag_id=&difficulty=`) |
| GET/PUT/DELETE | `/questions/{id}` | 질문 조회·수정·삭제 |
| GET/POST | `/tags/` | 태그 목록·생성 |
| GET/PUT/DELETE | `/tags/{id}` | 태그 조회·수정·삭제 |
| GET | `/reviews/due` | 오늘 복습할 질문 목록 |
| POST | `/reviews/{question_id}/submit` | 복습 결과 제출 (`quality: 0-5`) |

## 주요 설계 결정

- `User.__tablename__ = "users"` — MySQL에서 `user`는 예약어
- 질문 생성 시 `ReviewSchedule` 자동 생성 (`next_review_at = 지금`)
- `Optional["ReviewSchedule"]` 사용 — SQLAlchemy는 `"X | None"` 문자열 어노테이션 미지원
- `deps.py`에서 `uuid.UUID(token_data.sub)` 변환 필수 — MySQL CHAR(32) UUID 쿼리 시 필요
- `content`/`answer` 필드는 `sa_type=Text()` — MySQL TEXT 타입 매핑
- Next.js 16: `middleware.ts` → `proxy.ts`로 이름 변경됨 (아직 미사용)

## SM-2 알고리즘

`crud._sm2_update(repetitions, ease_factor, interval_days, quality)`:
- `quality < 3`: 리셋 (repetitions=0, interval=1)
- `repetitions 0→1`: interval=1일
- `repetitions 1→2`: interval=6일
- 이후: `interval = round(interval * ease_factor)`
- `ease_factor` 조정: `ef += 0.1 - (5-q) * (0.08 + (5-q) * 0.02)`, 최솟값 1.3

## 환경 변수

**`backend/.env`**
```
PROJECT_NAME=prepkit
SECRET_KEY=<32자 이상 랜덤>
MYSQL_SERVER=localhost   # Docker에서는 compose가 "db"로 오버라이드
MYSQL_PORT=3306
MYSQL_USER=prepkit
MYSQL_PASSWORD=prepkit
MYSQL_DB=prepkit
FIRST_SUPERUSER=admin@prepkit.dev
FIRST_SUPERUSER_PASSWORD=<비밀번호>
```

**`frontend/.env.local`**
```
BACKEND_URL=http://localhost:8000
```
