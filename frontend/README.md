# FindComments — YouTube 커뮤니티 반응 분석기

YouTube 영상의 댓글을 AI로 분석해 감정 분포, 반응 토픽, 시간대별 트렌드, 핵심 인사이트를 시각화하는 대시보드입니다.

---

## 실행 방법

### 1. 환경변수 설정

`backend/.env` 파일을 생성하고 API 키를 입력합니다.

```
YOUTUBE_API_KEY=여기에_유튜브_API_키
OPENAI_API_KEY=여기에_OpenAI_API_키
```

### 2. Backend 실행

```bash
# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 패키지 설치 (처음 한 번만)
pip install -r backend/requirements.txt

# ⚠️ backend 폴더로 이동 후 실행해야 합니다
cd backend
uvicorn main:app --reload --port 4000
```

→ http://localhost:4000

### 3. Frontend 실행

```bash
cd frontend

npm install     # 패키지 설치 (처음 한 번만)
npm run dev     # 개발 서버 실행
```

→ http://localhost:5173

---

## 주요 기능

- **YouTube 댓글 분석** — URL 입력 한 번으로 댓글 전체 수집 → GPT 감정 분석 → 결과 대시보드 표시
- **실시간 진행 상황** — SSE 스트리밍으로 분석 단계를 사이드바 인디케이터와 함께 실시간 표시
- **분석 기록 저장** — 서버 JSON 캐시 기반 이전 결과 저장 및 재열람 (동일 영상 재분석 없이 즉시 로드)
- **상위 반응 토픽** — AI 추출 주제별 언급수·감정 분포, 클릭 시 해당 댓글 목록 드로어 표시
- **시간대별 트렌드** — 업로드 후 0–1h / 1–24h / 1–7d / 7–30d / 30d+ 구간별 감정 흐름 차트
- **분석 지표 카드** — 감정 점수, 댓글 반응률, 좋아요율, 논쟁성, 가중 감정(좋아요 가중 평균) 5가지 지표 제공
- **주요 인사이트** — 좋아요 높은 대표 긍정·부정 댓글 요약 및 언어 분포 시각화
- **영상 비교** — 분석된 영상 2~3개를 나란히 비교 (기본정보·분석지표·감정분포·토픽·언어분포)
- **PDF 내보내기** — 분석 기록 열람 시 현재 대시보드 화면 그대로 PDF 출력
- **4개 언어 지원** — 한국어 / English / 中文 / 日本語 실시간 전환 (선택 언어 localStorage 저장)
- **다크/라이트 모드** — 테마 전환 (설정 localStorage 저장)

---

## 기술 스택

**Frontend**
Vue 3 (Composition API) · TypeScript · Pinia · Vue Router · Tailwind CSS v4 · Vite

**Backend**
Python · FastAPI · OpenAI GPT-4o-mini · text-embedding-3-small · YouTube Data API v3

**통신 / 상태관리**
SSE (Server-Sent Events) 스트리밍 · Axios · Pinia setup store

---

## 폴더 구조

```
frontend/src/
├── locales/
│   └── messages.ts         — ko/en/zh/ja 4개 언어 번역 데이터
├── features/
│   ├── insight/
│   │   ├── api/            insightApi.ts — 백엔드 API 호출 분리
│   │   ├── components/     VideoInfoCard, TopReactionTopics, ReactionTimeline,
│   │   │                   KeyInsights, LoadingState, TopicComments
│   │   ├── pages/          HomeView, HistoryView, CompareView
│   │   ├── stores/         analysis.ts — SSE 분석 상태 및 전역 결과 관리
│   │   └── types/          insight.ts — 공유 타입 정의 (Lang, InsightData 등)
│   └── settings/
│       ├── pages/          SettingsView
│       └── stores/         settings.ts — 테마(다크/라이트) · 언어 설정
├── layouts/                AppLayout.vue — 사이드바 + 탑바 전역 레이아웃
├── pages/                  HowToView, StatsView
├── router/                 index.ts
└── shared/
    └── api/                client.ts — Axios 인스턴스
```

```
backend/
├── main.py         — FastAPI 서버, 엔드포인트 정의, SSE 스트리밍
├── youtube.py      — YouTube Data API 댓글 수집
├── sentiment.py    — GPT 배치 감정 분석 (긍정/중립/부정)
├── topic.py        — GPT 토픽 추출 + 임베딩 기반 배정
├── cache/          — 영상별 JSON 분석 결과 캐시
└── requirements.txt
```

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/insight?url=...` | SSE 스트리밍 분석 시작 |
| GET | `/api/history` | 전체 분석 기록 목록 |
| GET | `/api/history/{video_id}` | 특정 영상 분석 결과 |
| DELETE | `/api/history/{video_id}` | 캐시 삭제 |
| GET | `/api/stats` | 분석 통계 (소요시간·처리량) |
| GET | `/api/comments/{video_id}` | 토픽별 댓글 목록 |
| POST | `/api/translate-labels` | 토픽 라벨 영문 번역 |
| POST | `/api/refresh/{video_id}` | 캐시 강제 재분석 |

---

## 라우트 구조

| 경로 | 설명 |
|---|---|
| `/` | 분석 입력 화면 / 분석 결과 대시보드 |
| `/history` | 분석 기록 목록 |
| `/history/view` | 기록에서 불러온 분석 결과 (HomeView 재사용) |
| `/compare` | 영상 비교 |
| `/stats` | 분석 통계 |
| `/howto` | 작동 방식 |
| `/settings` | 설정 |

---

## 트러블슈팅

**백엔드 실행 오류 (ModuleNotFoundError)**

반드시 `cd backend` 후 `uvicorn main:app`을 실행해야 합니다. 프로젝트 루트에서 `uvicorn backend.main:app`으로 실행하면 내부 모듈을 찾지 못합니다.

**화면이 이상하게 동작할 때 (HMR 캐시)**

Pinia 스토어 구조 변경 후 브라우저 메모리에 이전 상태가 남아 있으면 발생합니다.

```
F12 → 새로고침 버튼 우클릭 → "캐시 비우기 및 강력 새로고침"
```

단축키: `Ctrl + Shift + R`
