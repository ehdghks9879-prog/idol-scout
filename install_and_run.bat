@echo off
chcp 65001 >nul
title AI 아이돌 발굴 시스템 — 설치 및 실행

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   AI 아이돌 발굴 시스템 — idol_scout v1.0
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:: 현재 디렉토리 설정
cd /d "%~dp0"

:: Python 확인
echo [1/4] Python 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python이 설치되어 있지 않습니다.
    echo   https://www.python.org/downloads/ 에서 Python 3.9+ 설치 후 재실행하세요.
    pause
    exit /b 1
)
python --version
echo.

:: ffmpeg 확인
echo [2/4] ffmpeg 확인 중...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠ ffmpeg이 설치되어 있지 않습니다.
    echo   오디오 추출 기능이 제한될 수 있습니다.
    echo   https://ffmpeg.org/download.html 에서 설치를 권장합니다.
    echo.
) else (
    echo ✓ ffmpeg 확인 완료
    echo.
)

:: 패키지 설치
echo [3/4] idol_scout 패키지 설치 중...
pip install -e . --quiet
if errorlevel 1 (
    echo ✗ 패키지 설치 실패
    echo   pip install -e . 명령어를 수동으로 실행해 보세요.
    pause
    exit /b 1
)
echo ✓ 설치 완료
echo.

:: 설치 확인
echo [4/4] 설치 확인 중...
python -c "import idol_scout; print(f'idol_scout v{idol_scout.__version__} 로드 성공')"
if errorlevel 1 (
    echo ✗ 패키지 로드 실패
    pause
    exit /b 1
)
echo.

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   설치 완료! 아래 방법으로 사용하세요:
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo   [CLI 사용법]
echo   idol-screen https://youtube.com/watch?v=...
echo   idol-screen --compare url1 url2 url3
echo   idol-screen --file video.mp4 --type dance
echo.
echo   [Python 사용법]
echo   from idol_scout import screen
echo   result = screen("https://...")
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:: 스크리닝 실행 여부 확인
set /p RUN_NOW="지금 바로 스크리닝을 실행하시겠습니까? (y/n): "
if /i "%RUN_NOW%"=="y" (
    set /p VIDEO_URL="영상 URL을 입력하세요: "
    set /p CONTENT_TYPE="콘텐츠 유형 (vocal/dance/auto): "
    if "%CONTENT_TYPE%"=="" set CONTENT_TYPE=auto
    echo.
    echo 스크리닝 시작...
    idol-screen --type %CONTENT_TYPE% --save "%VIDEO_URL%"
)

echo.
pause
