import math

from openai import OpenAI


def cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b + 1e-10)


def embed(client: OpenAI, texts: list[str]) -> tuple[list[list[float]], int]:
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
