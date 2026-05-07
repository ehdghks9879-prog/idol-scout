"""
idol_screener/downloader.py
━━━━━━━━━━━━━━━━━━━━━━━━━━
URL → 로컬 파일 다운로드 (yt-dlp Python API)
subprocess 대신 Python API를 직접 사용하여 Streamlit Cloud 호환성 확보
"""

import os
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


def sanitize_filename(name: str) -> str:
    """파일명에 사용할 수 없는 문자 제거"""
    name = re.sub(r'[<>:"/\\|?*│｜┃]', '_', name)
    name = re.sub(r'[│｜┃]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name[:80]


def extract_info(url: str) -> dict:
    """yt-dlp Python API로 메타데이터만 추출 (다운로드 없이)"""
    try:
        import yt_dlp
    except ImportError:
        return {"_error": "yt-dlp가 설치되지 않았습니다"}

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "socket_timeout": 30,
    }
    if _FFMPEG_EXE:
        ydl_opts["ffmpeg_location"] = str(Path(_FFMPEG_EXE).parent)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info or {}
    except yt_dlp.utils.DownloadError as e:
        return {"_error": f"yt-dlp 오류: {str(e)[:300]}"}
    except Exception as e:
        return {"_error": f"메타데이터 추출 실패: {str(e)[:300]}"}


def download_video(url: str, output_dir: Optional[Path] = None) -> DownloadResult:
    """
    URL에서 영상 + 오디오를 다운로드 (yt-dlp Python API).
    """
    try:
        import yt_dlp
    except ImportError:
        return DownloadResult(success=False, url=url, error="yt-dlp가 설치되지 않았습니다")

    out_dir = output_dir or DOWNLOAD_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1단계: 메타데이터 추출
    info = extract_info(url)
    if not info or (isinstance(info, dict) and "_error" in info and len(info) == 1):
        err_detail = info.get("_error", "알 수 없는 오류") if isinstance(info, dict) else "응답 없음"
        return DownloadResult(success=False, url=url, error=f"메타데이터 추출 실패: {err_detail}")

    title = info.get("title", "unknown")
    duration = info.get("duration", 0) or 0
    uploader = info.get("uploader", info.get("channel", "unknown"))

    if duration > MAX_VIDEO_DURATION:
        return DownloadResult(
            success=False, url=url,
            error=f"영상 길이 {duration:.0f}초 > 최대 {MAX_VIDEO_DURATION}초"
        )

    safe_name = sanitize_filename(title)

    # 2단계: 영상 다운로드 (단일 포맷, 병합 불필요)
    video_path = out_dir / f"{safe_name}.mp4"
    ydl_opts_video = {
        "format": "best[ext=mp4]/best",
        "outtmpl": str(video_path),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
    }
    if _FFMPEG_EXE:
        ydl_opts_video["ffmpeg_location"] = str(Path(_FFMPEG_EXE).parent)

    try:
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            ydl.download([url])
    except Exception:
        pass

    actual_video = _find_downloaded_file(out_dir, safe_name, [".mp4", ".webm", ".mkv"])

    # 3단계: 오디오 다운로드
    audio_src_name = f"{safe_name}_audio"
    audio_src = out_dir / f"{audio_src_name}.m4a"
    ydl_opts_audio = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": str(audio_src),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
    }
    if _FFMPEG_EXE:
        ydl_opts_audio["ffmpeg_location"] = str(Path(_FFMPEG_EXE).parent)

    try:
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([url])
    except Exception:
        pass

    actual_audio_src = _find_downloaded_file(out_dir, audio_src_name, [".m4a", ".webm", ".opus", ".ogg"])

    # 오디오 다운로드 실패 시 영상 파일에서 추출
    if not actual_audio_src and actual_video:
        actual_audio_src = actual_video

    # wav 변환
    actual_audio = None
    if actual_audio_src and _FFMPEG_EXE:
        import subprocess
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

    if not actual_audio and actual_audio_src and actual_audio_src != actual_video:
        actual_audio = actual_audio_src

    success = bool(actual_video or actual_audio)
    error = ""
    if not success:
        error = "다운로드 후 파일을 찾을 수 없습니다. URL을 확인하세요."

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


def download_audio_only(url: str, output_dir: Optional[Path] = None) -> DownloadResult:
    """
    URL에서 오디오만 다운로드 (100차원 분석용 — 영상 불필요).
    단일 연결로 메타데이터 + 다운로드를 한 번에 처리하여 속도 최적화.
    """
    try:
        import yt_dlp
    except ImportError:
        return DownloadResult(success=False, url=url, error="yt-dlp가 설치되지 않았습니다")

    out_dir = output_dir or DOWNLOAD_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # 임시 이름으로 설정 (다운로드 후 실제 제목 확인)
    tmp_name = "audio_download"
    audio_src = out_dir / f"{tmp_name}.%(ext)s"

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": str(audio_src),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
    }
    if _FFMPEG_EXE:
        ydl_opts["ffmpeg_location"] = str(Path(_FFMPEG_EXE).parent)

    # 단일 연결: extract_info + download 동시 수행
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as e:
        return DownloadResult(success=False, url=url, error=f"다운로드 실패: {str(e)[:300]}")
    except Exception as e:
        return DownloadResult(success=False, url=url, error=f"오류: {str(e)[:200]}")

    if not info:
        return DownloadResult(success=False, url=url, error="메타데이터를 가져올 수 없습니다")

    title = info.get("title", "unknown")
    duration = info.get("duration", 0) or 0
    uploader = info.get("uploader", info.get("channel", "unknown"))

    if duration > MAX_VIDEO_DURATION:
        return DownloadResult(
            success=False, url=url,
            error=f"영상 길이 {duration:.0f}초 > 최대 {MAX_VIDEO_DURATION}초"
        )

    # 다운로드된 파일 찾기
    actual_audio_src = _find_downloaded_file(out_dir, tmp_name, [".m4a", ".webm", ".opus", ".ogg", ".mp3", ".mp4"])

    # wav 변환
    actual_audio = None
    if actual_audio_src and _FFMPEG_EXE:
        import subprocess
        safe_name = sanitize_filename(title)
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
                # 원본 소스 파일 정리
                try:
                    actual_audio_src.unlink()
                except Exception:
                    pass
        except Exception:
            pass

    if not actual_audio and actual_audio_src:
        actual_audio = actual_audio_src

    if not actual_audio:
        return DownloadResult(success=False, url=url, title=title, error="오디오 파일을 찾을 수 없습니다")

    return DownloadResult(
        success=True,
        audio_path=actual_audio,
        title=title,
        duration=duration,
        uploader=uploader,
        url=url,
    )


def _find_downloaded_file(directory: Path, base_name: str, extensions: list) -> Optional[Path]:
    """다운로드된 파일을 찾음 (yt-dlp가 확장자나 포맷ID를 추가할 수 있으므로)"""
    for ext in extensions:
        path = directory / f"{base_name}{ext}"
        if path.exists():
            return path

    for ext in extensions:
        matches = list(directory.glob(f"{base_name}*{ext}"))
        if matches:
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
