#!/usr/bin/env python3
"""
telegram-bot.py — Park 전용 파일 전송 봇
용도: 폰 ↔ PC 대용량 파일 송수신 (Telegram 2GB 무료)
실행: python bot.py (WSL 환경, 24시간 데몬)

환경변수:
  BOT_TOKEN  — Telegram Bot 토큰 (@BotFather에서 발급)
  CHAT_ID    — 허용할 채팅 ID (보안용)

또는 config.json에서 읽음.
"""

import os
import sys
import json
import logging
import asyncio
import shutil
from pathlib import Path
from datetime import datetime

try:
    from telegram import Update, BotCommand
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        ContextTypes,
    )
except ImportError:
    print("[ERROR] python-telegram-bot 미설치")
    print("  pip install python-telegram-bot==20.7")
    sys.exit(1)

# === 설정 ===
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"

# 기본 설정
DEFAULT_CONFIG = {
    "bot_token": "",
    "allowed_chat_ids": [],
    "download_dir": str(SCRIPT_DIR / "downloads"),
    "upload_dir": str(SCRIPT_DIR / "uploads"),
    "d_drive": "/mnt/d",
    "max_file_size_mb": 2000,
    "auto_organize": True,
}


def load_config():
    """config.json 또는 환경변수에서 설정 로드"""
    config = DEFAULT_CONFIG.copy()

    # config.json 읽기
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            file_config = json.load(f)
            config.update(file_config)

    # 환경변수 우선
    if os.environ.get("BOT_TOKEN"):
        config["bot_token"] = os.environ["BOT_TOKEN"]
    if os.environ.get("CHAT_ID"):
        config["allowed_chat_ids"] = [int(os.environ["CHAT_ID"])]

    return config


config = load_config()

