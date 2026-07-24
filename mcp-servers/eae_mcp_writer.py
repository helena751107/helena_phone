#!/usr/bin/env python3
"""
eae_mcp_writer.py — EAE MCP Series: eae-mcp-writer
워크센터: 텍스트 생성 공정 (박씨 스타일 필터)

역할:
  - BOR 공정 2번 (research_output → styled_text)
  - STYLE_PARAMS dict + parksy_voice_filter.md + parksy_v3_300.jsonl
  - LLM 런타임 필터링 → 박씨 발화 스타일 로데이터 생성
  - "살아있는 파인튜닝" — 파라미터 수정만으로 즉시 반영

FastMCP 서버. Claude Code settings.json에서 eae-mcp-writer 키로 등록.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ──────────────────────────────────────────────────────────────────
# 경로 상수
# ──────────────────────────────────────────────────────────────────
PAPYRUS_DIR = Path(__file__).parent
FILTER_MD   = PAPYRUS_DIR / "filters" / "parksy_voice_filter.md"
JSONL_PATH  = PAPYRUS_DIR / "filters" / "parksy_v3_300.jsonl"

# ──────────────────────────────────────────────────────────────────
# STYLE_PARAMS — 박씨 스타일 파라미터 (런타임 필터 핵심)
# ──────────────────────────────────────────────────────────────────
STYLE_PARAMS = {
    # 문장 구조
    "sentence_structure":   "[결론 한 줄] + [근거 1~2줄] + [실행 지시 or 반문]",
    "max_sentence_length":  "100자 이하 (60%는 50자 이하)",
    "person":               "1인칭 — '내가', '나는' 위주",
    "sentence_ending":      "단언형 — '~다.', '~거든.', '~잖아.'",
    "conclusion_first":     True,

    # 자주 쓰는 단어 (반드시 포함)
    "signature_words": ["구조", "자동화", "진짜", "솔직히", "무조건", "핵심", "전부"],

    # 금지어
    "forbidden_words": [
        "~인 것 같습니다",
        "혹시 ~하실 수 있을까요",
        "참고로 말씀드리면",
        "다양한 측면에서",
        "~에 대해서 알아보겠습니다",
        "이 부분은 좀 더 검토가 필요합니다",
    ],

    # 추임새 — 문장 흐름
    "fillers_transition": ["그러니까", "근데", "이제", "그래서", "일단", "솔직히"],
    "fillers_emphasis":   ["진짜", "그냥", "확실히"],

    # 허용 종결 (박씨 시그니처)
    "allowed_endings": ["~거든.", "~잖아.", "~거야.", "~아니야", "~아니냐", "됐어.", "끝."],

    # 논증법
    "logic_pattern": "1.단언(결론) → 2.근거(왜) → 3.비유(체감) → 4.실행(그래서)",
    "analogy_required": True,  # 기술 개념 나오면 일상 비유 1개 필수

    # 비용/효율 관점
    "cost_lens": True,         # 모든 판단에 "돈"이 기준
    "cost_priority": ["무료/오픈소스", "일회성 비용", "종량제", "구독(최후)"],

    # 욕설/강도
    "profanity":    "출판용 — 삭제 또는 '솔직히'로 대체. 날카로움은 유지",
    "tone_default": "직설, 단언, 짧게",

    # 주제별 전문성
    "domains": {
        "youtube":    "제작자 관점, 15채널 운영자",
        "ai":         "도구로 씀, '뭐 만들 수 있냐' 관점",
        "dev":        "비개발자, '나는 만트라 코드는 고스트'",
        "philosophy": "구조적 사고, 체계/시스템 집착",
        "business":   "현실 비용 중심, '이거 팔리냐'",
        "audio_daw":  "DAW/VSTi 직접 운용, 자동화 지향",
    },

    # 플랫폼별 규칙
    "platform_rules": {
        "telegram":  "한 줄~세 줄 최대. 임팩트 먼저. 링크 없이.",
        "blog_naver":"도입부 결론, 목록 쓰되 짧게. SEO 태그 포함.",
        "blog_tistory": "구조 중심, 섹션 헤더 활용, 코드블록 허용.",
        "youtube_script": "나레이션 가능 문장. 구어체. 1분 = 약 200자.",
        "discord":   "짧고 임팩트. 마크다운 허용.",
        "shorts":    "60초 이내. 결론 3초 안에.",
    },
}

# ──────────────────────────────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────────────────────────────

def _load_voice_filter() -> str:
    """parksy_voice_filter.md 전체 로드."""
    if FILTER_MD.exists():
        return FILTER_MD.read_text(encoding="utf-8")
    return "# Voice filter not found"


def _load_few_shots(n: int = 30) -> list[dict]:
    """parksy_v3_300.jsonl 앞 n개 로드."""
    examples = []
    if not JSONL_PATH.exists():
        return examples
    with open(JSONL_PATH, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            try:
                examples.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return examples


def _build_system_prompt(platform: str = "general") -> str:
    """STYLE_PARAMS + voice filter + few-shots → 시스템 프롬프트 생성."""
    filter_text = _load_voice_filter()
    few_shots = _load_few_shots(15)

    platform_rule = STYLE_PARAMS["platform_rules"].get(
        platform, "짧고 직설. 결론 먼저."
    )

    examples_text = ""
    if few_shots:
        examples_text = "\n\n## 실제 발화 예시 (참고용, 이 톤으로 생성)\n"
        for ex in few_shots[:8]:
            msgs = ex.get("messages", [])
            for m in msgs:
                if m.get("role") == "assistant":
                    examples_text += f"- {m['content'][:120]}\n"

    prompt = f"""당신은 박씨(Parksy) 스타일로 콘텐츠 로데이터를 생성하는 워크센터입니다.
