#!/usr/bin/env python3
"""
parksy_rawmat_mcp.py — Raw Material MCP 서버

로데이터 지식 추출 게이트웨이.
Playwright로 Perplexity Space에 직접 접속 → Computer 모드 → 메시지 전송 → 응답 수집.

등록 (~/.claude/settings.json):
  {
    "mcpServers": {
      "parksy-rawmat": {
        "command": "python3",
        "args": ["~/" + "dtslib-papyrus/parksy_rawmat_mcp.py"]
      }
    }
  }

사용 (Claude Code):
  mcp__parksy_rawmat__call_space_mcp space_id="body-bull" thesis="..." chain="..."
"""
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

# ── Playwright 조건부 임포트 ─────────────────────────────────
# Termux (phone aarch64)에서는 Chrome/Chromium 미지원 → playwright 설치 불가
# WSL/desktop에서는 정상 동작
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    _PLAYWRIGHT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    _PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None
    PwTimeout = Exception  # type: ignore

# ── FastMCP 서버 ────────────────────────────────────────────
mcp = FastMCP("parksy-rawmat", log_level="ERROR")

# ── DISPLAY 체크 ─────────────────────────────────────────────
_HEADLESS = os.environ.get("DISPLAY") is None

# ── 경로 ──────────────────────────────────────────────────────
BASE_DIR = Path.home() / "parksy-logs" / "perplexity"
CONFIG_PATH = BASE_DIR / "spaces_config.json"

# ── 확정 셀렉터 ──────────────────────────────────────────────
PERPLEXITY_BASE  = "https://www.perplexity.ai"
SEARCH_INPUT_CSS = "#ask-input"
ANSWER_PANEL_CSS = '[role="tabpanel"]'
WAIT_TIMEOUT_MS  = 180_000  # Computer 모드 딥리서치 포함 180초

# ── Evasion helpers ──────────────────────────────────────────
_JITTER_MIN = 0.3
_JITTER_MAX = 1.8

def _jitter(a: float = _JITTER_MIN, b: float = _JITTER_MAX) -> None:
    time.sleep(random.uniform(a, b))

def _human_type(page, selector: str, text: str) -> None:
    """글자 하나하나 타이핑 (랜덤 지터 + 오타)"""
    page.click(selector)
    _jitter(0.1, 0.4)
    for i, ch in enumerate(text):
        page.keyboard.type(ch, delay=random.randint(15, 90))
        if random.random() < 0.004 and len(text) > 15:
            page.keyboard.press("Backspace")
            _jitter(0.03, 0.1)
            page.keyboard.type(ch, delay=random.randint(20, 60))
        if i > 0 and i % random.randint(180, 280) == 0:
            _jitter(0.3, 1.0)

def _human_noise(page) -> None:
    """자연스러운 유휴 행동 — 스크롤/마우스/줌"""
    try:
        patterns = [
            lambda: page.evaluate(f"window.scrollBy(0,{random.randint(-120,120)})"),
            lambda: page.mouse.move(
                random.randint(100, 1100), random.randint(100, 700),
                steps=random.randint(3, 10)),
            lambda: page.evaluate(f"window.scrollTo(0,{random.randint(0,300)})"),
        ]
        random.choice(patterns)()
        _jitter(0.1, 0.3)
        if random.random() < 0.4:
            random.choice(patterns)()
        _jitter(0.05, 0.15)
    except Exception:
        pass

# ── config 로드 ────────────────────────────────────────────
def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)

def _get_space(config: dict, space_id: str) -> dict:
    for s in config["spaces"]:
        if s["id"] == space_id:
            return s
    raise ValueError(f"Space ID not found: {space_id}")

