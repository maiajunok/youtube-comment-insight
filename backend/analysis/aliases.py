"""팀/선수 별칭(닉네임, 영문 표기, 오타 등)을 표준 토큰으로 정규화하는 알고리즘만 모아두는 모듈.
실제 별칭 목록(데이터)은 backend/aliases_data.py에 따로 있음 — 여기는 그 데이터를 "어떻게
적용할지"만 다룬다(알고리즘/데이터 분리, backend/analysis 패키지의 다른 모듈들과 같은 원칙).

임베딩 모델은 "제우스"와 "최우제"가 같은 사람을 가리킨다는 걸 보장하지 않는다 — 학습 데이터에
그 연관성이 충분히 강하게 들어있지 않으면 그냥 서로 다른 문자열로 취급돼 임베딩 공간에서
멀어질 수 있다. 이 모듈은 임베딩 *전에* 알려진 별칭을 표준 토큰으로 치환해서, 같은 선수/팀을
가리키는 서로 다른 표기가 임베딩 시점에는 이미 하나의 문자열이 되도록 만든다 —
검색·중복제거 시스템에서 흔히 쓰는 gazetteer 기반 정규화(entity/alias normalization) 기법.

교체 시 지켜야 할 인터페이스: normalize_aliases(text: str) -> str.
"""

import re

from aliases_data import FAN_ALIASES, OFFICIAL_ALIASES, TEAM_ALIASES

# 팀명 → 공식 표기 → 팬 별명 순으로 신뢰도가 낮아지는 계층이라 사전은 분리해서 관리하지만,
# 실제 치환은 세 사전을 합친 뒤 "긴 표현부터" 한 번에 처리한다. 카테고리 순서대로 나눠
# 적용하면 카테고리 경계를 넘어선 부분 문자열 충돌(예: 짧은 팬 별명이 그보다 긴 공식
# 표기 안에 우연히 포함된 경우)은 못 막지만, 길이 기준 정렬은 그 경우까지 안전하게 처리함
_ALIAS_MAP = {**TEAM_ALIASES, **OFFICIAL_ALIASES, **FAN_ALIASES}
_SORTED_ALIASES = sorted(_ALIAS_MAP.keys(), key=len, reverse=True)


def _is_ascii(s: str) -> bool:
    return all(ord(ch) < 128 for ch in s)


def normalize_aliases(text: str) -> str:
    """텍스트 안의 팀/선수 별칭을 표준 토큰(TEAM_*/PLAYER_*)으로 치환.
    임베딩 직전에 적용하면 "제우스"와 "최우제"가 같은 문자열이 되어 임베딩 공간에서
    같은 사람/팀을 가리키는 것으로 자연스럽게 묶인다."""
    result = text
    for alias in _SORTED_ALIASES:
        canonical = _ALIAS_MAP[alias]
        if _is_ascii(alias):
            # 영문 별칭은 단어 경계로 매칭 — "kt" 같은 짧은 표현이 다른 단어 속 부분
            # 문자열로 잘못 걸리는 걸 방지(예: 이미 치환된 "TEAM_KT" 안의 "kt"는 안 걸림)
            result = re.sub(r"\b" + re.escape(alias) + r"\b", canonical, result, flags=re.IGNORECASE)
        else:
            # 한글은 띄어쓰기 기준 단어 경계가 불안정해서 부분 문자열 치환을 씀
            result = result.replace(alias, canonical)
    return result
