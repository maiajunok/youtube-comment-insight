import concurrent.futures
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

_PROMPT_TEMPLATE = """\
다음 유튜브 댓글들의 감정을 분석해줘.
각각 POSITIVE / NEUTRAL / NEGATIVE 중 하나로만 분류해.

판단 기준:
- 팬덤 표현("ㅋㅋㅋ 개웃김", "못참지", "미쳤다")은 맥락으로 판단
- 반어법 주의 ("가격 미쳤다" = 부정일 수도 있음)
- 이모지만 있으면 NEUTRAL
- 질문형은 NEUTRAL

댓글 목록:
{comments_json}

반드시 아래 JSON만 반환해. 다른 텍스트 없이:
{{"results": [{{"idx": 0, "sentiment": "POSITIVE"}}, ...]}}\
"""

_BATCH_SIZE = 50
# 배치를 동시에 여러 개 돌려서 벽시계 시간을 줄임(비용·토큰 총량은 그대로, 순서만 바뀜) —
# 댓글 수천 개인 영상을 순차로 처리하면 SSE 연결이 몇 분간 아무 진행 신호 없이 멈춰 있다가
# 무료/저사양 호스팅의 idle timeout에 끊길 위험이 있어서, 이 대기 시간 자체를 줄이는 쪽으로 접근함
_MAX_WORKERS = 6


def _call_sentiment_batch(client: OpenAI, batch: list[dict], batch_start: int) -> tuple[dict[int, str], dict]:
    payload = [{"idx": i, "text": c["text"]} for i, c in enumerate(batch)]
    prompt = _PROMPT_TEMPLATE.format(comments_json=json.dumps(payload, ensure_ascii=False))

    # 파싱 실패(드물게 GPT가 JSON을 깨뜨림)는 한 번만 재시도 — 그래도 실패하면 그 배치만
    # NEUTRAL로 폴백(전체 분석 실패시키는 대신 일부만 저하되고 계속 진행됨)
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
            )
            tokens = {"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens}
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            parsed = json.loads(raw)
            return {item["idx"]: item["sentiment"] for item in parsed["results"]}, tokens
        except Exception as e:
            print(f"[sentiment] 배치 {batch_start}~{batch_start + len(batch) - 1} "
                  f"파싱 실패(시도 {attempt + 1}/2): {e}")

    return {i: "NEUTRAL" for i in range(len(batch))}, {"input": 0, "output": 0}


def analyze_sentiment(comments: list[dict], api_key: str | None = None) -> tuple[list[dict], dict]:
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("MISSING_OPENAI_KEY")

    client = OpenAI(api_key=api_key)
    results = list(comments)
    tokens = {"input": 0, "output": 0}

    batches = [
        (batch_start, results[batch_start : batch_start + _BATCH_SIZE])
        for batch_start in range(0, len(results), _BATCH_SIZE)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        futures = {
            executor.submit(_call_sentiment_batch, client, batch, batch_start): batch
            for batch_start, batch in batches
        }
        for future in concurrent.futures.as_completed(futures):
            batch = futures[future]
            sentiment_map, batch_tokens = future.result()
            tokens["input"] += batch_tokens["input"]
            tokens["output"] += batch_tokens["output"]
            for i, comment in enumerate(batch):
                comment["sentiment"] = sentiment_map.get(i, "NEUTRAL")

    return results, tokens