# ── 메시지 빌드 ────────────────────────────────────────────
def _build_message(space: dict, **payload) -> str:
    """
    Evasion v2.1: 라벨(EPISODE_ID, THESIS, CHAIN)은 Space 파싱 가능하도록 일관되게.
    episode_id 값 자체만 랜덤화 (episode_runner.py에서 포맷 다양화).
    """
    lines = []
    ep_id = payload.get('episode_id', 'EP-' + space['id'].upper())

    if random.random() >= 0.15:
        lines.append(f"EPISODE_ID: {ep_id}")

    if "thesis" in payload:
        lines.append(f"THESIS: {payload['thesis']}")

    if "field" in payload:
        lines.append(f"FIELD: {payload['field']}")

    if "chain" in payload:
        lines.append(f"CHAIN: {payload['chain']}")

    if "bull" in payload:
        b = payload['bull']
        label = "BULL EVIDENCE SUMMARY:" if random.random() < 0.8 else "BULL EVIDENCE:"
        lines.append(f"{label}\n{b}")

    if "bear" in payload:
        b = payload['bear']
        label = "BEAR EVIDENCE SUMMARY:" if random.random() < 0.8 else "BEAR EVIDENCE:"
        lines.append(f"{label}\n{b}")

    if "risk_list" in payload:
        rl = payload["risk_list"]
        lines.append(f"RISK LIST: {json.dumps(rl, ensure_ascii=False) if isinstance(rl, dict) else str(rl)}")

    if "domain_hint" in payload:
        lines.append(f"DOMAIN: {payload['domain_hint']}")

    if random.random() < 0.3:
        fillers = [
            "Could you help me analyze this?",
            "Would love to hear your thoughts on this.",
            "I've been thinking about this lately.",
            "Curious what evidence exists for/against this.",
            "Let me know what you find.",
        ]
        lines.append(random.choice(fillers))

    lines.append(f"\nTask: {space.get('role', '')}")
    return "\n".join(lines)

# ── 출력 노이즈 제거 ───────────────────────────────────────
def _clean(raw: str) -> str:
    noise = [
        "Help improve our product", "We made two versions of this answer",
        "Compare", "Completed", "steps", "More videos", "Ask a follow-up",
        "Stop response",
    ]
    lines = [l for l in raw.split("\n") if not any(n in l for n in noise)]
    return "\n".join(lines).strip()