아래 규칙과 스타일 파라미터를 100% 따릅니다.

## 핵심 규칙 (STYLE_PARAMS)

**문장 구조:** {STYLE_PARAMS['sentence_structure']}
**인칭:** {STYLE_PARAMS['person']}
**종결:** {STYLE_PARAMS['sentence_ending']}
**논증법:** {STYLE_PARAMS['logic_pattern']}
**플랫폼 규칙 ({platform}):** {platform_rule}

**자주 쓰는 단어 (반드시 포함):** {', '.join(STYLE_PARAMS['signature_words'])}
**추임새:** {', '.join(STYLE_PARAMS['fillers_transition'][:4])}
**금지 표현:** {', '.join(STYLE_PARAMS['forbidden_words'][:4])}
**비용 관점:** 모든 판단에 비용이 기준. 무료 솔루션 우선.
**비유:** 기술 개념 나오면 일상 비유 1개 필수.
**욕설:** 출판용 — 삭제. 날카로움은 유지.
**결론 먼저:** 서론 없이 핵심부터.

## 박씨 Voice Filter (핵심 발췌)

{filter_text[:3000]}
{examples_text}

## 지시
위 규칙대로 요청된 콘텐츠를 생성하세요.
애매하거나 수동적인 표현은 절대 금지. 단언하고, 짧게, 임팩트 있게.
"""
    return prompt


def _run_claude_cli(system_prompt: str, user_prompt: str) -> str:
    """
    Claude CLI (claude --print) 호출.
    에러 시 에러 메시지 반환.
    """
    try:
        result = subprocess.run(
            ["claude", "--print", "--system", system_prompt, user_prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return f"[ERROR] claude CLI 실패: {result.stderr[:300]}"
    except FileNotFoundError:
        return "[ERROR] claude CLI 미설치. `npm install -g @anthropic-ai/claude-code`"
    except subprocess.TimeoutExpired:
        return "[ERROR] 120초 타임아웃"
    except Exception as e:
        return f"[ERROR] {e}"


# ──────────────────────────────────────────────────────────────────
# FastMCP 서버
# ──────────────────────────────────────────────────────────────────

mcp = FastMCP("eae-mcp-writer", host="0.0.0.0")


@mcp.tool()
def ping():
    """의존성 체크 및 서버 상태 확인."""
    status = {
        "server":      "eae-mcp-writer v1.0",
        "filter_md":   FILTER_MD.exists(),
        "jsonl":       JSONL_PATH.exists(),
        "style_params_keys": list(STYLE_PARAMS.keys()),
    }
    # few-shots 카운트
    shots = _load_few_shots(300)
    status["few_shots_loaded"] = len(shots)

    # claude CLI 존재 여부
    import shutil
    status["claude_cli"] = shutil.which("claude") is not None

    return json.dumps(status, ensure_ascii=False, indent=2)


@mcp.tool()
def generate_content(
    topic: str,
    platform: str = "general",
    format: str = "paragraph",
    length: str = "short",
    extra_context: str = "",
):
    """
    박씨 스타일 콘텐츠 로데이터 생성 (범용).

    Args:
        topic:         주제 또는 원문 텍스트
        platform:      telegram / blog_naver / blog_tistory / youtube_script / discord / shorts / general
        format:        paragraph / list / script / qa
        length:        short(~200자) / medium(~500자) / long(~1000자)
        extra_context: 추가 맥락 (리서치 결과, 키워드 등)
    """
    length_map = {"short": "200자 이내", "medium": "500자 내외", "long": "1000자 내외"}
    length_str = length_map.get(length, "200자 이내")

    system = _build_system_prompt(platform)
    user = f"""다음 주제로 박씨 스타일 {format} 콘텐츠를 생성해주세요.

