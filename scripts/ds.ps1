# ds.ps1 — Aider + DeepSeek 작업반장 (Windows PowerShell)
# 설치: C:\Users\$env:USERNAME\bin\ds.ps1
# 폰의 ds.sh 와 동일한 기능

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Rest
)

# 작업 디렉토리
$WorkDir = if ($env:WORK_DIR) { $env:WORK_DIR } else { "$env:USERPROFILE\work" }
if (-not (Test-Path $WorkDir)) {
    $WorkDir = "$env:USERPROFILE\work"
}
Set-Location $WorkDir -ErrorAction Stop

# API 키 확인
if (-not $env:DEEPSEEK_API_KEY) {
    Write-Host "❌ DEEPSEEK_API_KEY 없음" -ForegroundColor Red
    Write-Host "   시스템 환경변수에 추가:" -ForegroundColor Yellow
    Write-Host '   [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-...", "User")'
    exit 1
}

# Aider 확인
$aider = Get-Command aider -ErrorAction SilentlyContinue
if (-not $aider) {
    Write-Host "❌ aider 없음. pip install aider-chat" -ForegroundColor Red
    exit 1
}

# 모델
$Model = if ($env:AIDER_MODEL) { $env:AIDER_MODEL } else { "deepseek/deepseek-v4-pro" }

# 모델 설정 파일
$SettingsFile = if ($env:AIDER_MODEL_SETTINGS_FILE) {
    $env:AIDER_MODEL_SETTINGS_FILE
} else {
    "$env:USERPROFILE\.aider.model.settings.yml"
}

# DeepSeek Anthropic 호환 엔드포인트
if (-not $env:ANTHROPIC_BASE_URL) {
    $env:ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
}

Write-Host "▶ ds = Aider + DeepSeek" -ForegroundColor Cyan
Write-Host "  model: $Model"
Write-Host "  cwd:   $(Get-Location)"
Write-Host "  종료:  /exit 또는 Ctrl+C"
Write-Host ""

& aider `
    --model $Model `
    --model-settings-file $SettingsFile `
    --edit-format diff `
    --chat-language Korean `
    --no-auto-commits `
    --no-attribute-author `
    --no-attribute-committer `
    --no-restore-chat-history `
    --dark-mode `
    --pretty `
    --assistant-output-color "#FFD700" `
    --tool-error-color "#22CC66" `
    --tool-warning-color "#E6B800" `
    --user-input-color "#66FF66" `
    --code-theme gruvbox-dark `
    @Rest
