"""
indicators_100.py — 100개 보컬 지표 레지스트리
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
엑셀 'K-POP_1차음원시스템_정량수치화_핵심100개' 기반
ID 체계: {축}-{대분류}-{중분류}-{순번}
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 구조
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class IndicatorSpec:
    """지표 명세 (레지스트리 항목)"""
    id: str                        # "A-1-1-08"
    name: str                      # "극초고음역 음정정확도"
    axis: str                      # "A" / "B" / "C"
    category_major: str            # "음정정확도"
    category_mid: str              # "안정성"
    algorithm: str                 # "Pitch_Analysis"
    tier: int                      # 1=음향분석, 2=ML모델
    reliability: str               # "높음" / "중간(ML가능)"
    genius_signal: str             # "매우강함(천재신호)" / "강함" / "중간"
    mvp: bool                      # MVP 대상 여부
    unit: str = ""                 # 측정 단위 ("cent", "Hz", "dB" 등)
    description: str = ""          # 측정 설명

@dataclass
class IndicatorMeasurement:
    """1개 지표의 측정 결과"""
    indicator_id: str              # "A-1-1-08"
    name: str                      # "극초고음역 음정정확도"
    raw_value: float = 0.0         # 원시 측정값
    percentile: Optional[float] = None   # 백분위 (0-100), 기준DB 없으면 None
    tier: int = 1                  # 1=음향, 2=ML
    axis: str = ""                 # "A"/"B"/"C"
    category: str = ""             # "Pitch_Analysis"
    genius_level: Optional[str] = None   # "매우강함"/"강함"/"중간"/None
    confidence: float = 0.0        # 0~1
    measured: bool = False         # 측정 성공 여부
    error: str = ""                # 측정 실패 시 사유

@dataclass
class VocalVector100:
    """100차원 보컬 벡터 — 최종 분석 결과"""
    measurements: Dict[str, IndicatorMeasurement] = field(default_factory=dict)

    # 축별 극단값 (종합점수 아님 — 극단값 존재 여부만)
    axis_a_outliers: List[str] = field(default_factory=list)  # A축(기술적안정성) 극단값 IDs
    axis_b_outliers: List[str] = field(default_factory=list)  # B축(음색독창성) 극단값 IDs
    axis_c_outliers: List[str] = field(default_factory=list)  # C축(정서전달력) 극단값 IDs

    # 톤 프로파일 (기존 VocalProfile 연동)
    tone_quadrant: str = "unknown"
    tone_quadrant_ko: str = "미분류"
    brightness: float = 0.0
    weight: float = 0.0

    # 측정 통계
    total_measured: int = 0
    tier1_measured: int = 0
    tier2_measured: int = 0
    processing_time_sec: float = 0.0

    # OR 판정 결과
    has_any_outlier: bool = False
    outlier_summary: str = ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 100개 지표 레지스트리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INDICATOR_REGISTRY: Dict[str, IndicatorSpec] = {}

def _reg(id, name, axis, cat_major, cat_mid, algo, tier, reliability, genius, mvp, unit="", desc=""):
    INDICATOR_REGISTRY[id] = IndicatorSpec(
        id=id, name=name, axis=axis, category_major=cat_major,
        category_mid=cat_mid, algorithm=algo, tier=tier,
        reliability=reliability, genius_signal=genius, mvp=mvp,
        unit=unit, description=desc
    )

# ──────────────────────────────────────────────
# A축: 기술적 안정성
# ──────────────────────────────────────────────

# A-1: 음정정확도
_reg("A-1-1-08", "극초고음역(C6이상) 음정정확도", "A", "음정정확도", "안정성", "Pitch_Analysis", 1, "높음", "매우강함", False, "cent")
_reg("A-1-2-03", "지속음 안정성(10초이상)", "A", "음정정확도", "안정성", "Pitch_Analysis", 1, "높음", "매우강함", False, "cent")
_reg("A-1-2-09", "감정고조 시 안정성", "A", "음정정확도", "안정성", "Pitch_Analysis", 1, "높음", "매우강함", False, "cent")
_reg("A-1-2-10", "휘슬영역 안정성", "A", "음정정확도", "안정성", "Pitch_Analysis", 1, "높음", "매우강함", False, "cent")
_reg("A-1-3-05", "1.5옥타브이상 도약", "A", "음정정확도", "도약", "Pitch_Analysis", 1, "높음", "매우강함", False, "cent")
_reg("A-1-3-09", "연속도약 정확도", "A", "음정정확도", "도약", "Pitch_Analysis", 1, "높음", "매우강함", False, "cent")
_reg("A-2-5-06", "3옥타브이상 음역", "A", "음역대", "음역", "Voice_Range", 1, "높음", "매우강함", False, "semitone")
_reg("A-2-5-07", "4옥타브이상 음역", "A", "음역대", "음역", "Voice_Range", 1, "높음", "매우강함", False, "semitone")
_reg("A-5-1-07", "비브라토와 음정정확도 양립", "A", "표현기법", "비브라토", "Vibrato_Analysis", 1, "높음", "매우강함", False)
_reg("A-5-4-07", "ppp부터 fff까지 표현", "A", "다이내믹", "다이내믹", "Energy_Analysis", 1, "높음", "매우강함", False, "dB")
_reg("A-1-1-07", "초고음역(G5-C6) 음정정확도", "A", "음정정확도", "안정성", "Pitch_Analysis", 1, "높음", "강함", False, "cent")
_reg("A-1-1-10", "안정영역의 폭(반음단위)", "A", "음정정확도", "안정성", "Pitch_Analysis", 1, "높음", "강함", False, "semitone")
_reg("A-1-1-15", "이성 음역대 일부활용(GD/화사)", "A", "음정정확도", "안정성", "Pitch_Analysis", 1, "높음", "강함", False)
_reg("A-1-2-02", "지속음 안정성(5초이상)", "A", "음정정확도", "안정성", "Pitch_Analysis", 1, "높음", "강함", False, "cent")
_reg("A-1-2-14", "거친톤 사용 시 안정성", "A", "음정정확도", "안정성", "Pitch_Analysis", 1, "높음", "강함", False, "cent")
_reg("A-2-5-01", "최고 안정음역", "A", "음역대", "음역", "Voice_Range", 1, "높음", "강함", False, "Hz")
_reg("A-2-5-03", "음역대 폭(옥타브)", "A", "음역대", "음역", "Voice_Range", 1, "높음", "강함", False, "semitone")
_reg("A-2-5-08", "음역대 확장잠재력", "A", "음역대", "음역", "Voice_Range", 1, "높음", "강함", False)
_reg("A-2-5-10", "음역대 발성종류 다양성", "A", "음역대", "음역", "Voice_Range", 1, "높음", "강함", False)

# A-1-5: 미세통제 (Pitch Analysis 계속)
_reg("A-1-5-05", "벤딩(Bending) 통제", "A", "음정정확도", "미세통제", "Pitch_Analysis", 1, "높음", "매우강함", False)
_reg("A-1-5-06", "마이크로톤 인식(절대음감)", "A", "음정정확도", "미세통제", "Pitch_Analysis", 1, "높음", "매우강함", False)
_reg("A-1-5-07", "의도적 음정어긋남(Blues note)", "A", "음정정확도", "미세통제", "Pitch_Analysis", 1, "높음", "매우강함", False)

# A-1-6: 화성인식
_reg("A-1-6-03", "화성인식(화성/조성분석)", "A", "음정정확도", "화성인식", "ML_Harmonic", 2, "중간(ML가능)", "매우강함", False)
_reg("A-1-6-06", "비즈류음계 적응(블루스/5음계)", "A", "음정정확도", "화성인식", "ML_Harmonic", 2, "중간(ML가능)", "강함", False)
_reg("A-1-6-07", "절대음감 신호", "A", "음정정확도", "화성인식", "ML_Harmonic", 2, "중간(ML가능)", "매우강함", False)

# A-2: 발성
_reg("A-2-1-05", "발성종류변환정성(발성전환안정성)", "A", "발성", "발성", "ML_Voice_Classification", 2, "중간(ML가능)", "매우강함", False)
_reg("A-2-1-14", "발성종류변환정성(Yodel 전환 안정성)", "A", "발성", "발성", "ML_Voice_Classification", 2, "중간(ML가능)", "매우강함", False)

# A-5: 표현기법
_reg("A-5-2-03", "멜리스마 음정정확도", "A", "표현기법", "멜리스마", "ML_Expression", 2, "중간(ML가능)", "강함", False)
_reg("A-5-2-09", "복잡 멜리스마(7음이상)", "A", "표현기법", "멜리스마", "ML_Expression", 2, "중간(ML가능)", "매우강함", False)
_reg("A-5-2-11", "즉흥 멜리스마", "A", "표현기법", "멜리스마", "ML_Expression", 2, "중간(ML가능)", "매우강함", False)

# A-1-4: 회복력
_reg("A-1-4-02", "어긋난회복패턴(회복구간분석)", "A", "음정정확도", "회복력", "Pitch_Analysis", 1, "높음", "강함", False)
_reg("A-1-4-05", "회복의 인지가능성", "A", "음정정확도", "회복력", "Pitch_Analysis", 1, "높음", "강함", False)
_reg("A-1-4-07", "고난도구간 회복", "A", "음정정확도", "회복력", "Pitch_Analysis", 1, "높음", "강함", False)

# A-2-4: 신체적발성자산 (Formant)
_reg("A-2-4-01", "성대 안정성(포먼트추출+공명분석)", "A", "발성", "신체적발성자산", "Formant_Analysis", 1, "높음", "강함", False, "Hz")
_reg("A-2-4-02", "성대 두께(자연도)", "A", "발성", "신체적발성자산", "Formant_Analysis", 1, "높음", "강함", False)
_reg("A-2-4-07", "취약함 표현 통제", "A", "발성", "신체적발성자산", "Formant_Analysis", 1, "높음", "강함", False)

# A-5-4: 다이내믹/에너지
_reg("A-5-4-02", "에너지 다이내믹 레인지", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False, "dB")
_reg("A-5-4-05", "에너지 시계열 분석(RMS 시계열)", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-07b", "고해상도음정변화(RMS시계열→다이내믹레인지)", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-08", "고해상도다이내믹(감정에너지시계열)", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-09", "모멘트별 에너지 패턴분석", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-10", "소리세기 조절능력(에너지통제분석)", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-11", "시간별 에너지 안정성(RMS분산)", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-12", "에너지 패턴 반복성(자기상관)", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-13", "에너지 클라이맥스 구축력", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-14", "에너지 변화율(1차미분)", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-15", "에너지 가속도(2차미분)", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-16", "에너지 엔트로피(정보량)", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-17", "에너지 스펙트럼 대역별 분포", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)
_reg("A-5-4-18", "에너지 피크 간격 분석", "A", "다이내믹", "에너지", "Energy_Analysis", 1, "높음", "강함", False)

# A-5-1: 비브라토 (Vibrato Analysis)
_reg("A-5-1-03", "멜리스마 음정정확도(멜리스마구간분석)", "A", "표현기법", "비브라토", "Vibrato_Analysis", 1, "높음", "강함", False)
_reg("A-5-1-04", "비브라토 진폭/주기(진폭주기분석)", "A", "표현기법", "비브라토", "Vibrato_Analysis", 1, "높음", "강함", False)
_reg("A-5-1-05", "비브라토 안정성", "A", "표현기법", "비브라토", "Vibrato_Analysis", 1, "높음", "강함", False)
_reg("A-5-1-06", "시간별 음색 정체성(음색시간분석)", "A", "표현기법", "비브라토", "Vibrato_Analysis", 1, "높음", "강함", False)
_reg("A-5-1-08", "음색시간안정성(정보화 시 음색유지)", "A", "표현기법", "비브라토", "Vibrato_Analysis", 1, "높음", "강함", False)
_reg("A-5-1-09", "음색의 카멜레온능력(음색변환능력)", "A", "표현기법", "비브라토", "Vibrato_Analysis", 1, "높음", "강함", False)
_reg("A-5-1-10", "시간별 음색 정체성", "A", "표현기법", "비브라토", "Vibrato_Analysis", 1, "높음", "강함", False)

# ──────────────────────────────────────────────
# B축: 음색 독창성
# ──────────────────────────────────────────────

_reg("B-1-1-12", "스펙트럼 엔트로피", "B", "관건적음색특성", "스펙트럼특성", "Spectrum_Analysis", 1, "높음", "강함", True, "", "FFT/MFCC추출")
_reg("B-1-1-15", "주파수 분포 특이성", "B", "관건적음색특성", "스펙트럼특성", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-1-16", "스펙트럼 피크 고유성", "B", "관건적음색특성", "스펙트럼특성", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-2-06", "홀수배음 vs 짝수배음 비율", "B", "관건적음색특성", "배음구조", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-2-07", "배음 안정성", "B", "관건적음색특성", "배음구조", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-2-08", "배음 패턴 고유성", "B", "관건적음색특성", "배음구조", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-2-09", "고차배음 통제", "B", "관건적음색특성", "배음구조", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-2-11", "배음 전폭 패턴", "B", "관건적음색특성", "배음구조", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-2-12", "배음 위상관계", "B", "관건적음색특성", "배음구조", "Spectrum_Analysis", 1, "높음", "강함", True)

_reg("B-1-4-04", "음색시간안정성(음색시간분석)", "B", "관건적음색특성", "음색시간안정성", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-4-06", "음색시간안정성(정보화 시 음색유지)", "B", "관건적음색특성", "음색시간안정성", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-4-10", "시간별 음색 정체성", "B", "관건적음색특성", "음색시간안정성", "Spectrum_Analysis", 1, "높음", "강함", True)
_reg("B-1-5-12", "음색의 카멜레온능력", "B", "관건적음색특성", "음색변환능력", "ML_Voice_Classification", 2, "중간(ML가능)", "매우강함", False)

# B-3: K-POP 가수풀거리 / 음색고유성지표
_reg("B-3-1-06", "음색임베딩 공간 고립도", "B", "음색독창성", "인지거리", "ML_Embedding", 2, "중간(ML가능)", "매우강함", False)
_reg("B-3-1-11", "음색의 개인 ID 강도", "B", "음색독창성", "인지거리", "ML_Embedding", 2, "중간(ML가능)", "매우강함", False)
_reg("B-3-3-01", "음색고유성지표(ML고유성평가)", "B", "음색독창성", "고유성지표", "ML_Embedding", 2, "중간(ML가능)", "매우강함", False)
_reg("B-3-3-03", "음색 유사인물 빈도(낮을수록 천재)", "B", "음색독창성", "고유성지표", "ML_Embedding", 2, "중간(ML가능)", "매우강함", False)
_reg("B-3-3-05", "음색의 모방 어려움", "B", "음색독창성", "고유성지표", "ML_Embedding", 2, "중간(ML가능)", "매우강함", False)

# B-5: 기능적가치
_reg("B-5-1-01", "국내포지션적합도(컬링핏 적합도)", "B", "음색독창성", "기능적가치", "ML_Integrated", 2, "중간(ML가능)", "매우강함", False)

# ──────────────────────────────────────────────
# C축: 정서 전달력
# ──────────────────────────────────────────────

# C-1: 정서표현기술
_reg("C-1-1-08", "표현도구활용(호흡/음색 다이나믹 표현)", "C", "정서표현기술", "표현도구활용", "ML_Expression", 2, "중간(ML가능)", "매우강함", False)
_reg("C-1-1-02", "표현도구활용(효율적인 정서표현)", "C", "정서표현기술", "표현도구활용", "ML_Expression", 2, "중간(ML가능)", "매우강함", False)
_reg("C-1-1-03", "다이내믹통한 정서표현(다이내믹ML분석)", "C", "정서표현기술", "표현도구활용", "ML_Expression", 2, "중간(ML가능)", "매우강함", False)
_reg("C-1-4-05", "순간(0.1초) 정서표현(조미세표현분석)", "C", "정서표현기술", "표현미시통제", "ML_Expression", 2, "중간(ML가능)", "매우강함", False)
_reg("C-1-4-21", "미시 표현 전체 신호", "C", "정서표현기술", "표현미시통제", "ML_Expression", 2, "중간(ML가능)", "매우강함", False)
_reg("C-1-1-01", "표현도구활용(다종도구활용분석)", "C", "정서표현기술", "표현도구활용", "ML_Expression", 2, "중간(ML가능)", "강함", False)
_reg("C-1-1-04", "음색변화 매끄러움(음색변환분석)", "C", "정서표현기술", "표현도구활용", "ML_Expression", 2, "중간(ML가능)", "강함", False)

# C-2: 정서종류
_reg("C-2-1-14", "기초정서(취약함 표현)", "C", "정서전달력", "정서종류", "ML_Emotion", 2, "중간(ML가능)", "매우강함", False)
_reg("C-2-3-14", "미요정서(성숙한 슬픔)", "C", "정서전달력", "정서종류", "ML_Emotion", 2, "중간(ML가능)", "매우강함", False)

# C-3: 정서전환과정
_reg("C-3-2-02", "정서흐름(국·정서와 가창정서 정합성)", "C", "정서전달력", "정서전환과정", "ML_Authenticity", 2, "중간(ML가능)", "매우강함", False)
_reg("C-3-2-21", "정서흐름통합(정서국선+가사 매칭ML)", "C", "정서전달력", "정서전환과정", "ML_Authenticity", 2, "중간(ML가능)", "매우강함", False)

# C-4: 심화진정성
_reg("C-4-1-02", "기본진정성(흉내내는 정서 vs 진짜 정서)", "C", "정서전달력", "심화진정성", "ML_Authenticity", 2, "중간(ML가능)", "매우강함", False)
_reg("C-4-1-13", "기본진정성(정서의 청자공감 유발)", "C", "정서전달력", "심화진정성", "ML_Authenticity", 2, "중간(ML가능)", "매우강함", False)
_reg("C-4-2-02", "심화진정성(자기 노출의 용기(BTS사례))", "C", "정서전달력", "심화진정성", "ML_Authenticity", 2, "중간(ML가능)", "매우강함", False)
_reg("C-4-2-03", "취약함 노출 능력", "C", "정서전달력", "심화진정성", "ML_Authenticity", 2, "중간(ML가능)", "매우강함", False)

# C-1 추가: 정서표현기술 (Expression)
_reg("C-1-1-01b", "표현도구활용(흐름있는 정서표현)", "C", "정서표현기술", "표현도구활용", "ML_Expression", 2, "중간(ML가능)", "강함", False)
_reg("C-1-1-02b", "비브라토통한 정서표현(비브라토ML)", "C", "정서표현기술", "표현도구활용", "ML_Expression", 2, "중간(ML가능)", "강함", False)
_reg("C-1-1-04b", "음색변환통한 정서표현", "C", "정서표현기술", "표현도구활용", "ML_Expression", 2, "중간(ML가능)", "강함", False)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 유틸리티 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_tier1_indicators() -> Dict[str, IndicatorSpec]:
    """1계층(음향분석) 지표만 반환"""
    return {k: v for k, v in INDICATOR_REGISTRY.items() if v.tier == 1}

def get_tier2_indicators() -> Dict[str, IndicatorSpec]:
    """2계층(ML모델) 지표만 반환"""
    return {k: v for k, v in INDICATOR_REGISTRY.items() if v.tier == 2}

def get_mvp_indicators() -> Dict[str, IndicatorSpec]:
    """MVP 대상 지표만 반환"""
    return {k: v for k, v in INDICATOR_REGISTRY.items() if v.mvp}

def get_by_axis(axis: str) -> Dict[str, IndicatorSpec]:
    """축별 지표 반환 (A/B/C)"""
    return {k: v for k, v in INDICATOR_REGISTRY.items() if v.axis == axis}

def get_by_algorithm(algo: str) -> Dict[str, IndicatorSpec]:
    """알고리즘 카테고리별 지표 반환"""
    return {k: v for k, v in INDICATOR_REGISTRY.items() if v.algorithm == algo}

def get_genius_signal_indicators() -> Dict[str, IndicatorSpec]:
    """천재신호(매우강함) 지표만 반환"""
    return {k: v for k, v in INDICATOR_REGISTRY.items() if v.genius_signal == "매우강함"}

# 통계
TOTAL_INDICATORS = len(INDICATOR_REGISTRY)
TIER1_COUNT = len(get_tier1_indicators())
TIER2_COUNT = len(get_tier2_indicators())
