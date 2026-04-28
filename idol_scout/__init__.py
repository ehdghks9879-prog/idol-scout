"""
idol_scout — AI 아이돌 발굴 시스템
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"채점 기계가 아니라 장기 추적 시스템"
"가장 잘하는 사람이 아니라, 가장 다른 사람 + 가장 타고난 사람"

사용법:
    from idol_scout import screen, compare, analyze, screen_file

    # URL 스크리닝
    result = screen("https://youtube.com/watch?v=...")

    # 복수 비교
    results = compare([url1, url2, url3])

    # 로컬 파일
    result = screen_file("video.mp4", content_type="dance")

    # 전체 파이프라인 (100지표 + 11변수)
    profile = analyze(idol_name="홍길동", snapshots=[...])
"""

__version__ = "1.0.0"

from idol_scout.api import (
    screen,
    screen_file,
    compare,
    analyze,
    build_profile,
    diagnose,
    ScreeningResult,
    IdolProfile,
)

__all__ = [
    "screen",
    "screen_file",
    "compare",
    "analyze",
    "build_profile",
    "diagnose",
    "ScreeningResult",
    "IdolProfile",
]
