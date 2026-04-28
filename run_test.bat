@echo off
chcp 65001 >nul
title idol_scout 테스트 실행

cd /d "%~dp0"

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   idol_scout 테스트 스크리닝 실행
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:: PATH에 Python Scripts 추가
for /f "delims=" %%i in ('python -c "import sys; import os; print(os.path.join(os.path.dirname(sys.executable), 'Scripts'))"') do set "SCRIPTS_DIR=%%i"
set PATH=%PATH%;%SCRIPTS_DIR%

echo [1] PATH 설정 완료: %SCRIPTS_DIR%
echo.

:: 보컬 테스트 1
echo ━━━ 보컬 테스트 1 ━━━
echo URL: https://www.youtube.com/watch?v=K5fr2Y3wIPw
echo.
python -m idol_scout.cli https://www.youtube.com/watch?v=K5fr2Y3wIPw --type vocal --save
echo.

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   테스트 완료!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
pause
