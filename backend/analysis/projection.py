"""고차원 임베딩을 3D 화면 좌표로 "투영"하는 알고리즘만 모아두는 모듈 —
어떤 텍스트를 임베딩할지, 그래프 간선을 어떻게 뽑을지 같은 도메인 로직은 여기 두지 않는다.

기존엔 force-directed 물리 시뮬레이션(스프링+반발력의 평형 상태)으로 노드 위치를 정했는데,
이건 실제 임베딩 공간에서 얼마나 가까운지와 무관하게 물리 파라미터에 따라 배치가 달라진다.
UMAP은 고차원에서의 이웃 구조(어떤 점들이 실제로 가까운지)를 보존하도록 저차원 좌표를
직접 최적화하는 차원 축소 기법이라, 노드 위치 자체가 "실제로 의미가 가까운 정도"를 반영한다.
BERTopic(임베딩 → UMAP → HDBSCAN) 파이프라인과 동일한 아이디어를 그래프 시각화에 적용한 것.

교체 시 지켜야 할 인터페이스: (vectors: list[list[float]], n_components: int) -> list[list[float]]
반환값은 vectors와 같은 길이의 좌표 리스트."""


def umap_project(vectors: list[list[float]], n_components: int = 3, target_extent: float = 220.0) -> list[list[float]]:
    n = len(vectors)
    if n < 4:
        # UMAP은 이웃 구조를 볼 만큼의 표본이 있어야 의미가 있음(기본 n_neighbors=15).
        # 그보다 적으면 계산이 불안정하므로 원점을 중심으로 순서대로만 펼쳐 그래프가
        # 깨지지 않게 함(중심을 0으로 둬서 UMAP 경로와 마찬가지로 항상 화면 중앙에 오게)
        step = target_extent / max(n, 1)
        offset = (n - 1) * step / 2
        return [[float(i) * step - offset, 0.0, 0.0] for i in range(n)]

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

    # UMAP 출력은 원점 근처에 있으리라는 보장이 없고, 절대 스케일도 데이터셋마다 들쭉날쭉함
    # (포인트가 적을수록 서로 더 촘촘하게 뭉쳐서 나오는 경향). 두 가지를 모두 보정:
    # 1) 무게중심을 원점으로 이동(centering) — 그래프가 항상 화면 박스 정중앙에 오도록
    # 2) 실제 산출된 좌표의 최대 절댓값 기준으로 target_extent만큼 채우게 정규화(scaling) —
    #    분석된 영상 수와 무관하게 항상 일정한 화면 크기로 나오게 함(3d-force-graph의
    #    zoomToFit이 안정적으로 프레임을 채울 수 있음)
    coords = coords - coords.mean(axis=0)
    max_abs = np.abs(coords).max()
    if max_abs > 1e-6:
        coords = coords / max_abs * target_extent
    return coords.tolist()
