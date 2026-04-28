"""
idol_scout.screener
━━━━━━━━━━━━━━━━━━━
1단계 고유성 스크리닝 서브패키지

Public API:
- screen_url(url, content_type) — URL에서 스크리닝 실행
- screen_file(video_path, audio_path, content_type) — 로컬 파일 스크리닝
- print_screening_report(result) — 콘솔에 리포트 출력
- save_screening_report(result, output_dir) — JSON 리포트 저장
- print_comparison_table(results) — 복수 결과 비교 테이블
- ScreeningResult — 최종 결과 데이터 구조
"""

from .orchestrator import (
    screen_url,
    screen_file,
    print_screening_report,
    save_screening_report,
    print_comparison_table,
    ScreeningResult,
)

__all__ = [
    "screen_url",
    "screen_file",
    "print_screening_report",
    "save_screening_report",
    "print_comparison_table",
    "ScreeningResult",
]
