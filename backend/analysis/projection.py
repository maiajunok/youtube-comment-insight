"""고차원 임베딩을 3D 화면 좌표로 "투영"하는 알고리즘만 모아두는 모듈 —
어떤 텍스트를 임베딩할지, 그래프 간선을 어떻게 뽑을지 같은 도메인 로직은 여기 두지 않는다.

기존엔 force-directed 물리 시뮬레이션(스프링+반발력의 평형 상태)으로 노드 위치를 정했는데,
이건 실제 임베딩 공간에서 얼마나 가까운지와 무관하게 물리 파라미터에 따라 배치가 달라진다.
UMAP은 고차원에서의 이웃 구조(어떤 점들이 실제로 가까운지)를 보존하도록 저차원 좌표를
직접 최적화하는 차원 축소 기법이라, 노드 위치 자체가 "실제로 의미가 가까운 정도"를 반영한다.
BERTopic(임베딩 → UMAP → HDBSCAN) 파이프라인과 동일한 아이디어를 그래프 시각화에 적용한 것.

다만 UMAP이 뱉는 좌표를 그대로 화면 좌표로 쓰면 안 되는 이유가 세 가지 있어서, 아래에서
후처리를 거친다:
1) UMAP 출력은 축마다 퍼진 정도가 다를 수 있다(한 축은 넓게, 다른 축은 좁게) — 이걸
   축 구분 없이 하나의 배율로만 정규화하면 좁은 축이 화면에서 실제로 한 줄로 눌린 것처럼
   보인다("세로로 좁은 레이아웃" 버그). 그래서 축마다 독립적으로 target_extent에 맞춘다.
2) UMAP은 지역 이웃 순서(무엇이 무엇과 가까운지)는 보존하지만, 서로 다른 군집 사이의
   "거리"는 의미가 없기로 유명하다(클러스터끼리 필요 이상으로 붙어 나올 수 있음). 노드에
   토픽/클러스터 라벨이 있으면 각 클러스터 중심을 원점 기준으로 살짝 더 밀어내서
   ("cluster_spread") 군집끼리 시각적으로 분리되게 하되, 클러스터 내부는 그대로 평행
   이동만 하므로 지역 유사도 순서는 전혀 바뀌지 않는다.
3) 위 두 단계를 거쳐도 점이 몇 개 안 되거나 우연히 겹칠 수 있어서, 최소 거리보다 가까운
   점 쌍만 아주 조금씩 밀어내는 완화(relaxation) 패스로 완전 겹침을 방지한다.

교체 시 지켜야 할 인터페이스: (vectors: list[list[float]], n_components: int) -> list[list[float]]
반환값은 vectors와 같은 길이의 좌표 리스트."""

import math


# 클러스터 중심을 원점에서 얼마나 더 밀어낼지(1.0 = 그대로, 클수록 더 벌어짐).
# "살짝"이 목적이라 너무 크게 잡으면 오히려 UMAP이 잡아낸 실제 유사도 차이가 안 보이게 됨
_CLUSTER_SPREAD_FACTOR = 1.25

# 이 값(전체 화면 크기 대비 비율)보다 가까운 두 점은 겹친 것으로 보고 밀어낸다
_MIN_SEPARATION_RATIO = 0.05
_OVERLAP_ITERATIONS = 40


def _spread_clusters(coords, labels: list[str] | None, spread_factor: float = _CLUSTER_SPREAD_FACTOR):
    """라벨(토픽 등)이 같은 점들의 중심을 원점 기준으로 밀어내고, 그 중심에 속한 점 전체를
    같은 만큼 평행이동(rigid translation)한다 — 클러스터 "내부" 배치는 손대지 않으므로
    UMAP이 만든 이웃 순서(지역 유사도)는 그대로 유지되고, 서로 다른 클러스터 사이의
    여백만 넓어진다. 라벨이 없거나 전부 같은 라벨이면(구분할 클러스터가 없으면) 아무것도
    하지 않는다."""
    if not labels or len(set(labels)) < 2:
        return coords

    import numpy as np

    labels_arr = np.asarray(labels)
    for label in np.unique(labels_arr):
        mask = labels_arr == label
        centroid = coords[mask].mean(axis=0)
        coords[mask] += centroid * (spread_factor - 1.0)
    return coords


def _rescale_axes(coords, target_extent: float):
    """축마다 독립적으로 최댓값 기준 정규화 — 한 축의 실제 분산이 다른 축보다 작다고 해서
    그 축을 인위적으로 늘리지는 않되(그 자체가 의미 있는 신호일 수 있음), 적어도 각 축이
    "이 화면에서 쓸 수 있는 최대 범위"를 균등하게 활용하게 만들어 UMAP 결과가 우연히
    한쪽으로 눌려 나오는 걸 막는다."""
    import numpy as np

    axis_max = np.abs(coords).max(axis=0)
    axis_max = np.where(axis_max > 1e-6, axis_max, 1.0)
    return coords / axis_max * target_extent


