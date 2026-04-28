"""idol_screener/screener.py — 1단계 고유성 스크리닝 오케스트레이터"""
import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from datetime import datetime
from .config import (UNIQUENESS_INDICATORS, OUTLIER_THRESHOLD, OUTLIER_LOW_THRESHOLD, REPORT_DIR)
from .downloader import download_video, DownloadResult
from .audio import analyze_audio, AudioAnalysisResult
from .video import analyze_video, VideoAnalysisResult, MultiPersonInfo

@dataclass
class IndicatorResult:
    """단일 지표 결과"""
    indicator_id: int
    name: str
    score: float = 0.0
    confidence: float = 0.0
    effective_score: float = 0.0
    measured: bool = False
    notes: str = ""

@dataclass
class ScreeningResult:
    """1단계 고유성 스크리닝 최종 결과"""
    url: str = ""
    title: str = ""
    uploader: str = ""
    content_type: str = ""
    indicators: Dict[int, IndicatorResult] = field(default_factory=dict)
    passed: bool = False
    max_single_score: float = 0.0
    outlier_count: int = 0
    outlier_dimensions: List[str] = field(default_factory=list)
    pass_reason: str = ""
    timestamp: str = ""
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    multi_person_detected: bool = False
    estimated_person_count: int = 1
    multi_person_method: str = ""
    multi_person_notes: str = ""

    def to_dict(self) -> dict:
        d = {"url": self.url, "title": self.title, "uploader": self.uploader, "content_type": self.content_type,
            "passed": self.passed, "max_single_score": round(self.max_single_score, 4),
            "outlier_count": self.outlier_count, "outlier_dimensions": self.outlier_dimensions,
            "pass_reason": self.pass_reason, "timestamp": self.timestamp, "processing_time": round(self.processing_time, 1),
            "indicators": {}, "errors": self.errors, "warnings": self.warnings,
            "multi_person_detected": self.multi_person_detected,
            "estimated_person_count": self.estimated_person_count,
            "multi_person_method": self.multi_person_method,
            "multi_person_notes": self.multi_person_notes}
        for iid, ir in self.indicators.items():
            d["indicators"][str(iid)] = {"name": ir.name, "score": round(ir.score, 4), "confidence": round(ir.confidence, 4),
                "effective_score": round(ir.effective_score, 4), "measured": ir.measured, "notes": ir.notes}
        return d

def screen_url(url: str, content_type: str = "auto") -> ScreeningResult:
    start_time = time.time()
    result = ScreeningResult(url=url, timestamp=datetime.now().isoformat())
    for iid, name in UNIQUENESS_INDICATORS.items():
        result.indicators[iid] = IndicatorResult(indicator_id=iid, name=name)
    print(f"\n{'='*60}\n[다운로드] {url}")
    dl = download_video(url)
    if not dl.success:
        result.errors.append(f"다운로드 실패: {dl.error}")
        result.processing_time = time.time() - start_time
        return result
    result.title = dl.title
    result.uploader = dl.uploader
    if content_type == "auto":
        content_type = _detect_content_type(dl.title)
    result.content_type = content_type
    print(f"  제목: {dl.title}\n  길이: {dl.duration:.0f}초\n  유형: {content_type}")
    audio_result = None
    if dl.audio_path and dl.audio_path.exists():
        print(f"\n[오디오 분석] {dl.audio_path.name}")
        audio_type = "vocal_video" if content_type == "vocal" else "dance_video"
        audio_result = analyze_audio(dl.audio_path, content_type=audio_type)
        if audio_result.error:
            result.warnings.append(f"오디오 분석 경고: {audio_result.error}")
        else:
            _map_audio_to_indicators(result, audio_result, content_type)
    else:
        result.warnings.append("오디오 파일 미생성 — 보컬 지표 미측정")
    video_result = None
    if dl.video_path and dl.video_path.exists():
        print(f"\n[영상 분석] {dl.video_path.name}")
        video_type = "dance_video" if content_type == "dance" else "face_video"
        video_result = analyze_video(dl.video_path, content_type=video_type)
        if video_result.error:
            result.warnings.append(f"영상 분석 경고: {video_result.error}")
        else:
            # ── 다인원 감지 결과 반영 ──
            mp_info = video_result.multi_person
            result.multi_person_detected = mp_info.multi_person_detected
            result.estimated_person_count = mp_info.estimated_person_count
            result.multi_person_method = mp_info.detection_method
            result.multi_person_notes = mp_info.notes

            if mp_info.multi_person_detected:
                _invalidate_all_indicators(result, mp_info)
            else:
                _map_video_to_indicators(result, video_result)
    else:
        result.warnings.append("영상 파일 미생성 — 영상 지표 미측정")
    _evaluate_pass_fail(result)
    result.processing_time = time.time() - start_time
    return result

