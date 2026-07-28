#!/usr/bin/env python3
"""
S21 TTS Bot — 텔레그램 메시지를 음성으로 읽어주는 봇

기능:
  /read [텍스트]  — 텍스트를 음성으로 읽기
  /tts            — 이전 메시지를 음성으로 읽기 (reply)
  /voice [이름]   — 음성 변경 (SunHi/InJoon)
  /stop           — 봇 중지

자동:
  - Claude 보고 메시지("*Claude*" 또는 "DTS 감사관" 포함) 자동 읽기

사용법:
  python3 s21-tts-bot.py                  # 1회 폴링
  python3 s21-tts-bot.py --daemon         # 백그라운드 지속
  bash s21-tts-bot.sh start               # 서비스로 실행

필요:
  pip install edge-tts
"""

import sys
import os
import json
import time
import signal
import asyncio
import tempfile
import requests
import subprocess
import argparse

# ── 설정 ───────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# .secrets.env 에서 TG 토큰 읽기
def load_token():
    env_file = os.path.join(os.path.dirname(SCRIPT_DIR), ".secrets.env")
    token = os.environ.get("TG_TOKEN", "")
    if not token and os.path.exists(env_file):
        for line in open(env_file):
            if line.startswith("TG_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"')
                break
    return token or os.environ.get("TG_TOKEN", "")

TG_TOKEN = load_token()
TG_API = f"https://api.telegram.org/bot{TG_TOKEN}"

VOICES = {
    "sunhi":  "ko-KR-SunHiNeural",    # 여성, 밝은 톤
    "injoon": "ko-KR-InJoonNeural",   # 남성
    "jimin":  "ko-KR-JiMinNeural",    # 여성, 차분
    "seohyun":"ko-KR-SeoHyeonNeural", # 여성, 뉴스톤
    "bora":   "ko-KR-YuBoraNeural",   # 여성, 또렷
}
DEFAULT_VOICE = "sunhi"
RUNNING = True

# ── Edge TTS ───────────────────────────────────────
async def text_to_voice(text: str, voice_key: str = "sunhi") -> str | None:
    """텍스트 → 음성 MP3 파일. 경로 반환."""
    voice = VOICES.get(voice_key, VOICES["sunhi"])
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(tmp.name)
        if os.path.getsize(tmp.name) > 100:
            return tmp.name
    except Exception as e:
        print(f"[TTS] {e}")
    os.unlink(tmp.name)
    return None

# ── TG API ─────────────────────────────────────────
def tg_send(chat_id: int, text: str):
    requests.post(f"{TG_API}/sendMessage",
                  json={"chat_id": chat_id, "text": text}, timeout=10)

def tg_send_voice(chat_id: int, mp3_path: str, caption: str = ""):
    with open(mp3_path, "rb") as f:
        requests.post(f"{TG_API}/sendVoice",
                      data={"chat_id": chat_id, "caption": caption},
                      files={"voice": (os.path.basename(mp3_path), f)},
                      timeout=30)

def tg_reply(chat_id: int, msg_id: int, text: str):
    requests.post(f"{TG_API}/sendMessage",
                  json={"chat_id": chat_id, "reply_to_message_id": msg_id, "text": text},
                  timeout=10)

# ── 자동 읽기 판단 ────────────────────────────────
def should_auto_read(text: str) -> bool:
    """Claude 보고나 중요 메시지 자동 감지"""
    if not text:
        return False
    triggers = [
        "DTS 감사관", "_Claude", "✅", "🎹", "🔊", "📋",
        "BGM Studio", "노드 프로토콜", "Allocation Rate",
        "render-bgm", "fridge", "health",
    ]
    text_lower = text.lower()
    return any(t.lower() in text_lower for t in triggers)

# ── 메시지 처리 ────────────────────────────────────
async def handle_message(msg: dict):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    msg_id = msg.get("message_id", 0)

    # /read 명령
    if text.startswith("/read "):
        content = text[6:].strip()
        if content:
            tg_send(chat_id, f"🔊 읽는 중... ({len(content)}자)")
            mp3 = await text_to_voice(content)
            if mp3:
                tg_send_voice(chat_id, mp3, f"🔊 {len(content)}자")
                os.unlink(mp3)
            else:
                tg_reply(chat_id, msg_id, "❌ TTS 변환 실패")
        return

    # /tts — 이전 메시지 읽기
    if text == "/tts":
        reply = msg.get("reply_to_message", {})
        reply_text = reply.get("text", "") if reply else ""
        if reply_text:
            tg_send(chat_id, f"🔊 읽는 중...")
            mp3 = await text_to_voice(reply_text[:1000])
            if mp3:
                tg_send_voice(chat_id, mp3)
                os.unlink(mp3)
        else:
            tg_reply(chat_id, msg_id, "❌ 읽을 메시지에 답장(reply)해서 /tts 입력")
        return

    # /voice 변경
    if text.startswith("/voice "):
        key = text[7:].strip().lower()
        if key in VOICES:
            tg_reply(chat_id, msg_id, f"✅ 음성 변경: {key} ({VOICES[key]})")
        else:
            names = ", ".join(VOICES.keys())
            tg_reply(chat_id, msg_id, f"🎤 사용 가능: {names}")
        return

    # /stop
    if text == "/stop":
        global RUNNING
        RUNNING = False
        tg_reply(chat_id, msg_id, "⏹️ TTS 봇 중지")
        return

    # /help
    if text == "/help" or text == "/start":
        tg_send(chat_id, """🎤 S21 TTS Bot
/read [텍스트] — 읽어줌
/tts          — 답장한 메시지 읽기
/voice [이름] — 음성 변경
/stop         — 중지
자동: Claude 보고 자동 읽기""")
        return

    # 자동 읽기
    if should_auto_read(text):
        short = text[:800]
        mp3 = await text_to_voice(short)
        if mp3:
            tg_send_voice(chat_id, mp3, f"🤖 자동 읽기: {text[:50]}...")
            os.unlink(mp3)

# ── 폴링 루프 ──────────────────────────────────────
async def poll_once(offset: int = 0) -> int:
    try:
        resp = requests.get(f"{TG_API}/getUpdates",
                           params={"offset": offset, "limit": 5, "timeout": 10},
                           timeout=15)
        data = resp.json()
        for update in data.get("result", []):
            update_id = update["update_id"]
            offset = max(offset, update_id + 1)
            msg = update.get("message", {})
            if msg.get("text"):
                await handle_message(msg)
        return offset
    except Exception as e:
        print(f"[poll] {e}")
        return offset

async def main_loop():
    print(f"🤖 S21 TTS Bot 시작 (토큰: {TG_TOKEN[:10]}...)")
    print(f"   /read /tts /voice /stop")

    # 마지막 업데이트부터 시작
    try:
        resp = requests.get(f"{TG_API}/getUpdates", params={"limit": 1}, timeout=10)
        data = resp.json()
        offset = max([u["update_id"] + 1 for u in data.get("result", [])], default=0)
    except:
        offset = 0

    global RUNNING
    RUNNING = True
    while RUNNING:
        offset = await poll_once(offset)
        await asyncio.sleep(3)

# ── 엔트리 ─────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", "-d", action="store_true", help="백그라운드 지속")
    parser.add_argument("--once", "-1", action="store_true", help="1회 폴링 후 종료")
    args = parser.parse_args()

    if args.once:
        asyncio.run(poll_once())
    else:
        signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
        asyncio.run(main_loop())
