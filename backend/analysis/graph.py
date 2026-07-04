import os

from openai import OpenAI

from analysis.aliases import normalize_aliases
from analysis.embedding import embed
from analysis.projection import umap_project
from analysis.similarity_graph import cosine_similarity_matrix, jensen_shannon_similarity_matrix, knn_graph_links

# 3D 그래프 가독성을 위해 토픽당 상위 좋아요 댓글만 노드로 사용 (5개 토픽 * 30 = 최대 150개)
_MAX_NODES_PER_TOPIC = 30
_COMMENT_TOP_K = 5
_COMMENT_MIN_SIMILARITY = 0.35

_VIDEO_TOP_K = 3
# 분석된 영상이 몇 개 안 될 때(예: 7~8개)는 top_k=4가 사실상 "나 빼고 거의 전부"를 강제로
# 연결하는 셈이라, 텍스트 유사도가 아무리 좋아져도 무관한 영상들이 계속 상위에 낀다.
# min_similarity도 0.35는 애초에 text-embedding-3-small이 임의의 두 한국어 문장 사이에도
# 흔히 깔고 가는 기본 유사도 수준이라 사실상 필터 역할을 못 했음 — 0.5로 올려서
# "진짜 비슷한" 것만 남게 함(그 결과 어떤 영상은 연결이 하나도 안 남을 수 있고, 그게 맞음)
_VIDEO_MIN_SIMILARITY = 0.5
# 영상 유사도 = 텍스트(제목+토픽) 유사도와 반응(감정 분포) 유사도의 가중 결합.
# "비슷한 반응의 영상"이라는 기능 이름과 달리 예전엔 텍스트 유사도만 봤어서,
# 소재는 완전히 다른데 추상적 정서 프레임만 겹쳐도(예: 면접 개그 ↔ 계약 논란) 높게 나왔음.
# 감정 분포 비중을 크게(0.35) 뒀더니 오히려 역효과 — 영상이 몇 개 안 되는 데다 다들
# 반응이 대체로 비슷하게 혼합돼 있어서(긍정 절반, 부정 절반 식), 이 3차원짜리 신호가
# 모든 쌍의 점수를 54~60% 좁은 구간으로 뭉개버려 텍스트가 만든 차이를 지워버렸음.
# 그래서 감정은 "미세한 타이브레이커"로만 남기고 텍스트 비중을 크게 높임
_VIDEO_TEXT_WEIGHT = 0.9


def build_comment_graph(
    comments: list[dict],
    id_to_topic: dict[str, str],
    topics: list[dict],
    api_key: str | None = None,
) -> tuple[dict, int]:
    """댓글을 토픽별 상위 좋아요 순으로 추린 뒤, 텍스트 임베딩의 코사인 유사도로
    의미상 비슷한 댓글끼리 연결한 반응 지도(노드=댓글, 간선=의미 유사도)를 만든다.
    그래프 생성 알고리즘 자체는 analysis/similarity_graph.py에 분리되어 있음."""
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("MISSING_OPENAI_KEY")

    topic_names = [t["label"] for t in topics]
    fallback = topic_names[0] if topic_names else "일반"

    buckets: dict[str, list[dict]] = {}
    for c in comments:
        topic = id_to_topic.get(c["id"], fallback)
        buckets.setdefault(topic, []).append(c)

    node_comments: list[dict] = []
    for topic, bucket in buckets.items():
        top = sorted(bucket, key=lambda c: c.get("likeCount", 0), reverse=True)[:_MAX_NODES_PER_TOPIC]
        for c in top:
            node_comments.append({**c, "topic": topic})

    if not node_comments:
        return {"nodes": [], "links": []}, 0

    client = OpenAI(api_key=api_key)
    vectors, embed_tokens = embed(client, [c.get("text", "") or " " for c in node_comments])
    sim_matrix = cosine_similarity_matrix(vectors)
    ids = [c["id"] for c in node_comments]
    link_list = knn_graph_links(ids, sim_matrix, _COMMENT_TOP_K, _COMMENT_MIN_SIMILARITY)

    # 노드 위치를 물리 시뮬레이션(힘 균형)이 아니라 UMAP으로 실제 임베딩 공간의 이웃 구조를
    # 그대로 좌표에 투영 — 같은 토픽끼리 가까이 보이는 게 "그렇게 보이도록 힘을 줘서"가
    # 아니라 실제로 의미가 가까워서가 됨(analysis/projection.py). 2D는 3D 좌표에서 한 축을
    # 그냥 버리는 게 아니라 독립적으로 다시 투영함 — 차원 수 자체가 UMAP의 최적화 목표라
    # 3D 결과를 2D로 눌러 찍으면 이웃 구조가 왜곡될 수 있음
    coords3d = umap_project(vectors, n_components=3)
    coords2d = umap_project(vectors, n_components=2)

    nodes = [
        {
            "id": c["id"],
            "text": c.get("text", "")[:140],
            "likeCount": c.get("likeCount", 0),
            "sentiment": c.get("sentiment", "NEUTRAL"),
            "topic": c["topic"],
            "x": xyz[0], "y": xyz[1], "z": xyz[2],
            "x2d": xy2[0], "y2d": xy2[1],
        }
        for c, xyz, xy2 in zip(node_comments, coords3d, coords2d)
    ]

    return {"nodes": nodes, "links": link_list}, embed_tokens


