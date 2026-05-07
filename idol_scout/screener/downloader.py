"""
idol_screener/downloader.py
━━━━━━━━━━━━━━━━━━━━━━━━━━
URL → 로컬 파일 다운로드 (yt-dlp 래퍼)
ffmpeg 병합 없이 단일 포맷 다운로드 + imageio-ffmpeg로 오디오 변환
"""

import subprocess
import sys
import os
import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from .config import DOWNLOAD_DIR, MAX_VIDEO_DURATION, AUDIO_SAMPLE_RATE

# imageio-ffmpeg에서 ffmpeg 실행파일 경로 확보
_FFMPEG_EXE = None
try:
    import imageio_ffmpeg
    _FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    _ffmpeg_dir = str(Path(_FFMPEG_EXE).parent)
    if _ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except ImportError:
    pass

# yt-dlp 기본 명령
_YT_DLP_BASE = [sys.executable, "-m", "yt_dlp"]

# Node.js가 있을 때만 JS 런타임 플래그 추가
import shutil as _shutil
if _shutil.which("node"):
    _YT_DLP_BASE += ["--js-runtimes", "node", "--remote-components", "ejs:github"]

if _FFMPEG_EXE:
    _YT_DLP_BASE += ["--ffmpeg-location", str(Path(_FFMPEG_EXE).parent)]


@dataclass
class DownloadResult:
    """다운로드 결과"""
    success: bool
    video_path: Optional[Path] = None
    audio_path: Optional[Path] = None
    title: str = ""
    duration: float = 0.0
    uploader: str = ""
    url: str = ""
    error: str = ""


