"""
예제 1: 기본 URL 스크리닝
━━━━━━━━━━━━━━━━━━━━━━━━

사전 준비:
    cd idol_scout
    pip install -e .
"""

from idol_scout import screen

# ── 단일 URL 스크리닝 ──────────────────────────────────
result = screen(
    "https://www.youtube.com/watch?v=K5fr2Y3wIPw",
    content_type="vocal",
)

# 결과 접근
print(f"통과 여부: {result.passed}")
print(f"극단값 차원 수: {result.outlier_count}개")
if result.outlier_dimensions:
    print(f"극단값 차원: {', '.join(result.outlier_dimensions)}")
print(f"최고 단일 차원: {result.max_single_score:.3f}")

# 개별 지표 접근
for iid, indicator in sorted(result.indicators.items()):
    if indicator.measured:
        print(f"  [{iid:3d}] {indicator.name}: "
              f"점수={indicator.score:.3f}, "
              f"신뢰도={indicator.confidence:.3f}, "
              f"유효={indicator.effective_score:.3f}")

# JSON으로 저장
if result.passed:
    print("\n✅ 통과 — 2단계 심층 분석 대상")
else:
    print("\n❌ 탈락 — 로그 기록 후 다음 대상으로")
