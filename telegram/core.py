"""
Parksy Telegram Bot Core — v2.1 Production
==========================================
공유 엔진: AsyncStreamClaude + DraftStreamer + SessionDB + AccessControl

두 봇이 이 파일 하나를 공유.
- @parksy_bridge_bot  (이미지+Claude)
- @parksy_bridges_bot (오디오+Claude)

권한 구조:
  ADMIN  → 자연어 명령 + 파일 드랍 + 모든 명령어
  SLOT   → 파일 드랍만 (이미지/문서/오디오) → 자동 처리 → 결과 전송
"""

import asyncio
import json
import os
import re
import sys
import time
import aiosqlite
from pathlib import Path

# ─── 설정 ───────────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "sessions.db"
CLAUDE_TIMEOUT = 300       # seconds
DRAFT_THROTTLE = 0.5       # telegram edit 최소 간격
MAX_MSG_LEN = 3800         # telegram 4096 한도, 여유 남김

TOOL_ICONS = {
    "Read":    "📖",
    "Edit":    "✏️",
    "Write":   "📝",
    "Bash":    "💻",
    "Glob":    "📂",
    "Grep":    "🔍",
    "WebFetch":"🌐",
    "WebSearch":"🔎",
}

# ─── SessionDB ───────────────────────────────────────────────────────────────

