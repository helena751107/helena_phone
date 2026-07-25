#!/usr/bin/env python3
"""
parksy_scm_mcp.py — Parksy SCM MCP 서버 (Node C)

콘텐츠 공급망 관리 (Content Supply Chain Management)

아이디어 → 리서치(Perplexity) → 아티클(article_writer) → 배포(이 서버)

Categories:
  1. Publishing  — telegram / discord / naver / tistory
  2. Research    — run_episode / write_article / run_and_publish
  3. Utility     — list_articles / get_article / list_episodes

등록 (~/.claude/settings.json):
  {
    "mcpServers": {
      "parksy-scm": {
        "command": "python3",
        "args": [str(Path.home() / "dtslib-papyrus/parksy_scm_mcp.py")]
      }
    }
  }
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests
from mcp.server.fastmcp import FastMCP

# ─── 경로 상수 ────────────────────────────────────────────────────────────────

PAPYRUS_DIR      = Path(__file__).parent
TOOLS_DIR        = PAPYRUS_DIR / "tools"
ARTICLES_DIR     = Path.home() / "parksy-logs" / "perplexity" / "articles"
EPISODE_RUNNER   = Path.home() / "parksy-logs" / "perplexity" / "episode_runner.py"
ARTICLE_WRITER   = Path("/home/dtsli/parksy-logs/perplexity/article_writer.py")
TELEGRAM_CONFIG  = Path("/home/dtsli/dtslib-localpc/telegram-bots/config.json")
DISCORD_WEBHOOKS = TOOLS_DIR / "discord" / "webhooks.json"
NAVER_POST_CJS   = TOOLS_DIR / "naver" / "post.cjs"
TISTORY_POST_PY  = TOOLS_DIR / "tistory" / "post.py"

# ─── MCP 서버 ─────────────────────────────────────────────────────────────────

mcp = FastMCP("parksy-scm")

# ──────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────────────────────────────────────

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

@mcp.tool()
def publish_telegram(
    article_path: str,
    chat_id: str = "",
    bot_token: str = "",
):
    """
    아티클 JSON → Telegram 채널 발행.

    Args:
        article_path: 아티클 JSON 경로 또는 episode_id
        chat_id: 텔레그램 chat_id (비워두면 config.json 기본값 사용)
        bot_token: 봇 토큰 (비워두면 config.json 기본값 사용)

    Returns:
        발행 결과 메시지
    """
    article = _load_article(article_path)
    text = _article_to_text(article, max_len=4000)

    cfg = _load_json(TELEGRAM_CONFIG)
    token = bot_token or cfg.get("bot_token", "")
    cid   = chat_id  or str(cfg.get("chat_id", ""))

    if not token or not cid:
        return "❌ 텔레그램 토큰/chat_id 없음. config.json 확인 요망."

    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": cid,
        "text": text,
        "parse_mode": "Markdown",
    }, timeout=15)

    if resp.ok:
        data = resp.json()
        msg_id = data.get("result", {}).get("message_id", "?")
        return f"✅ Telegram 발행 완료 (msg_id={msg_id})\n에피소드: {article.get('episode_id')}"
    else:
        return f"❌ Telegram 실패: {resp.status_code} {resp.text[:300]}"


@mcp.tool()
def publish_discord(
    article_path: str,
    repo: str = "parksy-logs",
):
    """
    아티클 JSON → Discord Webhook 발행.

    Args:
        article_path: 아티클 JSON 경로 또는 episode_id
        repo: webhooks.json의 키 (기본: parksy-logs)

    Returns:
        발행 결과 메시지
    """
    article = _load_article(article_path)
    webhooks = _load_json(DISCORD_WEBHOOKS)
    wh_map   = webhooks.get("webhooks", {})

    url = wh_map.get(repo)
    if not url:
        available = ", ".join(list(wh_map.keys())[:10])
        return f"❌ webhook 없음: '{repo}'\n사용 가능: {available}"

    title   = article.get("title", "(제목 없음)")
    verdict = article.get("verdict", "?")
    conv    = article.get("conviction", "?")
    conf    = article.get("confidence", 0)
    thesis  = article.get("thesis", "")
    chain   = article.get("chain", "")
    bull    = article.get("bull_summary", "")[:300]
    bear    = article.get("bear_summary", "")[:300]
    ep_id   = article.get("episode_id", "")

    color_map = {"BUY": 0x00C851, "REDUCE": 0xFF8800, "HOLD": 0x0099CC, "AVOID": 0xFF4444}
    color = color_map.get(verdict, 0x888888)

    payload = {
        "embeds": [{
            "title": title,
            "color": color,
            "fields": [
                {"name": "Verdict", "value": f"{verdict} | {conv} | {conf}%", "inline": True},
                {"name": "Episode", "value": ep_id, "inline": True},
                {"name": "Thesis", "value": thesis, "inline": False},
                {"name": "Chain",  "value": chain,  "inline": False},
                {"name": "Bull",   "value": bull or "—", "inline": False},
                {"name": "Bear",   "value": bear or "—", "inline": False},
            ],
            "footer": {"text": f"Parksy SCM · {time.strftime('%Y-%m-%d %H:%M KST')}"},
        }]
    }

    resp = requests.post(url, json=payload, timeout=15)
    if resp.status_code in (200, 204):
        return f"✅ Discord 발행 완료 (채널: {repo})\n에피소드: {ep_id}"
    else:
        return f"❌ Discord 실패: {resp.status_code} {resp.text[:300]}"


@mcp.tool()
def publish_naver(
    article_path: str,
    account: str = "parksy_kr",
):
    """
    아티클 JSON → Naver 블로그 발행 (post.cjs 경유).

    Args:
        article_path: 아티클 JSON 경로 또는 episode_id
        account: 네이버 계정 id (parksy_kr | eae_kr | dtslib)

    Returns:
        발행 결과 메시지
    """
    article = _load_article(article_path)

    # post spec JSON 임시 생성
    title   = article.get("title", "(제목 없음)")
    content = _build_html_content(article)
    tags    = _extract_tags(article)

    spec = {
        "account": account,
        "title":   title,
        "content": content,
        "tags":    tags,
    }

    posts_dir = TOOLS_DIR / "naver" / "posts"
    posts_dir.mkdir(exist_ok=True)
    ep_id    = article.get("episode_id", "unknown").replace(":", "-")
    spec_path = posts_dir / f"{ep_id}.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    result = subprocess.run(
        ["node", str(NAVER_POST_CJS), account, spec_path.name],
        cwd=str(TOOLS_DIR / "naver"),
        capture_output=True, text=True, timeout=120,
    )

    if result.returncode == 0:
        return f"✅ Naver 발행 완료 (account={account})\n{result.stdout[-300:]}"
    else:
        return f"❌ Naver 실패 (code={result.returncode})\n{result.stderr[-500:]}"


@mcp.tool()
def publish_tistory(
    article_path: str,
    account: str = "dtslib",
    blog: str = "blogger-parksy",
):
    """
    아티클 JSON → Tistory 블로그 발행 (post.py 경유).

    Args:
        article_path: 아티클 JSON 경로 또는 episode_id
        account: 티스토리 계정 id
        blog: 블로그 슬러그

    Returns:
        발행 결과 메시지
    """
    article = _load_article(article_path)

    title   = article.get("title", "(제목 없음)")
    content = _build_html_content(article)
    tags    = _extract_tags(article)

    spec = {
        "account":    account,
        "blog":       blog,
        "title":      title,
        "content":    content,
        "tags":       tags,
        "category":   "",
        "visibility": "public",
    }

    posts_dir = TOOLS_DIR / "tistory" / "posts"
    posts_dir.mkdir(exist_ok=True)
    ep_id    = article.get("episode_id", "unknown").replace(":", "-")
    spec_path = posts_dir / f"{ep_id}.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(TISTORY_POST_PY), "--post", spec_path.name],
        cwd=str(TOOLS_DIR / "tistory"),
        capture_output=True, text=True, timeout=180,
    )

    if result.returncode == 0:
        return f"✅ Tistory 발행 완료 (blog={blog})\n{result.stdout[-300:]}"
    else:
        return f"❌ Tistory 실패 (code={result.returncode})\n{result.stderr[-500:]}"


# ──────────────────────────────────────────────────────────────────────────────
# Category 2: Research Pipeline
# ──────────────────────────────────────────────────────────────────────────────

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


@mcp.tool()
def ping():
    """MCP 서버 헬스체크."""
    now = time.strftime("%Y-%m-%d %H:%M:%S KST")
    tools_status = {
        "episode_runner": EPISODE_RUNNER.exists(),
        "article_writer": ARTICLE_WRITER.exists(),
        "telegram_config": TELEGRAM_CONFIG.exists(),
        "discord_webhooks": DISCORD_WEBHOOKS.exists(),
        "naver_post_cjs": NAVER_POST_CJS.exists(),
        "tistory_post_py": TISTORY_POST_PY.exists(),
    }
    lines = [f"✅ parksy-scm MCP 정상 ({now})", ""]
    for k, v in tools_status.items():
        lines.append(f"  {'✅' if v else '❌'} {k}")
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    n_articles = len(list(ARTICLES_DIR.glob("*.json")))
    lines.append(f"\n  📄 아티클 {n_articles}개 ({ARTICLES_DIR})")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# 내부 헬퍼
# ──────────────────────────────────────────────────────────────────────────────

def _build_html_content(article: dict) -> str:
    """아티클 dict → 블로그 HTML 본문."""
    verdict_label = {
        "BUY":    "✅ 실행 권장",
        "REDUCE": "⚠️ 조건부 실행",
        "HOLD":   "⏸ 관찰 대기",
        "AVOID":  "❌ 보류",
    }.get(article.get("verdict", ""), article.get("verdict", ""))

    risk_html = ""
    for r in article.get("risk_list", [])[:5]:
        risk_html += f"<li>{r}</li>"

    conditions = article.get("conditions", "")
    review     = article.get("review_trigger", "")
    bull       = article.get("bull_summary", "")
    bear       = article.get("bear_summary", "")
    sources    = article.get("sources", [])

    src_html = ""
    for url in sources[:5]:
        src_html += f'<li><a href="{url}">{url}</a></li>'

    return f"""<h2>{article.get('title', '')}</h2>
