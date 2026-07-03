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
    quota_exhausted = False
    page_token = None

    while True:
        request_kwargs: dict = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": 100,
            "textFormat": "plainText",
            # relevance 정렬은 댓글 많은 영상에서 페이지네이션이 끝까지 안 가고 중간에
            # 끊기는 경우가 있음(YouTube API의 알려진 특성) — time 정렬이 훨씬 안정적으로
            # 전체 수집됨. 좋아요 기준 정렬은 topic.py에서 별도로 재정렬해서 쓰므로 문제없음
            "order": "time",
        }
        if page_token:
            request_kwargs["pageToken"] = page_token

        try:
            resp = youtube.commentThreads().list(**request_kwargs).execute()
        except HttpError as e:
            if e.resp.status == 403:
                print(f"[youtube] 댓글 수집 중단 (쿼터 초과 추정): {e.error_details}", flush=True)
                quota_exhausted = True
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

            # commentThreads.list가 스레드당 답글 최대 5개는 추가 쿼터 없이 같이 줌
            inline_replies = thread.get("replies", {}).get("comments", [])
            for reply in inline_replies:
                r = reply["snippet"]
                comments.append({
                    "id": reply["id"],
                    "text": r["textDisplay"],
                    "likeCount": int(r.get("likeCount", 0)),
                    "publishedAt": r["publishedAt"],
                    "authorName": r["authorDisplayName"],
                    "parentId": thread["id"],
                })

            # 답글이 5개보다 많은 스레드는 comments.list로 나머지를 따로 가져와야 함
            total_replies = thread["snippet"].get("totalReplyCount", 0)
            if total_replies > len(inline_replies) and not quota_exhausted:
                fetched = _fetch_remaining_replies(youtube, thread["id"], skip=len(inline_replies))
                if fetched is None:
                    quota_exhausted = True
                else:
                    comments.extend(fetched)

        page_token = resp.get("nextPageToken")
        if not page_token or quota_exhausted:
            break

        print(f"[youtube] {len(comments)}개 수집 중...", flush=True)

    return {
        "video": video_info,
        "comments": comments,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "quotaExhausted": quota_exhausted,
    }


def _fetch_remaining_replies(youtube, parent_id: str, skip: int) -> list[dict] | None:
    """답글 5개 초과분을 comments.list로 마저 수집. 쿼터 소진 시 None 반환."""
    replies = []
    page_token = None
    seen = 0

    while True:
        request_kwargs: dict = {
            "part": "snippet",
            "parentId": parent_id,
            "maxResults": 100,
            "textFormat": "plainText",
        }
        if page_token:
            request_kwargs["pageToken"] = page_token

        try:
            resp = youtube.comments().list(**request_kwargs).execute()
        except HttpError as e:
            if e.resp.status == 403:
                print(f"[youtube] 답글 수집 중단 (쿼터 초과 추정): {e.error_details}", flush=True)
                return None
            raise RuntimeError(
                f"YouTube API 오류 (status={e.resp.status}): {e.error_details}"
            ) from e

        for item in resp.get("items", []):
            seen += 1
            if seen <= skip:
                continue  # commentThreads.list가 이미 준 inline 답글과 중복 방지
            r = item["snippet"]
            replies.append({
                "id": item["id"],
                "text": r["textDisplay"],
                "likeCount": int(r.get("likeCount", 0)),
                "publishedAt": r["publishedAt"],
                "authorName": r["authorDisplayName"],
                "parentId": parent_id,
            })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return replies