def screen_file(video_path: str, audio_path: str = None, content_type: str = "auto") -> ScreeningResult:
    start_time = time.time()
    result = ScreeningResult(url=f"file://{video_path}", title=Path(video_path).stem, timestamp=datetime.now().isoformat())
    for iid, name in UNIQUENESS_INDICATORS.items():
        result.indicators[iid] = IndicatorResult(indicator_id=iid, name=name)
    video_p = Path(video_path)
    if not video_p.exists():
        result.errors.append(f"파일 없음: {video_path}")
        return result
    if content_type == "auto":
        content_type = _detect_content_type(video_p.name)
    result.content_type = content_type
    if audio_path:
        audio_p = Path(audio_path)
    else:
        audio_p = _extract_audio_from_video(video_p)
    if audio_p and audio_p.exists():
        audio_type = "vocal_video" if content_type == "vocal" else "dance_video"
        audio_result = analyze_audio(audio_p, content_type=audio_type)
        if not audio_result.error:
            _map_audio_to_indicators(result, audio_result, content_type)
        else:
            result.warnings.append(f"오디오 분석 경고: {audio_result.error}")
    video_type = "dance_video" if content_type == "dance" else "face_video"
    video_result = analyze_video(video_p, content_type=video_type)
    if not video_result.error:
        # ── 다인원 감지 결과 반영 ──
        mp_info = video_result.multi_person
        result.multi_person_detected = mp_info.multi_person_detected
        result.estimated_person_count = mp_info.estimated_person_count
        result.multi_person_method = mp_info.detection_method
        result.multi_person_notes = mp_info.notes

        if mp_info.multi_person_detected:
            _invalidate_all_indicators(result, mp_info)
        else:
            _map_video_to_indicators(result, video_result)
    else:
        result.warnings.append(f"영상 분석 경고: {video_result.error}")
    _evaluate_pass_fail(result)
    result.processing_time = time.time() - start_time
    return result

def _map_audio_to_indicators(result: ScreeningResult, audio: AudioAnalysisResult, content_type: str):
    t = audio.timbre
    r = audio.rhythm

    # ── 댄스 영상에서 보컬 미감지 시 음색 지표 비활성화 ──
    # 댄스 영상은 배경 음악(MR)만 나오는 경우가 대부분.
    # 보컬이 감지되지 않으면 음색 분석은 MR을 측정한 것이므로 무효.
    is_dance = (content_type == "dance")
    vocals_detected = audio.has_vocals

    if is_dance and not vocals_detected:
        # 음색 지표 1, 2는 측정하지 않음 — MR만 있으므로
        result.indicators[1].measured = False
        result.indicators[1].score = 0.0
        result.indicators[1].notes = "댄스 영상에서 사람 목소리 미감지 — 배경 음악만 분석됨 (음색 측정 불가)"
        result.indicators[2].measured = False
        result.indicators[2].score = 0.0
        result.indicators[2].notes = "댄스 영상에서 사람 목소리 미감지 — 배경 음악만 분석됨 (음색 측정 불가)"
        result.warnings.append("댄스 영상에서 사람 목소리가 감지되지 않아 음색 지표(1, 2)를 비활성화했습니다. 음색 분석은 보컬 영상으로 해주세요.")
    else:
        # 보컬 영상이거나, 댄스 영상이라도 보컬이 감지된 경우
        if t.uniqueness_confidence > 0:
            ir = result.indicators[1]
            ir.score = t.uniqueness_score
            ir.confidence = t.uniqueness_confidence
            ir.effective_score = ir.score * ir.confidence
            ir.measured = True
            ir.notes = f"MFCC분산={float(t.mfcc_std.mean()):.1f}, 스펙트럼평탄도={t.spectral_flatness_mean:.4f}"
            if is_dance:
                ir.notes += " [댄스 영상 — 보컬 감지됨, 참고 수준]"
        if t.identifiability_confidence > 0:
            ir = result.indicators[2]
            ir.score = t.identifiability_score
            ir.confidence = t.identifiability_confidence
            ir.effective_score = ir.score * ir.confidence
            ir.measured = True
            ir.notes = t.notes if t.notes else "세그먼트 간 MFCC 자기유사도 기반"
            if is_dance:
                ir.notes += " [댄스 영상 — 보컬 감지됨, 참고 수준]"

    # 리듬 인격(36)은 타악기 기반 분석이므로 보컬 유무와 무관하게 유지
    if r.rhythm_confidence > 0:
        ir = result.indicators[36]
        ir.score = r.rhythm_score
        ir.confidence = r.rhythm_confidence
        ir.effective_score = ir.score * ir.confidence
        ir.measured = True
        ir.notes = (f"유형={r.personality}, 오프셋={r.mean_onset_offset_ms:+.1f}ms, "
                    f"일관성={r.consistency:.2f}, BPM={r.tempo:.0f}")
    if content_type == "vocal" and r.rhythm_confidence > 0:
        result.indicators[36].notes += " [보컬 영상 — 리듬 분석 보조적]"