<p><strong>판정:</strong> {verdict_label} ({article.get('conviction', '')} | {article.get('confidence', 0)}%)</p>
<p><strong>Thesis:</strong> {article.get('thesis', '')}</p>
<p><strong>Chain:</strong> {article.get('chain', '')}</p>

<h3>Bull Evidence</h3>
<p>{bull}</p>

<h3>Bear Evidence</h3>
<p>{bear}</p>

{"<h3>리스크</h3><ul>" + risk_html + "</ul>" if risk_html else ""}
{"<h3>실행 조건</h3><p>" + conditions + "</p>" if conditions else ""}
{"<h3>리뷰 트리거</h3><p>" + review + "</p>" if review else ""}
{"<h3>출처</h3><ul>" + src_html + "</ul>" if src_html else ""}

<hr>
<p><small>에피소드: {article.get('episode_id', '')} | Parksy SCM</small></p>"""


def _extract_tags(article: dict) -> list:
    """아티클에서 태그 추출."""
    tags = []
    verdict = article.get("verdict", "")
    domain  = article.get("domain", "")
    if verdict:
        tags.append(verdict)
    if domain == "body":
        tags.extend(["헬스", "건강", "운동", "PARKSY"])
    elif domain == "butterfly":
        tags.extend(["바디마인드", "멘탈", "PARKSY"])
    thesis = article.get("thesis", "")
    # 키워드 2개 추출 (2글자 이상 한글/영문 단어)
    words = re.findall(r'[가-힣A-Za-z]{2,6}', thesis)
    tags.extend(words[:3])
    return list(dict.fromkeys(tags))[:10]  # 중복 제거, 최대 10개


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
