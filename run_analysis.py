"""
run_analysis.py — idol_scout 전체 파이프라인 실행 스크립트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

실행 방법:
    python run_analysis.py

파이프라인:
    1단계: URL → 자동 스크리닝 (6지표 측정)
    2단계: 스크리닝 결과 → 프로필 스냅샷 변환
    3단계: 프로필 생성 + 해석층 11변수 산출
    4단계: 복합지표 + NCPS/RNCS 실패구조 진단
    5단계: 종합 리포트 출력 + JSON 저장
"""

import json
from datetime import datetime
from pathlib import Path

from idol_scout import screen, build_profile, analyze, ScreeningResult
from idol_scout.api import screening_to_snapshot, quick_score
from idol_scout.models import Level, CDRSubScores, FailureType


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정: 여기만 수정하세요
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIG = {
    # ── 대상 정보 ──
    "url": "https://www.youtube.com/watch?v=7oEh1-QZVMY",
    "content_type": "dance",     # "vocal" | "dance" | "auto"

    # ── 프로필 기본 정보 ──
    "name": "",
    "name_en": "",
    "birth_year": 0,             # 알 수 없으면 0
    "debut_year": 0,             # 미데뷔면 0
    "group": "",
    "agency": "",

    # ── 수동 보충 지표 (선택사항) ──
    # 기획사 실무자가 합숙/면접에서 관찰한 값을 입력 (0.0 ~ 1.0)
    # 입력하지 않으면 자동 측정값만 사용
    "manual_scores": {
        # 3: 0.75,    # 음정 평균 편차
        # 26: 0.82,   # 동작-비트 싱크 정밀도
        # 35: 0.68,   # 자연 그루브
        # 38: 0.30,   # 훈련 흔적 비율 (낮을수록 타고남)
        # 99: 0.72,   # 천부적 비율
    },

    # ── 인간 관찰 변수 (3단계: 합숙/면접) ──
    # 각 항목은 Level 값 사용: LOWEST, LOW, MID_LOW, MID, MID_HIGH, HIGH, HIGHEST
    # 관찰하지 않은 항목은 주석 처리하면 기본값(MID) 적용
    "human_inputs": {
        "AAC": Level.MID,          # 자기 주도적 미적 선택
        "SCA": Level.MID,          # 자기 교정 민첩성
        "NVC": Level.MID,          # 비음악적 가치 전환
        "CCI": Level.MID,          # 문화 코드 통합력
        "CBP": Level.MID,          # 카테고리 경계 투과성
    },

    # ── CDR 하위 분화 (선택사항) ──
    "cdr_sub": CDRSubScores(
        cdr_a=Level.MID,           # 서사 발생 (선천적)
        cdr_b=Level.MID,           # 서사 설계 (학습 가능)
        cdr_c=Level.MID,           # 문화적 위치 설정
    ),

    # ── 실패 구조 맥락 (인간 판단) ──
    "failure_context": {
        "system_concealment": False,       # 시스템이 약점을 가리고 있나?
        "no_transition_prep": False,       # 전환 준비가 안 되어 있나?
        "system_supply_deficit": False,    # 시스템 콘텐츠 공급 부족?
        "non_musical_attention": False,    # 비음악적 요소로 주목 형성?
        "window_missed": False,            # 포지션 확립 윈도우 지남?
    },

    # ── 출력 설정 ──
    "save_report": True,
    "output_dir": "analysis_reports",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 전체 파이프라인 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_full_analysis(config: dict):
    """전체 분석 파이프라인 실행"""

    print("\n" + "=" * 60)
    print("  AI 아이돌 발굴 시스템 — 전체 분석 파이프라인")
    print("=" * 60)

    # ────────────────────────────────────────
    # Step 1: 1단계 자동 스크리닝
    # ────────────────────────────────────────
    print("\n[Step 1/5] 1단계 고유성 스크리닝")
    print("-" * 40)

    screening = screen(
        config["url"],
        content_type=config["content_type"],
        save=config["save_report"],
        verbose=True,
    )

    # ────────────────────────────────────────
    # Step 2: 스크리닝 결과 → 프로필 스냅샷 변환
    # ────────────────────────────────────────
    print("\n[Step 2/5] 스냅샷 변환 + 수동 지표 보충")
    print("-" * 40)

    timestamp = datetime.now().strftime("%Y-%m")
    snapshot = screening_to_snapshot(screening, timestamp)

    # 수동 보충 지표 추가
    for iid, value in config.get("manual_scores", {}).items():
        snapshot.scores[iid] = quick_score(iid, value)
        print(f"  + 수동 지표 [{iid:3d}]: {value:.3f}")

    measured = snapshot.measured_count
    print(f"  총 측정 지표: {measured}개 / 100개")

    # ────────────────────────────────────────
    # Step 3: 프로필 생성
    # ────────────────────────────────────────
    print("\n[Step 3/5] 프로필 생성")
    print("-" * 40)

    profile = build_profile(
        name=config["name"],
        name_en=config.get("name_en", ""),
        birth_year=config.get("birth_year", 0),
        debut_year=config.get("debut_year", 0),
        group=config.get("group", ""),
        agency=config.get("agency", ""),
        snapshots=[snapshot],
    )

    print(f"  이름: {profile.name} ({profile.name_en})")
    print(f"  데뷔: {'미데뷔' if profile.debut_year == 0 else profile.debut_year}")
    print(f"  소속: {profile.agency or '없음'} / {profile.group or '솔로'}")

    # ────────────────────────────────────────
    # Step 4: 전체 분석 (해석층 + 복합지표 + 실패진단)
    # ────────────────────────────────────────
    print("\n[Step 4/5] 해석층 + 복합지표 + 실패구조 진단")
    print("-" * 40)

    profile = analyze(
        profile,
        human_inputs=config.get("human_inputs"),
        cdr_sub=config.get("cdr_sub"),
        failure_context=config.get("failure_context"),
    )

    # ────────────────────────────────────────
    # Step 5: 종합 리포트 출력
    # ────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  종합 분석 리포트: {profile.name}")
    print("=" * 60)

    # 1단계 스크리닝 요약
    print(f"\n[1단계 스크리닝 결과]")

    if screening.multi_person_detected:
        print(f"\n  🚨 다인원 영상 감지! (추정 {screening.estimated_person_count}명)")
        print(f"     {screening.multi_person_notes}")
        print(f"     모든 지표가 무효화되었습니다. 1인 영상으로 재분석해 주세요.\n")

    print(f"  판정: {'통과' if screening.passed else '탈락'}")
    print(f"  극단값 차원 수: {screening.outlier_count}개")
    if screening.outlier_dimensions:
        print(f"  극단값 차원: {', '.join(screening.outlier_dimensions)}")
    print(f"  최고 단일 차원: {screening.max_single_score:.4f}")

    for iid, ind in sorted(screening.indicators.items()):
        status = "✓" if ind.measured else "-"
        print(f"  {status} [{iid:3d}] {ind.name}: "
              f"{ind.effective_score:.3f} "
              f"(원본={ind.score:.3f} × 신뢰={ind.confidence:.3f})")

    # 해석층 11변수
    print(f"\n[해석층 11변수]")
    if profile.interpret:
        var_names = {
            'SDI': '소리 차별화 지수',
            'EDT': '에너지 방향 유형',
            'CER': '핵심 감정 범위',
            'RMC': '리듬-움직임 일관성',
            'AAC': '자기주도 미적 선택',
            'SCA': '자기교정 민첩성',
            'CDR': '커리어 서사 밀도',
            'EDI': '노출 차별화 지수',
            'NVC': '비음악적 가치 전환',
            'CCI': '문화코드 통합력',
            'CBP': '카테고리 경계 투과성',
        }
        for attr, label in var_names.items():
            var = getattr(profile.interpret, attr.lower(), None)
            if var:
                print(f"  {attr}: {var.score:.3f} ({var.level.name:>8}) — {label}")
                if not var.ai_measurable:
                    print(f"        [인간 관찰 필요]")

    # 복합 지표
    print(f"\n[복합 지표]")
    if profile.composites:
        c = profile.composites
        print(f"  시스템 의존도:     {c.system_dependency:.3f}")
        print(f"  전환 준비도:       {c.transition_readiness:.3f}")
        print(f"  노출 전환 효율:    {c.exposure_conversion:.3f}")
        print(f"  자원 수렴도:       {c.resource_convergence:.3f}")
        print(f"  천부적 비율:       {c.innate_ratio:.3f}")
        print(f"  성장 궤적:         {c.growth_trajectory:.3f}")

    # 실패 구조 진단
    print(f"\n[실패 구조 진단]")
    if profile.failure_diag:
        fd = profile.failure_diag
        ft_label = {
            FailureType.NONE: "없음 (건강)",
            FailureType.NCPS: "NCPS (비핵심 포지션 고착 증후군)",
            FailureType.RNCS: "RNCS (자원 비수렴 증후군)",
            FailureType.MIXED: "복합 (NCPS + RNCS)",
        }
        print(f"  실패 유형: {ft_label.get(fd.failure_type, fd.failure_type.value)}")
        print(f"  위험 등급: {fd.risk_level}")

        if fd.ncps:
            print(f"\n  [NCPS 세부] {fd.ncps.conditions_met}/5 충족")
            print(f"    1. 단일차원 포지션:    {'■' if fd.ncps.cond1_single_dimension else '□'}")
            print(f"    2. CDR 결핍:           {'■' if fd.ncps.cond2_cdr_deficit else '□'}")
            print(f"    3. AAC 부족:           {'■' if fd.ncps.cond3_aac_low else '□'}")
            print(f"    4. 시스템 은폐:        {'■' if fd.ncps.cond4_system_concealment else '□'}")
            print(f"    5. 전환 미준비:        {'■' if fd.ncps.cond5_no_transition_prep else '□'}")

        if fd.rncs:
            print(f"\n  [RNCS 세부] {fd.rncs.conditions_met}/5 충족")
            print(f"    1. 프로필 분산:        {'■' if fd.rncs.cond1_dispersed_profile else '□'}")
            print(f"    2. 수렴 엔진 부재:     {'■' if fd.rncs.cond2_convergence_engine else '□'}")
            print(f"    3. 시스템 공급 부족:   {'■' if fd.rncs.cond3_system_supply else '□'}")
            print(f"    4. 비음악적 주목:      {'■' if fd.rncs.cond4_non_musical_attention else '□'}")
            print(f"    5. 윈도우 초과:        {'■' if fd.rncs.cond5_window_missed else '□'}")

    # JSON 저장
    if config.get("save_report"):
        _save_full_report(profile, screening, config)

    print("\n" + "=" * 60)
    print("  분석 완료")
    print("=" * 60 + "\n")

    return profile, screening


def _save_full_report(profile, screening, config):
    """분석 결과를 JSON으로 저장"""
    out_dir = Path(config.get("output_dir", "analysis_reports"))
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = profile.name.replace(" ", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = out_dir / f"analysis_{safe_name}_{ts}.json"

    report = {
        "meta": {
            "name": profile.name,
            "name_en": profile.name_en,
            "birth_year": profile.birth_year,
            "debut_year": profile.debut_year,
            "group": profile.group,
            "agency": profile.agency,
            "url": config["url"],
            "content_type": config["content_type"],
            "analysis_time": datetime.now().isoformat(),
        },
        "screening": {
            "passed": screening.passed,
            "max_single_score": round(screening.max_single_score, 4),
            "outlier_count": screening.outlier_count,
            "outlier_dimensions": screening.outlier_dimensions,
            "multi_person_detected": screening.multi_person_detected,
            "estimated_person_count": screening.estimated_person_count,
            "multi_person_method": screening.multi_person_method,
            "multi_person_notes": screening.multi_person_notes,
            "indicators": {
                str(iid): {
                    "name": ind.name,
                    "score": round(ind.score, 4),
                    "confidence": round(ind.confidence, 4),
                    "effective": round(ind.effective_score, 4),
                    "measured": ind.measured,
                }
                for iid, ind in sorted(screening.indicators.items())
            },
        },
        "interpret_11vars": {},
        "composites": {},
        "failure_diagnosis": {},
    }

    # 해석층
    if profile.interpret:
        for attr in ['sdi','edt','cer','rmc','aac','sca','cdr','edi','nvc','cci','cbp']:
            var = getattr(profile.interpret, attr, None)
            if var:
                report["interpret_11vars"][attr.upper()] = {
                    "score": round(var.score, 4),
                    "level": var.level.name,
                    "ai_measurable": var.ai_measurable,
                }

    # 복합지표
    if profile.composites:
        c = profile.composites
        report["composites"] = {
            "system_dependency": round(c.system_dependency, 4),
            "transition_readiness": round(c.transition_readiness, 4),
            "exposure_conversion": round(c.exposure_conversion, 4),
            "resource_convergence": round(c.resource_convergence, 4),
            "innate_ratio": round(c.innate_ratio, 4),
            "growth_trajectory": round(c.growth_trajectory, 4),
        }

    # 실패 진단
    if profile.failure_diag:
        fd = profile.failure_diag
        report["failure_diagnosis"] = {
            "failure_type": fd.failure_type.value,
            "risk_level": fd.risk_level,
            "ncps_conditions_met": fd.ncps.conditions_met if fd.ncps else 0,
            "rncs_conditions_met": fd.rncs.conditions_met if fd.rncs else 0,
        }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n  리포트 저장: {filepath}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    profile, screening = run_full_analysis(CONFIG)
