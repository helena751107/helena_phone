@echo off
REM ============================================================
REM  pc-install-ds.bat — Windows 10 DeepSeek + Aider 설치
REM  폰(Termux)에서 돌아가는 ds.sh 와 동일한 환경을 PC에 구성
REM
REM  사용법: pc-install-ds.bat
REM  Boss 2026-08-05
REM ============================================================

echo.
echo ╔══════════════════════════════════════════════╗
echo ║  🖥️  DeepSeek + Aider — PC 설치              ║
echo ║  폰(Termux) 환경을 Windows에 복제             ║
echo ╚══════════════════════════════════════════════╝
echo.

setlocal enabledelayedexpansion

REM ── [1/5] Python 확인 + 설치 ──
echo 📦 [1/5] Python 확인...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo    Python 없음. winget 으로 설치...
    winget install Python.Python.3.12
    echo    설치 후 이 스크립트를 다시 실행하세요.
    pause
    exit /b 0
)
for /f "tokens=*" %%i in ('python --version') do echo    ✅ %%i

REM ── [2/5] Aider 설치 ──
echo.
echo 🛠️  [2/5] Aider 설치...
pip install aider-chat 2>nul
if %ERRORLEVEL% neq 0 (
    echo    pip 실패. pipx 로 시도...
    pipx install aider-chat
)
for /f "tokens=*" %%i in ('aider --version 2^>nul') do echo    ✅ aider %%i

REM ── [3/5] DeepSeek API 키 ──
echo.
echo 🔑 [3/5] DeepSeek API 키...
set "KEY_FILE=%USERPROFILE%\.deepseek.env"

REM 이미 설정돼 있으면 건너뜀
if not "%DEEPSEEK_API_KEY%"=="" (
    echo    ✅ DEEPSEEK_API_KEY 이미 설정됨
    goto :skip_key
)

REM 사용자에게 키 입력 받기
echo.
echo    DeepSeek API 키를 입력하세요 (sk-...):
echo    ※ https://platform.deepseek.com/api_keys 에서 발급
set /p INPUT_KEY="    > "

if "!INPUT_KEY!"=="" (
    echo    ⚠️  키를 입력하지 않음. 나중에 직접 설정:
    echo       [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-...", "User")
) else (
    setx DEEPSEEK_API_KEY "!INPUT_KEY!"
    set "DEEPSEEK_API_KEY=!INPUT_KEY!"
    echo    ✅ DEEPSEEK_API_KEY 등록 완료
)
:skip_key

REM ANTHROPIC_BASE_URL
if "%ANTHROPIC_BASE_URL%"=="" (
    setx ANTHROPIC_BASE_URL "https://api.deepseek.com/anthropic"
    set "ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic"
    echo    ✅ ANTHROPIC_BASE_URL 등록 완료
)

REM ── [4/5] 설정 파일 복사 ──
echo.
echo 📝 [4/5] 설정 파일...

REM ds.bat, ds.ps1 → ~/bin
set "BIN_DIR=%USERPROFILE%\bin"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

REM 이 스크립트가 있는 디렉토리에서 파일 찾기
set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%ds.bat" (
    copy /Y "%SCRIPT_DIR%ds.bat" "%BIN_DIR%\ds.bat" >nul
    echo    ✅ ds.bat → %BIN_DIR%
)
if exist "%SCRIPT_DIR%ds.ps1" (
    copy /Y "%SCRIPT_DIR%ds.ps1" "%BIN_DIR%\ds.ps1" >nul
    echo    ✅ ds.ps1 → %BIN_DIR%
)

REM aider.model.settings.yml
if exist "%SCRIPT_DIR%..\configs\aider.model.settings.yml" (
    copy /Y "%SCRIPT_DIR%..\configs\aider.model.settings.yml" "%USERPROFILE%\.aider.model.settings.yml" >nul
    echo    ✅ aider.model.settings.yml → %USERPROFILE%
)

REM PATH에 bin 추가
echo %PATH% | findstr /C:"%BIN_DIR%" >nul
if %ERRORLEVEL% neq 0 (
    setx PATH "%PATH%;%BIN_DIR%" >nul
    echo    ✅ PATH에 %BIN_DIR% 추가
)

REM ── [5/5] 테스트 ──
echo.
echo 🧪 [5/5] 테스트...
aider --model deepseek/deepseek-v4-pro --message "안녕? 짧게 한국어로 대답해줘. 너는 누구고 뭘 할 수 있어?" --no-auto-commits --chat-language Korean --dark-mode 2>&1 | findstr /C:"DeepSeek" /C:"Aider" /C:"안녕"
if %ERRORLEVEL% equ 0 (
    echo    ✅ Aider + DeepSeek 정상 동작
) else (
    echo    ⚠️  수동 테스트: ds 실행해보세요
)

echo.
echo ╔══════════════════════════════════════════════╗
echo ║  🎉 설치 완료!                               ║
echo ║                                              ║
echo ║  사용법:                                      ║
echo ║    ds            → 대화 시작                   ║
echo ║    ds "작업내용"  → 바로 작업 지시              ║
echo ║                                              ║
echo ║  환경변수:                                    ║
echo ║    DEEPSEEK_API_KEY  = %DEEPSEEK_API_KEY:~0,16%...  ║
echo ║    ANTHROPIC_BASE_URL = %ANTHROPIC_BASE_URL%  ║
echo ║    AIDER_MODEL       = deepseek/deepseek-v4-pro ║
echo ╚══════════════════════════════════════════════╝

REM 자기 자신을 PATH에 복사
copy /Y "%~f0" "%BIN_DIR%\pc-install-ds.bat" >nul 2>&1

endlocal
pause
