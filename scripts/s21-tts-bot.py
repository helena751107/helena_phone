#!/usr/bin/env python3
"""
S21 TTS Bot — 🔊 읽어주기 버튼 처리 (최소형)
버튼 탭 → 음성 생성 → 전송. 중간 메시지 없음. 로그 최소화.

사용법:
  python3 s21-tts-bot.py --daemon
  bash s21-tts-bot.sh start
"""

import sys, os, json, time, signal, asyncio, tempfile, requests, argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_token():
    env_file = os.path.join(os.path.dirname(SCRIPT_DIR), ".secrets.env")
    t = os.environ.get("TG_TOKEN", "")
    if not t and os.path.exists(env_file):
        for line in open(env_file):
            if line.startswith("TG_TOKEN="):
                t = line.split("=", 1)[1].strip().strip('"')
                break
    return t or os.environ.get("TG_TOKEN", "")

TG_TOKEN = load_token()
TG_API = f"https://api.telegram.org/bot{TG_TOKEN}"

VOICES = {"injoon": "ko-KR-InJoonNeural", "sunhi": "ko-KR-SunHiNeural"}
DEFAULT_VOICE = "sunhi"

async def text_to_voice(text: str, voice_key: str = "sunhi") -> str | None:
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
        pass
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)
    return None

def tg_send_voice(chat_id: int, mp3_path: str):
    with open(mp3_path, "rb") as f:
        requests.post(f"{TG_API}/sendVoice",
                      data={"chat_id": chat_id},
                      files={"voice": (os.path.basename(mp3_path), f)},
                      timeout=30)

def tg_answer(cb_id: str):
    requests.post(f"{TG_API}/answerCallbackQuery",
                  json={"callback_query_id": cb_id}, timeout=5)

# ── 콜백 처리 ──────────────────────────────────────
async def handle_callback(cb: dict):
    cb_id = cb["id"]
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id", 0)
    text = msg.get("text", "")
    data = cb.get("data", "")

    if data != "tts_read" or not text:
        tg_answer(cb_id)
        return

    # 로딩 표시만 짧게 (버튼 멈춤 방지)
    requests.post(f"{TG_API}/answerCallbackQuery",
                  json={"callback_query_id": cb_id}, timeout=5)

    mp3 = await text_to_voice(text[:1200])
    if mp3:
        tg_send_voice(chat_id, mp3)
        os.unlink(mp3)

# ── 폴링 ───────────────────────────────────────────
async def poll_once(offset: int = 0) -> int:
    try:
        resp = requests.get(f"{TG_API}/getUpdates",
                           params={"offset": offset, "limit": 5, "timeout": 10},
                           timeout=15)
        for u in resp.json().get("result", []):
            offset = max(offset, u["update_id"] + 1)
            cb = u.get("callback_query")
            if cb:
                await handle_callback(cb)
    except Exception:
        pass
    return offset

async def main_loop():
    try:
        r = requests.get(f"{TG_API}/getUpdates", params={"limit": 1}, timeout=10)
        offset = max([u["update_id"] + 1 for u in r.json().get("result", [])], default=0)
    except:
        offset = 0

    while True:
        offset = await poll_once(offset)
        await asyncio.sleep(3)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", "-d", action="store_true")
    args = parser.parse_args()
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    asyncio.run(main_loop())