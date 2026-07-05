"""
Loads cached comment/video data from backend/cache/ into DataFrames.
The only file that knows about on-disk paths and the cache's JSON shape —
algorithms.py never touches a file path.
"""
import glob
import json
import os

import pandas as pd

from algorithms import SENTIMENT_SCORE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "backend", "cache")
COMMENTS_DIR = os.path.join(CACHE_DIR, "comments")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_video_comments(video_id: str) -> pd.DataFrame:
    """All comments for one video, topic-labeled, with a numeric sentiment score column."""
    path = os.path.join(COMMENTS_DIR, f"{video_id}.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for topic, comments in data.items():
        for c in comments:
            rows.append({
                "text": c.get("text", ""),
                "likeCount": c.get("likeCount", 0),
                "publishedAt": c.get("publishedAt"),
                "sentiment": c.get("sentiment", "NEUTRAL"),
                "topic": topic,
            })
    df = pd.DataFrame(rows)
    df["publishedAt"] = pd.to_datetime(df["publishedAt"])
    df["score"] = df["sentiment"].map(SENTIMENT_SCORE)
    return df


def load_all_comments() -> pd.DataFrame:
    """Every comment across every cached video, tagged with its video id."""
    rows = []
    for path in glob.glob(os.path.join(COMMENTS_DIR, "*.json")):
        video_id = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for topic, comments in data.items():
            for c in comments:
                rows.append({
                    "video": video_id,
                    "topic": topic,
                    "text": c.get("text", ""),
                    "likeCount": c.get("likeCount", 0),
                    "publishedAt": c.get("publishedAt"),
                    "sentiment": c.get("sentiment", "NEUTRAL"),
                })
    df = pd.DataFrame(rows)
    df = df[df["text"].str.strip().str.len() > 0].reset_index(drop=True)
    return df


def all_video_ids() -> list[str]:
    return [os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(COMMENTS_DIR, "*.json"))]


def load_video_upload_time(video_id: str) -> pd.Timestamp:
    path = os.path.join(CACHE_DIR, f"{video_id}.json")
    with open(path, encoding="utf-8") as f:
        video = json.load(f)["video"]
    return pd.to_datetime(video["publishedAt"]).tz_localize("UTC")
