"""그래프 '생성' 알고리즘만 모아두는 모듈 — 어떤 텍스트를 노드로 쓸지 같은 도메인
로직은 여기 두지 않는다. 나중에 top-k KNN 대신 다른 그래프 구성 방식(예: 임계값 기반,
HDBSCAN/Louvain 커뮤니티 탐지)을 시도하고 싶으면 이 파일만 교체하면 되도록 분리했다.

교체 시 지켜야 할 인터페이스: (ids: list[str], vectors: list[list[float]], **params) -> list[dict]
반환값은 항상 [{"source": id, "target": id, "similarity": float}, ...] 형태.
"""

import numpy as np


def cosine_similarity_matrix(vectors: list[list[float]]) -> np.ndarray:
    matrix = np.array(vectors)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    normalized = matrix / (norms + 1e-10)
    return normalized @ normalized.T


def jensen_shannon_similarity_matrix(distributions: list[list[float]]) -> np.ndarray:
    """확률분포(긍정/중립/부정 % 같은 비율 벡터)끼리의 유사도를 1 - Jensen-Shannon
    divergence(log base 2, 그래서 0~1 사이)로 계산. 코사인 유사도는 임의의 벡터
    비교용이라 "둘 다 합이 100인 비율" 같은 데이터엔 덜 적합하고, JS divergence는
    두 확률분포가 정보이론적으로 얼마나 다른지를 재는 표준 척도(대칭, 항상 유한,
    KL divergence와 달리 한쪽이 0이어도 안 터짐)."""
    p = np.array(distributions, dtype=float)
    row_sums = p.sum(axis=1, keepdims=True)
    p = p / np.where(row_sums == 0, 1, row_sums)

    n = len(distributions)
    sim = np.eye(n)

    def _kl(a: np.ndarray, b: np.ndarray) -> float:
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))

    for i in range(n):
        for j in range(i + 1, n):
            m = (p[i] + p[j]) / 2
            jsd = (_kl(p[i], m) + _kl(p[j], m)) / 2
            s = 1 - jsd
            sim[i, j] = sim[j, i] = s
    return sim


def knn_graph_links(
    ids: list[str], sim_matrix: np.ndarray, top_k: int, min_similarity: float,
) -> list[dict]:
    """각 노드마다 유사도 상위 top_k개 후보(min_similarity 이상)를 뽑은 뒤,
    "상호(mutual) k-NN" — 즉 A가 B를 자기 top-k에 넣었을 뿐 아니라 B도 A를 자기
    top-k에 넣었을 때만 간선으로 남긴다. 한쪽만 상대를 이웃으로 꼽은(비대칭) 관계는
    버린다. 스펙트럴 클러스터링·Isomap·LLE 등에서 표준으로 쓰는 방식으로(참고: von
    Luxburg, "A Tutorial on Spectral Clustering", 2007), 일반 k-NN 그래프는 "전체와
    두루 비슷한 허브" 노드가 실제로는 특별히 안 닮은 상대에게까지 간선을 만드는 경향이
    있는데, 상호 조건을 걸면 그런 비대칭 관계가 자동으로 걸러진다.

    argpartition으로 상위 (k+1)개 후보만 골라낸 뒤 그 안에서만 정렬 —
    전체를 정렬하는 것보다 저렴하다(노드 수가 커져도 스케일함)."""
    n = len(ids)

    # 1단계: 각 노드의 one-directional top-k 이웃 집합을 먼저 구함
    neighbor_sets: list[set[int]] = [set() for _ in range(n)]
    pairwise_sim: dict[tuple[int, int], float] = {}

    for i in range(n):
        sims = sim_matrix[i]
        k = min(top_k, n - 1)
        if k <= 0:
            continue
        # 자기 자신(유사도 1.0, 항상 최댓값)을 포함해 상위 (k+1)개 후보만 추출
        candidate_idx = np.argpartition(-sims, k)[: k + 1]
        candidate_idx = candidate_idx[np.argsort(-sims[candidate_idx])]

        picked = 0
        for j in candidate_idx:
            if j == i:
                continue
            sim = float(sims[j])
            if sim < min_similarity:
                break
            if picked >= top_k:
                break
            neighbor_sets[i].add(j)
            pairwise_sim[(i, j)] = sim
            picked += 1

    # 2단계: 양쪽 다 서로를 이웃으로 꼽았을 때만("상호") 간선으로 확정
    links: dict[tuple[str, str], float] = {}
    for i in range(n):
        for j in neighbor_sets[i]:
            if i in neighbor_sets[j]:
                key = (ids[i], ids[j]) if ids[i] < ids[j] else (ids[j], ids[i])
                sim = pairwise_sim.get((i, j), pairwise_sim.get((j, i)))
                links[key] = sim

    return [
        {"source": src, "target": dst, "similarity": round(sim, 3)}
        for (src, dst), sim in links.items()
    ]
