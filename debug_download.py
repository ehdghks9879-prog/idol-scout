"""댄스 URL 다운로드 디버깅"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

url = "https://www.youtube.com/watch?v=7oEh1-QZVMY"

print("=" * 60)
print(" 다운로드 디버깅")
print("=" * 60)

# 1단계: 메타데이터 확인
print("\n[1] 메타데이터 추출 중...")
from idol_scout.screener.downloader import extract_info, download_video
info = extract_info(url)
if info:
    print(f"  제목: {info.get('title', '?')}")
    print(f"  길이: {info.get('duration', '?')}초")
    print(f"  업로더: {info.get('uploader', '?')}")
else:
    print("  실패! 메타데이터를 가져올 수 없습니다.")
    print("  URL을 확인하거나 yt-dlp를 업데이트하세요: pip install -U yt-dlp")
    sys.exit(1)

# 2단계: 다운로드 시도
print("\n[2] 다운로드 시도 중...")
result = download_video(url)
print(f"  성공: {result.success}")
print(f"  영상: {result.video_path}")
print(f"  오디오: {result.audio_path}")
if result.error:
    print(f"  오류: {result.error}")

# 3단계: 오디오 파일 확인
if result.audio_path:
    print(f"\n[3] 오디오 파일 확인...")
    from pathlib import Path
    ap = Path(result.audio_path)
    if ap.exists():
        size = ap.stat().st_size
        print(f"  파일 존재: {ap.name} ({size:,} bytes)")

        # librosa 로드 시도
        print("\n[4] librosa 로드 시도...")
        try:
            import librosa
            y, sr = librosa.load(str(ap), sr=22050, mono=True)
            print(f"  성공! 길이={len(y)/sr:.1f}초, sr={sr}")
        except Exception as e:
            print(f"  실패: {e}")

            # ffmpeg 변환 시도
            print("\n[4b] ffmpeg 변환 후 재시도...")
            from idol_scout.screener.audio import _convert_to_wav
            wav = _convert_to_wav(ap)
            if wav:
                try:
                    y, sr = librosa.load(str(wav), sr=22050, mono=True)
                    print(f"  변환 후 성공! 길이={len(y)/sr:.1f}초")
                except Exception as e2:
                    print(f"  변환 후에도 실패: {e2}")
            else:
                print("  wav 변환 실패")
    else:
        print(f"  파일 없음!")
else:
    print("\n[3] 오디오 파일이 생성되지 않았습니다.")
    # downloads 폴더 내용 확인
    from idol_scout.screener.config import DOWNLOAD_DIR
    print(f"  다운로드 폴더: {DOWNLOAD_DIR}")
    if DOWNLOAD_DIR.exists():
        files = list(DOWNLOAD_DIR.iterdir())
        print(f"  파일 수: {len(files)}")
        for f in files[:10]:
            print(f"    {f.name} ({f.stat().st_size:,} bytes)")
    else:
        print("  폴더 없음")

print("\n" + "=" * 60)
print(" 디버깅 완료")
print("=" * 60)
