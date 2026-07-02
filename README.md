# YouTube Comment Insight Analyzer

**AI-powered YouTube comment sentiment analysis dashboard**

[![Vue](https://img.shields.io/badge/Vue-3.5-42b883?logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai)](https://openai.com/)
[![License](https://img.shields.io/badge/license-Private-red)](/)

---

## Overview

Paste any YouTube URL and instantly get a structured breakdown of what the audience thinks — sentiment distribution, trending topics, reaction timeline, and key insights extracted from thousands of comments using GPT-4o-mini.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   🔗 Paste YouTube URL   →   Comments collected via API    │
│   🧠 Sentiment Analysis  →   Positive / Neutral / Negative │
│   🏷️  Topic Clustering   →   Auto-grouped by subject       │
│   📈 Reaction Timeline   →   Sentiment trends over time    │
│   💡 Key Insights        →   Top comments by likes         │
│   📊 Video Compare       →   Side-by-side comparison       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### 1. Comment Sentiment Analysis
- Collects public comments via YouTube Data API v3
- Classifies each comment as **Positive / Neutral / Negative** using GPT-4o-mini
- Displays overall sentiment distribution as a percentage bar
- Language ratio detection (Korean / English / Other)

### 2. Topic Classification
- Automatically clusters comments into topics
- Shows mention count and sentiment breakdown per topic
- Click any topic to view the full list of comments (drawer)
- Supports Korean ↔ English label translation

### 3. Reaction Timeline
- Visualizes sentiment changes over time after video upload
- Time buckets: `0–1h`, `1–24h`, `1–7d`, `7–30d`, `30d+`
- Shows positive/neutral/negative stacked bars per period

### 4. Analytics Metrics
| Metric | Description |
|--------|-------------|
| Sentiment Score | `positive% − negative%` overall index |
| Weighted Sentiment | Likes-weighted sentiment score |
| Comment Rate | Comments ÷ Views × 100 |
| Like Rate | Likes ÷ Views × 100 |
| Controversy Score | `min(positive, negative) × 2` |

### 5. Key Insights
- Surfaces the most-liked positive and negative comments per topic
- Up to 4 insights (2 positive, 2 negative)

### 6. History & Compare
- All analyzed videos are cached and accessible from the History tab
- Compare up to **3 videos side-by-side**
- Export analysis as PDF

### 7. Stats Dashboard
- Total analyses, comments processed, tokens used
- Estimated OpenAI API cost per analysis
- Average / min / max analysis duration

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, TypeScript, Vite, Tailwind CSS 4, Pinia |
| Backend | FastAPI, Python |
| AI | OpenAI GPT-4o-mini (sentiment + topic classification) |
| Data | YouTube Data API v3 |
| Export | jsPDF, html2canvas |

---

## Getting Started

### Prerequisites
- Node.js `>=20`
- Python `3.10+`
- OpenAI API Key
- YouTube Data API v3 Key

### 1. Clone the repository
```bash
git clone https://github.com/maiajunok/T1A.git
cd T1A
```

### 2. Set up environment variables
Create `backend/.env`:
```
OPENAI_API_KEY=your_openai_api_key
YOUTUBE_API_KEY=your_youtube_api_key
```

### 3. Run the backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. Run the frontend
```bash
cd frontend
npm install
npm run dev
```

### 5. Open the app
| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## Project Structure

```
T1A/
├── backend/
│   ├── main.py              # FastAPI app, SSE streaming endpoint
│   ├── sentiment.py         # GPT-4o-mini sentiment analysis
│   ├── topic.py             # Topic classification + clustering
│   ├── youtube.py           # YouTube Data API integration
│   ├── requirements.txt
│   └── cache/               # Analysis result cache (JSON)
│       └── comments/        # Per-topic comment cache
│
└── frontend/
    └── src/
        ├── features/
        │   ├── insight/
        │   │   ├── api/         # insightApi.ts — backend calls
        │   │   ├── components/  # VideoInfoCard, ReactionTimeline, KeyInsights …
        │   │   ├── pages/       # HomeView, HistoryView, CompareView
        │   │   ├── stores/      # Pinia analysis store
        │   │   └── types/       # TypeScript interfaces
        │   └── settings/        # Language / theme settings
        ├── pages/               # StatsView, HowToView
        ├── layouts/             # AppLayout
        ├── router/              # Vue Router
        └── locales/             # i18n (ko / en)
```

---

## API Overview

### `POST /api/insight`
Analyzes a YouTube video. Streams progress via **Server-Sent Events (SSE)**.

```json
{ "url": "https://www.youtube.com/watch?v=VIDEO_ID" }
```

SSE events:
```
data: {"step": "댓글 수집 중", "progress": 1}
data: {"step": "감정 분석 중", "progress": 2}
data: {"step": "토픽 분류 중", "progress": 3}
data: {"step": "done", "data": { ... }}
```

### `GET /api/history`
Returns list of all previously analyzed videos.

### `GET /api/history/{video_id}`
Returns cached analysis for a specific video.

### `GET /api/comments/{video_id}?topic=&sentiment=`
Returns filtered comments by topic and sentiment.

### `POST /api/refresh/{video_id}`
Clears cache and forces re-analysis.

### `GET /api/stats`
Returns token usage and cost statistics.

---

## Coming Soon
- Reddit comment analysis
- TikTok comment analysis
- Voice-based search

---

---

# YouTube 댓글 인사이트 분석기

**AI 기반 YouTube 댓글 감정 분석 대시보드**

---

## 소개

YouTube URL을 붙여넣으면 AI가 댓글을 수집하고 감정 분석 · 토픽 분류 · 반응 타임라인 · 핵심 인사이트를 시각화해 보여주는 대시보드입니다. GPT-4o-mini로 수천 개의 댓글을 분석합니다.

---

## 주요 기능

### 1. 댓글 감정 분석
- YouTube Data API v3로 공개 댓글 수집
- GPT-4o-mini로 **긍정 / 중립 / 부정** 분류
- 전체 감정 분포를 퍼센트 바로 시각화
- 언어 비율 감지 (한국어 / 영어 / 기타)

### 2. 토픽 분류
- 댓글을 주제별로 자동 그룹화
- 토픽별 언급 수 및 감정 비율 표시
- 토픽 클릭 시 해당 댓글 전체 보기 (드로어)
- 한국어 ↔ 영어 레이블 번역 지원

### 3. 반응 타임라인
- 영상 업로드 이후 시간대별 감정 변화 시각화
- 구간: `0–1h`, `1–24h`, `1–7d`, `7–30d`, `30d+`
- 구간별 긍정/중립/부정 스택 바 차트

### 4. 분석 지표
| 지표 | 설명 |
|------|------|
| 감정 점수 | `긍정% − 부정%` 전체 지수 |
| 가중 감정 점수 | 좋아요 수 가중 감정 점수 |
| 댓글 비율 | 댓글 수 ÷ 조회수 × 100 |
| 좋아요 비율 | 좋아요 수 ÷ 조회수 × 100 |
| 논란 지수 | `min(긍정, 부정) × 2` |

### 5. 핵심 인사이트
- 토픽별 좋아요 수 기준 상위 긍정 · 부정 댓글 추출
- 최대 4개 인사이트 (긍정 2개, 부정 2개)

### 6. 히스토리 & 비교
- 분석된 영상은 모두 캐시로 저장되어 히스토리 탭에서 확인 가능
- 최대 **3개 영상 나란히 비교**
- 분석 결과 PDF 내보내기

### 7. 통계 대시보드
- 전체 분석 수, 처리 댓글 수, 사용 토큰 수
- OpenAI API 예상 비용
- 분석 소요 시간 (평균 / 최소 / 최대)

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| Frontend | Vue 3, TypeScript, Vite, Tailwind CSS 4, Pinia |
| Backend | FastAPI, Python |
| AI | OpenAI GPT-4o-mini (감정 분석 + 토픽 분류) |
| 데이터 수집 | YouTube Data API v3 |
| PDF 출력 | jsPDF, html2canvas |

---

## 시작하기

### 사전 준비
- Node.js `>=20`
- Python `3.10+`
- OpenAI API 키
- YouTube Data API v3 키

### 1. 저장소 클론
```bash
git clone https://github.com/maiajunok/T1A.git
cd T1A
```

### 2. 환경 변수 설정
`backend/.env` 파일 생성:
```
OPENAI_API_KEY=your_openai_api_key
YOUTUBE_API_KEY=your_youtube_api_key
```

### 3. 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. 프론트엔드 실행
```bash
cd frontend
npm install
npm run dev
```

### 5. 서비스 접속
| 서비스 | URL |
|--------|-----|
| 프론트엔드 | http://localhost:5173 |
| 백엔드 API | http://localhost:8000 |
| API 문서 (Swagger) | http://localhost:8000/docs |

---

## 출시 예정
- Reddit 댓글 분석
- TikTok 댓글 분석
- 음성 검색