def build_video_graph(videos: list[dict], api_key: str | None = None) -> tuple[dict, int]:
    """분석된 영상들을 (1) 제목+상위 토픽 임베딩의 코사인 유사도(텍스트가 무슨 얘기를 하는지)와
    (2) 감정 분포(긍정/중립/부정 %) 벡터의 코사인 유사도(반응이 실제로 어땠는지)를
    가중 결합한 점수로 연결한다. 그래프 생성(top-k 선별) 자체는 댓글 단위 반응 지도와
    동일하게 analysis/similarity_graph.py의 knn_graph_links를 그대로 재사용한다 —
    이 함수가 만드는 건 "무엇으로 유사도를 계산할지"이지, 그래프를 어떻게 뽑을지가 아님.

    videos: [{"videoId", "title", "thumbnailUrl", "commentCount",
              "sentiment": {"positive","neutral","negative"}, "topics": [str, ...],
              "hasGraph": bool}]
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("MISSING_OPENAI_KEY")

    if len(videos) < 2:
        nodes = [
            {
                "id": v["videoId"],
                "title": v["title"],
                "thumbnailUrl": v.get("thumbnailUrl", ""),
                "commentCount": v.get("commentCount", 0),
                "sentiment": v["sentiment"],
                "topics": v.get("topics") or [],
                "hasGraph": v.get("hasGraph", False),
            }
            for v in videos
        ]
        return {"nodes": nodes, "links": []}, 0

    client = OpenAI(api_key=api_key)
    # 토픽 라벨만 임베딩하면 "면접", "T1" 같은 구체적인 소재 단어가 하나도 안 들어가서,
    # 소재는 완전히 다른데 "충성 vs 보상", "실망한 반응" 같은 추상적 정서 프레임만 겹쳐도
    # 유사도가 높게 나오는 문제가 있었음(예: 면접 개그 영상 ↔ T1 계약 논란 영상).
    # 제목을 같이 넣어서 실제 소재(고유명사)가 임베딩에 반영되게 함
    profiles = [
        f"{v['title']} - {', '.join(v.get('topics') or [])}" if v.get("topics") else v["title"]
        for v in videos
    ]
    # 같은 선수/팀이 닉네임·본명·팬 별명 등 다른 표기로 등장해도 임베딩 전에 하나의 토큰으로
    # 통일(analysis/aliases.py) — 안 그러면 "제우스"와 "최우제"가 같은 사람인지 임베딩
    # 모델이 보장해주지 않아서, 같은 선수를 다루는 영상끼리도 안 묶일 수 있음
    profiles = [normalize_aliases(p) for p in profiles]
    vectors, embed_tokens = embed(client, profiles)
    text_sim_matrix = cosine_similarity_matrix(vectors)

    # (긍정, 중립, 부정) %는 합이 100인 확률분포이지 임의의 벡터가 아니라서, 코사인 유사도보다
    # Jensen-Shannon 유사도가 통계적으로 더 맞는 비교 방법 — 두 영상의 "반응 프로필"이
    # 얼마나 닮았는지를 텍스트와 별개로 측정(analysis/similarity_graph.py)
    sentiment_vectors = [
        [v["sentiment"]["positive"], v["sentiment"]["neutral"], v["sentiment"]["negative"]]
        for v in videos
    ]
    sentiment_sim_matrix = jensen_shannon_similarity_matrix(sentiment_vectors)

    combined_sim_matrix = (
        _VIDEO_TEXT_WEIGHT * text_sim_matrix + (1 - _VIDEO_TEXT_WEIGHT) * sentiment_sim_matrix
    )

    ids = [v["videoId"] for v in videos]
    link_list = knn_graph_links(ids, combined_sim_matrix, _VIDEO_TOP_K, _VIDEO_MIN_SIMILARITY)

    # 위치는 텍스트 임베딩만 UMAP으로 투영(감정 벡터는 간선 판단에만 쓰고 위치엔 안 섞음 —
    # 3차원짜리 감정 벡터가 섞이면 위치가 "무슨 얘기를 하는지"보다 "반응이 비슷한지"쪽으로
    # 쏠려서 오히려 위치의 의미가 흐려짐). 2D는 3D를 눌러 찍는 게 아니라 독립적으로 다시 투영
    coords3d = umap_project(vectors, n_components=3)
    coords2d = umap_project(vectors, n_components=2)

    nodes = [
        {
            "id": v["videoId"],
            "title": v["title"],
            "thumbnailUrl": v.get("thumbnailUrl", ""),
            "commentCount": v.get("commentCount", 0),
            "sentiment": v["sentiment"],
            "topics": v.get("topics") or [],
            "hasGraph": v.get("hasGraph", False),
            "x": xyz[0], "y": xyz[1], "z": xyz[2],
            "x2d": xy2[0], "y2d": xy2[1],
        }
        for v, xyz, xy2 in zip(videos, coords3d, coords2d)
    ]

    return {"nodes": nodes, "links": link_list}, embed_tokens