def extract_info(url: str) -> dict:
    """yt-dlp로 메타데이터만 추출 (다운로드 없이)"""
    cmd = [*_YT_DLP_BASE, "--dump-json", "--no-download", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            # 에러 정보를 dict에 담아 반환 (호출자가 에러 확인 가능)
            return {"_error": result.stderr.strip() or f"yt-dlp exit code {result.returncode}"}
    except subprocess.TimeoutExpired:
        return {"_error": "메타데이터 추출 타임아웃 (60초)"}
    except json.JSONDecodeError as e:
        return {"_error": f"JSON 파싱 실패: {e}"}
    except Exception as e:
        return {"_error": str(e)}
    return {}


def sanitize_filename(name: str) -> str:
    """파일명에 사용할 수 없는 문자 제거"""
    name = re.sub(r'[<>:"/\\|?*\u2502\uff5c\u2503]', '_', name)  # 파이프/특수문자 포함
    name = re.sub(r'[│｜┃]', '_', name)  # 유니코드 파이프 문자
    name = re.sub(r'\s+', '_', name)
    return name[:80]


def download_video(url: str, output_dir: Optional[Path] = None) -> DownloadResult:
    """
    URL에서 영상 + 오디오를 다운로드.
    병합 불필요한 단일 포맷으로 다운로드하고,
    오디오는 imageio-ffmpeg로 직접 변환.
    """
    out_dir = output_dir or DOWNLOAD_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1단계: 메타데이터 추출
    info = extract_info(url)
    if not info or (isinstance(info, dict) and "_error" in info and len(info) == 1):
        err_detail = info.get("_error", "알 수 없는 오류") if isinstance(info, dict) else "응답 없음"
        return DownloadResult(
            success=False, url=url,
            error=f"메타데이터 추출 실패: {err_detail}"
        )

    title = info.get("title", "unknown")
    duration = info.get("duration", 0) or 0
    uploader = info.get("uploader", info.get("channel", "unknown"))

    if duration > MAX_VIDEO_DURATION:
        return DownloadResult(
            success=False, url=url,
            error=f"영상 길이 {duration:.0f}초 > 최대 {MAX_VIDEO_DURATION}초"
        )

    safe_name = sanitize_filename(title)

    # 2단계: 영상 다운로드 — 병합 필요 없는 단일 포맷
    video_path = out_dir / f"{safe_name}.mp4"
    cmd_video = [
        *_YT_DLP_BASE,
        "-f", "best[ext=mp4]/best",  # 단일 포맷 (병합 불필요)
        "-o", str(video_path),
        "--no-playlist",
        url
    ]

    try:
        result = subprocess.run(cmd_video, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            # fallback
            cmd_fallback = [
                *_YT_DLP_BASE,
                "-f", "best",
                "-o", str(video_path),
                "--no-playlist",
                url
            ]
            result = subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return DownloadResult(
            success=False, url=url, title=title,
            error="영상 다운로드 시간 초과"
        )

    actual_video = _find_downloaded_file(out_dir, safe_name, [".mp4", ".webm", ".mkv"])

    # 3단계: 오디오 추출
    # 방법 A: 오디오만 별도 다운로드 (m4a/webm — 병합 불필요)
    audio_src = out_dir / f"{safe_name}_audio.m4a"
    cmd_audio = [
        *_YT_DLP_BASE,
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "-o", str(audio_src),
        "--no-playlist",
        url
    ]

    try:
        subprocess.run(cmd_audio, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        pass

    # 실제 다운로드된 오디오 파일 찾기
    actual_audio_src = _find_downloaded_file(out_dir, f"{safe_name}_audio", [".m4a", ".webm", ".opus", ".ogg"])

    # 다운로드 실패 시 영상 파일에서 오디오 추출 시도
    if not actual_audio_src and actual_video:
        actual_audio_src = actual_video

    # 방법 B: imageio-ffmpeg로 wav 변환
    actual_audio = None
    if actual_audio_src and _FFMPEG_EXE:
        wav_path = out_dir / f"{safe_name}.wav"
        try:
            cmd_convert = [
                _FFMPEG_EXE, "-y",
                "-i", str(actual_audio_src),
                "-ar", str(AUDIO_SAMPLE_RATE),
                "-ac", "1",
                "-f", "wav",
                str(wav_path)
            ]
            r = subprocess.run(cmd_convert, capture_output=True, timeout=60)
            if r.returncode == 0 and wav_path.exists():
                actual_audio = wav_path
        except Exception:
            pass

    # wav 변환 실패 시 원본 오디오 파일이라도 반환
    if not actual_audio and actual_audio_src and actual_audio_src != actual_video:
        actual_audio = actual_audio_src

    # 성공 여부: 영상 또는 오디오 중 하나라도 있으면 성공
    success = bool(actual_video or actual_audio)
    error = ""
    if not success:
        error = f"다운로드 후 파일을 찾을 수 없음: {result.stderr[:300] if result else 'unknown'}"

    return DownloadResult(
        success=success,
        video_path=actual_video,
        audio_path=actual_audio,
        title=title,
        duration=duration,
        uploader=uploader,
        url=url,
        error=error,
    )


def _find_downloaded_file(directory: Path, base_name: str, extensions: list) -> Optional[Path]:
    """다운로드된 파일을 찾음 (yt-dlp가 확장자나 포맷ID를 추가할 수 있으므로)"""
    # 정확한 이름 매칭
    for ext in extensions:
        path = directory / f"{base_name}{ext}"
        if path.exists():
            return path

    # glob 시도 (포맷ID 등이 붙은 경우: name.f140.m4a)
    for ext in extensions:
        matches = list(directory.glob(f"{base_name}*{ext}"))
        if matches:
            # 가장 큰 파일 반환 (포맷ID 파일 중 최적 선택)
            return max(matches, key=lambda p: p.stat().st_size)

    return None


# ── CLI 테스트 ──────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = download_video(sys.argv[1])
        print(f"성공: {result.success}")
        print(f"제목: {result.title}")
        print(f"길이: {result.duration:.0f}초")
        print(f"영상: {result.video_path}")
        print(f"오디오: {result.audio_path}")
        if result.error:
            print(f"오류: {result.error}")
