#!/usr/bin/env python3
"""
telegram-bridge.py v3.0 — WSL 네이티브 브릿지
  User -> @mention -> Bot API -> bridge.py -> inbox/{role}/
                                        -> tmux send-keys (local)
                                        -> subprocess claude --print -> response
"""
import json, os, sys, time, signal, subprocess, threading
import urllib.request, urllib.error, urllib.parse, logging
from datetime import datetime, timezone
from pathlib import Path

BOT_TOKEN = "7574253601:AAHkD6V3uvb3gVQhqF4hJE_r39vaT4Iu_yA"
CHAT_ID = "6858098283"
POLL_TIMEOUT = 30
POLL_INTERVAL = 5

BASE_DIR = Path.home() / "hq"
INBOX_DIR = BASE_DIR / "inbox"
STATE_DIR = BASE_DIR / "state"
LOG_DIR = BASE_DIR / "logs"
TELEGRAM_LOG_DIR = LOG_DIR / "telegram"
BRIDGE_LOG_DIR = LOG_DIR / "bridge"
OFFSETS_FILE = STATE_DIR / "offsets.json"

ROLE_SESSION = {"secretary": "phone_claude", "auditor": "phone_aider", "aider": "phone_aider"}
ROLE_TAGS = {
    "@비서실장": "secretary", "@secretary": "secretary",
    "@감사관": "auditor", "@auditor": "auditor",
    "@에이더": "aider", "@aider": "aider",
    "@all": "all", "@everyone": "all",
}

AGENT_PROMPTS = {
    "secretary": (
        "You are the Chief Secretary (비서실장) of HQ. You manage infrastructure, "
        "Telegram bridge, and agent orchestration on WSL/Windows.\n"
        "Answer concisely in Korean. Keep under 2000 chars.\n\nMessage: {text}"
    ),
    "auditor": (
        "You are the Auditor (감사관) of HQ. Audit code, review logs, monitor health.\n"
        "Answer concisely in Korean. Be direct and analytical.\n\nMessage: {text}"
    ),
}

logger = logging.getLogger("tg-bridge")
logger.setLevel(logging.DEBUG)
_fh = logging.FileHandler(str(BRIDGE_LOG_DIR / "bridge.log"), encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(_fh)
_sh = logging.StreamHandler()
_sh.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(_sh)
for h in logger.handlers:
    orig = h.emit
    def _emit(r, orig=orig, h=h): orig(r); h.flush()
    h.emit = _emit

def kst_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " KST"

def kst_date():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def kst_ts():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def telegram_api(method, params=None):
    if params is None: params = {}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode() if params else None
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=POLL_TIMEOUT+5) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP {e.code}: {e.read().decode() if e.fp else ''}")
        return {"ok": False, "error": str(e)}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        logger.warning(f"Network: {e}")
        return {"ok": False, "error": str(e)}

def send_message(text):
    r = telegram_api("sendMessage", {"chat_id": CHAT_ID, "text": text})
    ok = r.get("ok", False)
    if ok:
        logger.info(f"Sent ({len(text)} chars)")
    else:
        logger.error(f"Send fail: {r.get('error')}")
    return ok

def dispatch_tmux(role, text, sender):
    session = ROLE_SESSION.get(role)
    if not session: return False
    instruction = f"[TG:{role}:{sender}] {text}"
    safe = instruction.replace("'", "'\\''")
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, f"echo '{safe}'", "Enter"],
                      capture_output=True, timeout=10)
        logger.info(f"tmux->{session} ({instruction[:60]})")
        return True
    except Exception as e:
        logger.warning(f"tmux fail: {e}")
        return False

def agent_respond(role, user_text, sender_name):
    import uuid
    prompt = AGENT_PROMPTS.get(role, AGENT_PROMPTS["secretary"]).format(text=user_text)
    label = {"secretary": "비서실장", "auditor": "감사관"}.get(role, role)
    send_message(f"⏳ @{label} 응답 준비 중...")
    try:
        logger.info(f"Respond: {role} ({user_text[:50]})")
        tmp = f"/tmp/tg_{uuid.uuid4().hex}.txt"
        with open(tmp, "w", encoding="utf-8") as f: f.write(prompt)
        result = subprocess.run(["claude", "--print"], stdin=open(tmp), capture_output=True, timeout=180)
        os.unlink(tmp)
        resp = result.stdout.strip()
        if not resp:
            send_message(f"⚠️ @{label} 응답 없음"); return
        if len(resp) > 4000: resp = resp[:3997] + "..."
        send_message(f"\U0001f4ec [{label}] {sender_name}님 회신:\n\n{resp}")
        logger.info(f"Response: {role} ({len(resp)} chars)")
    except subprocess.TimeoutExpired:
        send_message(f"⏰ @{label} 시간 초과")
    except Exception as e:
        logger.error(f"Agent: {e}"); send_message(f"⚠️ @{label} 오류: {e}")