def _invalidate_all_indicators(result: ScreeningResult, mp_info: MultiPersonInfo):
    """다인원 영상 감지 시 — 모든 지표를 무효화하고 경고 추가"""
    method_desc = "동시 등장" if mp_info.detection_method == "simultaneous" else "교차 등장"
    warning_msg = (f"⚠️ 다인원 영상 감지 ({method_desc}, 추정 {mp_info.estimated_person_count}명) — "
                   f"개인 분석 결과를 신뢰할 수 없습니다. 1인 영상으로 다시 분석해 주세요.")
    result.warnings.insert(0, warning_msg)

    # 이미 측정된 오디오 지표도 무효화 (여러 사람 목소리가 섞였을 수 있음)
    for iid, ir in result.indicators.items():
        if ir.measured:
            ir.measured = False
            ir.score = 0.0
            ir.effective_score = 0.0
            ir.notes = f"다인원 영상 감지로 무효화됨 — {method_desc}, 추정 {mp_info.estimated_person_count}명"


def _map_video_to_indicators(result: ScreeningResult, video: VideoAnalysisResult):
    m = video.movement
    v = video.visual
    e = video.expression
    if m.identity_confidence > 0:
        ir = result.indicators[50]
        ir.score = m.identity_score
        ir.confidence = m.identity_confidence
        ir.effective_score = ir.score * ir.confidence
        ir.measured = True
        ir.notes = (f"엔트로피={m.joint_angle_entropy:.2f}, ROM={m.range_of_motion:.2f}, "
                    f"복잡도={m.movement_complexity:.2f}")
        if m.notes:
            ir.notes = m.notes
    if v.afterimage_confidence > 0:
        ir = result.indicators[64]
        ir.score = v.afterimage_score
        ir.confidence = v.afterimage_confidence
        ir.effective_score = ir.score * ir.confidence
        ir.measured = True
        ir.notes = (f"기하편차={v.face_geometry_deviation:.4f}, 대칭도={v.face_symmetry:.3f}, "
                    f"특이비율={v.distinctive_ratio_count}개")
        if v.notes:
            ir.notes = v.notes
    if e.signature_confidence > 0:
        ir = result.indicators[83]
        ir.score = e.signature_score
        ir.confidence = e.signature_confidence
        ir.effective_score = ir.score * ir.confidence
        ir.measured = True
        ir.notes = (f"변화범위={e.expression_range:.4f}, 엔트로피={e.expression_entropy:.2f}, "
                    f"입/눈/눈썹={e.mouth_expressiveness:.4f}/{e.eye_expressiveness:.4f}/{e.brow_expressiveness:.4f}")
        if e.notes:
            ir.notes = e.notes

def _evaluate_pass_fail(result: ScreeningResult):
    """
    ★ 회사 헌법: 종합 점수/합산/가중평균 영구 금지
    판정 로직은 순수 OR — 어느 한 차원이라도 극단값이면 통과.
    합산, 평균, AND 조건 일체 없음.
    """
    measured = [ir for ir in result.indicators.values() if ir.measured]
    if not measured:
        result.passed = False
        result.pass_reason = "no_data"
        result.warnings.append("측정된 지표 없음 — 판정 불가")
        return

    # ── 각 차원 독립 극단값 판정 (OR 논리) ──
    outlier_dims = []
    max_score = 0.0
    for ir in measured:
        score = ir.score
        if score > max_score:
            max_score = score
        # 오른쪽 꼬리 (초우월) 또는 왼쪽 꼬리 (초이질)
        if score >= OUTLIER_THRESHOLD:
            outlier_dims.append(f"{ir.name}(↑{score:.2f})")
        elif 0 < score <= OUTLIER_LOW_THRESHOLD:
            outlier_dims.append(f"{ir.name}(↓{score:.2f})")

    result.max_single_score = max_score
    result.outlier_count = len(outlier_dims)
    result.outlier_dimensions = outlier_dims

    # ★ OR 논리: 단 하나의 극단값이라도 있으면 통과
    if outlier_dims:
        result.passed = True
        result.pass_reason = f"outlier_{len(outlier_dims)}dims"
    else:
        result.passed = False
        result.pass_reason = "no_outlier"

    unmeasured = [ir for ir in result.indicators.values() if not ir.measured]
    if unmeasured:
        names = ", ".join(ir.name for ir in unmeasured)
        result.warnings.append(f"미측정 지표: {names}")

