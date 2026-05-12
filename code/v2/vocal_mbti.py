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

    근거:
    - Spectral centroid 높음 = 밝음
    - Spectral rolloff 높음 = 밝음
    - F2/F1 비율 높음 = 밝음
    - 흉성 비율 높음 = 어두움
    """
    factors = []

    # Spectral centroid (정규화: 1000Hz=0.5, 3000Hz=1.0)
    centroid = measurements.get("spectral_centroid_hz", 1500)
    factors.append(np.clip((centroid - 500) / 2500, 0, 1))

    # 흉성 비율 (높을수록 어두움)
    chest_ratio = measurements.get("chest_voice_ratio", 0.5)
    factors.append(1.0 - chest_ratio)

    # Formant F2/F1 ratio (높을수록 밝음, 일반 1.5~3.5)
    f1 = measurements.get("formant_1_hz", 600)
    f2 = measurements.get("formant_2_hz", 1500)
    if f1 > 0:
        ratio = f2 / f1
        factors.append(np.clip((ratio - 1.5) / 2.0, 0, 1))

    return float(np.mean(factors)) if factors else 0.5


def measure_weight(measurements: Dict) -> float:
    """
    축 2: Tone Weight (Warm vs Dry).

    근거:
    - 비강 공명 비율 높음 = 따뜻 (Warm)
    - 호흡성(breathiness) 높음 = 따뜻
    - HNR 낮음 + harmonic 안정 = 따뜻
    - F3 위치 높음 + 건조한 발성 = Dry
    """
    factors = []

    # 비강 공명 (높을수록 따뜻 = 0 방향)
    nasal = measurements.get("nasal_resonance_ratio", 0.5)
    factors.append(1.0 - nasal)

    # 호흡성 (높을수록 따뜻)
    breathiness = measurements.get("breathiness", 0.5)
    factors.append(1.0 - breathiness)

    # HNR (높을수록 깨끗 → Dry 쪽)
    hnr = measurements.get("hnr_db", 20)
    factors.append(np.clip((hnr - 15) / 15, 0, 1))

    return float(np.mean(factors)) if factors else 0.5


def measure_direction(measurements: Dict) -> float:
    """
    축 3: Energy Direction (Outward vs Inward).

    근거:
    - Dynamic range 높음 = Outward (발산)
    - Attack 강함 = Outward
    - Loudness 변화 크기 = Outward
    - 다이내믹 부드러움 = Inward (점진적)
    """
    factors = []

    # Dynamic range (높을수록 Outward)
    dyn_range = measurements.get("dynamic_range_db", 20)
    factors.append(np.clip((dyn_range - 10) / 30, 0, 1))

    # Attack sharpness (높을수록 Outward)
    attack = measurements.get("attack_sharpness", 0.5)
    factors.append(attack)

    # Loudness smoothness (낮을수록 Outward)
    smoothness = measurements.get("loudness_smoothness", 0.5)
    factors.append(1.0 - smoothness)

    return float(np.mean(factors)) if factors else 0.5


def measure_style(measurements: Dict) -> float:
    """
    축 4: Expression Style (Peak vs Subtle).

    근거:
    - 에너지 클라이맥스 구축력 높음 = Peak
    - 에너지 변화율(1차미분) 높음 = Peak
    - 에너지 엔트로피 낮음 = Peak (단일 클라이맥스에 집중)
    - 점진적 빌드업 = Subtle (휘인형)
    """
    factors = []

    # 클라이맥스 구축력
    climax = measurements.get("climax_building", 0.5)
    factors.append(climax)

    # 에너지 변화율 (높을수록 Peak)
    energy_change_rate = measurements.get("energy_change_rate", 0.5)
    factors.append(energy_change_rate)

    # 다이내믹 smoothness (낮을수록 Peak)
    smoothness = measurements.get("loudness_smoothness", 0.5)
    factors.append(1.0 - smoothness)

    return float(np.mean(factors)) if factors else 0.5


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
    """결과에 5프레임 메시지 자동 생성."""

    # Frame 1 — 주의 환기
    if has_outlier:
        result.frame_1_attention = "당신의 목소리에 남들과 다른 점이 있습니다"
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

    # Frame 4 — 셀럽 매칭
    if result.celeb_matches:
        top = result.celeb_matches[0]
        result.frame_4_celeb = (
            f"가장 닮은 보컬: {top.name} ({top.similarity_percent:.0f}%)\n"
            f"({top.code} — {MAMAMOO_REFERENCE[top.name]['description']})"
        )

    # Frame 5 — 감정 트리거 (코드별)
    emotional_msgs = {
        "BWOP": "당신의 목소리는 청량한 햇살처럼 외향적으로 빛납니다",
        "BWIS": "당신의 목소리는 따뜻한 속삭임처럼 사람을 끌어들입니다",
        "DWOP": "당신의 목소리는 깊은 흉성으로 공간을 압도합니다",
        "BRIS": "당신의 목소리는 건조하고 보이쉬한 매력으로 받침이 됩니다",
    }
    result.frame_5_emotional = emotional_msgs.get(
        result.code,
        f"당신의 목소리는 {result.code} 유형의 고유한 매력을 가졌습니다"
    )


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

    result = VocalMBTIResult(
        axis_scores=scores,
        code=code,
        code_description=description,
        type_percentile=type_percentile,
        celeb_matches=celeb_matches,
        outlier_high_dimensions=out_high,
        outlier_low_dimensions=out_low,
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
