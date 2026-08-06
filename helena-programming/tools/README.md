# 🛠 헬레나 툴킷 — Galaxy S21 proot-Ubuntu 전용

> 오빠가 골라준 도구 모음. Galaxy S21 ARM64 CPU에서 전부 동작함.

---

## 📁 구조

```
tools/
├── voice/          ← 음성 도구 (TTS)
├── phone/          ← 폰 관리·자막
└── ai/             ← AI 대화 도구
```

---

## 🎙 voice/ — 음성 도구

### tts-speak.py — 온디맨드 TTS
```bash
python3 tts-speak.py "안녕 헬레나!"
echo "읽어줄 텍스트" | python3 tts-speak.py -o output.mp3
```
설치: `pip install edge-tts`

### grok_tts.py — xAI Grok 고품질 TTS
```bash
XAI_API_KEY=키입력 python3 grok_tts.py --text "안녕하세요"
```
- SuperGrok 구독 시 사용 가능
- 상업용 라이선스 OK

### s21-tts-bot.py — 텔레그램 버튼 탭 → 음성 봇
```bash
TG_BOT_TOKEN=토큰 python3 s21-tts-bot.py
```
설치: `pip install python-telegram-bot`

### voice_engine.py — TTS 우선순위 엔진
```python
from voice_engine import synthesize
synthesize("안녕하세요", Path("/tmp/out.wav"))
# Grok → 박씨TTS(parksy-tts-v1) → OpenAI → edge-tts 자동 폴백
```
- parksy-tts-v1이 설치되어 있으면 오프라인 박씨 목소리 자동 사용

---

## 📱 phone/ — 폰 관리

### phone-health.sh — S21 헬스체크
```bash
bash phone-health.sh
```
- 배터리·저장공간·프로세스·네트워크 점검

### capcut_captions.py — CapCut 자막 자동생성
```bash
python3 capcut_captions.py --audio 파일.mp3 --out 자막.srt
```

---

## 🤖 ai/ — AI 대화

### ds.sh — DeepSeek 터미널 대화
```bash
bash ds.sh "질문 입력"
```
설치: `pip install openai`  
API키: `export DEEPSEEK_API_KEY=키입력`

---

## ⚡ 빠른 설치

```bash
# 음성 도구 의존성
pip install edge-tts requests python-telegram-bot openai

# 환경변수 (필요한 것만)
export XAI_API_KEY=...        # Grok TTS
export TG_BOT_TOKEN=...       # 텔레그램 봇
export DEEPSEEK_API_KEY=...   # DeepSeek
```

---

## 버전

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-08-06 | 최초 선물 배포 |

*parksy-tts-v1 선물과 함께 사용하면 오프라인 박씨 목소리 자동 연동됨* 💌
