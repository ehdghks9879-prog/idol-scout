"""
idol_scout_v1/engine.py
━━━━━━━━━━━━━━━━━━━━━━
해석 엔진 — 100개 지표 → 11변수 해석, 복합 지표 산출, NCPS/RNCS 진단, 파이프라인
"""

from typing import List, Dict, Optional
import math

from .models import (
    IdolProfile, Snapshot, IndicatorScore, InterpretVar, InterpretProfile,
    CDRSubScores, CompositeMetrics, FailureDiagnosis, NCPSDiagnosis, RNCSDiagnosis,
    GrowthSlope, Level, FailureType, Category
)
from .indicators import REGISTRY, INTERPRET_MAPPING, UNIQUENESS_IDS, INNATE_MARKER_IDS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1단계: 고유성 스크리닝
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def screen_uniqueness(snapshot: Snapshot, threshold: float = 0.5) -> dict:
    """
    1단계 스크리닝: 고유성 지표 6개 (ID: 1, 2, 36, 50, 64, 83)

    Returns:
        {
            "pass": bool,
            "scores": {id: score},
            "avg_uniqueness": float,
            "top_unique": int (가장 높은 고유성 지표 ID),
            "reason": str
        }
    """
    scores = {}
    for uid in UNIQUENESS_IDS:
        s = snapshot.get(uid)
        scores[uid] = s.effective_score

    measured = {k: v for k, v in scores.items() if v > 0}

    if len(measured) < 2:
        return {
            "pass": False,
            "scores": scores,
            "avg_uniqueness": 0.0,
            "top_unique": 0,
            "reason": f"측정된 고유성 지표 부족 ({len(measured)}/6)"
        }

    avg = sum(measured.values()) / len(measured)

    # 통과 조건: 평균 고유성 >= threshold OR 단일 지표 >= 0.8 (극단적 돌출)
    any_extreme = any(v >= 0.8 for v in measured.values())
    passed = avg >= threshold or any_extreme

    top_id = max(measured, key=measured.get) if measured else 0

    return {
        "pass": passed,
        "scores": scores,
        "avg_uniqueness": round(avg, 3),
        "top_unique": top_id,
        "reason": "통과" if passed else f"평균 고유성 {avg:.3f} < {threshold}"
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2단계: 100지표 → 11변수 해석
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compute_interpret_var(var_name: str, snapshot: Snapshot,
                          human_override: Optional[Level] = None) -> InterpretVar:
    """
    측정층 지표 → 해석층 변수 하나 산출

    AI 측정 불가 변수(AAC, SCA, NVC, CCI, CBP)는 human_override 필수.
    """
    indicator_ids = INTERPRET_MAPPING.get(var_name, [])
    ai_measurable = len(indicator_ids) > 0

    if human_override is not None:
        return InterpretVar(
            name=var_name,
            level=human_override,
            score=human_override.score,
            source_indicators=indicator_ids,
            ai_measurable=ai_measurable,
            notes="인간 평가 입력" if not ai_measurable else "인간 오버라이드"
        )

    if not ai_measurable:
        return InterpretVar(
            name=var_name,
            level=Level.MID,
            score=Level.MID.score,
            source_indicators=[],
            ai_measurable=False,
            notes="AI 측정 불가 — 인간 입력 필요"
        )

    # ★ 회사 헌법: 종합 점수/합산/가중평균 금지
    # 매핑된 지표 중 가장 극단적인 값을 대표값으로 사용 (OR 논리)
    measured_scores = []
    for iid in indicator_ids:
        s = snapshot.get(iid)
        if s.measured:
            measured_scores.append(s.normalized if s.normalized is not None else 0.0)

    if not measured_scores:
        return InterpretVar(
            name=var_name, level=Level.MID, score=0.5,
            source_indicators=indicator_ids, ai_measurable=True,
            notes="매핑 지표 중 측정된 것 없음"
        )

    # 가장 극단적인 값 = 평균에서 가장 멀리 떨어진 값
    # 오른쪽 꼬리(높은 값)와 왼쪽 꼬리(낮은 값) 모두 고려
    max_score = max(measured_scores)
    min_score = min(measured_scores)
    # 0.5(중앙)에서 가장 먼 쪽을 대표값으로 선택
    if abs(max_score - 0.5) >= abs(min_score - 0.5):
        representative = max_score
    else:
        representative = min_score

    level = Level.from_score(representative)

    return InterpretVar(
        name=var_name, level=level, score=round(representative, 3),
        source_indicators=indicator_ids, ai_measurable=True
    )


def compute_cdr_special(snapshot: Snapshot,
                         human_cdr_a: Optional[Level] = None,
                         human_cdr_b: Optional[Level] = None,
                         human_cdr_c: Optional[Level] = None) -> InterpretVar:
    """
    CDR은 고유성 지표 조합 희소성으로 산출.
    CDR-a, CDR-c는 인간 입력 필수. CDR-b는 부분 관찰 가능.
    """
    # 고유성 지표 조합으로 기본 CDR 산출
    uniqueness_scores = []
    for uid in UNIQUENESS_IDS:
        s = snapshot.get(uid)
        if s.measured:
            uniqueness_scores.append(s.effective_score)

    if uniqueness_scores:
        # 교차 조합 희소성: 개별 고유성의 기하평균
        product = 1.0
        for v in uniqueness_scores:
            product *= max(0.01, v)
        base_cdr = product ** (1 / len(uniqueness_scores))
    else:
        base_cdr = 0.5

    # 인간 입력으로 보정
    if human_cdr_a or human_cdr_b or human_cdr_c:
        human_scores = []
        if human_cdr_a: human_scores.append(human_cdr_a.score)
        if human_cdr_b: human_scores.append(human_cdr_b.score)
        if human_cdr_c: human_scores.append(human_cdr_c.score)
        human_avg = sum(human_scores) / len(human_scores)
        # AI 산출과 인간 입력의 가중 결합 (인간 70%, AI 30%)
        final_cdr = human_avg * 0.7 + base_cdr * 0.3
    else:
        final_cdr = base_cdr

    level = Level.from_score(final_cdr)

    return InterpretVar(
        name="CDR", level=level, score=round(final_cdr, 3),
        source_indicators=UNIQUENESS_IDS,
        ai_measurable=True,  # 부분적
        notes=f"AI기반={base_cdr:.3f}, 인간보정={'있음' if human_cdr_a else '없음'}"
    )


def build_interpret_profile(snapshot: Snapshot,
                             human_inputs: Dict[str, Level] = None,
                             cdr_sub: CDRSubScores = None) -> InterpretProfile:
    """전체 11변수 해석 프로필 구축"""
    h = human_inputs or {}
    profile = InterpretProfile()

    for var_name in ['sdi', 'edt', 'cer', 'rmc', 'aac', 'sca', 'edi', 'nvc', 'cci', 'cbp']:
        override = h.get(var_name.upper())
        setattr(profile, var_name,
                compute_interpret_var(var_name.upper(), snapshot, override))

    # CDR 특별 처리
    cdr_s = cdr_sub or CDRSubScores()
    profile.cdr = compute_cdr_special(
        snapshot,
        human_cdr_a=cdr_s.cdr_a if cdr_sub else None,
        human_cdr_b=cdr_s.cdr_b if cdr_sub else None,
        human_cdr_c=cdr_s.cdr_c if cdr_sub else None,
    )
    profile.cdr_sub = cdr_s

    return profile


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 복합 지표 산출
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compute_composites(profile: InterpretProfile, snapshot: Snapshot) -> CompositeMetrics:
    """해석층 프로필에서 복합 지표 산출"""
    p = profile.to_dict()
    aac = p.get("AAC", 0.5)
    cdr = p.get("CDR", 0.5)
    nvc = p.get("NVC", 0.5)
    sdi = p.get("SDI", 0.5)
    edi = p.get("EDI", 0.5)
    cer = p.get("CER", 0.5)

    # 시스템 의존 계수: 1 - (AAC × CDR × NVC) / max
    max_product = 1.0
    system_dep = 1.0 - (aac * cdr * nvc) / max_product

    # 전환 준비도 (4요소 평균)
    transition = (aac + cdr + nvc + sdi) / 4

    # 노출 전환 효율
    exposure = sdi * edi * cdr * cer * aac
    # 5개 곱이므로 0~1 범위이나 매우 작음, 5제곱근으로 정규화
    exposure_norm = exposure ** 0.2

    # 자원 수렴도 (분산의 역수 — 모든 변수가 고르면 높음)
    scores = list(p.values())
    if scores:
        mean_s = sum(scores) / len(scores)
        variance = sum((s - mean_s) ** 2 for s in scores) / len(scores)
        # 수렴도: 분산이 낮고 평균이 높을수록 좋음
        resource_conv = mean_s * (1 - min(1, math.sqrt(variance) * 3))
    else:
        resource_conv = 0.0

    # 천부적 비율 (지표 99번)
    innate_score = snapshot.get(99)
    innate_ratio = innate_score.effective_score if innate_score.measured else 0.5

    # 성장 궤적 (지표 100번)
    growth_score = snapshot.get(100)
    growth_traj = growth_score.effective_score if growth_score.measured else 0.0

    return CompositeMetrics(
        system_dependency=round(system_dep, 3),
        transition_readiness=round(transition, 3),
        exposure_conversion=round(exposure_norm, 3),
        resource_convergence=round(resource_conv, 3),
        innate_ratio=round(innate_ratio, 3),
        growth_trajectory=round(growth_traj, 3),
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NCPS / RNCS 진단
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def diagnose_ncps(profile: InterpretProfile,
                   system_concealment: bool = False,
                   no_transition_prep: bool = False) -> NCPSDiagnosis:
    """NCPS 5개 필요조건 점검"""
    p = profile.to_dict()

    # 조건1: 역량 1~2개 차원 편중
    # 판정: 최고 변수와 나머지 평균의 차이가 크면 편중
    scores = list(p.values())
    if scores:
        max_s = max(scores)
        others = [s for s in scores if s != max_s]
        avg_others = sum(others) / len(others) if others else 0
        cond1 = (max_s - avg_others) > 0.25  # 차이 > 0.25면 편중
    else:
        cond1 = False

    # 조건2: CDR-a/b/c 중 2개+ 임계치 이하
    cdr_sub = profile.cdr_sub
    low_cdr_count = sum(1 for lvl in [cdr_sub.cdr_a, cdr_sub.cdr_b, cdr_sub.cdr_c]
                        if lvl.value <= Level.MID_LOW.value)
    cond2 = low_cdr_count >= 2

    # 조건3: AAC 중간-하 이하
    aac_level = profile.aac.level if profile.aac else Level.MID
    cond3 = aac_level.value <= Level.MID_LOW.value

    # 조건4, 5: 인간 입력 (시스템 은폐, 전환 준비 미실행)
    cond4 = system_concealment
    cond5 = no_transition_prep

    return NCPSDiagnosis(
        cond1_single_dimension=cond1,
        cond2_cdr_deficit=cond2,
        cond3_aac_low=cond3,
        cond4_system_concealment=cond4,
        cond5_no_transition_prep=cond5,
    )


def diagnose_rncs(profile: InterpretProfile,
                   system_supply_deficit: bool = False,
                   non_musical_attention: bool = False,
                   window_missed: bool = False) -> RNCSDiagnosis:
    """RNCS 5개 필요조건 점검"""
    p = profile.to_dict()
    scores = list(p.values())

    # 조건1: 비돌출 분산 프로필
    # 판정: 최고 변수가 '상' 미만이고, 표준편차가 작으면 비돌출 분산
    if scores:
        max_s = max(scores)
        mean_s = sum(scores) / len(scores)
        std = math.sqrt(sum((s - mean_s) ** 2 for s in scores) / len(scores))
        cond1 = max_s < Level.HIGH.score and std < 0.15
    else:
        cond1 = False

    # 조건2: 수렴 엔진 불충분 (AAC × CDR-b < 임계치)
    aac_score = p.get("AAC", 0.5)
    cdr_b_score = profile.cdr_sub.cdr_b.score
    convergence_engine = aac_score * cdr_b_score
    cond2 = convergence_engine < 0.2  # 임계치

    # 조건3~5: 인간 입력
    cond3 = system_supply_deficit
    cond4 = non_musical_attention
    cond5 = window_missed

    return RNCSDiagnosis(
        cond1_dispersed_profile=cond1,
        cond2_convergence_engine=cond2,
        cond3_system_supply=cond3,
        cond4_non_musical_attention=cond4,
        cond5_window_missed=cond5,
    )


def diagnose_failure(profile: InterpretProfile, **kwargs) -> FailureDiagnosis:
    """통합 실패 구조 진단"""
    ncps = diagnose_ncps(
        profile,
        system_concealment=kwargs.get("system_concealment", False),
        no_transition_prep=kwargs.get("no_transition_prep", False),
    )
    rncs = diagnose_rncs(
        profile,
        system_supply_deficit=kwargs.get("system_supply_deficit", False),
        non_musical_attention=kwargs.get("non_musical_attention", False),
        window_missed=kwargs.get("window_missed", False),
    )
    return FailureDiagnosis(ncps=ncps, rncs=rncs)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 성장 기울기 계산
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compute_growth_slopes(snapshots: List[Snapshot]) -> Dict[int, GrowthSlope]:
    """복수 시점 스냅샷에서 지표별 성장 기울기 산출"""
    if len(snapshots) < 2:
        return {}

    slopes = {}
    n = len(snapshots)

    for iid in range(1, 101):
        points = []
        for t_idx, snap in enumerate(snapshots):
            s = snap.get(iid)
            if s.measured and s.normalized is not None:
                points.append((t_idx, s.normalized))

        if len(points) < 2:
            continue

        # 단순 선형 회귀
        x_mean = sum(p[0] for p in points) / len(points)
        y_mean = sum(p[1] for p in points) / len(points)

        numerator = sum((p[0] - x_mean) * (p[1] - y_mean) for p in points)
        denominator = sum((p[0] - x_mean) ** 2 for p in points)

        if denominator == 0:
            continue

        slope = numerator / denominator

        # R² 계산
        ss_res = sum((p[1] - (y_mean + slope * (p[0] - x_mean))) ** 2 for p in points)
        ss_tot = sum((p[1] - y_mean) ** 2 for p in points)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # 트렌드 판정
        if len(points) >= 3:
            first_half = points[:len(points)//2]
            second_half = points[len(points)//2:]
            first_slope = (first_half[-1][1] - first_half[0][1]) / max(1, first_half[-1][0] - first_half[0][0])
            second_slope = (second_half[-1][1] - second_half[0][1]) / max(1, second_half[-1][0] - second_half[0][0])
            if second_slope > first_slope * 1.2:
                trend = "accelerating"
            elif second_slope < first_slope * 0.5:
                trend = "decelerating"
            elif abs(slope) < 0.01:
                trend = "plateau"
            else:
                trend = "linear"
        else:
            trend = "linear"

        slopes[iid] = GrowthSlope(
            indicator_id=iid,
            slope_per_quarter=round(slope, 4),
            r_squared=round(r_squared, 3),
            data_points=len(points),
            trend=trend,
        )

    return slopes


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 전체 파이프라인 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_full_pipeline(idol: IdolProfile,
                       human_inputs: Dict[str, Level] = None,
                       cdr_sub: CDRSubScores = None,
                       failure_context: dict = None) -> IdolProfile:
    """
    전체 파이프라인 실행:
    1단계 스크리닝 → 2단계 해석 → 복합지표 → 실패진단 → 성장기울기

    Args:
        idol: 기본 정보 + 스냅샷이 입력된 프로필
        human_inputs: 3단계 인간 변수 입력 {"AAC": Level.MID_LOW, ...}
        cdr_sub: CDR 하위 분화 점수
        failure_context: NCPS/RNCS 진단용 맥락 정보

    Returns:
        해석·진단 결과가 채워진 IdolProfile
    """
    fc = failure_context or {}

    # 최신 스냅샷 기준
    if not idol.snapshots:
        return idol

    latest = idol.latest_snapshot

    # Step 1: 고유성 스크리닝
    screening = screen_uniqueness(latest)
    # (스크리닝 결과는 참고용, 기존 사례 검증에서는 무시하고 진행)

    # Step 2: 해석층 구축
    idol.interpret = build_interpret_profile(latest, human_inputs, cdr_sub)

    # Step 3: 복합 지표
    idol.composites = compute_composites(idol.interpret, latest)

    # Step 4: 실패 구조 진단
    idol.failure_diag = diagnose_failure(idol.interpret, **fc)

    # Step 5: 성장 기울기 (복수 스냅샷이 있을 경우)
    if len(idol.snapshots) >= 2:
        idol.growth_slopes = compute_growth_slopes(idol.snapshots)

    return idol
