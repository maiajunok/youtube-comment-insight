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


def analyze_sentiment(comments: list[dict], api_key: str | None = None) -> tuple[list[dict], dict]:
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("MISSING_OPENAI_KEY")

    client = OpenAI(api_key=api_key)
    results = list(comments)
    tokens = {"input": 0, "output": 0}

    batch_size = 50
    for batch_start in range(0, len(results), batch_size):
        batch = results[batch_start : batch_start + batch_size]
        payload = [{"idx": i, "text": c["text"]} for i, c in enumerate(batch)]

        prompt = _PROMPT_TEMPLATE.format(comments_json=json.dumps(payload, ensure_ascii=False))

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
            sentiment_map = {item["idx"]: item["sentiment"] for item in parsed["results"]}
        except Exception as e:
            print(f"[sentiment] 배치 {batch_start}~{batch_start + len(batch) - 1} 파싱 실패, NEUTRAL 처리: {e}")
            sentiment_map = {i: "NEUTRAL" for i in range(len(batch))}

        for i, comment in enumerate(batch):
            comment["sentiment"] = sentiment_map.get(i, "NEUTRAL")

    return results, tokens