def parse_mentions(text):
    return [ROLE_TAGS[w.strip()] for w in text.split() if w.strip() in ROLE_TAGS]

def load_offset():
    if OFFSETS_FILE.exists():
        try: return json.load(open(OFFSETS_FILE)).get("last_update_id", 0)
        except: pass
    return 0

def save_offset(uid):
    OFFSETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"last_update_id": uid, "updated_at": kst_now()}, open(OFFSETS_FILE, "w"))

def route_message(update):
    msg = update.get("message", {})
    text = msg.get("text", "").strip()
    update_id = update.get("update_id", 0)
    msg_id = msg.get("message_id", 0)
    sender = msg.get("from", {})
    if sender.get("is_bot"): return

    mentions = parse_mentions(text)
    target_roles = mentions if mentions else ["all"]

    obj = {
        "update_id": update_id, "message_id": msg_id,
        "from": sender.get("first_name", ""), "text": text,
        "mentions": mentions, "routed_to": target_roles,
        "received_at": kst_now(),
    }
    ts = kst_ts()

    for role in set(target_roles):
        p = INBOX_DIR / role; p.mkdir(parents=True, exist_ok=True)
        json.dump(obj, open(p / f"{ts}_{msg_id}.json", "w"), ensure_ascii=False, indent=2)
        dispatch_tmux(role, text, sender.get("first_name", ""))

    save_offset(update_id)

    if target_roles != ["all"]:
        names = {"secretary": "비서실장", "auditor": "감사관", "aider": "에이더"}
        send_message(f"✅ 접수 — {', '.join(names.get(r,r) for r in set(target_roles))} 전달됨")
        sn = sender.get("first_name", "")
        for role in set(target_roles):
            if role in ("secretary", "auditor"):
                t = threading.Thread(target=agent_respond, args=(role, text, sn), daemon=True)
                t.start()

running = True

def signal_handler(signum, frame):
    global running; running = False; logger.info(f"Signal {signum}")

def poll_loop():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    for d in [INBOX_DIR, STATE_DIR, TELEGRAM_LOG_DIR, BRIDGE_LOG_DIR]: d.mkdir(parents=True, exist_ok=True)
    logger.info("="*50)
    logger.info("tg-bridge v3.0 WSL native")
    logger.info(f"Inbox: {INBOX_DIR}")
    logger.info("="*50)
    offset = load_offset()
    logger.info(f"Offset: {offset}")
    while running:
        try:
            result = telegram_api("getUpdates", {"offset": offset+1, "timeout": POLL_TIMEOUT, "allowed_updates": json.dumps(["message"])})
        except Exception as e:
            logger.error(f"Poll: {e}"); time.sleep(POLL_INTERVAL); continue
        if not result.get("ok"): time.sleep(POLL_INTERVAL); continue
        updates = result.get("result", [])
        if not updates: time.sleep(0.1); continue
        logger.info(f"{len(updates)} updates")
        for u in updates:
            try:
                route_message(u); uid = u.get("update_id", 0)
                if uid > offset: offset = uid
            except Exception as e:
                logger.error(f"Route: {e}", exc_info=True)
                uid = u.get("update_id", 0)
                if uid > offset: offset = uid; save_offset(offset)
    logger.info("Stopped.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--send":
        text = " ".join(sys.argv[2:]) if sys.argv[2:] else sys.stdin.read().strip()
        sys.exit(0 if text and send_message(text) else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "--once":
        off = load_offset()
        r = telegram_api("getUpdates", {"offset": off+1, "timeout": 5, "allowed_updates": json.dumps(["message"])})
        if r.get("ok"):
            for u in r.get("result", []): route_message(u)
    else:
        poll_loop()
