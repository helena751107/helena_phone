#!/usr/bin/env python3
"""
pd_pipeline_mcp.py — PD Pipeline MCP Server v1.0

Short-form video production on demand.
produce_pd.sh wrapper — start, monitor, stop, list.

Usage:
  python3 pd_pipeline_mcp.py          # STDIO mode (Claude Code direct)
  python3 pd_pipeline_mcp.py --http    # HTTP mode (curl-able, port 8765)

Register (~/.claude.json mcpServers):
  "pd-pipeline": {
    "command": "python3",
    "args": ["/root/work/helena-programming/mcp/pd_pipeline_mcp.py"]
  }

Tools:
  pd_produce  — Run full PD pipeline (ep_id, url, bgm_volume, voice)
  pd_status   — Check job status (running/complete/failed)
  pd_list     — List available episodes (shot_bible.json directories)
  pd_stop     — Stop a running pipeline job
  pd_output   — Get output file paths for a completed job
"""

import json
import os
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── Paths ───────────────────────────────────────────────────────────────
ROOT = Path("/root/work")
PRODUCE_SCRIPT = ROOT / "scripts" / "produce_pd.sh"
OUT_BASE = ROOT / "out"
TOOLS_DIR = ROOT / "helena-programming" / "tools"
JOBS_FILE = Path("/tmp/pd_mcp_jobs.json")

# ─── Tool definitions ────────────────────────────────────────────────────
TOOLS: list[dict[str, Any]] = [
    {
        "name": "pd_produce",
        "description": "PD 파이프라인 풀가동 — Playwright 캡처 → Edge TTS → Ken Burns xfade → BGM 더킹 → ASS 자막 → QA → TG 전송. produce_pd.sh를 백그라운드로 실행하고 job_id를 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ep_id": {
                    "type": "string",
                    "description": "에피소드 ID (out/ 아래 디렉토리명). 예: pd_intro, pd_magic, pd_sherpa",
                },
                "url": {
                    "type": "string",
                    "description": "캡처할 페이지 URL. 기본값: https://helena751107.github.io/helena_phone/",
                },
                "bgm_volume": {
                    "type": "number",
                    "description": "BGM 볼륨 (0.0~1.0). 기본값 0.025 (golden whisper)",
                },
                "voice": {
                    "type": "string",
                    "description": "TTS 음성. 기본값: ko-KR-YuJinNeural (유진 · 차분한 여성 내레이션, Edge 무료)",
                },
                "force": {
                    "type": "boolean",
                    "description": "기존 출력 덮어쓰기 (기본: false, 이미 있으면 스킵)",
                },
            },
            "required": ["ep_id"],
        },
    },
    {
        "name": "pd_status",
        "description": "파이프라인 작업 상태 확인. job_id 없으면 최근 10개 작업 목록을 보여줍니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "확인할 작업 ID. 생략 시 최근 작업 목록.",
                }
            },
        },
    },
    {
        "name": "pd_list",
        "description": "사용 가능한 에피소드 목록 — out/ 아래 shot_bible.json이 있는 모든 디렉토리.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "pd_stop",
        "description": "실행 중인 PD 파이프라인 작업을 중지합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "중지할 작업 ID. 생략 시 가장 최근 실행 중인 작업을 중지.",
                }
            },
        },
    },
    {
        "name": "pd_output",
        "description": "완료된 작업의 출력 파일 경로와 크기를 확인합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "작업 ID. 생략 시 가장 최근 완료된 작업.",
                }
            },
        },
    },
]


