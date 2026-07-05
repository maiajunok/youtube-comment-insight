"""댓글 전체를 하나의 숫자/시계열로 요약하는 집계 통계 — 토픽 분류나 임베딩처럼 GPT/OpenAI를
호출하지 않고 pandas만으로 계산되는 부분이라 sentiment.py/topic.py와 분리해뒀다."""

import math

import pandas as pd

# 등빈도 구간화 기준 버킷 크기 + z-score 이상치 임계값
_TIMELINE_BUCKET_SIZE = 40
_TIMELINE_Z_THRESHOLD = 1.5
_TIMELINE_MIN_COMMENTS = 20  # 이보다 적으면 구간화 없이 통짜 1개 구간으로 반환


def language_ratio(comments: list[dict]) -> dict:
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


def weighted_sentiment(comments: list[dict]) -> int:
    """좋아요 수를 그대로 가중치로 쓰면(예: 10,000 vs 100) 바이럴 댓글 한두 개가 전체
    점수를 사실상 혼자 결정해버린다 — 좋아요는 실제 공감보다 노출 순서/업로드 타이밍에도
    크게 좌우되는 값이라, 원 댓글 수만큼의 영향력을 주는 건 과도하다. log1p로 눌러서
    "좋아요 많을수록 더 신뢰"는 유지하되 격차 자체는 완만하게 만듦
    (예: 10,000:100의 원 비율 100:1 -> log1p 후 약 2:1)."""
    weighted_sum = 0.0
    weight_total = 0.0
    for c in comments:
        s = c.get("sentiment", "NEUTRAL")
        score = 1 if s == "POSITIVE" else (-1 if s == "NEGATIVE" else 0)
        likes = c.get("likeCount", 0) or 0
        w = math.log1p(likes) + 1
        weighted_sum += score * w
        weight_total += w
    if not weight_total:
        return 0
    return round(weighted_sum / weight_total * 100)


def reaction_timeline(comments: list[dict], video_published_at: str) -> list[dict]:
    try:
        from datetime import datetime, timezone
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
