"""비율(%) 하나만 보여주면 댓글 5개짜리 토픽과 5,000개짜리 토픽의 "80% 긍정"이 똑같이
확정적으로 보인다. Wilson score interval은 정규근사(Wald, p ± 1.96*sqrt(p(1-p)/n))보다
표본이 작거나 p가 0%/100%에 가까울 때 안정적인 비율 신뢰구간이라(Wilson, 1927) 여기 쓴다.
참값 p 자체보다 "이 % 숫자를 얼마나 믿어도 되는지"가 문제라, 어려운 통계 용어 대신
등급(LOW/MEDIUM/HIGH)과 95% 구간만 계산해서 프론트에 넘긴다."""

import math

_Z_95 = 1.96

# 표본 크기 등급 임계값 — Wilson 구간 폭이 급격히 좁아지는 지점을 기준으로 한 경험적 값.
# 10 미만은 구간 폭이 보통 30%p를 넘어 사실상 방향성 정도만 알 수 있는 수준(LOW),
# 30 이상부터는 구간 폭이 20%p 이내로 들어와 추세를 믿을 만한 수준(HIGH)
_LOW_SAMPLE_SIZE = 10
_MEDIUM_SAMPLE_SIZE = 30


def wilson_interval(count: int, total: int, z: float = _Z_95) -> tuple[float, float]:
    """count/total 비율의 95% 신뢰구간을 (0~1 범위로) 반환."""
    if total <= 0:
        return (0.0, 0.0)
    phat = count / total
    z2 = z * z
    denom = 1 + z2 / total
    center = phat + z2 / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z2 / (4 * total)) / total)
    lower = max(0.0, (center - margin) / denom)
    upper = min(1.0, (center + margin) / denom)
    return (lower, upper)


def confidence_level(total: int) -> str:
    if total < _LOW_SAMPLE_SIZE:
        return "LOW"
    if total < _MEDIUM_SAMPLE_SIZE:
        return "MEDIUM"
    return "HIGH"


def rate_confidence(count: int, total: int) -> dict:
    """count/total 비율(%) 하나에 대한 신뢰도 메타데이터.
    ciLow/ciHigh는 0~100 스케일의 원시 값 — 소수점 표시 자리는 프론트에서 결정"""
    lower, upper = wilson_interval(count, total)
    return {
        "level": confidence_level(total),
        "ciLow": round(lower * 100, 1),
        "ciHigh": round(upper * 100, 1),
        "sampleSize": total,
    }
