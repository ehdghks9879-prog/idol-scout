#!/usr/bin/env python3
"""
idol_scout/cli.py
━━━━━━━━━━━━━━━━
커맨드라인 인터페이스 — `idol-screen` 명령어

설치 후 사용:
    idol-screen https://youtube.com/watch?v=...
    idol-screen --compare url1 url2 url3
    idol-screen --file video.mp4 --type dance
"""

import argparse
import sys

from .api import screen, screen_file, compare


def main():
    parser = argparse.ArgumentParser(
        description="AI 아이돌 발굴 시스템 — 1단계 고유성 스크리닝",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  idol-screen https://youtube.com/watch?v=...
  idol-screen --type dance --save https://youtube.com/watch?v=...
  idol-screen --compare url1 url2 url3
  idol-screen --file my_video.mp4 --type vocal
        """,
    )

    parser.add_argument("urls", nargs="*", help="분석할 영상 URL(들)")
    parser.add_argument("--file", "-f", type=str, help="로컬 영상 파일 경로")
    parser.add_argument("--audio", "-a", type=str, help="로컬 오디오 파일 경로")
    parser.add_argument("--type", "-t", choices=["vocal", "dance", "auto"],
                        default="auto", help="콘텐츠 유형 (기본: auto)")
    parser.add_argument("--compare", "-c", action="store_true", help="복수 비교 모드")
    parser.add_argument("--save", "-s", action="store_true", help="JSON 리포트 저장")
    parser.add_argument("--quiet", "-q", action="store_true", help="출력 최소화")

    args = parser.parse_args()

    if not args.urls and not args.file:
        parser.print_help()
        print("\n오류: URL 또는 --file을 지정하세요.")
        sys.exit(1)

    verbose = not args.quiet

    if args.file:
        result = screen_file(
            args.file, audio_path=args.audio,
            content_type=args.type, save=args.save, verbose=verbose,
        )
        return 0 if result.passed else 1

    if args.compare and len(args.urls) > 1:
        results = compare(
            args.urls, content_type=args.type,
            save=args.save, verbose=verbose,
        )
        passed = [r for r in results if r.passed]
        if verbose:
            print(f"\n📊 종합: {len(passed)}/{len(results)} 통과")
        return 0 if passed else 1

    # 단일 또는 순차 스크리닝
    any_passed = False
    for url in args.urls:
        result = screen(url, content_type=args.type, save=args.save, verbose=verbose)
        if result.passed:
            any_passed = True

    return 0 if any_passed else 1


if __name__ == "__main__":
    sys.exit(main())
