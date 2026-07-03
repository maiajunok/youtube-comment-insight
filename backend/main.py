import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

from sentiment import analyze_sentiment
from topic import classify_topics, _cosine_sim, _embed
from youtube import extract_video_id, fetch_comments

load_dotenv(override=True)

app = FastAPI(title="Comment Insight API")

_extra_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", *_extra_origins],
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
COMMENTS_DIR = CACHE_DIR / "comments"
COMMENTS_DIR.mkdir(exist_ok=True)


class InsightRequest(BaseModel):
    url: str


def _language_ratio(comments: list[dict]) -> dict:
    try:
        from langdetect import detect
    except ImportError:
        return {"ko": 60, "en": 30, "other": 10}

    counts = {"ko": 0, "en": 0, "other": 0}
    for c in comments:
        try:
            lang = detect(c["text"])
            if lang == "ko":
                counts["ko"] += 1
            elif lang == "en":
                counts["en"] += 1
            else:
                counts["other"] += 1
        except Exception:
            counts["other"] += 1

    total = max(sum(counts.values()), 1)
    return {
        "ko": round(counts["ko"] / total * 100),
        "en": round(counts["en"] / total * 100),
        "other": round(counts["other"] / total * 100),
    }


# 등빈도 구간화 기준 버킷 크기 + z-score 이상치 임계값
_TIMELINE_BUCKET_SIZE = 40
_TIMELINE_Z_THRESHOLD = 1.5
_TIMELINE_MIN_COMMENTS = 20  # 이보다 적으면 구간화 없이 통짜 1개 구간으로 반환


def _reaction_timeline(comments: list[dict], video_published_at: str) -> list[dict]:
    try:
        video_dt = datetime.fromisoformat(video_published_at.replace("Z", "+00:00"))
        if video_dt.tzinfo is None:
            video_dt = video_dt.replace(tzinfo=timezone.utc)
    except Exception:
        video_dt = None

    df = pd.DataFrame([c for c in comments if c.get("publishedAt")])
    if df.empty:
        return []

    df["publishedAt"] = pd.to_datetime(df["publishedAt"], utc=True, errors="coerce")
    df = df.dropna(subset=["publishedAt"]).sort_values("publishedAt").reset_index(drop=True)
    if df.empty:
        return []

    df["sentiment"] = df.get("sentiment", "NEUTRAL").fillna("NEUTRAL")
    df["score"] = df["sentiment"].map({"POSITIVE": 1, "NEUTRAL": 0, "NEGATIVE": -1}).fillna(0)

    size = _TIMELINE_BUCKET_SIZE if len(df) >= _TIMELINE_MIN_COMMENTS else max(len(df), 1)
    df["bucket_id"] = df.index // size

    grouped = df.groupby("bucket_id").agg(
        total=("score", "size"),
        net_sentiment=("score", "mean"),
        positive=("sentiment", lambda s: int((s == "POSITIVE").sum())),
        neutral=("sentiment", lambda s: int((s == "NEUTRAL").sum())),
        negative=("sentiment", lambda s: int((s == "NEGATIVE").sum())),
        bucket_start=("publishedAt", "min"),
        bucket_end=("publishedAt", "max"),
    )
    grouped = grouped[grouped["total"] >= max(size * 0.5, 1)]
    if grouped.empty:
        return []

    mean, std = grouped["net_sentiment"].mean(), grouped["net_sentiment"].std()
    if std and not pd.isna(std):
        grouped["z_score"] = (grouped["net_sentiment"] - mean) / std
    else:
        grouped["z_score"] = 0.0
    grouped["is_burst"] = grouped["z_score"].abs() >= _TIMELINE_Z_THRESHOLD

    timeline = []
    for bucket_id, row in grouped.iterrows():
        elapsed_seconds = (
            (row["bucket_start"] - pd.Timestamp(video_dt)).total_seconds()
            if video_dt is not None else None
        )

        point = {
            # 프론트에서 lang별로 포맷팅 (예: "3시간 후" / "3 hours later" / "3小时后")
            "elapsedSeconds": elapsed_seconds,
            "bucketStart": row["bucket_start"].isoformat(),
            "bucketEnd": row["bucket_end"].isoformat(),
            "positive": row["positive"],
            "neutral": row["neutral"],
            "negative": row["negative"],
            "netSentiment": round(float(row["net_sentiment"]), 3),
            "zScore": round(float(row["z_score"]), 3),
            "isBurst": bool(row["is_burst"]),
            "direction": ("POSITIVE_SPIKE" if row["z_score"] > 0 else "NEGATIVE_SPIKE") if row["is_burst"] else None,
        }

        if row["is_burst"]:
            # 버킷 전체(등빈도라 ~40개 수준)를 다 보냄 — 드로어에서 감정별 필터링하려면 전체가 있어야 함
            window = df[
                (df["bucket_id"] == bucket_id)
            ].sort_values("likeCount", ascending=False)
            point["topComments"] = [
                {"text": c["text"], "likeCount": int(c.get("likeCount", 0)), "sentiment": c["sentiment"]}
                for _, c in window.iterrows()
            ]

        timeline.append(point)

    return timeline