# ── JSON 추출 ──────────────────────────────────────────────
def _extract_json(raw: str) -> str:
    m = re.search(r"```json?\n?(.*?)```", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    search_from = raw
    show_pos = raw.rfind("Show more")
    if show_pos != -1:
        search_from = raw[show_pos:]
    m = re.search(r"(\{|\[)", search_from)
    if m:
        return search_from[m.start():]
    return raw.strip()

# ── Playwright 호출 (내부) ─────────────────────────────────
def _call_via_playwright(space_url: str, message: str) -> str:
    """Space URL → Computer 모드 → 메시지 → 폴링 응답"""
    if not _PLAYWRIGHT_AVAILABLE:
        return json.dumps({
            "error": "Playwright not available on this platform (Termux aarch64)",
            "note": "This tool requires Chrome/Chromium which is not supported on Android Termux. "
                    "Run on WSL/desktop instead.",
            "space_url": space_url,
        })
    session_dir = Path.home() / ".config" / "perplexity_session"

    with sync_playwright() as p:
        ctx_kwargs = dict(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        extra = dict(
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        if session_dir.exists():
            browser = p.chromium.launch_persistent_context(
                str(session_dir), headless=_HEADLESS, **ctx_kwargs, **extra
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
        else:
            browser = p.chromium.launch(headless=_HEADLESS, **extra)
            ctx = browser.new_context(**ctx_kwargs)
            page = ctx.new_page()

        # 1. 접속
        page.goto(space_url, wait_until="domcontentloaded")
        _jitter(1.5, 3.5)

        # 2. 쿠키 팝업
        try:
            page.get_by_role("button", name="Got it").click(timeout=5000)
            _jitter(0.5, 1.2)
        except PwTimeout:
            pass

        # 3. Computer 모드 전환
        try:
            comp_btn = page.locator('button:has-text("Computer")')
            if comp_btn.is_visible(timeout=5000):
                is_active = comp_btn.get_attribute("aria-selected") or ""
                if "true" not in is_active:
                    comp_btn.click()
                    _jitter(0.8, 1.8)
        except Exception:
            pass

        # 4. 입력창 대기
        page.wait_for_selector(SEARCH_INPUT_CSS, timeout=15_000)
        _jitter(0.5, 1.2)

        # 5. 노이즈 + 타이핑
        _human_noise(page)
        _jitter(0.3, 0.8)
        _human_type(page, SEARCH_INPUT_CSS, message)
        _jitter(0.3, 0.8)
        page.keyboard.press("Enter")

        # 6. 폴링 응답 대기
        _jitter(1.0, 2.0)
        prev_len = 0
        stable_count = 0
        poll_start = time.time()
        last_raw = ""

        while time.time() - poll_start < WAIT_TIMEOUT_MS / 1000:
            _jitter(0.5, 1.5)
            try:
                raw = page.evaluate(f"""
                    () => {{
                        const panel = document.querySelector('{ANSWER_PANEL_CSS}');
                        return panel ? panel.innerText : '';
                    }}
                """)
                cur_len = len(raw.strip())
            except Exception:
                cur_len = 0
                raw = ""

            if cur_len > 0 and cur_len == prev_len:
                stable_count += 1
            else:
                stable_count = 0

            if cur_len > 0:
                last_raw = raw

            if stable_count >= 3:  # ~15초 안정화
                break
            prev_len = cur_len

        if not last_raw:
            try:
                last_raw = page.evaluate(f"""
                    () => {{
                        const panel = document.querySelector('{ANSWER_PANEL_CSS}');
                        return panel ? panel.innerText : '';
                    }}
                """)
            except Exception:
                last_raw = ""

        _human_noise(page)
        _jitter(0.3, 0.8)
        browser.close()

    return _clean(last_raw)


# ── JSON 검증 ──────────────────────────────────────────────
def _validate(space: dict, raw: str) -> dict:
    expected = space.get("expected_output", {})
    if isinstance(expected, str):
        return {"ok": True, "missing": [], "errors": []}
    fmt = expected.get("format", "")
    result = {"ok": True, "missing": [], "errors": []}
    if fmt == "json":
        try:
            clean = _extract_json(raw)
            data, _ = json.JSONDecoder().raw_decode(clean)
        except (json.JSONDecodeError, ValueError) as e:
            return {"ok": False, "missing": [], "errors": [f"JSON parse error: {e}"]}
        for field in expected.get("required_fields", []):
            if field not in data:
                result["ok"] = False
                result["missing"].append(field)
        for field, valid in expected.get("enums", {}).items():
            if field in data and data[field] not in valid:
                result["ok"] = False
                result["errors"].append(f"enum: {field}={data[field]!r}")
    elif fmt == "structured_text":
        for field in expected.get("required_fields", []):
            if not re.search(r"\b" + re.escape(field) + r"\b", raw, re.IGNORECASE):
                result["ok"] = False
                result["missing"].append(field)
    return result


def call_space(space_id: str, **payload) -> dict:
    """
    call_space() — Perplexity Space를 호출하고 전체 결과 dict를 반환.

    Args:
        space_id: spaces_config.json의 id (예: "body-bull")
        **payload: thesis, chain, bull, bear, risk_list, episode_id 등

    Returns:
        { "space_id": str, "ok": bool, "raw": str, "parsed": dict|str, "validation": dict, "tokens": 0 }
    """
    config = _load_config()
    space = _get_space(config, space_id)
    slug = space.get("slug", "")
    if not slug:
        raise ValueError(f"slug 없음: {space_id}")

    space_url = f"{PERPLEXITY_BASE}/spaces/{slug}"
    message = _build_message(space, **payload)
    raw = _call_via_playwright(space_url, message)

    validation = _validate(space, raw)
    exp_out = space.get("expected_output", {})
    fmt = "" if isinstance(exp_out, str) else exp_out.get("format", "")
    parsed = raw
    if fmt == "json" and validation["ok"]:
        try:
            clean = _extract_json(raw)
            parsed, _ = json.JSONDecoder().raw_decode(clean)
        except Exception:
            pass

    return {
        "space_id": space_id,
        "ok": validation["ok"],
        "raw": raw,
        "parsed": parsed,
        "validation": validation,
        "tokens": 0,
    }


# ── MCP Tools ──────────────────────────────────────────────

@mcp.tool()
def call_space_mcp(
    space_id: str,
    thesis: str = "",
    chain: str = "",
    field: str = "",
    bull: str = "",
    bear: str = "",
    risk_list: str = "",
    domain_hint: str = "",
    episode_id: str = "",
) -> str:
    """
    Perplexity Space를 호출하고 응답을 반환한다 (MCP 인터페이스).

    Args:
        space_id: 호출할 Space ID (spaces_config.json 기준)
        thesis:   THESIS 문장
        chain:    CHAIN 문장
        field:    FIELD (primer-collector 전용)
        bull:     BULL EVIDENCE SUMMARY (risk-debators/manager 전용)
        bear:     BEAR EVIDENCE SUMMARY (risk-debators/manager 전용)
        risk_list: RISK LIST JSON 문자열
        domain_hint: DOMAIN 힌트
        episode_id: EPISODE_ID (생략 시 자동 생성)

    Returns:
        Space 응답 텍스트 (raw)
    """
    payload = {k: v for k, v in {
        "episode_id": episode_id, "thesis": thesis, "chain": chain,
        "field": field, "bull": bull, "bear": bear, "domain_hint": domain_hint,
    }.items() if v}
    if risk_list:
        try:
            payload["risk_list"] = json.loads(risk_list)
        except json.JSONDecodeError:
            payload["risk_list"] = risk_list

    result = call_space(space_id, **payload)
    raw = result.get("raw", "")
    if len(raw) > 50_000:
        raw = raw[:50000] + "\n\n[...truncated]"
    return raw



@mcp.tool()
def list_spaces(domain: str = "") -> str:
    """
    사용 가능한 Space 목록을 반환한다.

    Args:
        domain: "body", "butterfly", 또는 "" (전체)

    Returns:
        Space 목록 (id, slug, role)
    """
    config = _load_config()
    spaces = config.get("spaces", [])
    results = []
    for s in spaces:
        sid = s["id"]
        if domain and not sid.startswith(domain):
            continue
        results.append(f"  • {sid}: {s.get('slug','')} — {s.get('role','')[:60]}")
    return f"Spaces ({len(results)}uac1c):\n" + "\n".join(results)


@mcp.tool()
def ping() -> str:
    """MCP 서버 헬스체크"""
    return "pong"


# ── 메인 ─────────────────────────────────────────────────────


# ══════════════════════════════════════════════════
# 옛 parksy-scm Research/Utility 흡수 (2026-05-09)
# ══════════════════════════════════════════════════

# ─── 옛 parksy-scm 흡수: Research/Utility 경로 ─────────────
import subprocess as _sp
ARTICLES_DIR     = Path.home() / "parksy-logs" / "perplexity" / "articles"
EPISODE_RUNNER   = Path.home() / "parksy-logs" / "perplexity" / "episode_runner.py"
ARTICLE_WRITER   = Path.home() / "parksy-logs" / "perplexity" / "article_writer.py"
ARTICLE_TO_HTML  = Path.home() / "parksy-logs" / "perplexity" / "article_to_html.py"

# ─── 공통 헬퍼 (옛 scm) ───
def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_article(episode_id_or_path: str) -> dict:
    """에피소드 ID 또는 파일 경로로 아티클 JSON 로드."""
    p = Path(episode_id_or_path)
    if p.exists():
        return _load_json(p)
    # articles/ 디렉토리에서 검색
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    for f in ARTICLES_DIR.glob("*.json"):
        if episode_id_or_path in f.stem:
            return _load_json(f)
    raise FileNotFoundError(f"아티클을 찾을 수 없음: {episode_id_or_path}")


def _article_to_text(article: dict, max_len: int = 2000) -> str:
    """아티클 dict → 게시용 텍스트 (마크다운)."""
    parts = [
        f"# {article.get('title', '(제목 없음)')}",
        "",
        article.get("deck", ""),
        "",
        f"**에피소드:** {article.get('episode_id', '')}",
        f"**판정:** {article.get('verdict', '')} | {article.get('conviction', '')} | {article.get('confidence', '')}%",
        "",
        f"**thesis:** {article.get('thesis', '')}",
        f"**chain:** {article.get('chain', '')}",
        "",
        "## Bull",
        article.get("bull_summary", "")[:500],
        "",
        "## Bear",
        article.get("bear_summary", "")[:500],
    ]
    if article.get("conditions"):
        parts += ["", f"**조건:** {article['conditions'][:200]}"]
    if article.get("review_trigger"):
        parts += [f"**리뷰 트리거:** {article['review_trigger'][:100]}"]
    text = "\n".join(parts)
    return text[:max_len]


# ──────────────────────────────────────────────────────────────────────────────
# Category 1: Publishing
# ──────────────────────────────────────────────────────────────────────────────


# ─── Research/Utility tools (옛 scm) ───
@mcp.tool()
def run_episode(
    thesis: str,
    chain: str,
    ticker: str = "",
    domain: str = "body",
    demo: bool = False,
):
    """
    Perplexity 리서치 파이프라인 실행 → episodes.db 저장.

    Args:
        thesis: 에피소드 테제 (예: "아침 20분 유산소 → 오후 집중력 향상")
        chain:  인과 체인 (예: "운동 → BDNF 증가 → 해마 활성화 → 집중력↑")
        ticker: 종목/키워드 (선택)
        domain: "body" 또는 "butterfly"
        demo:   True면 --demo 모드 (Perplexity 실제 호출 없이 시뮬레이션)

    Returns:
        실행 결과 및 생성된 episode_id
    """
    if not EPISODE_RUNNER.exists():
        return f"❌ episode_runner.py 없음: {EPISODE_RUNNER}"

    cmd = [
        sys.executable, str(EPISODE_RUNNER),
        "--thesis", thesis,
        "--chain", chain,
        "--domain", domain,
    ]
    if ticker:
        cmd += ["--ticker", ticker]
    if demo:
        cmd += ["--demo"]

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=600,
        cwd=str(EPISODE_RUNNER.parent),
    )

    out = result.stdout[-1000:] + result.stderr[-500:]
    if result.returncode == 0:
        # episode_id 추출 시도
        m = re.search(r'EP-[A-Z]+-\d{8}-\d{6}', out)
        ep_id = m.group(0) if m else "확인 필요"
        return f"✅ episode_runner 완료\nepisode_id: {ep_id}\n\n{out}"
    else:
        return f"❌ episode_runner 실패 (code={result.returncode})\n{out}"


@mcp.tool()
def write_article(
    episode_id: int,
    domain: str = "body",
    out_path: str = "",
):
    """
    episodes.db row → article JSON artifact 변환.

    Args:
        episode_id: DB row id (정수)
        domain:     "body" 또는 "butterfly"
        out_path:   출력 경로 (비워두면 articles/ 자동 저장)

    Returns:
        생성된 아티클 경로 및 요약
    """
    if not ARTICLE_WRITER.exists():
        return f"❌ article_writer.py 없음: {ARTICLE_WRITER}"

    cmd = [
        sys.executable, str(ARTICLE_WRITER),
        "--episode-id", str(episode_id),
        "--domain", domain,
    ]
    if out_path:
        cmd += ["--out", out_path]

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60,
        cwd=str(ARTICLE_WRITER.parent),
    )

    out = result.stdout + result.stderr
    if result.returncode == 0:
        # 저장 경로 추출
        m = re.search(r'Saved:\s*(\S+)', out)
        path = m.group(1) if m else "알 수 없음"
        return f"✅ 아티클 생성 완료\n경로: {path}\n\n{out[:600]}"
    else:
        return f"❌ article_writer 실패 (code={result.returncode})\n{out[-600:]}"


@mcp.tool()


@mcp.tool()
def collect_primer(field: str) -> str:
    """Generalist Primer Collector: 지정된 학문 분야의 개론서 요약을 수집해 eae-univ/primers/에 저장한다. 예: collect_primer('물리학')"""
    import sys, subprocess
    pipeline = str(Path.home() / "parksy-logs/perplexity/generalist_pipeline.py")
    if not Path(pipeline).exists():
        return f"에러: generalist_pipeline.py 없음 ({pipeline})"
    result = subprocess.run(
        [sys.executable, pipeline, field],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        return f"에러: {result.stderr[:500]}"
    return f"✅ {field} primer 수집 완료.\n{result.stdout[:1000]}"


def run_and_publish(
    thesis: str,
    chain: str,
    ticker: str = "",
    domain: str = "body",
    publish_to: str = "telegram,discord",
    demo: bool = False,
):
    """
    원클릭 전체 파이프라인: 에피소드 실행 → 아티클 생성 → 멀티플랫폼 배포.

    Args:
        thesis:      에피소드 테제
        chain:       인과 체인
        ticker:      종목/키워드 (선택)
        domain:      "body" 또는 "butterfly"
        publish_to:  콤마 구분 배포 대상 (telegram, discord, naver, tistory)
        demo:        True면 --demo 모드

    Returns:
        전체 파이프라인 실행 결과
    """
    results = []

    # Step 1: episode_runner
    results.append("─── Step 1: episode_runner ───")
    ep_result = run_episode(thesis, chain, ticker, domain, demo)
    results.append(ep_result)

    if "❌" in ep_result:
        return "\n".join(results) + "\n\n⛔ Step 1 실패 — 중단"

    # episode_id 추출 (DB 최신 row로 대신 article 생성)
    m = re.search(r'EP-[A-Z]+-\d{8}-\d{6}', ep_result)
    ep_text = m.group(0) if m else ""

    # Step 2: article_writer (latest)
    results.append("\n─── Step 2: article_writer (latest) ───")
    cmd = [
        sys.executable, str(ARTICLE_WRITER),
        "--latest", "--domain", domain,
    ]
    art_result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60,
        cwd=str(ARTICLE_WRITER.parent),
    )
    art_out = art_result.stdout + art_result.stderr
    results.append(art_out[:400])

    if art_result.returncode != 0:
        return "\n".join(results) + "\n\n⛔ Step 2 실패 — 중단"

    # article 파일 찾기
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    latest_file = max(ARTICLES_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, default=None)
    if not latest_file:
        return "\n".join(results) + "\n\n⛔ 아티클 파일 없음"

    article_path = str(latest_file)
    results.append(f"아티클: {article_path}")

    # Step 3: 배포
    targets = [t.strip() for t in publish_to.split(",") if t.strip()]
    results.append(f"\n─── Step 3: 배포 ({', '.join(targets)}) ───")

    for target in targets:
        if target == "telegram":
            r = publish_telegram(article_path)
        elif target == "discord":
            r = publish_discord(article_path)
        elif target == "naver":
            r = publish_naver(article_path)
        elif target == "tistory":
            r = publish_tistory(article_path)
        elif target == "eae-univ":
            r = publish_eae_univ(article_path, domain)
        else:
            r = f"⚠️ 알 수 없는 배포 대상: {target}"
        results.append(f"[{target}] {r}")

    return "\n".join(results)


# ──────────────────────────────────────────────────────────────────────────────
# Category 3: Utility
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_articles(domain: str = ""):
    """
    articles/ 디렉토리의 아티클 목록 조회.

    Args:
        domain: 필터 ("body" | "butterfly" | "" = 전체)

    Returns:
        아티클 목록 (id, domain, title, verdict, confidence)
    """
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(ARTICLES_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

    rows = []
    for f in files:
        try:
            a = _load_json(f)
            if domain and a.get("domain") != domain:
                continue
            rows.append(
                f"[{a.get('db_id', '?')}] {a.get('episode_id', f.stem)}"
                f"  {a.get('verdict', '?')} {a.get('confidence', '?')}%"
                f"  {a.get('title', '')[:50]}"
            )
        except Exception:
            rows.append(f"[ERR] {f.name}")

    if not rows:
        return "아티클 없음 (articles/ 비어 있음)"
    return f"총 {len(rows)}개 아티클:\n" + "\n".join(rows)


@mcp.tool()
def get_article(episode_id_or_path: str):
    """
    특정 아티클의 전체 내용 조회.

    Args:
        episode_id_or_path: 에피소드 ID (EP-BODY-...) 또는 파일 경로

    Returns:
        아티클 JSON 전체
    """
    try:
        article = _load_article(episode_id_or_path)
        return json.dumps(article, ensure_ascii=False, indent=2)
    except FileNotFoundError as e:
        return f"❌ {e}"


@mcp.tool()
def list_episodes_db():
    """
    episodes.db의 에피소드 목록 조회 (article_writer.py --list 래핑).

    Returns:
        에피소드 목록
    """
    if not ARTICLE_WRITER.exists():
        return f"❌ article_writer.py 없음: {ARTICLE_WRITER}"

    result = subprocess.run(
        [sys.executable, str(ARTICLE_WRITER), "--list"],
        capture_output=True, text=True, timeout=30,
        cwd=str(ARTICLE_WRITER.parent),
    )
    return result.stdout or result.stderr or "출력 없음"


# ────────────────────────────────────────────────────────────
# 개념어 그림 사전 MCP 툴
# ────────────────────────────────────────────────────────────

def _load_pipeline_module():
    """concept_picture_pipeline.py 동적 임포트"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "concept_picture_pipeline",
        str(Path.home() / "parksy-logs" / "pipelines" / "concept_picture_pipeline.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@mcp.tool()
def concept_dict_generate(
    concept: str,
    category: str = "concept",
    definition: str = "",
    stage: str = "meta",
    phl_token: str = "Expansion",
    seven_axis: str = "{}",
    four_axis: str = "{}",
    related: str = "",
    use_vast: bool = False,
) -> str:
    """
    개념어 그림 사전 엔트리 생성.

    Args:
        concept: 개념어 (예: "자유", "진리", "소중함")
        category: 사전 카테고리 (seed/cliche/concept/emotion/symbol/masterpiece)
        definition: 개념 정의 (1-2문장)
        stage: 사유 단계 (meta/reverse/module/zoom/quantum/spiral/language)
        phl_token: PHL 토큰 (Expansion/Hardening/Reverse)
        seven_axis: 7축 분석 JSON ({"semantic":"의미","temporal":"현대"})
        four_axis: 4축×8감정 JSON
        related: 관련 개념어 (쉼표 구분)
        use_vast: Vast.ai ComfyUI로 이미지 생성 여부

    Returns:
        생성 결과 요약 (JSON)
    """
    mod = _load_pipeline_module()
    from dataclasses import asdict

    entry = mod.ConceptEntry(
        id=concept.lower().replace(" ", "_"),
        term=concept,
        category=category,
        definition=definition or f"{concept} 개념 정의",
        seven_axis=json.loads(seven_axis) if seven_axis != "{}" else {},
        four_axis_emotion=json.loads(four_axis) if four_axis != "{}" else {},
        thinking_stage=stage,
        phl_token=phl_token,
        related_terms=related.split(",") if related else [],
    )

    # Step 1: 프롬프트 생성
    prompt = mod.concept_to_image_prompt(entry)

    # Step 2: 이미지 생성
    img_path = mod.generate_image_vast(
        prompt, f"{category}_{entry.id}",
        use_vast=use_vast,
    )
    if img_path:
        entry.image_path = img_path

    # Step 3: 영상 생성
    video_path = mod.create_slideshow_video(entry, img_path)
    if video_path:
        entry.video_path = video_path

    # Step 4: 메타데이터
    meta = mod.generate_youtube_metadata(entry)

    result = asdict(entry)
    result["prompt_length"] = len(prompt)
    result["metadata"] = meta
    result["prompt_file"] = f"{entry.category}_{entry.id}_prompt.txt"

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def concept_dict_batch(
    category: str = "concept",
    use_vast: bool = False,
) -> str:
    """
    ParksyLog 최신 파일에서 개념어를 추출하여 그림 사전 엔트리 배치 생성.

    Args:
        category: 추출할 사전 카테고리
        use_vast: Vast.ai ComfyUI로 이미지 생성 여부

    Returns:
        배치 생성 결과 요약
    """
    mod = _load_pipeline_module()

    # 최신 ParksyLog 찾기
    log_dir = Path.home() / "parksy-logs" / "logs" / "2026" / "05"
    latest_log = None
    if log_dir.exists():
        log_files = sorted(log_dir.glob("*.md"))
        if log_files:
            latest_log = str(log_files[-1])

    if not latest_log or not os.path.exists(latest_log):
        # fallback: uploads 디렉토리
        uploads = sorted((Path.home() / "uploads").glob("ParksyLog_*.md"))
        if uploads:
            latest_log = str(uploads[-1])

    if not latest_log:
        return "❌ ParksyLog 파일을 찾을 수 없습니다."

    entries = mod.parse_concepts_from_log(latest_log, category)
    if not entries:
        return f"❌ {latest_log}에서 개념어를 찾을 수 없습니다."

    results = []
    for entry in entries[:10]:  # 최대 10개
        prompt = mod.concept_to_image_prompt(entry)
        entry.image_prompt = prompt

        img_path = mod.generate_image_vast(
            prompt, f"{category}_{entry.id}",
            use_vast=use_vast,
        )
        if img_path:
            entry.image_path = img_path

        entry.status = "completed"
        results.append(entry.id)

    return json.dumps({
        "source_log": latest_log,
        "category": category,
        "total_found": len(entries),
        "processed": len(results),
        "concepts": results,
        "note": "실제 이미지 생성은 --use-vast 필요 (Vast.ai ComfyUI)",
    }, ensure_ascii=False, indent=2)


# (옛 scm ping은 rawmat 본래 ping과 중복이라 제거)


if __name__ == "__main__":
    mcp.run()
