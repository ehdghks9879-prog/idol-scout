"""
idol_scout/api.py
━━━━━━━━━━━━━━━━
통합 공개 API — 외부에서 import하여 사용하는 주요 진입점

사용법:
    from idol_scout import screen, compare, screen_file, analyze

    # 1단계: URL 고유성 스크리닝
    result = screen("https://youtube.com/watch?v=...")
    print(result.passed)                    # True/False
    print(result.indicators[1].score)       # 음색 고유성 점수

    # 복수 비교
    results = compare(["url1", "url2"], content_type="dance")
    for r in results:
        print(r.title, r.outlier_count, r.passed)

    # 로컬 파일 스크리닝
    result = screen_file("video.mp4", content_type="vocal")

    # 2단계: 전체 프로필 분석 (100지표 + 11변수)
    profile = build_profile("홍길동", snapshots=[...])
    profile = analyze(profile, human_inputs={"AAC": Level.HIGH})
    print(profile.failure_diag.failure_type)   # NONE / NCPS / RNCS
"""

from typing import List, Dict, Optional, Union
from pathlib import Path

from .models import (
    IdolProfile, Snapshot, IndicatorScore, Level,
    CDRSubScores, InterpretProfile, CompositeMetrics,
    FailureDiagnosis, GrowthSlope,
)
from .engine import (
    screen_uniqueness,
    build_interpret_profile,
    compute_composites,
    diagnose_failure,
    compute_growth_slopes,
    run_full_pipeline,
)
from .screener import (
    screen_url as _screen_url,
    screen_file as _screen_file,
    print_screening_report,
    save_screening_report,
    print_comparison_table,
    ScreeningResult,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1단계: 고유성 스크리닝 API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def screen(url: str, *,
           content_type: str = "auto",
           save: bool = False,
           verbose: bool = True) -> ScreeningResult:
    """
    URL에서 1단계 고유성 스크리닝 실행.

    6개 지표(음색고유성, 음색판별력, 리듬인격, 동작식별도, 비주얼잔상, 표정시그니처)를
    자동 측정하여 통과/탈락을 판정합니다.

    Args:
        url: YouTube/Instagram 영상 URL
        content_type: "vocal" | "dance" | "auto" (자동 감지)
        save: True이면 JSON 리포트 자동 저장
        verbose: True이면 콘솔에 리포트 출력

    Returns:
        ScreeningResult: 6개 지표 점수 + 통과/탈락 판정

    Example:
        >>> result = screen("https://youtube.com/watch?v=...")
        >>> result.passed
        True
        >>> result.outlier_count
        2
        >>> result.indicators[1].score  # 음색 고유성
        0.671
    """
    result = _screen_url(url, content_type=content_type)
    if verbose:
        print_screening_report(result)
    if save:
        save_screening_report(result)
    return result


def screen_file(video_path: str, *,
                audio_path: str = None,
                content_type: str = "auto",
                save: bool = False,
                verbose: bool = True) -> ScreeningResult:
    """
    로컬 파일에서 1단계 고유성 스크리닝 실행.

    Args:
        video_path: MP4/WEBM 영상 파일 경로
        audio_path: WAV/MP3 오디오 파일 경로 (None이면 영상에서 추출)
        content_type: "vocal" | "dance" | "auto"
        save: JSON 리포트 저장 여부
        verbose: 콘솔 출력 여부

    Returns:
        ScreeningResult
    """
    result = _screen_file(video_path, audio_path=audio_path,
                          content_type=content_type)
    if verbose:
        print_screening_report(result)
    if save:
        save_screening_report(result)
    return result


def compare(urls: List[str], *,
            content_type: str = "auto",
            save: bool = False,
            verbose: bool = True) -> List[ScreeningResult]:
    """
    복수 URL을 스크리닝하여 비교.

    Args:
        urls: 영상 URL 리스트
        content_type: 전체에 적용할 콘텐츠 유형
        save: JSON 리포트 저장 여부
        verbose: 콘솔 출력 여부

    Returns:
        List[ScreeningResult]: 각 URL의 스크리닝 결과

    Example:
        >>> results = compare(["url1", "url2", "url3"])
        >>> passed = [r for r in results if r.passed]
        >>> print(f"{len(passed)}/{len(results)} 통과")
    """
    results = []
    for i, url in enumerate(urls):
        if verbose:
            print(f"\n[{i+1}/{len(urls)}] 스크리닝: {url}")
        result = _screen_url(url, content_type=content_type)
        if verbose:
            print_screening_report(result)
        if save:
            save_screening_report(result)
        results.append(result)

    if verbose and len(results) > 1:
        print_comparison_table(results)

    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2단계: 전체 프로필 분석 API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_profile(name: str, *,
                  name_en: str = "",
                  birth_year: int = 0,
                  debut_year: int = 0,
                  group: str = "",
                  agency: str = "",
                  snapshots: List[Snapshot] = None) -> IdolProfile:
    """
    아이돌 프로필 객체 생성.

    Args:
        name: 이름 (한글)
        name_en: 영문명
        birth_year: 출생년도
        debut_year: 데뷔년도
        group: 소속 그룹
        agency: 소속 기획사
        snapshots: 측정 스냅샷 리스트

    Returns:
        IdolProfile: 기본 정보가 채워진 프로필 (분석 미실행)

    Example:
        >>> profile = build_profile("홍길동", debut_year=2024, group="NexGen")
    """
    return IdolProfile(
        name=name,
        name_en=name_en,
        birth_year=birth_year,
        debut_year=debut_year,
        group=group,
        agency=agency,
        snapshots=snapshots or [],
    )


def analyze(profile: IdolProfile, *,
            human_inputs: Dict[str, Level] = None,
            cdr_sub: CDRSubScores = None,
            failure_context: dict = None) -> IdolProfile:
    """
    전체 파이프라인 실행: 해석층 구축 → 복합지표 → 실패진단 → 성장기울기.

    Args:
        profile: build_profile()로 생성한 프로필 (스냅샷 포함 필수)
        human_inputs: 인간 평가 변수 {"AAC": Level.HIGH, "SCA": Level.MID, ...}
        cdr_sub: CDR 하위 분화 (CDRSubScores)
        failure_context: NCPS/RNCS 진단용 맥락
            - system_concealment: bool (NCPS 조건4)
            - no_transition_prep: bool (NCPS 조건5)
            - system_supply_deficit: bool (RNCS 조건3)
            - non_musical_attention: bool (RNCS 조건4)
            - window_missed: bool (RNCS 조건5)

    Returns:
        IdolProfile: 해석·진단 결과가 채워진 프로필

    Example:
        >>> profile = analyze(profile, human_inputs={"AAC": Level.MID_LOW})
        >>> profile.failure_diag.failure_type
        FailureType.NCPS
        >>> profile.composites.system_dependency
        0.723
    """
    return run_full_pipeline(
        profile,
        human_inputs=human_inputs,
        cdr_sub=cdr_sub,
        failure_context=failure_context,
    )


def diagnose(profile: IdolProfile, **failure_context) -> FailureDiagnosis:
    """
    실패 구조(NCPS/RNCS) 진단만 단독 실행.

    Args:
        profile: 해석층이 구축된 프로필 (analyze() 실행 후)
        **failure_context: 인간 입력 맥락 변수

    Returns:
        FailureDiagnosis: 진단 결과

    Example:
        >>> diag = diagnose(profile, system_concealment=True)
        >>> diag.failure_type
        FailureType.NCPS
    """
    return diagnose_failure(profile.interpret, **failure_context)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 유틸리티: 스크리닝 결과 → 프로필 변환
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def screening_to_snapshot(result: ScreeningResult,
                          timestamp: str = None) -> Snapshot:
    """
    스크리닝 결과를 Snapshot으로 변환 (idol_scout_v1 모델과 연동).

    Args:
        result: screen() 또는 screen_file()의 결과
        timestamp: ISO 날짜 (기본: 현재)

    Returns:
        Snapshot: 100개 지표 중 6개가 채워진 스냅샷

    Example:
        >>> result = screen("https://...")
        >>> snapshot = screening_to_snapshot(result, "2026-Q2")
        >>> profile = build_profile("이름", snapshots=[snapshot])
    """
    from datetime import datetime
    ts = timestamp or datetime.now().strftime("%Y-Q%q" if False else "%Y-%m")

    snapshot = Snapshot(timestamp=ts, source=result.url)
    for iid, ir in result.indicators.items():
        if ir.measured:
            snapshot.scores[iid] = IndicatorScore(
                indicator_id=iid,
                normalized=ir.score,
                confidence=ir.confidence,
                measured=True,
            )
    return snapshot


def quick_score(indicator_id: int, value: float,
                confidence: float = 0.8) -> IndicatorScore:
    """
    빠른 IndicatorScore 생성 헬퍼.

    Example:
        >>> scores = {
        ...     1: quick_score(1, 0.9),      # 음색 고유성 0.9
        ...     36: quick_score(36, 0.7),     # 리듬 인격 0.7
        ... }
    """
    return IndicatorScore(
        indicator_id=indicator_id,
        normalized=value,
        confidence=confidence,
        measured=True,
    )