def _remove_overlap(coords, min_separation: float, iterations: int = _OVERLAP_ITERATIONS):
    """min_separation보다 가까운 점 쌍만 서로 반대 방향으로 아주 조금씩 밀어내는 반복
    완화. 겹치지 않는 점은 건드리지 않으므로 이웃 관계나 전체 레이아웃은 그대로 유지되고,
    화면에서 점이 완전히 포개져 안 보이는 경우만 없앤다."""
    import numpy as np

    n = len(coords)
    if n < 2:
        return coords

    coords = coords.copy()
    step = min_separation * 0.08
    for _ in range(iterations):
        moved = False
        for i in range(n):
            diff = coords[i] - coords
            dist = np.linalg.norm(diff, axis=1)
            dist[i] = np.inf
            close = dist < min_separation
            if not close.any():
                continue
            moved = True
            direction = diff[close] / dist[close, None]
            direction = np.nan_to_num(direction)
            push = direction.sum(axis=0)
            push_norm = np.linalg.norm(push)
            if push_norm > 1e-9:
                coords[i] += push / push_norm * step
        if not moved:
            break
    return coords


def umap_project(
    vectors: list[list[float]],
    n_components: int = 3,
    target_extent: float = 220.0,
    cluster_labels: list[str] | None = None,
) -> list[list[float]]:
    n = len(vectors)
    if n < 4:
        # UMAP은 이웃 구조를 볼 만큼의 표본이 있어야 의미가 있음(기본 n_neighbors=15).
        # 그보다 적으면 계산이 불안정하므로 원점을 중심으로 순서대로만 펼쳐 그래프가
        # 깨지지 않게 함(중심을 0으로 둬서 UMAP 경로와 마찬가지로 항상 화면 중앙에 오게)
        step = target_extent / max(n, 1)
        offset = (n - 1) * step / 2
        return [[float(i) * step - offset, 0.0, 0.0][:n_components] for i in range(n)]

    import numpy as np
    import umap  # 임포트 자체가 무거워서(numba JIT 등) 실제로 쓸 때만 로드

    n_neighbors = max(2, min(15, n - 1))
    # 기본 init='spectral'은 표본이 적을 때(n_components에 비해 N이 작으면) scipy 희소
    # eigensolver가 "k >= N" 에러로 죽는다 — init='random'을 쓰면 그 경로를 안 타서
    # 표본이 몇 개 안 되는 초반 분석 상태에서도 항상 안정적으로 동작함.
    # metric='cosine': 이 파이프라인의 나머지 전부(knn_graph_links의 간선 판단, topic.py의
    # 토픽 배정)가 코사인 유사도를 기준으로 삼는데, UMAP 기본값(euclidean)을 그대로 두면
    # "간선은 코사인 기준으로 이어져 있는데 위치는 유클리드 기준으로 배치되는" 불일치가
    # 생긴다 — 실제로 BERTopic도 문서 임베딩에 UMAP을 적용할 때 metric='cosine'을 씀.
    # min_dist=0.1(기본값): 낮을수록 지역 구조(같은 토픽끼리 얼마나 뭉치는지)를 더 타이트하게
    # 보존한다는 게 UMAP 공식 문서의 설명 — 토픽별로 뚜렷이 갈라진 섬처럼 보이는 게
    # 목적이라 "고르게 펼치는" 높은 min_dist보다 이쪽이 이 용도에 더 맞음
    reducer = umap.UMAP(
        n_components=n_components, n_neighbors=n_neighbors, min_dist=0.1,
        metric="cosine", random_state=42, init="random",
    )
    coords = reducer.fit_transform(np.array(vectors, dtype=float))

    # UMAP 출력은 원점 근처에 있으리라는 보장이 없음 — 무게중심을 원점으로 이동해서
    # 이후 단계(클러스터 밀어내기, 겹침 방지)가 "중심으로부터의 거리" 기준으로 일관되게 동작하게 함
    coords = coords - coords.mean(axis=0)

    coords = _spread_clusters(coords, cluster_labels)

    # 여기서 최종 화면 스케일로 확정 — 뒤이은 겹침 방지 패스가 화면 단위(target_extent
    # 기준)로 최소 거리를 판단할 수 있도록 축 정규화를 먼저 끝낸다
    coords = _rescale_axes(coords, target_extent)

    coords = _remove_overlap(coords, min_separation=target_extent * _MIN_SEPARATION_RATIO)

    return coords.tolist()