def _weighted_sentiment(comments: list[dict]) -> int:
    weighted_sum = 0
    weight_total = 0
    for c in comments:
        s = c.get("sentiment", "NEUTRAL")
        score = 1 if s == "POSITIVE" else (-1 if s == "NEGATIVE" else 0)
        likes = c.get("likeCount", 0) or 0
        w = likes + 1
        weighted_sum += score * w
        weight_total += w
    if not weight_total:
        return 0
    return round(weighted_sum / weight_total * 100)


def _topic_translations(t: dict) -> dict:
    return {
        **({"topicEn": t["labelEn"]} if t.get("labelEn") else {}),
        **({"topicZh": t["labelZh"]} if t.get("labelZh") else {}),
        **({"topicJa": t["labelJa"]} if t.get("labelJa") else {}),
    }


def _detect_lang(text: str) -> str | None:
    try:
        from langdetect import detect
        code = detect(text)
        if code.startswith("zh"):
            return "zh"
        if code in ("ko", "en", "ja"):
            return code
        return None
    except Exception:
        return None


def _key_insights(topics: list[dict]) -> list[dict]:
    positives = sorted(
        ({"type": "positive", "topic": t["label"], **_topic_translations(t),
          "comment": t["topPositiveComment"]["text"], "commentLang": _detect_lang(t["topPositiveComment"]["text"]),
          "likes": t["topPositiveComment"]["likes"]}
         for t in topics if t.get("topPositiveComment")),
        key=lambda x: x["likes"], reverse=True,
    )
    negatives = sorted(
        ({"type": "negative", "topic": t["label"], **_topic_translations(t),
          "comment": t["topNegativeComment"]["text"], "commentLang": _detect_lang(t["topNegativeComment"]["text"]),
          "likes": t["topNegativeComment"]["likes"]}
         for t in topics if t.get("topNegativeComment")),
        key=lambda x: x["likes"], reverse=True,
    )

    result = []
    for pos, neg in zip(positives[:2], negatives[:2]):
        result.append(pos)
        result.append(neg)
    return result[:4]


def _build_response(video_id: str, video: dict, comments: list[dict], topics: list[dict]) -> dict:
    clean_topics = [
        {
            "label": t["label"],
            **({"labelEn": t["labelEn"]} if t.get("labelEn") else {}),
            **({"labelZh": t["labelZh"]} if t.get("labelZh") else {}),
            **({"labelJa": t["labelJa"]} if t.get("labelJa") else {}),
            "mentionCount": t["mentionCount"],
            "sentiment": t["sentiment"],
        }
        for t in topics
    ]
    return {
        "video": {
            "videoId": video_id,
            "title": video["title"],
            "channelTitle": video["channelTitle"],
            "thumbnailUrl": video["thumbnailUrl"],
            "publishedAt": video["publishedAt"][:10],
            "viewCount": video["viewCount"],
            "likeCount": video["likeCount"],
            "analyzedComments": len(comments),
            "languageRatio": _language_ratio(comments),
            "weightedSentiment": _weighted_sentiment(comments),
        },
        "topics": clean_topics,
        "reactionTimeline": _reaction_timeline(comments, video["publishedAt"]),
        "keyInsights": _key_insights(topics),
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
    }


