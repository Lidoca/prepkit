# prepkit

면접 질문 관리 앱. SM-2 스페이스드 리피티션 기반 복습 스케줄러 내장.

| | |
|---|---|
| **백엔드** | FastAPI · SQLModel · MySQL · Alembic · JWT |
| **프론트엔드** | Next.js 16 · TypeScript · Tailwind CSS 4 |
| **인프라** | Docker Compose |

## 빠른 시작 (Docker)

```bash
# 1. 환경 변수 설정
cp backend/.env.example backend/.env
# SECRET_KEY, FIRST_SUPERUSER_PASSWORD 수정 권장

# 2. 전체 스택 실행
docker compose up -d
```

| 서비스 | URL |
|--------|-----|
| 프론트엔드 | http://localhost:3000 |
| 백엔드 API | http://localhost:8000 |
| API 문서 (Swagger) | http://localhost:8000/docs |

## 로컬 개발

DB만 Docker로 띄우고 각 앱을 로컬에서 실행합니다.

```bash
# MySQL만 실행
docker compose up -d db

# 백엔드 (터미널 1)
source .venv/bin/activate       # 또는 cd backend && uv venv && uv sync
cd backend
make dev                        # fastapi dev app/main.py → :8000

# 프론트엔드 (터미널 2)
cd frontend
npm install
npm run dev                     # → :3000
```

### 마이그레이션

```bash
cd backend
make migrate                    # alembic upgrade head
make makemigration m="설명"      # 새 마이그레이션 파일 생성
```

## 프로젝트 구조

```
prepkit/
├── backend/
│   ├── app/
│   │   ├── models.py           # User · Tag · Question · ReviewSchedule
│   │   ├── crud.py             # CRUD + SM-2 알고리즘
│   │   ├── main.py             # FastAPI 진입점
│   │   ├── core/               # config · security · db
│   │   └── api/routes/         # login · users · questions · tags · reviews
│   ├── alembic.ini
│   ├── Makefile
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── login/page.tsx
│   │   ├── questions/page.tsx
│   │   └── reviews/page.tsx
│   ├── components/Nav.tsx
│   ├── lib/
│   │   ├── api.ts              # FastAPI 클라이언트 (fetch 래퍼)
│   │   └── types.ts            # TypeScript 타입
│   ├── next.config.ts          # /api/* → FastAPI rewrite
│   └── Dockerfile
└── docker-compose.yml
```

## API 엔드포인트

모든 엔드포인트는 `/api/v1` 접두사. 인증: `Authorization: Bearer <token>`.

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/login/access-token` | 로그인 (form-data) |
| GET | `/users/me` | 내 정보 |
| POST | `/users/signup` | 회원가입 |
| GET/POST | `/questions/` | 질문 목록·생성 |
| GET/PUT/DELETE | `/questions/{id}` | 질문 조회·수정·삭제 |
| GET/POST | `/tags/` | 태그 목록·생성 |
| GET | `/reviews/due` | 오늘 복습할 질문 |
| POST | `/reviews/{id}/submit` | 복습 결과 제출 (`quality: 0-5`) |

## SM-2 알고리즘

`quality < 3`: 복습 리셋 (interval=1일)  
`quality >= 3`: `interval = round(interval × ease_factor)` 로 다음 복습일 계산
