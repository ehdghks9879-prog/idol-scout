"""
예제 3: 전체 파이프라인 — 스크리닝 → 프로필 → 진단
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1단계 스크리닝 통과 후 → 2단계 전체 프로필 분석까지의 흐름.
"""

from idol_scout import screen, build_profile, analyze, screen_file
from idol_scout.api import screening_to_snapshot, quick_score
from idol_scout.models import Level, CDRSubScores, Snapshot, IndicatorScore


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 1: 자동 스크리닝
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

screening_result = screen(
    "https://www.youtube.com/watch?v=...",
    content_type="dance",
    verbose=True,
)

if not screening_result.passed:
    print("1단계 탈락 — 분석 종료")
    exit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 2: 스크리닝 결과를 프로필로 변환
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 자동 스크리닝 결과 → 스냅샷 변환
snapshot_auto = screening_to_snapshot(screening_result, "2026-Q2")

# 추가 수동 측정 지표를 보충 (Tier 2, 3 지표)
# 예: 기획사 실무자가 합숙/면접에서 측정한 항목
snapshot_auto.scores[3] = quick_score(3, 0.75)    # 음정 평균 편차
snapshot_auto.scores[26] = quick_score(26, 0.82)  # 동작-비트 싱크 정밀도
snapshot_auto.scores[35] = quick_score(35, 0.68)  # 자연 그루브
snapshot_auto.scores[38] = quick_score(38, 0.30)  # 훈련 흔적 비율 (낮을수록 타고남)
snapshot_auto.scores[99] = quick_score(99, 0.72)  # 천부적 비율

# 프로필 생성
profile = build_profile(
    name="김신인",
    name_en="Kim Shinin",
    birth_year=2008,
    debut_year=0,  # 미데뷔
    group="",
    agency="",
    snapshots=[snapshot_auto],
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 3: 전체 분석 (인간 입력 포함)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 인간 관찰 변수 (3단계: 합숙/면접에서 파악)
human_inputs = {
    "AAC": Level.MID_HIGH,    # 자기 주도적 미적 선택
    "SCA": Level.MID,         # 자기 교정 민첩성
    "NVC": Level.MID_LOW,     # 비음악적 가치 전환
    "CCI": Level.LOW,         # 문화 코드 통합력
    "CBP": Level.MID,         # 카테고리 경계 투과성
}

# CDR 하위 분화 (인간 관찰)
cdr_sub = CDRSubScores(
    cdr_a=Level.MID_HIGH,     # 서사 발생 (선천적)
    cdr_b=Level.MID,          # 서사 설계 (학습 가능)
    cdr_c=Level.MID_LOW,      # 문화적 위치 설정
)

# 실패 구조 맥락 (인간 판단)
failure_context = {
    "system_concealment": False,       # 시스템이 약점을 가리고 있나?
    "no_transition_prep": False,       # 전환 준비가 안 되어 있나?
    "system_supply_deficit": False,    # 시스템 콘텐츠 공급 부족?
    "non_musical_attention": False,    # 비음악적 요소로 주목 형성?
    "window_missed": False,            # 포지션 확립 윈도우 지남?
}

# 분석 실행
profile = analyze(
    profile,
    human_inputs=human_inputs,
    cdr_sub=cdr_sub,
    failure_context=failure_context,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 4: 결과 확인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print(f"\n{'='*50}")
print(f"프로필: {profile.name}")
print(f"{'='*50}")

# 11변수
print("\n[해석층 11변수]")
for var_name, var in profile.interpret.to_dict().items():
    print(f"  {var_name}: {var:.3f}")

# 복합 지표
c = profile.composites
print(f"\n[복합 지표]")
print(f"  시스템 의존도: {c.system_dependency:.3f}")
print(f"  전환 준비도:   {c.transition_readiness:.3f}")
print(f"  노출 전환 효율: {c.exposure_conversion:.3f}")
print(f"  자원 수렴도:   {c.resource_convergence:.3f}")
print(f"  천부적 비율:   {c.innate_ratio:.3f}")

# 실패 진단
fd = profile.failure_diag
print(f"\n[실패 구조 진단]")
print(f"  유형: {fd.failure_type.value}")
print(f"  위험도: {fd.risk_level}")
print(f"  NCPS: {fd.ncps.conditions_met}/5 충족")
print(f"  RNCS: {fd.rncs.conditions_met}/5 충족")
