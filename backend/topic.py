import json
import math
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b + 1e-10)


def _embed(client: OpenAI, texts: list[str]) -> tuple[list[list[float]], int]:
    results = []
    total_tokens = 0
    for i in range(0, len(texts), 2048):
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts[i : i + 2048],
        )
        results.extend(item.embedding for item in resp.data)
        total_tokens += resp.usage.total_tokens
    return results, total_tokens


def classify_topics(comments: list[dict], api_key: str | None = None) -> tuple[list[dict], dict[str, str], dict]:
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("MISSING_OPENAI_KEY")

    client = OpenAI(api_key=api_key)
    tokens = {"input": 0, "output": 0, "embedding": 0}

    # 좋아요 많은 순 상위 300개 → GPT로 토픽 추출
    top_comments = sorted(comments, key=lambda c: c.get("likeCount", 0), reverse=True)[:300]
    payload = [{"idx": i, "text": c["text"]} for i, c in enumerate(top_comments)]

    prompt = f"""다음은 유튜브 영상의 댓글입니다.
팬들이 가장 많이 반응한 주제(Topic) 5개를 찾아줘.

규칙:
- 단순 응원("화이팅", 이모지만)은 토픽으로 뽑지 마
- 각 토픽에 해당하는 댓글 인덱스 리스트 포함
- 토픽명은 한국어(name_ko)와 영어(name_en) 둘 다 반환

댓글: {json.dumps(payload, ensure_ascii=False)}

JSON만 반환:
{{
  "topics": [
    {{"name_ko": "팀워크", "name_en": "Teamwork", "comment_indices": [0, 3, 7]}},
    ...
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        tokens["input"]  += response.usage.prompt_tokens
        tokens["output"] += response.usage.completion_tokens
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        parsed = json.loads(raw)
        topic_defs = parsed["topics"][:5]
    except Exception as e:
        print(f"[topic] OpenAI 토픽 추출 실패: {e}")
        topic_defs = [{"name_ko": "일반", "name_en": "General", "comment_indices": list(range(min(len(top_comments), 50)))}]

    topic_names_ko = [td.get("name_ko") or td.get("name", "일반") for td in topic_defs]
    topic_names_en = [td.get("name_en") or td.get("name_ko") or td.get("name", "General") for td in topic_defs]

    # GPT가 top 300에서 배정한 id → topic 맵 (한국어 이름 기준)
    idx_to_topic: dict[int, str] = {}
    for td in topic_defs:
        name_ko = td.get("name_ko") or td.get("name", "일반")
        for idx in td.get("comment_indices", []):
            if idx < len(top_comments):
                idx_to_topic[idx] = name_ko

    id_to_topic: dict[str, str] = {
        top_comments[i]["id"]: name for i, name in idx_to_topic.items()
    }

    fallback = topic_names_ko[0] if topic_names_ko else "일반"

    # 미배정 댓글 → 임베딩으로 가장 가까운 토픽에 배정
    unassigned = [c for c in comments if c["id"] not in id_to_topic]

    if unassigned and topic_names_ko:
        # 빈 텍스트는 임베딩 API가 거부하므로 fallback으로 처리
        to_embed = [c for c in unassigned if c.get("text", "").strip()]
        empty_text = [c for c in unassigned if not c.get("text", "").strip()]
        for c in empty_text:
            id_to_topic[c["id"]] = fallback

        if to_embed:
            print(f"[topic] 임베딩으로 {len(to_embed)}개 댓글 배정 중...")
            topic_embeddings, t1 = _embed(client, topic_names_ko)
            comment_embeddings, t2 = _embed(client, [c["text"] for c in to_embed])
            tokens["embedding"] += t1 + t2

            for i, comment in enumerate(to_embed):
                sims = [_cosine_sim(comment_embeddings[i], te) for te in topic_embeddings]
                id_to_topic[comment["id"]] = topic_names_ko[sims.index(max(sims))]

    # 버킷 분배
    buckets: dict[str, list] = {name: [] for name in topic_names_ko}

    for comment in comments:
        topic = id_to_topic.get(comment["id"], fallback)
        if topic not in buckets:
            topic = fallback
        buckets[topic].append(comment)

    # ko→en 매핑
    ko_to_en = dict(zip(topic_names_ko, topic_names_en))

    # 집계
    result = []
    for name in topic_names_ko:
        tc = buckets[name]
        pos = sum(1 for c in tc if c.get("sentiment") == "POSITIVE")
        neu = sum(1 for c in tc if c.get("sentiment") == "NEUTRAL")
        neg = sum(1 for c in tc if c.get("sentiment") == "NEGATIVE")
        total = max(pos + neu + neg, 1)

        top_pos = max(
            (c for c in tc if c.get("sentiment") == "POSITIVE"),
            key=lambda c: c.get("likeCount", 0),
            default=None,
        )
        top_neg = max(
            (c for c in tc if c.get("sentiment") == "NEGATIVE"),
            key=lambda c: c.get("likeCount", 0),
            default=None,
        )

        result.append({
            "label": name,
            "labelEn": ko_to_en.get(name, name),
            "mentionCount": len(tc),
            "sentiment": {
                "positive": round(pos / total * 100),
                "neutral": round(neu / total * 100),
                "negative": round(neg / total * 100),
            },
            "topPositiveComment": {"text": top_pos["text"], "likes": top_pos["likeCount"]} if top_pos else None,
            "topNegativeComment": {"text": top_neg["text"], "likes": top_neg["likeCount"]} if top_neg else None,
        })

    result.sort(key=lambda t: t["mentionCount"], reverse=True)
    return result[:5], id_to_topic, tokens