주제: {topic}
플랫폼: {platform}
길이: {length_str}
형식: {format}
{f'추가 맥락: {extra_context}' if extra_context else ''}

결론 먼저. 짧게. 단언하게. 비유 1개 포함. 금지어 없이."""

    result = _run_claude_cli(system, user)
    return result


@mcp.tool()
def generate_blog_post(
    topic: str,
    platform: str = "blog_tistory",
    research_summary: str = "",
    keywords: str = "",
):
    """
    박씨 스타일 블로그 포스트 생성.
    BOR: research → writer → platform

    Args:
        topic:            포스트 주제
        platform:         blog_naver / blog_tistory
        research_summary: eae-mcp-research 결과 (있으면 우선 사용)
        keywords:         SEO 키워드 (쉼표 구분)
    """
    system = _build_system_prompt(platform)
    kw_str = f"\nSEO 키워드: {keywords}" if keywords else ""
    ctx_str = f"\n리서치 요약:\n{research_summary}" if research_summary else ""

    user = f"""박씨 스타일 블로그 포스트를 작성해주세요.

주제: {topic}
플랫폼: {platform}{kw_str}{ctx_str}

구조:
1. 결론 먼저 — 첫 문장에 핵심
2. 왜 — 근거 2~3줄
3. 어떻게 — 실행 방법 (목록 가능)
4. 비용/효율 관점 포함
5. 마무리 — 한 줄 단언

제목도 박씨 스타일로 생성해주세요. (결론 + 반문 형식)"""

    result = _run_claude_cli(system, user)
    return result


@mcp.tool()
def generate_telegram_post(
    topic: str,
    one_liner: bool = True,
):
    """
    텔레그램용 초단문 포스트 생성.
    BOR: writer → platform(telegram)

    Args:
        topic:      메시지 주제 or 원문
        one_liner:  True=한 줄, False=세 줄 이내
    """
    system = _build_system_prompt("telegram")
    length_inst = "한 줄 (50자 이내)" if one_liner else "세 줄 이내 (150자 이내)"

    user = f"""텔레그램용 박씨 스타일 포스트를 생성해주세요.

주제: {topic}
길이: {length_inst}

조건: 링크 없이. 임팩트 먼저. 결론 = 첫 줄."""

    result = _run_claude_cli(system, user)
    return result


@mcp.tool()
def generate_youtube_script(
    topic: str,
    duration_minutes: int = 5,
    research_summary: str = "",
    include_hook: bool = True,
):
    """
    유튜브 나레이션 대본 생성.
    BOR: research → writer → studio(gptsovits) → platform(youtube)

    Args:
        topic:             영상 주제
        duration_minutes:  영상 길이 (분) — 1분 ≈ 200자
        research_summary:  eae-mcp-research 결과
        include_hook:      True=훅(3초 결론) 포함
    """
    system = _build_system_prompt("youtube_script")
    target_chars = duration_minutes * 200
    ctx_str = f"\n리서치 요약:\n{research_summary}" if research_summary else ""

    hook_inst = """