def _detect_content_type(title: str) -> str:
    title_lower = title.lower()
    dance_keywords = ["dance", "댄스", "choreography", "안무", "practice", "연습", "cover", "performance video"]
    vocal_keywords = ["vocal", "보컬", "singing", "노래", "cover", "live", "라이브", "acoustic"]
    dance_score = sum(1 for kw in dance_keywords if kw in title_lower)
    vocal_score = sum(1 for kw in vocal_keywords if kw in title_lower)
    if dance_score > vocal_score:
        return "dance"
    elif vocal_score > dance_score:
        return "vocal"
    return "mixed"

def _extract_audio_from_video(video_path: Path) -> Optional[Path]:
    import subprocess
    audio_path = video_path.with_suffix(".wav")
    try:
        subprocess.run(["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le",
            "-ar", "22050", "-ac", "1", str(audio_path), "-y"], capture_output=True, timeout=60)
        if audio_path.exists():
            return audio_path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None

def print_screening_report(result: ScreeningResult):
    verdict = "통과" if result.passed else "탈락"
    print(f"\n{'━'*60}\n  1단계 고유성 스크리닝 결과\n{'━'*60}")
    print(f"  대상: {result.title}\n  채널: {result.uploader}\n  유형: {result.content_type}\n  URL:  {result.url}\n{'─'*60}")
    for iid in sorted(result.indicators.keys()):
        ir = result.indicators[iid]
        bar_len = int(ir.effective_score * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        status = "✓" if ir.measured else "—"
        print(f"  {status} [{iid:3d}] {ir.name:<14s}  |{bar}| {ir.effective_score:.3f}  "
              f"(원본={ir.score:.3f} × 신뢰={ir.confidence:.3f})")
        if ir.notes:
            print(f"        {ir.notes}")
    print(f"{'─'*60}\n  최고 단일 차원: {result.max_single_score:.4f}")
    print(f"  극단값 차원 수: {result.outlier_count}개")
    if result.outlier_dimensions:
        print(f"  극단값 차원: {', '.join(result.outlier_dimensions)}")
    print(f"  판정: {verdict}  (사유: {result.pass_reason})\n  처리 시간: {result.processing_time:.1f}초")
    if result.warnings:
        print(f"\n  경고:")
        for w in result.warnings:
            print(f"    - {w}")
    if result.errors:
        print(f"\n  오류:")
        for e in result.errors:
            print(f"    - {e}")
    print(f"{'━'*60}\n")

def save_screening_report(result: ScreeningResult, output_dir: Optional[Path] = None) -> Path:
    out_dir = output_dir or REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in result.title[:40])
    filename = f"screen_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = out_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"  리포트 저장: {filepath}")
    return filepath

def print_comparison_table(results: List[ScreeningResult]):
    if not results:
        return
    print(f"\n{'━'*80}\n  고유성 스크리닝 비교표\n{'━'*80}")
    header = f"  {'지표':<14s}"
    for r in results:
        name = r.title[:12] if r.title else r.url[-12:]
        header += f"  {name:>12s}"
    print(header)
    print(f"  {'─'*14}" + "  " + "  ".join("─" * 12 for _ in results))
    for iid in sorted(UNIQUENESS_INDICATORS.keys()):
        name = UNIQUENESS_INDICATORS[iid]
        row = f"  {name:<14s}"
        for r in results:
            ir = r.indicators.get(iid)
            if ir and ir.measured:
                row += f"  {ir.effective_score:>10.3f}  "
            else:
                row += f"  {'—':>10s}  "
        print(row)
    print(f"  {'─'*14}" + "  " + "  ".join("─" * 12 for _ in results))
    row_outlier = f"  {'극단값 수':<14s}"
    row_max = f"  {'최고 단일':<14s}"
    row_verdict = f"  {'판정':<14s}"
    for r in results:
        row_outlier += f"  {r.outlier_count:>10d}  "
        row_max += f"  {r.max_single_score:>10.3f}  "
        v = "통과" if r.passed else "탈락"
        row_verdict += f"  {v:>10s}  "
    print(row_outlier)
    print(row_max)
    print(row_verdict)
    print(f"{'━'*80}\n")