# ─── Job management ──────────────────────────────────────────────────────
def load_jobs() -> dict:
    """Load job state from disk."""
    if JOBS_FILE.exists():
        try:
            return json.loads(JOBS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_jobs(jobs: dict) -> None:
    """Persist job state to disk."""
    JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    JOBS_FILE.write_text(json.dumps(jobs, indent=2, ensure_ascii=False))


def _job_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def list_episodes() -> list[dict]:
    """Scan out/ for episodes with shot_bible.json."""
    episodes = []
    if not OUT_BASE.exists():
        return episodes
    for d in sorted(OUT_BASE.iterdir()):
        if not d.is_dir():
            continue
        bible = d / "shot_bible.json"
        if not bible.exists():
            continue
        try:
            meta = json.loads(bible.read_text())
        except (json.JSONDecodeError, OSError):
            meta = {}
        playable = d / f"{d.name}_playable.mp4"
        tg_file = d / f"{d.name}_tg.mp4"
        episodes.append(
            {
                "id": d.name,
                "version": meta.get("version", "?"),
                "url": meta.get("url", "?"),
                "beats": len(meta.get("beats", [])),
                "has_playable": playable.exists(),
                "playable_mb": round(playable.stat().st_size / 1e6, 1) if playable.exists() else 0,
                "has_tg": tg_file.exists(),
                "tg_mb": round(tg_file.stat().st_size / 1e6, 1) if tg_file.exists() else 0,
            }
        )
    return episodes


def produce(ep_id: str, url: str, bgm_volume: float, voice: str = "ko-KR-YuJinNeural", force: bool = False) -> dict:
    """Launch produce_pd.sh as a background job."""
    outdir = OUT_BASE / ep_id
    playable = outdir / f"{ep_id}_playable.mp4"

    if playable.exists() and not force:
        return {
            "ok": False,
            "error": f"이미 완료된 에피소드입니다: {playable} ({playable.stat().st_size/1e6:.1f}MB). force=true 로 재실행하세요.",
            "ep_id": ep_id,
        }

    job_id = f"pd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    log_file = Path("/tmp") / f"{job_id}.log"
    env = os.environ.copy()
    env["EP"] = ep_id
    env["URL"] = url
    env["OUTDIR"] = str(outdir)
    env["BGM_VOLUME"] = str(bgm_volume)
    env["VOICE"] = voice
    env["TTS_ENGINE"] = "edge"

    with open(log_file, "w") as f:
        proc = subprocess.Popen(
            ["bash", str(PRODUCE_SCRIPT), ep_id, url],
            stdout=f,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=str(ROOT),
        )

    jobs = load_jobs()
    jobs[job_id] = {
        "ep_id": ep_id,
        "url": url,
        "pid": proc.pid,
        "status": "running",
        "started": _job_now(),
        "ended": None,
        "log": str(log_file),
        "outdir": str(outdir),
        "bgm_volume": bgm_volume,
        "voice": voice,
        "exit_code": None,
    }
    save_jobs(jobs)

    return {
        "ok": True,
        "job_id": job_id,
        "ep_id": ep_id,
        "pid": proc.pid,
        "status": "running",
        "log": str(log_file),
        "outdir": str(outdir),
        "hint": f"pd_status('{job_id}') 로 진행상황을 확인하세요. 예상 소요시간: 3~5분.",
    }


def check_job(job_id: str | None) -> dict:
    """Check status of one or all jobs."""
    jobs = load_jobs()

    if job_id:
        if job_id not in jobs:
            return {"ok": False, "error": f"작업을 찾을 수 없습니다: {job_id}"}
        job = jobs[job_id]

        # Refresh status — check if process is still alive
        if job["status"] == "running" and job.get("pid"):
            try:
                os.kill(job["pid"], 0)  # signal 0 = check exists
            except OSError:
                # Process is gone — check exit
                job["status"] = "complete"
                job["ended"] = _job_now()
                job["exit_code"] = _reap_exit_code(job["pid"])
                save_jobs(jobs)

        # Append tail of log
        log_path = Path(job["log"]) if job.get("log") else None
        log_tail = ""
        if log_path and log_path.exists():
            lines = log_path.read_text().splitlines()
            log_tail = "\n".join(lines[-15:]) if len(lines) > 15 else "\n".join(lines)

        return {
            "ok": True,
            "job_id": job_id,
            **{k: v for k, v in job.items()},
            "log_tail": log_tail,
        }

    # No job_id — list recent
    recent = []
    for jid, j in sorted(jobs.items(), key=lambda x: x[1].get("started", ""), reverse=True)[:10]:
        # Refresh running jobs
        if j["status"] == "running" and j.get("pid"):
            try:
                os.kill(j["pid"], 0)
            except OSError:
                j["status"] = "complete"
                j["ended"] = _job_now()
                j["exit_code"] = _reap_exit_code(j["pid"])
        recent.append({"job_id": jid, **{k: v for k, v in j.items() if k != "log"}})

    if jobs != load_jobs():
        save_jobs(jobs)

    return {"ok": True, "total": len(jobs), "jobs": recent}


def _reap_exit_code(pid: int) -> int | None:
    """Try to get exit code of a finished process."""
    try:
        _, status = os.waitpid(pid, os.WNOHANG)
        if os.WIFEXITED(status):
            return os.WEXITSTATUS(status)
        if os.WIFSIGNALED(status):
            return -os.WTERMSIG(status)
    except ChildProcessError:
        pass
    return None


def stop_job(job_id: str | None) -> dict:
    """Stop a running pipeline job."""
    jobs = load_jobs()

    if not job_id:
        # Find most recent running
        running = [
            (jid, j)
            for jid, j in sorted(jobs.items(), key=lambda x: x[1].get("started", ""), reverse=True)
            if j["status"] == "running"
        ]
        if not running:
            return {"ok": False, "error": "실행 중인 작업이 없습니다."}
        job_id = running[0][0]

    if job_id not in jobs:
        return {"ok": False, "error": f"작업을 찾을 수 없습니다: {job_id}"}

    job = jobs[job_id]
    if job["status"] != "running":
        return {"ok": False, "error": f"작업이 실행 중이 아닙니다: {job['status']}"}

    pid = job.get("pid")
    killed = False
    if pid:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            time.sleep(0.5)
            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except OSError:
                pass
            killed = True
        except OSError:
            pass

    job["status"] = "stopped"
    job["ended"] = _job_now()
    save_jobs(jobs)

    return {"ok": True, "job_id": job_id, "killed": killed, "status": "stopped"}


def get_output(job_id: str | None) -> dict:
    """Get output file info for a completed job."""
    jobs = load_jobs()

    if not job_id:
        completed = [
            (jid, j)
            for jid, j in sorted(jobs.items(), key=lambda x: x[1].get("started", ""), reverse=True)
            if j["status"] in ("complete",)
        ]
        if not completed:
            return {"ok": False, "error": "완료된 작업이 없습니다."}
        job_id = completed[0][0]

    if job_id not in jobs:
        return {"ok": False, "error": f"작업을 찾을 수 없습니다: {job_id}"}

    job = jobs[job_id]
    outdir = Path(job["outdir"])
    ep_id = job["ep_id"]

    files = {}
    for suffix, label in [
        ("_playable.mp4", "playable"),
        ("_tg.mp4", "telegram_720p"),
        ("_final.mp4", "final_1080p"),
        (".ass", "ass_subtitles"),
        (".srt", "srt_subtitles"),
    ]:
        f = outdir / f"{ep_id}{suffix}"
        if f.exists():
            files[label] = {"path": str(f), "size_mb": round(f.stat().st_size / 1e6, 1)}

    return {"ok": True, "job_id": job_id, "ep_id": ep_id, "status": job["status"], "files": files}


# ─── MCP handler (STDIO JSON-RPC) ────────────────────────────────────────
def handle_request(method: str, params: dict | None = None) -> dict:
    """Route MCP JSON-RPC methods."""
    params = params or {}

    if method == "tools/list":
        return {"tools": TOOLS}

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "pd_list":
                return {
                    "content": [{"type": "text", "text": json.dumps({"episodes": list_episodes()}, indent=2, ensure_ascii=False)}]
                }
            elif name == "pd_produce":
                result = produce(
                    ep_id=args.get("ep_id", "pd_intro"),
                    url=args.get("url", "https://helena751107.github.io/helena_phone/"),
                    bgm_volume=float(args.get("bgm_volume", 0.025)),
                    voice=args.get("voice", "ko-KR-YuJinNeural"),
                    force=bool(args.get("force", False)),
                )
                return {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}
            elif name == "pd_status":
                result = check_job(args.get("job_id"))
                return {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}
            elif name == "pd_stop":
                result = stop_job(args.get("job_id"))
                return {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}
            elif name == "pd_output":
                result = get_output(args.get("job_id"))
                return {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}
            else:
                return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}

    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "pd-pipeline", "version": "1.0.0"},
        }

    if method == "notifications/initialized":
        return {}

    return {"error": f"Unknown method: {method}"}