class SessionDB:
    """SQLite 기반 세션 저장소. (chat_id, workdir) → claude session_id"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = str(db_path)
        self._db: aiosqlite.Connection | None = None

    async def init(self):
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                chat_id   TEXT,
                workdir   TEXT,
                session_id TEXT,
                updated_at REAL,
                PRIMARY KEY (chat_id, workdir)
            )
        """)
        await self._db.commit()

    async def get(self, chat_id: int, workdir: str) -> str | None:
        async with self._db.execute(
            "SELECT session_id FROM sessions WHERE chat_id=? AND workdir=?",
            (str(chat_id), workdir)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None

    async def save(self, chat_id: int, workdir: str, session_id: str):
        await self._db.execute("""
            INSERT OR REPLACE INTO sessions (chat_id, workdir, session_id, updated_at)
            VALUES (?, ?, ?, ?)
        """, (str(chat_id), workdir, session_id, time.time()))
        await self._db.commit()

    async def delete(self, chat_id: int, workdir: str):
        await self._db.execute(
            "DELETE FROM sessions WHERE chat_id=? AND workdir=?",
            (str(chat_id), workdir)
        )
        await self._db.commit()

    async def close(self):
        if self._db:
            await self._db.close()


# ─── DraftStreamer ────────────────────────────────────────────────────────────

class DraftStreamer:
    """
    Claude 출력을 실시간으로 Telegram 메시지에 반영.
    같은 메시지를 계속 editMessageText로 업데이트.
    (RichardAtCT DraftStreamer 방식 참고, Claude Max CLI 적용)
    """

    def __init__(self, bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id: int | None = None
        self._text = ""
        self._tool_lines: list[str] = []
        self._last_edit = 0.0
        self._last_sent = ""   # 중복 편집 방지
        self._finalized = False

    async def start(self, initial: str = "⏳ 생각 중..."):
        msg = await self.bot.send_message(self.chat_id, initial)
        self.message_id = msg.message_id

    def on_text(self, full_text: str):
        self._text = full_text

    def on_tool(self, tool_name: str, tool_input: dict):
        icon = TOOL_ICONS.get(tool_name, "🔧")
        # input 요약 (첫 70자)
        raw = json.dumps(tool_input, ensure_ascii=False)
        summary = raw[:70] + ("…" if len(raw) > 70 else "")
        self._tool_lines.append(f"{icon} `{tool_name}` {summary}")
        if len(self._tool_lines) > 6:
            self._tool_lines = self._tool_lines[-6:]

    async def tick(self):
        """주기적 업데이트 - 0.5s throttle"""
        now = time.monotonic()
        if now - self._last_edit < DRAFT_THROTTLE:
            return
        await self._do_edit()

    async def finalize(self, final_text: str | None = None):
        """최종 결과 업데이트"""
        if final_text:
            self._text = final_text
        self._tool_lines = []
        await self._do_edit(is_final=True)
        self._finalized = True

    async def _do_edit(self, is_final: bool = False):
        if not self.message_id:
            return
        body = self._build()
        # 내용이 동일하면 edit 스킵 (Telegram 400 "message is not modified" 방지)
        if body == self._last_sent:
            return
        try:
            await self.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=body,
                parse_mode=None,
            )
            self._last_sent = body
            self._last_edit = time.monotonic()
        except Exception as e:
            err = str(e).lower()
            if "message is not modified" in err:
                self._last_sent = body  # 이미 전달됨 — 정상
                return
            if is_final:
                # 최종 결과 edit 실패 시 새 메시지로 fallback
                try:
                    await self.bot.send_message(self.chat_id, body)
                    self._last_sent = body
                except Exception:
                    pass

    def _build(self) -> str:
        parts = []

        # 툴 활동 헤더
        if self._tool_lines:
            parts.append("\n".join(self._tool_lines))
            parts.append("─────────────")

        # 본문
        text = self._text or "⏳ 처리 중..."
        # 너무 길면 뒷부분만 표시
        if len(text) > MAX_MSG_LEN:
            text = "…\n" + text[-MAX_MSG_LEN:]
        parts.append(text)

        return "\n".join(parts)


# ─── AsyncStreamClaude ────────────────────────────────────────────────────────

class AsyncStreamClaude:
    """
    claude -p PROMPT --output-format stream-json 을 비동기 subprocess로 실행.
    줄별 NDJSON 파싱 → DraftStreamer 실시간 업데이트.
    """

    ALLOWED_TOOLS = "Bash,Read,Write,Edit,Glob,Grep"

    def __init__(
        self,
        workdir: str,
        streamer: DraftStreamer,
        session_id: str | None = None,
        allowed_tools: str | None = None,
        system_prompt: str | None = None,
        model: str | None = None,
    ):
        self.workdir = workdir
        self.streamer = streamer
        self.session_id = session_id
        self.allowed_tools = allowed_tools or self.ALLOWED_TOOLS
        self.system_prompt = system_prompt
        self.model = model
        self._proc: asyncio.subprocess.Process | None = None

    async def run(self, prompt: str) -> tuple[str, str | None]:
        """
        Returns: (final_text, new_session_id)
        """
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "stream-json",
            "--verbose",
            "--allowedTools", self.allowed_tools,
        ]
        if self.session_id:
            cmd += ["--resume", self.session_id]
        if self.system_prompt:
            cmd += ["--system-prompt", self.system_prompt]
        if self.model:
            cmd += ["--model", self.model]

        self._proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.workdir,
        )

        accumulated_text = ""
        new_session_id = self.session_id

        # 스트림 읽기 + 주기적 Telegram 업데이트
        tick_task = asyncio.create_task(self._tick_loop())

        try:
            async for raw_line in self._proc.stdout:
                line = raw_line.decode(errors="replace").strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ev_type = ev.get("type", "")

                if ev_type == "system" and ev.get("subtype") == "init":
                    sid = ev.get("session_id")
                    if sid:
                        new_session_id = sid

                elif ev_type == "assistant":
                    msg = ev.get("message", {})
                    for block in msg.get("content", []):
                        if block.get("type") == "text":
                            accumulated_text += block.get("text", "")
                    self.streamer.on_text(accumulated_text)

                elif ev_type == "tool_use":
                    self.streamer.on_tool(
                        ev.get("name", "tool"),
                        ev.get("input", {})
                    )

                elif ev_type == "result":
                    final = ev.get("result", "")
                    sid = ev.get("session_id")
                    if sid:
                        new_session_id = sid
                    if final:
                        accumulated_text = final

        finally:
            tick_task.cancel()
            try:
                await tick_task
            except asyncio.CancelledError:
                pass

        await self._proc.wait()
        return accumulated_text, new_session_id

    async def _tick_loop(self):
        """0.5초마다 Telegram 메시지 업데이트"""
        while True:
            await asyncio.sleep(DRAFT_THROTTLE)
            await self.streamer.tick()

    async def abort(self):
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()


