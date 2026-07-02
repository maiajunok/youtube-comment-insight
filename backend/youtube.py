import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv(override=True)


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)

    if parsed.netloc in ("youtu.be", "www.youtu.be"):
        vid = parsed.path.lstrip("/").split("?")[0]
        if vid:
            return vid

    if "youtube.com" in parsed.netloc:
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]

        m = re.match(r"^/shorts/([^/?]+)", parsed.path)
        if m:
            return m.group(1)

    raise ValueError(f"YouTube URL에서 video_id를 추출할 수 없습니다: {url}")


def _best_thumbnail(thumbnails: dict) -> str:
    for key in ("maxres", "standard", "high", "medium", "default"):
        if key in thumbnails:
            return thumbnails[key]["url"]
    return ""


def fetch_comments(video_url: str, api_key: str | None = None) -> dict:
    """
    YouTube URL을 받아 영상 정보 + 전체 댓글을 반환한다 (제한 없음).
    """
    api_key = api_key or os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise EnvironmentError("MISSING_YOUTUBE_KEY")

    video_id = extract_video_id(video_url)
    youtube = build("youtube", "v3", developerKey=api_key)

    video_resp = youtube.videos().list(
        part="snippet,statistics",
        id=video_id,
    ).execute()

    if not video_resp.get("items"):
        raise ValueError(f"영상을 찾을 수 없습니다 (video_id={video_id})")

    item = video_resp["items"][0]
    snippet = item["snippet"]
    stats = item.get("statistics", {})

    video_info = {
        "videoId": video_id,
        "title": snippet["title"],
        "channelTitle": snippet["channelTitle"],
        "thumbnailUrl": _best_thumbnail(snippet.get("thumbnails", {})),
        "publishedAt": snippet["publishedAt"],
        "viewCount": int(stats.get("viewCount", 0)),
        "likeCount": int(stats.get("likeCount", 0)),
        "commentCount": int(stats.get("commentCount", 0)),
    }

    comments = []
    page_token = None

    while True:
        request_kwargs: dict = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "order": "relevance",
        }
        if page_token:
            request_kwargs["pageToken"] = page_token

        try:
            resp = youtube.commentThreads().list(**request_kwargs).execute()
        except HttpError as e:
            if e.resp.status == 403:
                print(f"[youtube] 댓글 수집 중단: {e.error_details}")
                break
            raise RuntimeError(
                f"YouTube API 오류 (status={e.resp.status}): {e.error_details}"
            ) from e

        for thread in resp.get("items", []):
            top = thread["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "id": thread["id"],
                "text": top["textDisplay"],
                "likeCount": int(top.get("likeCount", 0)),
                "publishedAt": top["publishedAt"],
                "authorName": top["authorDisplayName"],
            })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

        print(f"[youtube] {len(comments)}개 수집 중...")

    return {
        "video": video_info,
        "comments": comments,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
    }