# ─── HTTP mode (for testing / standalone operation) ──────────────────────
def run_http(port: int = 8765):
    """Minimal HTTP JSON-RPC server — no dependencies beyond stdlib."""
    import http.server

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            try:
                req = json.loads(body)
            except json.JSONDecodeError:
                self._respond(400, {"error": "invalid json"})
                return
            result = handle_request(req.get("method", ""), req.get("params"))
            self._respond(200, result)

        def do_GET(self):
            if self.path == "/health":
                self._respond(200, {"status": "ok", "server": "pd-pipeline-mcp"})
            elif self.path == "/tools":
                self._respond(200, {"tools": [t["name"] for t in TOOLS]})
            else:
                self._respond(200, {
                    "server": "pd-pipeline-mcp v1.0",
                    "endpoints": {
                        "POST /": "JSON-RPC (tools/call, tools/list, initialize)",
                        "GET /health": "Health check",
                        "GET /tools": "Tool list",
                    }
                })

        def _respond(self, code: int, data: dict):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass  # quiet

    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print(f"[pd-pipeline MCP] HTTP mode — http://0.0.0.0:{port}", file=sys.stderr)
    print(f"[pd-pipeline MCP] Tools: {[t['name'] for t in TOOLS]}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[pd-pipeline MCP] shutting down...", file=sys.stderr)
        server.shutdown()


# ─── STDIO mode (Claude Code direct) ─────────────────────────────────────
def run_stdio():
    """STDIO JSON-RPC mode — Claude Code MCP protocol."""
    print(f"[pd-pipeline MCP] v1.0 — STDIO mode", file=sys.stderr)
    print(f"[pd-pipeline MCP] Tools: {[t['name'] for t in TOOLS]}", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"error": "invalid json"}), flush=True)
            continue

        result = handle_request(req.get("method", ""), req.get("params"))
        print(json.dumps(result), flush=True)


# ─── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--http" in sys.argv:
        port = 8765
        for i, a in enumerate(sys.argv):
            if a == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        run_http(port)
    elif "--list" in sys.argv:
        print(json.dumps({"episodes": list_episodes()}, indent=2, ensure_ascii=False))
    elif "--produce" in sys.argv:
        ep = sys.argv[sys.argv.index("--produce") + 1] if "--produce" in sys.argv and sys.argv.index("--produce") + 1 < len(sys.argv) else "pd_intro"
        url = "https://helena751107.github.io/helena_phone/"
        result = produce(ep, url, 0.025, "ko-KR-YuJinNeural", True)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        run_stdio()