# === 로깅 ===
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(SCRIPT_DIR / "bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# === 보안: 허용된 사용자만 ===
def authorized(func):
    """허용된 chat_id만 접근 가능"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        allowed = config.get("allowed_chat_ids", [])
        if allowed and chat_id not in allowed:
            logger.warning(f"비인가 접근: chat_id={chat_id}")
            await update.message.reply_text(
                f"비인가 접근. 너의 chat_id: {chat_id}\n"
                "config.json의 allowed_chat_ids에 추가하세요."
            )
            return
        return await func(update, context)
    return wrapper


# === 명령어 핸들러 ===
@authorized
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇 시작 + 사용법"""
    chat_id = update.effective_chat.id
    msg = (
        "Park 파일 전송 봇 활성화\n\n"
        "명령어:\n"
        "/status — PC 상태 확인\n"
        "/ls [경로] — 파일 목록\n"
        "/get [경로] — PC에서 파일 받기\n"
        "/disk — 디스크 사용량\n"
        "/put — 이 봇에 파일 보내면 PC에 저장\n\n"
        f"chat_id: {chat_id}\n"
        f"다운로드 폴더: {config['download_dir']}\n"
        f"D: 드라이브: {config['d_drive']}"
    )
    await update.message.reply_text(msg)


@authorized
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """PC 상태 확인"""
    # 시스템 정보
    disk = shutil.disk_usage(config["d_drive"]) if Path(config["d_drive"]).exists() else None
    uptime = "unknown"
    try:
        with open("/proc/uptime", "r") as f:
            secs = float(f.read().split()[0])
            hours = int(secs // 3600)
            mins = int((secs % 3600) // 60)
            uptime = f"{hours}h {mins}m"
    except (FileNotFoundError, ValueError):
        pass

    msg = f"PC 상태\n\n"
    msg += f"Uptime: {uptime}\n"
    if disk:
        total_gb = disk.total / (1024**3)
        used_gb = disk.used / (1024**3)
        free_gb = disk.free / (1024**3)
        pct = (disk.used / disk.total) * 100
        msg += f"D: {used_gb:.0f}GB / {total_gb:.0f}GB ({pct:.0f}%) — {free_gb:.0f}GB 여유\n"

    # 다운로드 폴더 파일 수
    dl_dir = Path(config["download_dir"])
    if dl_dir.exists():
        files = list(dl_dir.iterdir())
        msg += f"다운로드 대기: {len(files)}개 파일\n"

    await update.message.reply_text(msg)


@authorized
async def cmd_ls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """디렉토리 목록"""
    args = context.args
    target = config["d_drive"] if not args else " ".join(args)

    # 보안: d_drive 밖 접근 제한
    target_path = Path(target).resolve()
    d_drive = Path(config["d_drive"]).resolve()
    if not str(target_path).startswith(str(d_drive)):
        await update.message.reply_text(f"D: 드라이브 외부 접근 불가: {target}")
        return

    if not target_path.exists():
        await update.message.reply_text(f"경로 없음: {target}")
        return

    items = sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    lines = []
    for item in items[:50]:  # 최대 50개
        if item.is_dir():
            lines.append(f"[DIR]  {item.name}/")
        else:
            size_mb = item.stat().st_size / (1024 * 1024)
            lines.append(f"       {item.name} ({size_mb:.1f}MB)")

    total = len(list(target_path.iterdir()))
    header = f"{target_path}\n{'=' * 40}\n"
    footer = f"\n총 {total}개" + (" (50개만 표시)" if total > 50 else "")

    await update.message.reply_text(header + "\n".join(lines) + footer)


@authorized
async def cmd_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """PC에서 파일을 Telegram으로 전송"""
    if not context.args:
        await update.message.reply_text("사용법: /get /mnt/d/path/to/file")
        return

    filepath = Path(" ".join(context.args))

    if not filepath.exists():
        await update.message.reply_text(f"파일 없음: {filepath}")
        return

    if not filepath.is_file():
        await update.message.reply_text(f"파일이 아님 (디렉토리?): {filepath}")
        return

    size_mb = filepath.stat().st_size / (1024 * 1024)
    if size_mb > config["max_file_size_mb"]:
        await update.message.reply_text(f"파일 너무 큼: {size_mb:.0f}MB (최대 {config['max_file_size_mb']}MB)")
        return

    await update.message.reply_text(f"전송 중: {filepath.name} ({size_mb:.1f}MB)...")

    try:
        with open(filepath, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=filepath.name,
                caption=f"From PC: {filepath}",
            )
        logger.info(f"파일 전송: {filepath} ({size_mb:.1f}MB)")
    except Exception as e:
        await update.message.reply_text(f"전송 실패: {e}")


@authorized
async def cmd_disk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """디스크 사용량"""
    paths = ["/mnt/d", "/mnt/c", "/"]
    lines = ["디스크 사용량\n"]

    for p in paths:
        if Path(p).exists():
            d = shutil.disk_usage(p)
            total = d.total / (1024**3)
            used = d.used / (1024**3)
            free = d.free / (1024**3)
            pct = (d.used / d.total) * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            lines.append(f"{p}\n  {bar} {pct:.0f}%\n  {used:.0f}G / {total:.0f}G ({free:.0f}G free)\n")

    await update.message.reply_text("\n".join(lines))


@authorized
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """파일 수신 → PC에 저장"""
    doc = update.message.document
    if not doc:
        # 사진/비디오도 처리
        if update.message.photo:
            photo = update.message.photo[-1]  # 가장 큰 사이즈
            file = await photo.get_file()
            filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        elif update.message.video:
            file = await update.message.video.get_file()
            filename = update.message.video.file_name or f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        else:
            return
    else:
        file = await doc.get_file()
        filename = doc.file_name or f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 저장 경로
    dl_dir = Path(config["download_dir"])
    dl_dir.mkdir(parents=True, exist_ok=True)

    if config.get("auto_organize"):
        # 날짜별 정리
        date_dir = dl_dir / datetime.now().strftime("%Y-%m-%d")
        date_dir.mkdir(exist_ok=True)
        save_path = date_dir / filename
    else:
        save_path = dl_dir / filename

    # 중복 방지
    if save_path.exists():
        stem = save_path.stem
        suffix = save_path.suffix
        i = 1
        while save_path.exists():
            save_path = save_path.parent / f"{stem}_{i}{suffix}"
            i += 1

    await file.download_to_drive(str(save_path))
    size_mb = save_path.stat().st_size / (1024 * 1024)

    logger.info(f"파일 수신: {save_path} ({size_mb:.1f}MB)")
    await update.message.reply_text(
        f"저장 완료\n"
        f"파일: {filename}\n"
        f"크기: {size_mb:.1f}MB\n"
        f"경로: {save_path}"
    )


# === 메인 ===
def main():
    token = config.get("bot_token", "")
    if not token:
        print("[ERROR] BOT_TOKEN 미설정")
        print("  방법 1: export BOT_TOKEN='your-token'")
        print("  방법 2: config.json에 bot_token 추가")
        print("  토큰 발급: Telegram에서 @BotFather에게 /newbot")
        sys.exit(1)

    logger.info("Park 파일 전송 봇 시작...")
    logger.info(f"다운로드: {config['download_dir']}")
    logger.info(f"D드라이브: {config['d_drive']}")

    app = Application.builder().token(token).build()

    # 명령어 등록
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("ls", cmd_ls))
    app.add_handler(CommandHandler("get", cmd_get))
    app.add_handler(CommandHandler("disk", cmd_disk))

    # 파일 수신 핸들러
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.PHOTO, handle_file))
    app.add_handler(MessageHandler(filters.VIDEO, handle_file))

    # 폴링 시작 (24시간 상주)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
