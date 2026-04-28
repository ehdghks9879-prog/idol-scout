"""
예제 2: 복수 영상 비교 스크리닝
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

여러 URL을 한 번에 분석하고 비교 테이블 출력.
"""

from idol_scout import compare

# ── 복수 URL 비교 ──────────────────────────────────────
urls = [
    "https://www.youtube.com/watch?v=K5fr2Y3wIPw",       # 보컬 1
    "https://www.instagram.com/p/CSGsN98JhMv/",          # 보컬 2
    "https://www.youtube.com/watch?v=7oEh1-QZVMY",       # 댄스 1
    "https://www.youtube.com/watch?v=kV2dw41uZ8c",       # 댄스 2
]

results = compare(urls, save=True)
# → 각각의 리포트 출력 후 비교 테이블 자동 출력
# → reports/ 디렉토리에 JSON 저장

# ── 통과 대상만 필터링 ─────────────────────────────────
passed = [r for r in results if r.passed]
print(f"\n{'='*40}")
print(f"통과: {len(passed)}/{len(results)}")
for r in passed:
    print(f"  • {r.title} (극단값={r.outlier_count}개)")

# ── 특정 지표 기준 정렬 ───────────────────────────────
print(f"\n음색 고유성(ID 1) 기준 정렬:")
sorted_by_timbre = sorted(
    results,
    key=lambda r: r.indicators[1].effective_score if r.indicators[1].measured else 0,
    reverse=True,
)
for i, r in enumerate(sorted_by_timbre):
    score = r.indicators[1].effective_score
    print(f"  {i+1}. {r.title[:30]}: {score:.3f}")
