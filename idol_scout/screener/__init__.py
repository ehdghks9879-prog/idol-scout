"""
idol_scout.screener
━━━━━━━━━━━━━━━━━━━
1단계 고유성 스크리닝 서브패키지

Public API (v1 — 6지표):
- screen_url(url, content_type) — URL에서 스크리닝 실행
- screen_file(video_path, audio_path, content_type) — 로컬 파일 스크리닝
- print_screening_report(result) — 콘솔에 리포트 출력
- save_screening_report(result, output_dir) — JSON 리포트 저장
- print_comparison_table(results) — 복수 결과 비교 테이블
- ScreeningResult — 최종 결과 데이터 구조

v2 — 100차원 보컬 벡터:
- measure_tier1(audio_path, content_type) — tier-1 57개 지표 측정
- VocalVector100 — 100차원 결과 구조
- INDICATOR_REGISTRY — 100개 지표 레지스트리
"""

from .orchestrator import (
    screen_url,
    screen_file,
    print_screening_report,
    save_screening_report,
    print_comparison_table,
    ScreeningResult,
)

from .audio_v2 import measure_tier1
from .indicators_100 import INDICATOR_REGISTRY, VocalVector100, IndicatorMeasurement
from .normalizer import screen_vocal_100, VocalNormalizer, ReferenceDB

__all__ = [
    # v1 — 6지표
    "screen_url",
    "screen_file",
    "print_screening_report",
    "save_screening_report",
    "print_comparison_table",
    "ScreeningResult",
    # v2 — 100차원
    "measure_tier1",
    "screen_vocal_100",
    "VocalNormalizer",
    "ReferenceDB",
    "INDICATOR_REGISTRY",
    "VocalVector100",
    "IndicatorMeasurement",
]
