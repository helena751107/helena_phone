@echo off
REM ds.bat — Aider + DeepSeek 작업반장 (Windows CMD)
REM 설치: C:\Users\%USERNAME%\bin\ds.bat  또는 PATH 아무데나
REM 폰의 ds.sh 와 동일한 기능

setlocal enabledelayedexpansion

REM 작업 디렉토리
if "%WORK_DIR%"=="" set "WORK_DIR=%USERPROFILE%\work"
if not exist "%WORK_DIR%" set "WORK_DIR=%USERPROFILE%\work"
cd /d "%WORK_DIR%" 2>nul || (
    echo ❌ %WORK_DIR% 없음
    exit /b 1
)

REM API 키 확인
if "%DEEPSEEK_API_KEY%"=="" (
    echo ❌ DEEPSEEK_API_KEY 없음
    echo    시스템 환경변수에 DEEPSEEK_API_KEY=sk-... 추가하세요
    exit /b 1
)

REM Aider 확인
where aider >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ aider 없음. pip install aider-chat
    exit /b 1
)

REM 모델
if "%AIDER_MODEL%"=="" set "AIDER_MODEL=deepseek/deepseek-v4-pro"

REM 모델 설정 파일
if "%AIDER_MODEL_SETTINGS_FILE%"=="" (
    set "AIDER_MODEL_SETTINGS_FILE=%USERPROFILE%\.aider.model.settings.yml"
)

echo ▶ ds = Aider + DeepSeek
echo   model: %AIDER_MODEL%
echo   cwd:   %CD%
echo   종료:  /exit 또는 Ctrl+C
echo.

REM ANTHROPIC_BASE_URL 설정 (DeepSeek Anthropic 호환 엔드포인트)
if not "%ANTHROPIC_BASE_URL%"=="" (
    set "ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic"
)

aider ^
  --model "%AIDER_MODEL%" ^
  --model-settings-file "%AIDER_MODEL_SETTINGS_FILE%" ^
  --edit-format diff ^
  --chat-language Korean ^
  --no-auto-commits ^
  --no-attribute-author ^
  --no-attribute-committer ^
  --no-restore-chat-history ^
  --dark-mode ^
  --pretty ^
  --assistant-output-color "#FFD700" ^
  --tool-error-color "#22CC66" ^
  --tool-warning-color "#E6B800" ^
  --user-input-color "#66FF66" ^
  --code-theme gruvbox-dark ^
  %*
