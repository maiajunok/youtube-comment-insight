"""댓글 전체를 하나의 숫자/시계열로 요약하는 집계 통계 — 토픽 분류나 임베딩처럼 GPT/OpenAI를
호출하지 않고 pandas만으로 계산되는 부분이라 sentiment.py/topic.py와 분리해뒀다."""

import math

import numpy as np
import pandas as pd

# 등빈도 구간화 기준 버킷 크기 + z-score 이상치 임계값
_TIMELINE_BUCKET_SIZE = 40
_TIMELINE_Z_THRESHOLD = 1.5
_TIMELINE_MIN_COMMENTS = 20  # 이보다 적으면 구간화 없이 통짜 1개 구간으로 반환
# 댓글량(volume) 급증 이상치 임계값 — 감정 z-score와 같은 값을 쓰되 별도 상수로 분리해
# 나중에 독립적으로 튜닝할 수 있게 함
_VOLUME_Z_THRESHOLD = 1.5


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

    # 댓글량(volume) 급증 — 등빈도 버킷이라 버킷당 댓글 수(total)는 이미 거의 일정하게
    # 고정돼 있어서, "개수 자체가 늘었다"로는 절대 못 잡는다. 대신 그 일정한 개수가 "얼마나
    # 짧은 시간 동안 몰렸는지"(초당 댓글 속도)를 봐야 함 — 버킷이 커버하는 시간 구간이
    # 비정상적으로 짧을수록 화제성이 순간적으로 폭발했다는 뜻. 속도는 오른쪽 꼬리가 긴
    # 분포라(weighted_sentiment의 log1p와 같은 이유로) log를 취한 뒤 z-score 계산.
    # 뜸한 구간(속도가 느림)은 그냥 조용한 것이지 "버스트"가 아니므로 한쪽(단측)만 이상치로 봄
    duration_seconds = (grouped["bucket_end"] - grouped["bucket_start"]).dt.total_seconds().clip(lower=1.0)
    comment_rate = grouped["total"] / duration_seconds
    log_rate = np.log(comment_rate)
    rate_mean, rate_std = log_rate.mean(), log_rate.std()
    if rate_std and not pd.isna(rate_std):
        grouped["volume_z_score"] = (log_rate - rate_mean) / rate_std
    else:
        grouped["volume_z_score"] = 0.0
    grouped["is_volume_burst"] = grouped["volume_z_score"] >= _VOLUME_Z_THRESHOLD
    grouped["duration_seconds"] = duration_seconds

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
            "volumeZScore": round(float(row["volume_z_score"]), 3),
            "isVolumeBurst": bool(row["is_volume_burst"]),
            "durationSeconds": round(float(row["duration_seconds"]), 1),
        }

        if row["is_burst"] or row["is_volume_burst"]:
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
