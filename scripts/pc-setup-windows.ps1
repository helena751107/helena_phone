# 🖥️ pc-setup-windows.ps1 — Windows Native 개발환경 셋업
# 사용법: PowerShell에서 ./pc-setup-windows.ps1
# Boss 2026-08-05

$ErrorActionPreference = "Stop"

Write-Host "🖥️  Windows Native 개발환경 셋업..." -ForegroundColor Cyan
Write-Host "=" * 50

# 1. Python 확인
Write-Host ""
Write-Host "📦 [1/5] Python 확인..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "❌ Python 없음. https://python.org 에서 설치하세요." -ForegroundColor Red
    Write-Host "   또는: winget install Python.Python.3.12"
    exit 1
}
Write-Host "✅ Python: $(python --version)"

# 2. Tailscale 확인
Write-Host ""
Write-Host "🔗 [2/5] Tailscale 확인..." -ForegroundColor Yellow
$ts = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $ts) {
    Write-Host "❌ Tailscale 없음. https://tailscale.com/download/windows" -ForegroundColor Red
} else {
    Write-Host "✅ Tailscale 설치됨"
    tailscale status
}

# 3. API 키 확인
Write-Host ""
Write-Host "🤖 [3/5] DeepSeek API 키 확인..." -ForegroundColor Yellow
if (-not $env:OPENROUTER_API_KEY -and -not $env:DEEPSEEK_API_KEY) {
    Write-Host "⚠️  API 키가 설정되지 않았습니다." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   시스템 환경 변수에 추가:"
    Write-Host '   [Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "sk-or-v1-XXXX", "User")'
    Write-Host '   [Environment]::SetEnvironmentVariable("DEEPSEEK_MODEL", "deepseek/deepseek-chat", "User")'
} else {
    Write-Host "✅ API 키 설정됨"
}

# 4. Aider 설치
Write-Host ""
Write-Host "🛠️ [4/5] Aider 설치..." -ForegroundColor Yellow
pip install aider-chat 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  pip install 실패. pipx로 시도..."
    pipx install aider-chat
}
Write-Host "✅ Aider: $(aider --version 2>$null)"

# 5. ds 래퍼 스크립트
Write-Host ""
Write-Host "📝 [5/5] ds 래퍼 설치..." -ForegroundColor Yellow

$binDir = "$HOME\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null

@"
# ds.ps1 — Aider + DeepSeek 작업반장 (Windows Native)
# 사용법: ds "작업 지시"
#         ds --apply "코드 수정"

param(
    [Parameter(ValueFromRemainingArguments=`$true)]
    [string[]]`$Args
)

`$repo = if (`$env:REPO) { `$env:REPO } else { "`$env:USERPROFILE\work\helena_phone" }
`$model = if (`$env:DEEPSEEK_MODEL) { `$env:DEEPSEEK_MODEL } else { "deepseek/deepseek-chat" }

if (-not (Test-Path `$repo)) {
    Write-Host "❌ `$repo 없음. Git clone 먼저." -ForegroundColor Red
    Write-Host "   git clone --recurse-submodules https://github.com/helena751107/helena_phone.git `$env:USERPROFILE\work\helena_phone"
    exit 1
}

Set-Location `$repo

Write-Host "🔧 ds (Windows) — Aider + DeepSeek (`$model)" -ForegroundColor Cyan
Write-Host "📂 `$repo" -ForegroundColor Cyan
Write-Host ""

aider --model "openrouter/`$model" --no-auto-commits --no-gitignore @Args
"@ | Out-File -FilePath "$binDir\ds.ps1" -Encoding UTF8

Write-Host "✅ ds.ps1 설치됨: $binDir\ds.ps1"

# PATH 등록 확인
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$binDir", "User")
    Write-Host "✅ PATH에 $binDir 추가됨 (새 터미널에서 적용)"
}

Write-Host ""
Write-Host "=" * 50
Write-Host "🎉 Windows Native 셋업 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "✨ 다음 수동 작업:"
Write-Host "   1. Tailscale 설치 + 로그인 (https://tailscale.com/download/windows)"
Write-Host "   2. API 키 환경 변수 설정"
Write-Host "   3. Git 클론: git clone --recurse-submodules https://github.com/helena751107/helena_phone.git ~/work/helena_phone"
Write-Host "   4. 새 PowerShell 터미널 열어서 PATH 반영"
Write-Host ""
Write-Host "🧪 테스트:"
Write-Host "   ds '이 레포 설명해줘'"