첫 3초 훅: 결론 한 문장. "이걸 모르면 손해다." 형식.
""" if include_hook else ""

    user = f"""유튜브 나레이션 대본을 박씨 스타일로 생성해주세요.

주제: {topic}
목표 길이: 약 {target_chars}자 ({duration_minutes}분){ctx_str}

구조:
{hook_inst}1. [훅] 결론 3초
2. [왜] 문제/근거 — 구어체로
3. [어떻게] 실행 — 단계별
4. [비유] 일상 비유 1개
5. [마무리] 한 줄 단언 + CTA

나레이션 가능한 구어체로. 읽을 때 호흡 단위로 짧게."""

    result = _run_claude_cli(system, user)
    return result


@mcp.tool()
def generate_shorts_script(
    topic: str,
    seconds: int = 60,
):
    """
    유튜브 쇼츠 / 릴스 대본 생성 (60초 이내).
    BOR: writer → studio(voice+image) → platform

    Args:
        topic:   쇼츠 주제
        seconds: 길이 (초, 최대 60)
    """
    system = _build_system_prompt("shorts")
    seconds = min(seconds, 60)
    target_chars = int(seconds * 3.5)  # 1초 ≈ 3.5자

    user = f"""유튜브 쇼츠 대본을 박씨 스타일로 생성해주세요.

주제: {topic}
길이: {seconds}초 (약 {target_chars}자)

규칙:
- 첫 2초: 결론/충격 한 문장
- 중간: 근거 2줄
- 마지막 3초: 행동 유도 한 줄
- 구어체, 짧게, 임팩트"""

    result = _run_claude_cli(system, user)
    return result


@mcp.tool()
def style_filter(
    raw_text: str,
    platform: str = "general",
):
    """
    기존 텍스트를 박씨 스타일로 변환 (필터링).
    연구 결과, 타인의 글, GPT 출력 등을 박씨 말투로 바꿀 때 사용.

    Args:
        raw_text: 변환할 원본 텍스트
        platform: 목표 플랫폼
    """
    system = _build_system_prompt(platform)

    user = f"""다음 텍스트를 박씨 스타일로 변환해주세요.

원본:
{raw_text}

변환 규칙:
- 금지어 제거
- 단언형으로 변환
- 결론을 앞으로
- 비유 1개 추가 (없으면)
- 길이는 원본의 50~70% (군더더기 제거)
- 플랫폼: {platform}"""

    result = _run_claude_cli(system, user)
    return result


@mcp.tool()
def get_style_params():
    """현재 STYLE_PARAMS 조회. 파라미터 확인/디버그용."""
    return json.dumps(STYLE_PARAMS, ensure_ascii=False, indent=2)


@mcp.tool()
def get_few_shot_examples(n: int = 10):
    """
    parksy_v3_300.jsonl에서 N개 예시 조회.
    스타일 확인 및 파인튜닝 데이터 검토용.

    Args:
        n: 가져올 예시 수 (최대 50)
    """
    n = min(n, 50)
    examples = _load_few_shots(n)
    output = []
    for ex in examples:
        msgs = ex.get("messages", [])
        for m in msgs:
            if m.get("role") == "assistant":
                output.append(m["content"])
    return json.dumps(output, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────────────
# 엔트리포인트
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Railway/Koyeb: --sse 또는 MCP_TRANSPORT=sse → HTTP SSE 모드
    # 로컬 stdio: 인자 없음 (Claude Code settings.json command 방식)
    sse_mode = "--sse" in sys.argv or os.environ.get("MCP_TRANSPORT") == "sse"
    if sse_mode:
        import uvicorn

        port = int(os.environ.get("PORT", "8000"))
        sse_app = mcp.sse_app()

        # 순수 ASGI 미들웨어: Starlette Mount("/") 우회 → Railway 엣지 프록시 502 방지
        async def app(scope, receive, send):
            if scope["type"] == "http" and scope.get("path") == "/health":
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"content-type", b"application/json")],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"status":"ok","server":"eae-mcp-writer"}',
                })
            else:
                await sse_app(scope, receive, send)

        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        mcp.run()