# ─── CLAUDE.md 로더 ──────────────────────────────────────────────────────────

def load_claude_md(workdir: str) -> str | None:
    """workdir 안의 CLAUDE.md를 읽어서 system prompt로 주입"""
    p = Path(workdir) / "CLAUDE.md"
    if p.exists():
        content = p.read_text(encoding="utf-8")
        return f"[CLAUDE.md — 프로젝트 컨텍스트]\n{content[:3000]}"
    return None


# ─── 공통 메시지 헬퍼 ────────────────────────────────────────────────────────

def escape_md(text: str) -> str:
    """Telegram MarkdownV1 특수문자 이스케이프"""
    return re.sub(r'([_*`\[])', r'\\\1', text)


def split_message(text: str, max_len: int = 4000) -> list[str]:
    """긴 메시지를 max_len 단위로 분할"""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:max_len])
        text = text[max_len:]
    return chunks


# ─── AccessControl ────────────────────────────────────────────────────────────

class AccessControl:
    """
    권한 관리
    ADMIN : 자연어 명령 + 파일 + 모든 명령어
    SLOT  : 파일 드랍만 → 자동 처리
    NONE  : 차단
    """

    ROLE_ADMIN = "admin"
    ROLE_SLOT  = "slot"
    ROLE_NONE  = "none"

    def __init__(self, config: dict):
        self.admin_id: int = int(config["admin_id"])
        # slots: id가 null이면 비어있는 슬롯
        self.slots: list[dict] = config.get("slots", [])

    def role(self, user_id: int) -> str:
        if user_id == self.admin_id:
            return self.ROLE_ADMIN
        for s in self.slots:
            if s.get("id") and int(s["id"]) == user_id:
                return self.ROLE_SLOT
        return self.ROLE_NONE

    def is_admin(self, user_id: int) -> bool:
        return self.role(user_id) == self.ROLE_ADMIN

    def can_file(self, user_id: int) -> bool:
        return self.role(user_id) in (self.ROLE_ADMIN, self.ROLE_SLOT)

    def can_command(self, user_id: int) -> bool:
        return self.role(user_id) == self.ROLE_ADMIN

    def slot_name(self, user_id: int) -> str:
        for s in self.slots:
            if s.get("id") and int(s["id"]) == user_id:
                return s.get("name", "슬롯유저")
        return "알 수 없음"

    def add_slot(self, user_id: int, name: str, config_path: str) -> tuple[bool, str]:
        """빈 슬롯에 유저 추가. config 파일도 업데이트."""
        for i, s in enumerate(self.slots):
            if not s.get("id"):
                self.slots[i]["id"] = user_id
                self.slots[i]["name"] = name
                self._save(config_path)
                return True, f"슬롯{i+1} 등록 완료"
        return False, "슬롯이 가득 찼습니다 (최대 3명)"

    def remove_slot(self, user_id: int, config_path: str) -> tuple[bool, str]:
        """슬롯에서 유저 제거."""
        for i, s in enumerate(self.slots):
            if s.get("id") and int(s["id"]) == user_id:
                name = s.get("name", "")
                self.slots[i]["id"] = None
                self.slots[i]["name"] = ""
                self.slots[i]["note"] = ""
                self._save(config_path)
                return True, f"{name} 슬롯 해제 완료"
        return False, "해당 유저가 슬롯에 없습니다"

    def status_text(self) -> str:
        lines = [f"👑 어드민: `{self.admin_id}`", "", "📋 슬롯 현황:"]
        for i, s in enumerate(self.slots):
            uid = s.get("id")
            name = s.get("name") or "비어있음"
            note = s.get("note") or ""
            if uid:
                lines.append(f"  슬롯{i+1}: {name} (`{uid}`) {note}")
            else:
                lines.append(f"  슬롯{i+1}: — 비어있음")
        return "\n".join(lines)

    def _save(self, config_path: str):
        with open(config_path) as f:
            data = json.load(f)
        data["slots"] = self.slots
        with open(config_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