def _save_comments_by_topic(video_id: str, comments: list[dict], id_to_topic: dict[str, str], fallback: str):
    groups: dict[str, list] = {}
    for c in comments:
        topic = id_to_topic.get(c["id"], fallback)
        entry = {
            "id": c["id"],
            "authorName": c.get("authorName", ""),
            "text": c.get("text", ""),
            "likeCount": c.get("likeCount", 0),
            "publishedAt": c.get("publishedAt", ""),
            "sentiment": c.get("sentiment", "NEUTRAL"),
        }
        groups.setdefault(topic, []).append(entry)

    for topic in groups:
        groups[topic].sort(key=lambda x: x["likeCount"], reverse=True)

    (COMMENTS_DIR / f"{video_id}.json").write_text(
        json.dumps(groups, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _error_payload(prefix: str, e: Exception) -> dict:
    msg = str(e)
    if msg in ("MISSING_YOUTUBE_KEY", "MISSING_OPENAI_KEY"):
        return {"step": "error", "code": msg}
    return {"step": "error", "detail": f"{prefix}: {msg}"}


@app.post("/api/insight")
async def analyze(
    req: InsightRequest,
    x_openai_key: str | None = Header(default=None),
    x_youtube_key: str | None = Header(default=None),
):
    async def generate():
        try:
            video_id = extract_video_id(req.url)
        except ValueError as e:
            yield _sse({"step": "error", "detail": str(e)})
            return

        cache_file = CACHE_DIR / f"{video_id}.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            data.setdefault("video", {})["videoId"] = video_id
            data["cached"] = True
            yield _sse({"step": "done", "data": data})
            return

        analysis_start = time.time()

        # 댓글 수집
        yield _sse({"step": "댓글 수집 중", "progress": 1})
        try:
            fetched = await asyncio.to_thread(fetch_comments, req.url, x_youtube_key)
        except Exception as e:
            yield _sse(_error_payload("댓글 수집 실패", e))
            return
        print(f"[insight] 댓글 {len(fetched['comments'])}개 수집됨, "
              f"quotaExhausted={fetched.get('quotaExhausted')}", flush=True)

        # 감정 분석
        yield _sse({"step": "감정 분석 중", "progress": 2})
        try:
            comments, sentiment_tokens = await asyncio.to_thread(analyze_sentiment, fetched["comments"], x_openai_key)
        except Exception as e:
            yield _sse(_error_payload("감정 분석 실패", e))
            return

        # 토픽 분류
        yield _sse({"step": "토픽 분류 중", "progress": 3})
        try:
            topics, id_to_topic, topic_tokens = await asyncio.to_thread(classify_topics, comments, x_openai_key)
        except Exception as e:
            yield _sse(_error_payload("토픽 분류 실패", e))
            return

        topic_names = [t["label"] for t in topics]
        fallback = topic_names[0] if topic_names else "일반"
        await asyncio.to_thread(_save_comments_by_topic, video_id, comments, id_to_topic, fallback)

        # GPT-4o-mini: input $0.15/1M, output $0.60/1M
        # text-embedding-3-small: $0.02/1M
        input_tokens  = sentiment_tokens["input"]  + topic_tokens["input"]
        output_tokens = sentiment_tokens["output"] + topic_tokens["output"]
        embed_tokens  = topic_tokens["embedding"]
        cost = round(
            input_tokens  * 0.15  / 1_000_000 +
            output_tokens * 0.60  / 1_000_000 +
            embed_tokens  * 0.02  / 1_000_000,
            6
        )

        response = _build_response(video_id, fetched["video"], comments, topics)
        response["analysisDuration"] = round(time.time() - analysis_start, 1)
        response["tokenUsage"] = {
            "input": input_tokens,
            "output": output_tokens,
            "embedding": embed_tokens,
            "total": input_tokens + output_tokens + embed_tokens,
            "estimatedCostUsd": cost,
        }
        cache_file.write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
        response["cached"] = False
        yield _sse({"step": "done", "data": response})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/refresh/{video_id}")
async def refresh(video_id: str):
    cache_file = CACHE_DIR / f"{video_id}.json"
    comments_file = COMMENTS_DIR / f"{video_id}.json"
    if cache_file.exists():
        cache_file.unlink()
    if comments_file.exists():
        comments_file.unlink()
    return {"message": f"{video_id} 캐시 삭제 완료"}


@app.get("/api/history")
def get_history():
    items = []
    for path in sorted(CACHE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            v = data["video"]
            topics = data.get("topics", [])
            total_mentions = sum(t["mentionCount"] for t in topics) or 1
            overall_pos = round(sum(t["sentiment"]["positive"] * t["mentionCount"] for t in topics) / total_mentions)
            overall_neg = round(sum(t["sentiment"]["negative"] * t["mentionCount"] for t in topics) / total_mentions)
            items.append({
                "videoId": path.stem,
                "title": v["title"],
                "channelTitle": v["channelTitle"],
                "thumbnailUrl": v["thumbnailUrl"],
                "publishedAt": v["publishedAt"],
                "analyzedComments": v["analyzedComments"],
                "analyzedAt": data.get("analyzedAt", ""),
                "topTopics": [
                    {
                        "label": t["label"],
                        **({"labelEn": t["labelEn"]} if t.get("labelEn") else {}),
                        **({"labelZh": t["labelZh"]} if t.get("labelZh") else {}),
                        **({"labelJa": t["labelJa"]} if t.get("labelJa") else {}),
                    }
                    for t in topics[:3]
                ],
                "overallSentiment": {"positive": overall_pos, "negative": overall_neg},
            })
        except Exception:
            pass
    return items


@app.get("/api/history/{video_id}")
def get_cached(video_id: str):
    cache_file = CACHE_DIR / f"{video_id}.json"
    if not cache_file.exists():
        raise HTTPException(status_code=404, detail="캐시 없음")
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    data.setdefault("video", {})["videoId"] = video_id
    data["cached"] = True
    return data


@app.get("/api/stats")
def get_stats():
    records = []
    for path in sorted(CACHE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            v = data.get("video", {})
            tu = data.get("tokenUsage") or {}
            records.append({
                "videoId":          path.stem,
                "title":            v.get("title", ""),
                "analyzedComments": v.get("analyzedComments", 0),
                "analyzedAt":       data.get("analyzedAt", ""),
                "duration":         data.get("analysisDuration"),
                "totalTokens":      tu.get("total"),
                "estimatedCostUsd": tu.get("estimatedCostUsd"),
            })
        except Exception:
            pass

    durations = [r["duration"] for r in records if r["duration"] is not None]
    total_comments = sum(r["analyzedComments"] for r in records)
    total_tokens = sum(r["totalTokens"] for r in records if r["totalTokens"] is not None)
    total_cost   = sum(r["estimatedCostUsd"] for r in records if r["estimatedCostUsd"] is not None)

    return {
        "totalAnalyses":    len(records),
        "totalComments":    total_comments,
        "totalTokens":      total_tokens,
        "totalCostUsd":     round(total_cost, 4),
        "avgDuration":      round(sum(durations) / len(durations), 1) if durations else None,
        "minDuration":      min(durations) if durations else None,
        "maxDuration":      max(durations) if durations else None,
        "records":          records,
    }


class TranslateRequest(BaseModel):
    labels: List[str]
    target_lang: str = "en"


_TARGET_LANG_NAMES = {
    "en": "concise English (2-4 words each)",
    "zh": "concise Simplified Chinese (2-4 characters/words each)",
    "ja": "concise Japanese (2-4 words each)",
}


@app.post("/api/translate-labels")
async def translate_labels(req: TranslateRequest, x_openai_key: str | None = Header(default=None)):
    if not req.labels:
        return {"translations": []}
    api_key = x_openai_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"translations": req.labels}
    client = OpenAI(api_key=api_key)
    target_desc = _TARGET_LANG_NAMES.get(req.target_lang, _TARGET_LANG_NAMES["en"])
    prompt = (
        f"Translate these Korean topic labels to {target_desc}. "
        "Return ONLY a JSON array of strings in the same order. No explanation.\n"
        f"Input: {json.dumps(req.labels, ensure_ascii=False)}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
            raw = raw.rsplit("```", 1)[0].strip()
        return {"translations": json.loads(raw)}
    except Exception:
        return {"translations": req.labels}


_TARGET_LANG_NAMES_FULL = {
    "en": "English",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
    "ko": "Korean",
}


class TranslateCommentsRequest(BaseModel):
    texts: List[str]
    target_lang: str = "en"


@app.post("/api/translate-comments")
async def translate_comments(req: TranslateCommentsRequest, x_openai_key: str | None = Header(default=None)):
    if not req.texts:
        return {"translations": []}
    api_key = x_openai_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"translations": req.texts}
    client = OpenAI(api_key=api_key)
    target_desc = _TARGET_LANG_NAMES_FULL.get(req.target_lang, "English")
    prompt = (
        f"Translate these YouTube comments to natural, casual {target_desc}, preserving tone, meaning, and any emojis. "
        "Return ONLY a JSON array of strings in the same order. No explanation.\n"
        f"Input: {json.dumps(req.texts, ensure_ascii=False)}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
            raw = raw.rsplit("```", 1)[0].strip()
        return {"translations": json.loads(raw)}
    except Exception:
        return {"translations": req.texts}


class CommonTopicsRequest(BaseModel):
    groups: List[List[str]]  # 영상별 토픽 라벨(한국어) 목록
    threshold: float = 0.75


def _label_match(a: str, b: str) -> bool:
    """완전 일치 또는 포함 관계("T1의 팀워크" ⊃ "팀워크")면 API 없이 바로 매칭."""
    a_norm, b_norm = a.strip(), b.strip()
    if a_norm == b_norm:
        return True
    if len(a_norm) >= 2 and len(b_norm) >= 2 and (a_norm in b_norm or b_norm in a_norm):
        return True
    return False


@app.post("/api/common-topics")
async def common_topics(req: CommonTopicsRequest, x_openai_key: str | None = Header(default=None)):
    groups = [g for g in req.groups if g]
    if len(groups) < 2:
        return {"commonLabels": []}

    # 임베딩은 문자열 매칭으로 못 잡은 경우에만 필요하므로, 키가 있을 때만 미리 계산
    api_key = x_openai_key or os.getenv("OPENAI_API_KEY")
    group_embeddings: list[list[list[float]]] | None = None
    if api_key:
        try:
            client = OpenAI(api_key=api_key)
            all_labels = [label for g in groups for label in g]
            embeddings, _tokens = _embed(client, all_labels)
            group_embeddings = []
            idx = 0
            for g in groups:
                group_embeddings.append(embeddings[idx : idx + len(g)])
                idx += len(g)
        except Exception:
            group_embeddings = None

    common = []
    for i, label in enumerate(groups[0]):
        matched_all = True
        for gi, other_labels in enumerate(groups[1:], start=1):
            # 1) 문자열 일치/포함 여부부터 확인 (API 호출 없이 즉시 판단)
            if any(_label_match(label, other) for other in other_labels):
                continue
            # 2) 못 잡았고 임베딩을 쓸 수 있으면 의미 유사도로 재확인
            if group_embeddings:
                sims = [_cosine_sim(group_embeddings[0][i], oe) for oe in group_embeddings[gi]]
                if sims and max(sims) >= req.threshold:
                    continue
            matched_all = False
            break
        if matched_all:
            common.append(label)

    return {"commonLabels": common}


@app.get("/api/comments/{video_id}")
def get_topic_comments(video_id: str, topic: str = "", sentiment: str = "all"):
    comments_file = COMMENTS_DIR / f"{video_id}.json"
    if not comments_file.exists():
        raise HTTPException(status_code=404, detail="댓글 데이터가 없습니다. 영상을 다시 분석해주세요.")
    all_groups: dict[str, list] = json.loads(comments_file.read_text(encoding="utf-8"))

    raw = all_groups.get(topic, [])
    counts = {
        "POSITIVE": sum(1 for c in raw if c["sentiment"] == "POSITIVE"),
        "NEUTRAL": sum(1 for c in raw if c["sentiment"] == "NEUTRAL"),
        "NEGATIVE": sum(1 for c in raw if c["sentiment"] == "NEGATIVE"),
    }

    if sentiment != "all":
        raw = [c for c in raw if c["sentiment"] == sentiment.upper()]

    return {"topic": topic, "comments": raw, "total": len(raw), "counts": counts}
