"""
vocal_mbti.py — 보컬 MBTI 코드 체계 (모델 v2 핵심)
=====================================================

목적:
    음원 측정값을 4축 16타입의 보컬 MBTI 코드로 자동 변환.
    회사 헌법 정합: 단일 점수 산출 X, 차원별 독립 분류.

4축 정의:
    Axis 1 — Tone Brightness: Bright (B) ↔ Dark (D)
    Axis 2 — Tone Weight: Warm (W) ↔ Dry (R)
    Axis 3 — Energy Direction: Outward (O) ↔ Inward (I)
    Axis 4 — Expression Style: Peak (P) ↔ Subtle (S)

마마무 4인 기준 코드:
    솔라  = BWOP (Bright-Warm-Outward-Peak)
    휘인  = BWIS (Bright-Warm-Inward-Subtle)
    화사  = DWOP (Dark-Warm-Outward-Peak)
    문별  = BRIS (Bright-Dry-Inward-Subtle)

회사 헌법 정합:
    - 코드 4글자는 분류일 뿐, 종합 점수 아님
    - 백분위 숫자는 "이 타입 내부에서의 희소성" — 단일 판정 기준 X
    - 양쪽 꼬리 (Bright 끝 + Dark 끝, 양쪽 모두 outlier 가능)

작성일: 2026-05-12 (v2 통합 시스템 핵심)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


# ============================================================
# 1. 4축 정의 + 마마무 기준값
# ============================================================

AXIS_NAMES = {
    1: ("Brightness", "Bright (B)", "Dark (D)"),
    2: ("Weight", "Warm (W)", "Dry (R)"),
    3: ("Direction", "Outward (O)", "Inward (I)"),
    4: ("Style", "Peak (P)", "Subtle (S)"),
}

# 마마무 4인 기준 코드 (메모리 가설 기반)
MAMAMOO_REFERENCE = {
    "솔라": {"code": "BWOP", "brightness": 0.75, "weight": 0.30,
            "direction": 0.80, "style": 0.75,
            "description": "청량한 따뜻함의 외향적 정점 — 메탈릭 광택 + 후렴 폭발"},
    "휘인": {"code": "BWIS", "brightness": 0.55, "weight": 0.25,
            "direction": 0.30, "style": 0.20,
            "description": "청량한 따뜻함의 내향적 정밀 — 가벼운 성대 + 점진적 빌드업"},
    "화사": {"code": "DWOP", "brightness": 0.25, "weight": 0.30,
            "direction": 0.85, "style": 0.85,
            "description": "묵직한 따뜻함의 외향적 정점 — 흉성 두꺼움 + 강한 클라이맥스"},
    "문별": {"code": "BRIS", "brightness": 0.65, "weight": 0.75,
            "direction": 0.25, "style": 0.30,
            "description": "청량한 건조함의 내향적 정밀 — 보이쉬 + 저음 화음 받침"},
}

# 16타입 설명
TYPE_DESCRIPTIONS = {
    "BWOP": "솔라형 — 청량·따뜻·외향·정점. K-POP 후렴 폭발 표준",
    "BWOS": "청량·따뜻·외향·정밀. 외향적이면서도 디테일 강함",
    "BWIP": "청량·따뜻·내향·정점. 끌어들이면서 강한 임팩트",
    "BWIS": "휘인형 — 청량·따뜻·내향·정밀. 섬세한 정점의 정의",
    "BROP": "청량·건조·외향·정점. 시원시원한 보이쉬 외향",
    "BROS": "청량·건조·외향·정밀. 신선한 외향적 디테일",
    "BRIP": "청량·건조·내향·정점. 보이쉬한 임팩트",
    "BRIS": "문별형 — 청량·건조·내향·정밀. 저음 화음 받침형",
    "DWOP": "화사형 — 묵직·따뜻·외향·정점. 흉성 캐릭터 보이스",
    "DWOS": "묵직·따뜻·외향·정밀. 묵직하면서 정교한 표현",
    "DWIP": "묵직·따뜻·내향·정점. 깊은 흡인력 + 강한 임팩트",
    "DWIS": "묵직·따뜻·내향·정밀. R&B 발라드 정점 유형",
    "DROP": "묵직·건조·외향·정점. 거친 카리스마 외향",
    "DROS": "묵직·건조·외향·정밀. 묵직한 외향적 디테일",
    "DRIP": "묵직·건조·내향·정점. 깊고 무거운 임팩트",
    "DRIS": "묵직·건조·내향·정밀. 음울한 정밀 보컬",
}


# ============================================================
# 2. 측정값 → 4축 점수 산출
# ============================================================

@dataclass
class AxisScores:
    """4축 점수 (각 0.0~1.0)."""
    brightness: float = 0.5      # 0=Dark, 1=Bright
    weight: float = 0.5          # 0=Warm, 1=Dry
    direction: float = 0.5       # 0=Inward, 1=Outward
    style: float = 0.5           # 0=Subtle, 1=Peak
    confidence: float = 1.0      # 측정 신뢰도


def measure_brightness(measurements: Dict) -> float:
    """
    축 1: Tone Brightness 측정.

    v2.1 개선:
    - 한국 여자 보컬 spectral centroid 분포(1000~2800Hz)에 맞춤
    - 흉성 비율에 더 큰 가중치 (벨팅 고주파 잡음 강건성)

    근거:
    - Spectral centroid 높음 = 밝음 (단, 잡음 영향 받음)
    - 흉성 비율 높음 = 어두움 (가장 강력한 다크니스 지표)
    - F2/F1 비율 높음 = 밝음
    """
    factors = []
    weights = []

    # 1. Spectral centroid (한국 여자 1000=어두움, 2800=밝음으로 재조정)
    centroid = measurements.get("spectral_centroid_hz", 1800)
    factors.append(np.clip((centroid - 1000) / 1800, 0, 1))
    weights.append(1.0)

    # 2. 흉성 비율 (높을수록 어두움) — 가중치 ↑
    chest_ratio = measurements.get("chest_voice_ratio", 0.5)
    factors.append(1.0 - chest_ratio)
    weights.append(2.0)  # 흉성이 가장 강력한 다크니스 지표

    # 3. Formant F2/F1 ratio (높을수록 밝음, 일반 1.5~3.5)
    f1 = measurements.get("formant_1_hz", 600)
    f2 = measurements.get("formant_2_hz", 1500)
    if f1 > 0:
        ratio = f2 / f1
        factors.append(np.clip((ratio - 1.5) / 2.0, 0, 1))
        weights.append(0.8)

    if factors:
        return float(np.average(factors, weights=weights))
    return 0.5


def measure_weight(measurements: Dict) -> float:
    """
    축 2: Tone Weight (Warm vs Dry).

    v2.2 개선:
    - F3 위치 정밀 활용 (Parselmouth)
    - F2/F1 비율로 구강 형태 추정

    근거:
    - 비강 공명 비율 높음 = 따뜻 (Warm)
    - 호흡성 높음 = 따뜻
    - F3 낮음 (~2400Hz 아래) = 따뜻
    - F2/F1 비율 낮음 = 어두운/따뜻
    """
    factors = []
    weights = []

    # 1. 비강 공명 (높을수록 Warm = 0 방향)
    nasal = measurements.get("nasal_resonance_ratio", 0.5)
    factors.append(1.0 - nasal)
    weights.append(1.2)

    # 2. 호흡성 (높을수록 Warm)
    breathiness = measurements.get("breathiness", 0.5)
    factors.append(1.0 - breathiness)
    weights.append(0.8)

    # 3. HNR (높을수록 Dry)
    hnr = measurements.get("hnr_db", 20)
    factors.append(np.clip((hnr - 15) / 15, 0, 1))
    weights.append(0.7)

    # 4. F3 위치 (있을 때 — Parselmouth) — 낮으면 Warm
    f3 = measurements.get("formant_3_hz", None)
    if f3 is not None:
        # F3: 2400Hz=Warm, 3200Hz=Dry
        factors.append(np.clip((f3 - 2400) / 800, 0, 1))
        weights.append(1.0)

    if factors:
        return float(np.average(factors, weights=weights))
    return 0.5


def measure_direction(measurements: Dict) -> float:
    """
    축 3: Energy Direction (Outward vs Inward).

    v2.2 개선: MR 제거 음원의 압축 다이내믹스 강건성
    - Jitter/Shimmer (Parselmouth)로 발성 강도 추정
    - HNR로 발성 압력 추정
    - 압축된 음원에서도 측정 가능한 지표 추가

    근거:
    - Dynamic range 높음 = Outward
    - Attack 강함 = Outward
    - Shimmer 높음 = 강한 발성 = Outward
    - F1 위치 높음 (입 크게 벌림) = Outward
    """
    factors = []
    weights = []

    # 1. Dynamic range (낮은 임계값으로 조정 — MR 제거 음원 압축 고려)
    dyn_range = measurements.get("dynamic_range_db", 20)
    factors.append(np.clip((dyn_range - 5) / 20, 0, 1))
    weights.append(0.8)

    # 2. Attack sharpness
    attack = measurements.get("attack_sharpness", 0.5)
    factors.append(attack)
    weights.append(1.0)

    # 3. Loudness smoothness (낮을수록 Outward)
    smoothness = measurements.get("loudness_smoothness", 0.5)
    factors.append(1.0 - smoothness)
    weights.append(0.6)

    # 4. Shimmer (Parselmouth) — 높음 = 강한 발성 = Outward
    shimmer = measurements.get("shimmer_local", None)
    if shimmer is not None:
        # 일반 0.01~0.10. 높을수록 Outward
        factors.append(np.clip(shimmer * 15, 0, 1))
        weights.append(1.2)  # 압축 음원에서도 신뢰 가능한 지표

    # 5. F1 위치 (입 크게 벌리면 F1 높아짐, 700Hz 이상=Outward)
    f1 = measurements.get("formant_1_hz", 600)
    factors.append(np.clip((f1 - 500) / 400, 0, 1))
    weights.append(0.7)

    if factors:
        return float(np.average(factors, weights=weights))
    return 0.5


def measure_style(measurements: Dict) -> float:
    """
    축 4: Expression Style (Peak vs Subtle).

    v2.2 개선: 압축 음원 강건성
    - Spectral energy variance (스펙트럼 변동성) 추가
    - Jitter로 보컬 표현력 추정

    근거:
    - 클라이맥스 구축력 높음 = Peak
    - Jitter 높음 = 표현력 큼 = Peak
    - HNR 낮음 = 거친 음색 = Peak
    - 균등한 빌드업 = Subtle
    """
    factors = []
    weights = []

    # 1. 클라이맥스 구축력
    climax = measurements.get("climax_building", 0.5)
    factors.append(climax)
    weights.append(1.0)

    # 2. 에너지 변화율 (낮은 임계값)
    energy_change_rate = measurements.get("energy_change_rate", 0.5)
    factors.append(np.clip(energy_change_rate * 1.5, 0, 1))
    weights.append(0.8)

    # 3. Loudness smoothness (낮을수록 Peak)
    smoothness = measurements.get("loudness_smoothness", 0.5)
    factors.append(1.0 - smoothness)
    weights.append(0.6)

    # 4. Jitter (Parselmouth) — 높음 = 표현력 = Peak
    jitter = measurements.get("jitter_local", None)
    if jitter is not None:
        # 일반 0.005~0.030. 높을수록 Peak
        factors.append(np.clip(jitter * 35, 0, 1))
        weights.append(1.0)

    # 5. HNR — 낮음 = 거친 음색 = Peak (벨팅·샤우팅)
    hnr = measurements.get("hnr_db", 20)
    factors.append(np.clip(1.0 - (hnr - 5) / 25, 0, 1))
    weights.append(0.9)

    if factors:
        return float(np.average(factors, weights=weights))
    return 0.5


# ============================================================
# 3. 4축 점수 → 4글자 코드
# ============================================================

def scores_to_code(scores: AxisScores) -> str:
    """4축 점수를 4글자 MBTI 코드로 변환."""
    char_1 = "B" if scores.brightness >= 0.5 else "D"
    char_2 = "W" if scores.weight <= 0.5 else "R"  # 0=Warm, 1=Dry
    char_3 = "O" if scores.direction >= 0.5 else "I"
    char_4 = "P" if scores.style >= 0.5 else "S"
    return f"{char_1}{char_2}{char_3}{char_4}"


def code_to_description(code: str) -> str:
    """4글자 코드를 설명으로 변환."""
    return TYPE_DESCRIPTIONS.get(code, "알 수 없는 타입")


# ============================================================
# 4. 통합 결과 — VocalMBTIResult
# ============================================================

@dataclass
class CelebMatch:
    """셀럽 매칭 결과 — 4인 + 화사."""
    name: str
    code: str
    similarity_percent: float  # 0~100
    distance: float            # 정규화 거리


@dataclass
class VocalMBTIResult:
    """v2 통합 결과 — 5프레임 표시용."""

    # 4축 점수
    axis_scores: AxisScores

    # 4글자 코드
    code: str
    code_description: str

    # 타입 내부 백분위 (회사 헌법: 종합 점수 아님)
    type_percentile: float

    # 셀럽 매칭 (마마무 4인)
    celeb_matches: List[CelebMatch] = field(default_factory=list)

    # 5프레임 메시지
    frame_1_attention: str = ""    # "당신은 평범하지 않다"
    frame_2_code_intro: str = ""   # 코드 한 줄 설명
    frame_3_rarity: str = ""       # 희소성 순위
    frame_4_celeb: str = ""        # 셀럽 매칭 메시지
    frame_5_emotional: str = ""    # 감정 트리거 메시지

    # outlier 차원 (회사 헌법 OR 논리)
    outlier_high_dimensions: List[str] = field(default_factory=list)
    outlier_low_dimensions: List[str] = field(default_factory=list)

    # 고유성 점수 (회사 헌법 핵심 — 닮음이 아닌 다름이 가치)
    uniqueness: Optional[Dict] = None

    # 신뢰도 메타데이터
    confidence: float = 1.0
    measurements_count: int = 0


# ============================================================
# 5. 셀럽 매칭 — 마마무 4인 거리 계산
# ============================================================

def compute_celeb_matches(scores: AxisScores) -> List[CelebMatch]:
    """4축 점수와 마마무 4인 기준값의 거리로 매칭."""
    matches = []
    user_vector = np.array([scores.brightness, scores.weight,
                            scores.direction, scores.style])

    for name, ref in MAMAMOO_REFERENCE.items():
        ref_vector = np.array([ref["brightness"], ref["weight"],
                              ref["direction"], ref["style"]])
        distance = float(np.linalg.norm(user_vector - ref_vector))
        # 거리 → 유사도 변환 (0~100%)
        # 최대 거리 √4 ≈ 2.0
        similarity = max(0, 100 * (1 - distance / 2.0))
        matches.append(CelebMatch(
            name=name,
            code=ref["code"],
            similarity_percent=similarity,
            distance=distance,
        ))

    # 유사도 높은 순으로 정렬
    matches.sort(key=lambda m: -m.similarity_percent)
    return matches


# ============================================================
# 6. 5프레임 메시지 생성
# ============================================================

def generate_frame_messages(
    result: VocalMBTIResult, has_outlier: bool
) -> None:
    """결과에 5프레임 메시지 자동 생성. 고유성(uniqueness) 중심으로 톤 정렬."""

    # 고유성 점수 활용
    u = result.uniqueness or {}
    u_score = u.get("score", 50)

    # Frame 1 — 주의 환기 (고유성 기반)
    if u_score >= 80:
        result.frame_1_attention = "기존 K-POP에서 보기 힘든 영역의 목소리입니다"
    elif u_score >= 60:
        result.frame_1_attention = "당신의 목소리에 남다른 점이 있습니다"
    elif has_outlier:
        result.frame_1_attention = "일부 차원에서 outlier가 감지됐습니다"
    else:
        result.frame_1_attention = "당신의 목소리를 분석했습니다"

    # Frame 2 — 코드 소개
    result.frame_2_code_intro = (
        f"보컬 코드: {result.code}-{int(result.type_percentile):02d}\n"
        f"{result.code_description}"
    )

    # Frame 3 — 희소성
    pct = result.type_percentile
    if pct >= 99:
        result.frame_3_rarity = "이 타입 안에서 상위 1% — 매우 희귀한 보컬"
    elif pct >= 95:
        result.frame_3_rarity = "이 타입 안에서 상위 5% — 뚜렷한 outlier"
    elif pct >= 75:
        result.frame_3_rarity = "이 타입 안에서 상위 25% — 평균보다 뚜렷"
    else:
        result.frame_3_rarity = "이 타입 안에서 평균 범위"

    # Frame 4 — 고유성 (닮음이 아닌 다름 강조)
    closest = u.get("closest_reference", "")
    min_dist = u.get("min_reference_distance", 0)
    if u_score >= 80:
        result.frame_4_celeb = (
            f"기존 가수 영역 밖 — 발굴 가치 매우 높음\n"
            f"가장 가까운 기존 가수도 {int(min_dist*100)}% 다름"
        )
    elif u_score >= 60:
        result.frame_4_celeb = (
            f"독특한 영역 — {closest}와도 {int(min_dist*100)}% 차이"
        )
    else:
        result.frame_4_celeb = (
            f"기존 가수와 유사 영역 — 가장 가까움: {closest}\n"
            f"차별화 가능 차원 추가 검토 필요"
        )

    # Frame 5 — 감정 트리거 (고유성 톤 정렬)
    if u_score >= 80:
        result.frame_5_emotional = (
            f"기존 K-POP에 없던 새로운 영역. {result.code} 유형의 진짜 신선함."
        )
    elif u_score >= 60:
        result.frame_5_emotional = (
            f"당신의 보컬은 {result.code} 유형 안에서도 독특한 색을 갖고 있습니다"
        )
    else:
        emotional_msgs = {
            "BWOP": "청량한 햇살의 외향성. 기존 솔라형 영역",
            "BWIS": "따뜻한 속삭임의 정밀. 기존 휘인형 영역",
            "DWOP": "깊은 흉성의 압도력. 기존 화사형 영역",
            "BRIS": "건조하고 보이쉬. 기존 문별형 영역",
        }
        result.frame_5_emotional = emotional_msgs.get(
            result.code,
            f"{result.code} 유형 — 기존 영역과의 차별점 추가 검토 필요"
        )


# ============================================================
# 6.5. 고유성 점수 — 회사 헌법 정합 핵심 지표
# ============================================================

def compute_uniqueness(scores: AxisScores) -> Dict:
    """기존 K-POP 가수와 얼마나 다른가 = 고유성 점수.

    회사 헌법:
    - 닮음 = 템플릿 복사 = 캐스팅 가치 낮음
    - 다름 = 새로운 천재 가능성 = 캐스팅 가치 높음

    계산:
        1. 축 극단성 (max |axis - 0.5|) — OR 논리 (한 차원이라도 극단)
        2. 마마무 4인과의 평균 거리 (4축 공간 유클리드)
        3. 마마무 4인 중 최단 거리 (가장 가까운 가수와도 멀면 진짜 outlier)

    Returns:
        {
            "score": 0~100 (고유성 점수),
            "tier": str (영역 분류),
            "axis_extremeness": float,
            "min_reference_distance": float,
            "avg_reference_distance": float,
            "closest_reference": str,
        }
    """
    # 1. 축 극단성 — OR 논리 (가장 극단적인 축이 가치)
    axis_distances_from_center = [
        abs(scores.brightness - 0.5),
        abs(scores.weight - 0.5),
        abs(scores.direction - 0.5),
        abs(scores.style - 0.5),
    ]
    max_extremeness = max(axis_distances_from_center) * 2  # 0~1
    avg_extremeness = (sum(axis_distances_from_center) / 4) * 2  # 0~1

    # 2. 마마무 4인과의 거리 (4축 유클리드 공간)
    ref_distances = {}
    for name, ref in MAMAMOO_REFERENCE.items():
        dist = np.sqrt(
            (scores.brightness - ref["brightness"]) ** 2 +
            (scores.weight - ref["weight"]) ** 2 +
            (scores.direction - ref["direction"]) ** 2 +
            (scores.style - ref["style"]) ** 2
        )
        # 최대 거리 = sqrt(4) = 2, 정규화 0~1
        ref_distances[name] = float(dist / 2.0)

    min_dist = min(ref_distances.values())
    avg_dist = sum(ref_distances.values()) / len(ref_distances)
    closest_member = min(ref_distances, key=ref_distances.get)

    # 3. 종합 고유성 점수
    # - 축 극단성 50% (얼마나 평범하지 않은가)
    # - 레퍼런스로부터 거리 50% (얼마나 기존 가수와 다른가)
    uniqueness_raw = (max_extremeness * 0.5) + (min_dist * 0.5)
    uniqueness_score = float(np.clip(uniqueness_raw * 100, 0, 100))

    # 4. 영역 분류
    if uniqueness_score >= 80:
        tier = "극히 희귀"
        tier_desc = "기존 K-POP에서 거의 볼 수 없는 영역. 발굴 가치 매우 높음"
        tier_color = "extreme"
    elif uniqueness_score >= 60:
        tier = "독특"
        tier_desc = "기존 가수들과 뚜렷이 구별되는 영역. 추가 검토 가치"
        tier_color = "high"
    elif uniqueness_score >= 40:
        tier = "차별 가능"
        tier_desc = "일부 차원에서 차별점 존재. 잠재력 있음"
        tier_color = "medium"
    else:
        tier = "평범"
        tier_desc = "기존 K-POP 가수와 유사 영역. 차별화 어려움"
        tier_color = "low"

    return {
        "score": uniqueness_score,
        "tier": tier,
        "tier_desc": tier_desc,
        "tier_color": tier_color,
        "axis_extremeness": float(max_extremeness),
        "avg_extremeness": float(avg_extremeness),
        "min_reference_distance": min_dist,
        "avg_reference_distance": avg_dist,
        "closest_reference": closest_member,
        "all_reference_distances": ref_distances,
    }


# ============================================================
# 7. 통합 분석 진입점
# ============================================================

def analyze_vocal_mbti(
    measurements: Dict,
    outlier_high: Optional[List[str]] = None,
    outlier_low: Optional[List[str]] = None,
) -> VocalMBTIResult:
    """
    음원 측정값 dict를 받아 보컬 MBTI 결과 생성.

    Args:
        measurements: audio_v2 + vocal_ability_analyzer 측정 결과
            (spectral_centroid_hz, chest_voice_ratio, formant_1_hz, ...)
        outlier_high: 초우월 outlier 차원 ID 리스트
        outlier_low: 초이질 outlier 차원 ID 리스트

    Returns:
        VocalMBTIResult — 5프레임 표시 준비된 결과
    """
    # 4축 점수 산출
    scores = AxisScores(
        brightness=measure_brightness(measurements),
        weight=measure_weight(measurements),
        direction=measure_direction(measurements),
        style=measure_style(measurements),
    )

    # 4글자 코드
    code = scores_to_code(scores)
    description = code_to_description(code)

    # 셀럽 매칭
    celeb_matches = compute_celeb_matches(scores)

    # 타입 내부 백분위 (각 축 점수의 평균 거리 → 백분위 변환)
    # 회사 헌법: 종합 점수 아닌 "이 타입 안에서의 희소성"으로만 해석
    type_percentile = float(50 + 50 * (
        abs(scores.brightness - 0.5) +
        abs(scores.weight - 0.5) +
        abs(scores.direction - 0.5) +
        abs(scores.style - 0.5)
    ) / 2.0)
    type_percentile = min(99.9, max(50, type_percentile))

    # outlier 차원 정리
    out_high = outlier_high or []
    out_low = outlier_low or []
    has_outlier = len(out_high) + len(out_low) > 0

    # 고유성 점수 계산 (회사 헌법 핵심 지표)
    uniqueness = compute_uniqueness(scores)

    result = VocalMBTIResult(
        axis_scores=scores,
        code=code,
        code_description=description,
        type_percentile=type_percentile,
        celeb_matches=celeb_matches,
        outlier_high_dimensions=out_high,
        outlier_low_dimensions=out_low,
        uniqueness=uniqueness,
        measurements_count=len(measurements),
    )

    # 5프레임 메시지 자동 생성
    generate_frame_messages(result, has_outlier)

    return result


# ============================================================
# 8. CLI / 빠른 테스트
# ============================================================

if __name__ == "__main__":
    # 휘인 기준값으로 자가 테스트
    sample_measurements = {
        "spectral_centroid_hz": 2200,
        "chest_voice_ratio": 0.25,
        "formant_1_hz": 700,
        "formant_2_hz": 1900,
        "nasal_resonance_ratio": 0.65,
        "breathiness": 0.55,
        "hnr_db": 18,
        "dynamic_range_db": 15,
        "attack_sharpness": 0.30,
        "loudness_smoothness": 0.85,
        "climax_building": 0.25,
        "energy_change_rate": 0.20,
    }

    result = analyze_vocal_mbti(sample_measurements)

    print("=" * 60)
    print(f"보컬 MBTI 결과 (휘인 시뮬레이션)")
    print("=" * 60)
    print(f"4축 점수:")
    print(f"  Brightness: {result.axis_scores.brightness:.2f}")
    print(f"  Weight:     {result.axis_scores.weight:.2f}")
    print(f"  Direction:  {result.axis_scores.direction:.2f}")
    print(f"  Style:      {result.axis_scores.style:.2f}")
    print(f"\n코드: {result.code}-{int(result.type_percentile)}")
    print(f"설명: {result.code_description}")
    print(f"\n5프레임 메시지:")
    print(f"  [1] {result.frame_1_attention}")
    print(f"  [2] {result.frame_2_code_intro}")
    print(f"  [3] {result.frame_3_rarity}")
    print(f"  [4] {result.frame_4_celeb}")
    print(f"  [5] {result.frame_5_emotional}")
    print(f"\n셀럽 매칭 TOP 3:")
    for m in result.celeb_matches[:3]:
        print(f"  {m.name} ({m.code}): {m.similarity_percent:.1f}%")
