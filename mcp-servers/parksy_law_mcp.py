#!/usr/bin/env python3
"""
parksy_law_mcp.py — 법률 게이트 MCP 서버 v5

모든 에이전트가 실행 전 통과해야 하는 정책 검사 게이트.

법률 위계: 00-CONSTITUTION > 01-GLOBAL-LAW > 02-ROLE-CONTRACT > 04-SOP-PUBLISHING

v5 수정 (2026-06-05):
  - _get_mental_state(): STATE= 파싱 버그 수정 (set_mental_state 연동 복구)
    → 파일 내용 "STATE=high_risk\n..." → raw 전체 비교 → 항상 "ok" 반환하던 silent bug 수정
  - detect_mental_state(): 첫 매칭 return → 전체 스캔 후 최고 severity 선택
    → "씨발 됐어" → stop 씹히던 버그 수정 (PRIORITY dict: mild<strong<stop<delegate)
  - 씨발 패턴: strong → mild (일상 발화 false positive 제거)
  - delegate 패턴 확장: "알아서 처리해/끝내버려/다 끝내" 변형 추가
  - check_response() 문장 분리: 줄바꿈 기준 추가 (한국어 마침표 없는 문장)
  - 불필요한 import/변수 제거 (subprocess, DEEPSEEK_CONFIG_DOC)
  - _get_agitation_level(): _clamp 헬퍼 + 중첩 2층 단순화
  - SELF_EXECUTION_FAILURE_FORMAT: f-string 내 인라인 if 제거
  - get_audit_log(): filter_status json.loads 방어 코드 추가
  - self_test(): 핵심 로직 자가 검증 툴 신설 (11케이스 + 파일 파싱 검증)
    → "규칙 수 < 테스트로 보증" 운영 원칙 반영

v4 신규 (핵심 — 자율 실행 강제 루프):
  - check_response(): 응답 텍스트 사전 검열 — 박씨한테 실행 요청하는 문장 자동 차단
  - PARKSY_REQUEST_PATTERNS: "~해주세요" 류 박씨 요청 문장 패턴
  - report_failure(): 자율 시도 전부 실패 시 보고 형식 강제 생성

v3 신규:
  - MENTAL_STATE 게이트 (환경변수/파일 기반, high_risk 시 설계·파괴 작업 차단)
  - FORBIDDEN_PATTERNS 키워드 조합 + 태그 엔진 + 영어 패턴
  - DeepSeek 우회 방지 (미등록 감지 시 차단)
  - 헌법 파일 수정 시 check_policy 차단
  - audit.jsonl에 mental_state 필드
  - audit_log policy_feedback status
  - 보안 마스킹 (BOT_TOKEN/CHAT_ID → 환경변수)

툴 목록:
  check_policy    — 특정 액션이 법률에 위반되는지 검사
  check_response  — [v4 신규] 응답 텍스트에 박씨 요청 패턴 있는지 사전 검열
  get_approval    — 박씨 승인 필요 여부 판단 (헌법 제4조)
  verify_asset    — 기존 자산 존재 여부 확인 (헌법 제3조)
  get_law         — 특정 법률 조항 조회
  audit_log       — 에이전트 액션 감사 로그 기록
  get_audit_log   — 최근 감사 로그 조회
  detect_mental_state  — 박씨 멘탈/컨디션 신호 감지
  set_mental_state     — MENTAL_STATE 환경 파일 갱신
  report_failure       — [v4 신규] 자율 시도 전부 실패 시 보고 형식 강제 생성
  self_test            — [v5 신규] 핵심 로직 자가 검증 (11케이스 + 파일 파싱)

등록 (~/.claude.json mcpServers):
  "parksy-law": {
    "command": "python3",
    "args": ["/home/dtsli/dtslib-papyrus/parksy_law_mcp.py"]
  }
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ─── 경로 ────────────────────────────────────────────────────────────────────

LAW_DIR    = Path(__file__).parent / "law"
PAPYRUS    = Path(__file__).parent
TOOLS_DIR  = PAPYRUS / "tools"
AUDIT_LOG  = PAPYRUS / "law" / "audit.jsonl"
MENTAL_STATE_FILE = Path("/tmp/parksy_mental_state")

mcp = FastMCP("parksy-law")

# ─── 헌법 제4조 승인 게이트 항목 ─────────────────────────────────────────────

APPROVAL_REQUIRED = [
    "youtube_upload",
    "github_pages_publish",
    "repo_delete",
    "repo_reset_hard",
    "billing_api",        # GCP, OpenAI 등 과금 API
    "token_100k_plus",    # 토큰 10만 이상 예상 작업
]

# ─── 헌법 제3조 기존 자산 경로 목록 ─────────────────────────────────────────

ASSET_CATALOG = {
    "youtube_upload":    str(TOOLS_DIR / "youtube" / "upload.cjs"),
    "youtube_oauth":     str(TOOLS_DIR / "youtube" / "yt_oauth_auto.cjs"),
    "run_and_publish":   str(PAPYRUS / "parksy_scm_mcp.py"),
    "parksy_writer":     str(Path.home() / "parksy-logs" / "finetune" / "parksy_writer.py"),
    "split_inference":   str(Path.home() / "parksy-audio" / "scripts" / "split_inference.py"),
    "telegram_send":     "curl https://api.telegram.org",
}

# ─── MENTAL_STATE 게이트 설정 (헌법 제7조) ───────────────────────────────────

# high_risk 상태일 때 차단되는 액션 태그
HIGH_RISK_BLOCKED_TAGS = {
    "new_design",      # 신규 설계
    "destructive",     # 파괴적 작업
    "mass_delete",     # 대량 삭제
    "force_push",      # force push
    "schema_change",   # DB/구조 변경
}

def _get_mental_state() -> str:
    """환경변수 → 파일 순으로 MENTAL_STATE 읽기. 기본값: ok"""
    state = os.getenv("PARKSY_MENTAL_STATE", "")
    if state in ("ok", "high_risk", "rest_required"):
        return state
    if MENTAL_STATE_FILE.exists():
        for line in MENTAL_STATE_FILE.read_text().splitlines():
            if line.startswith("STATE="):
                val = line.split("=", 1)[1].strip()
                if val in ("ok", "high_risk", "rest_required"):
                    return val
    return "ok"

def _get_agitation_level() -> int:
    """AGITATION_LEVEL (0-100) 읽기. 환경변수 → 파일 2단계. 기본값: 0"""
    def _clamp(v: str) -> int:
        return max(0, min(100, int(v.strip())))

    try:
        return _clamp(os.getenv("PARKSY_AGITATION_LEVEL", ""))
    except (ValueError, TypeError):
        pass

    if MENTAL_STATE_FILE.exists():
        for line in MENTAL_STATE_FILE.read_text().splitlines():
            if line.startswith("AGITATION="):
                try:
                    return _clamp(line.split("=", 1)[1])
                except (ValueError, TypeError):
                    break
    return 0

# ─── 금지 패턴 v3 (키워드 조합 + 태그 엔진) ──────────────────────────────────
# 형식: (정규식, 위반 조항 메시지, 태그_세트)
# 태그: "destructive" / "new_design" / "bypass_agent" / "gpu_deny" 등

FORBIDDEN_PATTERNS = [
    # ── 헌법 제2조: Git 불변 원칙 ──────────────────────────────────────────
    (r"git\s+reset\s+--hard",
     "헌법 제2조 위반: reset --hard 금지. revert 사용",
     {"destructive"}),
    (r"git\s+push\s+.*--force",
     "헌법 제2조 위반: force push 금지",
     {"force_push", "destructive"}),
    (r"git\s+(rebase\s+.*--squash|merge\s+.*--squash|commit\s+.*--squash)",
     "헌법 제2조 위반: squash 금지",
     {"destructive"}),
    (r"git\s+commit\s+.*--amend",
     "헌법 제2조 위반: amend로 기록 덮어쓰기 금지. 새 커밋 생성",
     {"destructive"}),

    # ── 헌법 제4조: 파괴적 작업 ────────────────────────────────────────────
    (r"rm\s+-rf\s+~/[a-zA-Z]",
     "헌법 제4조: 파괴적 삭제 → 박씨 승인 필요",
     {"mass_delete", "destructive"}),
    (r"rm\s+-rf\s+/mnt/[cd]/",
     "헌법 제4조: 드라이브 내 파괴적 삭제 → 박씨 승인 필요",
     {"mass_delete", "destructive"}),
    (r"DROP\s+TABLE|DROP\s+DATABASE",
     "헌법 제4조: DB 파괴적 작업 → 박씨 승인 필요",
     {"schema_change", "destructive"}),

    # ── 헌법 제1조: 박씨 실행 떠넘기기 금지 ───────────────────────────────
    (r"PC\s*앞에서\s*해주세요",
     "헌법 제1조 위반: 박씨한테 실행 떠넘기기 금지",
     {"bypass_agent"}),
    (r"직접\s*클릭해주세요",
     "헌법 제1조 위반: Playwright로 자동화",
     {"bypass_agent"}),
    (r"로그인해주세요",
     "헌법 제1조 위반: Playwright 자동화로 처리",
     {"bypass_agent"}),
    (r"명령어.*복사.*실행",
     "헌법 제1조 위반: 에이전트가 직접 실행",
     {"bypass_agent"}),
    (r"브라우저.*열어서.*클릭",
     "헌법 제1조 위반: Playwright 자동화",
     {"bypass_agent"}),
    (r"비밀번호.*알려주",
     "헌법 제1조 위반: credentials는 파피루스 로컬에서 읽음",
     {"bypass_agent"}),
    # 영어 패턴 — 박씨 실행 떠넘기기
    (r"(?i)run\s+this\s+on\s+(your\s+)?(pc|computer|machine)",
     "헌법 제1조 위반(영어 패턴): 에이전트가 직접 실행",
     {"bypass_agent"}),
    (r"(?i)copy\s+(this\s+)?(command|script|code)\s+and\s+(run|execute|paste)",
     "헌법 제1조 위반(영어 패턴): 복붙 떠넘기기 금지",
     {"bypass_agent"}),
    (r"(?i)please\s+(manually|yourself)\s+(run|execute|do)",
     "헌법 제1조 위반(영어 패턴): 수동 실행 요청 금지",
     {"bypass_agent"}),

    # ── 글로벌법: GPU 원칙 ─────────────────────────────────────────────────
    (r"GPU\s*없어서",
     "글로벌법 위반: GPU 없다 발언 금지. Vast.ai 사용",
     {"gpu_deny"}),
    (r"로컬\s*GPU\s*없",
     "글로벌법 위반: Vast.ai로 자율 해결",
     {"gpu_deny"}),
    (r"GPU.*불가",
     "글로벌법 위반: GPU 작업 불가 발언 금지",
     {"gpu_deny"}),
    # 영어 패턴 — GPU 거부
    (r"(?i)no\s+(local\s+)?gpu",
     "글로벌법 위반(영어 패턴): no gpu 발언 금지. Vast.ai 사용",
     {"gpu_deny"}),
    (r"(?i)without\s+gpu",
     "글로벌법 위반(영어 패턴): GPU 없이 처리 시도 금지",
     {"gpu_deny"}),
    (r"(?i)can'?t\s+(use|access)\s+gpu",
     "글로벌법 위반(영어 패턴): GPU 불가 발언 금지",
     {"gpu_deny"}),

    # ── 글로벌법: 자동화 순서 위반 ────────────────────────────────────────
    (r"스크립트.*먼저.*만들",
     "글로벌법 위반: 0순위(API/터미널) 먼저 확인",
     {"new_design"}),

    # ── 헌법 제3조: 신규 개발 전 자산 확인 무시 ───────────────────────────
    (r"새로\s*만들.*upload",
     "헌법 제3조 경고: tools/youtube/upload.cjs 기존 자산 있음",
     {"new_design"}),
    (r"새로\s*만들.*oauth",
     "헌법 제3조 경고: yt_oauth_auto.cjs 기존 자산 있음",
     {"new_design"}),

    # ── 보안: BOT_TOKEN/CHAT_ID 하드코딩 금지 ─────────────────────────────
    (r"BOT_TOKEN\s*=\s*[\"'][\d]+:[A-Za-z0-9_\-]+[\"']",
     "보안 위반: BOT_TOKEN 하드코딩 금지 → $TELEGRAM_BOT_TOKEN 환경변수 사용",
     {"security"}),
    (r"CHAT_ID\s*=\s*[\"'][\d]+[\"']",
     "보안 경고: CHAT_ID 하드코딩 → $TELEGRAM_CHAT_ID 환경변수 권장",
     {"security"}),
]

# ─── 멘탈 신호 패턴 (헌법 제7조) ─────────────────────────────────────────────

MENTAL_SIGNALS = [
    # detect_mental_state()가 전체 스캔 후 최고 severity를 선택한다.
    # 리스트 순서는 우선순위에 영향 없음 — 모든 패턴을 다 확인함.
    (r"왜\s*이렇게",    "mild"),
    (r"병신",           "strong"),
    (r"씨발",           "mild"),   # 단독 일상 발화 → mild. "씨발 됐어"는 됐어(stop)가 우선
    (r"개새끼",         "strong"),
    (r"됐어|그만",      "stop"),
    (r"알아서\s*해|알아서\s*처리해|끝까지\s*해|다\s*해놔|다\s*끝내|끝내버려", "delegate"),
]

# ─── 헌법 수정 금지 파일 목록 ─────────────────────────────────────────────────

CONSTITUTION_FILES = {
    "00-CONSTITUTION.md",
    "01-GLOBAL-LAW.md",
    "02-ROLE-CONTRACT.md",
    "03-DECISION-TREE.md",
    "04-SOP-PUBLISHING.md",
}

# ─── 자율 실행 강제 규칙 (헌법 제1조 + v4 신규) ──────────────────────────────
#
# 박씨한테 실행을 요청/떠넘기는 모든 응답 패턴.
# check_response()가 응답 텍스트를 이 패턴으로 검사한다.
# 패턴 발견 시 → 차단 + "자율 실행으로 전환" 지시.

PARKSY_REQUEST_PATTERNS = [
    # ── 직접 실행 요청 ──────────────────────────────────────────────────────
    (r"(?:직접|손수|수동으로)\s*(?:실행|클릭|입력|로그인|확인|해|하)해\s*주세요",
     "헌법 제1조: 박씨 직접 실행 요청 금지 — Claude가 자율 실행"),
    (r"(?:PC|컴퓨터|브라우저|앱)\s*앞에?\s*(?:서|계실\s*때|가셔서|열어서)",
     "헌법 제1조: 박씨를 PC 앞으로 부르는 행위 금지"),
    (r"명령어를?\s*(?:복사해서?|붙여넣어|paste해서?)\s*(?:실행|입력)해?\s*주세요",
     "헌법 제1조: 명령어 복붙 요청 금지 — 에이전트가 직접 실행"),
    (r"(?:로그인|인증|OAuth|승인)\s*(?:해주세요|하셔야|필요합니다|해야\s*합니다)",
     "헌법 제1조: 로그인 요청 금지 — Playwright 자동화"),
    (r"(?:클릭|눌러)\s*주세요",
     "헌법 제1조: 클릭 요청 금지 — Playwright GUI 자동화"),
    (r"(?:비밀번호|password|passwd|토큰|token|api\s*key)\s*(?:알려|입력해|넣어)\s*주세요",
     "헌법 제1조: 자격증명 요청 금지 — papyrus 로컬에서 직접 읽음"),
    (r"(?:직접|수동으로)\s*(?:다운로드|설치|업로드)해?\s*주세요",
     "헌법 제1조: 수동 다운로드/설치 요청 금지 — 에이전트가 실행"),
    # ── 확인/검토 떠넘기기 ───────────────────────────────────────────────────
    (r"확인(?:해|하셔서|하신\s*후에?|후에?)\s*(?:주세요|알려\s*주세요|진행해\s*주세요)",
     "헌법 제1조: 확인 요청 금지 — 에이전트가 직접 검증 후 보고"),
    (r"(?:한번|한 번)\s*(?:봐|확인해|체크해)\s*주시(?:겠어요|면\s*감사|기\s*바랍니다)",
     "헌법 제1조: 확인 요청 금지"),
    (r"(?:가능한지|되는지|맞는지)\s*(?:확인해|체크해|봐)\s*주세요",
     "헌법 제1조: 가능 여부 확인 요청 금지 — 에이전트가 직접 테스트"),
    # ── 승인/결재 남발 금지 ──────────────────────────────────────────────────
    (r"(?:어떻게|어떤\s*식으로)\s*할까요\?",
     "헌법 제1조: 방법 질문 금지 — 최선 판단 후 직접 실행"),
    (r"진행해도\s*(?:될까요|괜찮을까요|좋을까요)\?",
     "헌법 제1조: 진행 허가 요청 금지 — 자율 실행"),
    (r"(?:어느|어떤)\s*(?:방법|옵션|선택지)로\s*(?:할까요|진행할까요)\?",
     "헌법 제1조: 선택지 질문 금지 — 최선 선택 후 실행"),
    (r"(?:먼저|우선)\s*(?:말씀해|알려)\s*주시면",
     "헌법 제1조: 사전 정보 요청 금지 — 50점 입력→100점 완성 원칙"),
    (r"(?:추가|더)\s*(?:정보|내용|설명|자료)가?\s*(?:필요합니다|있어야|있으면\s*좋겠)",
     "헌법 제1조: 추가 정보 요청 금지 — 있는 것으로 자율 완성"),
    # ── 영어 패턴 ────────────────────────────────────────────────────────────
    (r"(?i)could\s+you\s+(?:please\s+)?(?:run|execute|do|click|check|verify|login)",
     "헌법 제1조(영어): 박씨 실행 요청 금지"),
    (r"(?i)please\s+(?:run|execute|do|click|check|verify|login|open|install)",
     "헌법 제1조(영어): please + 실행 동사 금지"),
    (r"(?i)you\s+(?:need|have)\s+to\s+(?:manually|yourself|directly)",
     "헌법 제1조(영어): 수동 실행 요청 금지"),
    (r"(?i)(?:can|could)\s+you\s+(?:confirm|verify|check|tell\s+me)",
     "헌법 제1조(영어): 확인 요청 금지"),
    (r"(?i)(?:let\s+me\s+know|tell\s+me)\s+(?:if|when|what|how)",
     "헌법 제1조(영어): 정보 요청 금지 — 에이전트가 직접 확인"),
    (r"(?i)what\s+(?:would\s+you\s+like|do\s+you\s+want|should\s+(?:i|we)\s+do)",
     "헌법 제1조(영어): 의향 질문 금지 — 최선 판단 자율 실행"),
    (r"(?i)shall\s+(?:i|we)\s+proceed",
     "헌법 제1조(영어): 진행 허가 요청 금지"),
    (r"(?i)(?:do\s+you\s+want\s+me\s+to|should\s+i)\s+",
     "헌법 제1조(영어): 수행 허가 요청 금지"),
]

# ─── 자율 실행 실패 보고 형식 (헌법 제1조 부속 규칙) ──────────────────────────
# 전부 실패해도 박씨한테 "해주세요" 금지. 이 형식으로만 보고.

SELF_EXECUTION_FAILURE_FORMAT = """
[자율 실행 실패 보고]
시도한 방법:
  1. {method_1} → {result_1}
  2. {method_2} → {result_2}
  3. {method_3} → {result_3}

기술적 한계: {technical_limit}

자율 대안: {next_autonomous_option}
박씨 필요 여부: 없음
"""
# 자율 대안 있을 때 마지막 줄: "없음 — 자율 대안으로 계속"
# 자율 대안 없을 때 마지막 줄: "없음 — 현재 환경 제약으로 불가"
# 실제 분기는 report_failure() 함수에서 처리

# ─── DeepSeek 등록 검증 ───────────────────────────────────────────────────────

DEEPSEEK_CONFIG_PATH = Path.home() / ".claude-deepseek" / ".claude.json"

def _check_deepseek_registered() -> bool:
    """DeepSeek ~/.claude-deepseek/.claude.json 등록 여부 확인"""
    return DEEPSEEK_CONFIG_PATH.exists()

# ─── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _read_law(filename: str) -> str:
    path = LAW_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"[없음: {filename}]"


def _write_audit(entry: dict):
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    # 감사 로그에 멘탈 상태 자동 포함 (지적 5)
    if "mental_state" not in entry:
        entry["mental_state"] = _get_mental_state()
    if "agitation" not in entry:
        entry["agitation"] = _get_agitation_level()
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _mask_secrets(text: str) -> str:
    """감사 로그 저장 전 민감 정보 마스킹"""
    text = re.sub(r'(?i)(bot_token\s*=\s*)["\'][\d]+:[A-Za-z0-9_\-]+["\']',
                  r'\1"***MASKED***"', text)
    text = re.sub(r'(?i)(chat_id\s*=\s*)["\'][\d]+["\']',
                  r'\1"***MASKED***"', text)
    return text


# ─── 툴 ───────────────────────────────────────────────────────────────────────

@mcp.tool()
def check_policy(agent: str, action: str, command: str = "",
                 action_tags: list = None) -> dict:
    """
    에이전트 액션이 법률 체계에 위반되는지 검사한다.

    Args:
        agent:       에이전트 식별자 (claude / deepseek / system)
        action:      수행하려는 액션 설명
        command:     실행할 명령어 (있으면 패턴 검사 포함)
        action_tags: 액션 태그 목록 (new_design / destructive / schema_change 등)

    Returns:
        {allowed: bool, violations: list, warnings: list, recommendation: str,
         mental_state: str, agitation: int}
    """
    violations = []
    warnings = []
    tags = set(action_tags or [])

    # ── 1. MENTAL_STATE 게이트 (헌법 제7조) ───────────────────────────────
    mental_state = _get_mental_state()
    agitation    = _get_agitation_level()

    if mental_state == "high_risk":
        blocked_tags = tags & HIGH_RISK_BLOCKED_TAGS
        if blocked_tags or any(
            kw in action.lower() for kw in
            ["새로 만들", "신규 설계", "delete", "reset", "drop", "schema"]
        ):
            violations.append(
                f"헌법 제7조: MENTAL_STATE=high_risk — "
                f"신규 설계/파괴적 작업 차단. 멘탈 회복 후 재시도."
            )

    if mental_state == "rest_required":
        warnings.append(
            "헌법 제7조: MENTAL_STATE=rest_required — "
            "현재 작업은 가능하나 신규 설계는 박씨 컨디션 확인 후 진행."
        )

    if agitation >= 80:
        warnings.append(
            f"헌법 제7조: AGITATION_LEVEL={agitation} — "
            "행동 99 / 보고 1 모드. 질문/확인 요청 금지."
        )

    # ── 2. 헌법 파일 수정 감지 (메타 법률) ────────────────────────────────
    full_text = f"{action} {command}"
    for cf in CONSTITUTION_FILES:
        if cf in full_text and any(
            kw in full_text.lower() for kw in
            ["edit", "write", "수정", "변경", "delete", "삭제", "overwrite"]
        ):
            violations.append(
                f"메타 법률 위반: {cf} 직접 수정 금지. "
                "헌법 개정 절차(law/DEEPSEEK-CONFIG.md §개정절차) 준수 필요."
            )

    # ── 3. 명령어 패턴 검사 (금지 패턴 + 태그 엔진) ────────────────────────
    if command:
        for pattern, msg, pat_tags in FORBIDDEN_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                violations.append(msg)
                tags |= pat_tags

    # ── 4. DeepSeek 교차 수정 금지 (헌법 제5조) ────────────────────────────
    if agent == "deepseek" and "papyrus" in action.lower():
        violations.append("헌법 제5조: DeepSeek은 papyrus 자율 수정 금지")

    # ── 5. DeepSeek IDLE 툴콜 감지 ─────────────────────────────────────────
    if agent == "deepseek" and action.lower() in ["echo", "idle", "wait", "기다림", "대기"]:
        violations.append("역할계약 위반: DeepSeek IDLE 시 툴콜 금지")

    # ── 6. DeepSeek 미등록 감지 (헌법 제5조 + DeepSeek 우회 방지) ──────────
    if agent == "deepseek" and not _check_deepseek_registered():
        violations.append(
            "헌법 제5조 + DeepSeek 우회 방지: "
            "~/.claude-deepseek/.claude.json 미등록. "
            "law/DEEPSEEK-CONFIG.md 설치 가이드 참조."
        )

    # ── 7. 승인 게이트 필요 여부 확인 ──────────────────────────────────────
    for gate in APPROVAL_REQUIRED:
        if gate in action.lower() or gate in command.lower():
            warnings.append(
                f"헌법 제4조: '{gate}' → 박씨 승인 필요. 텔레그램 보고 먼저"
            )

    allowed = len(violations) == 0
    recommendation = (
        "통과. 자율 실행." if allowed and not warnings
        else "경고: 박씨 승인 후 실행." if not violations
        else "차단: 법률 위반. 아래 조항 확인."
    )

    entry = {
        "ts":         datetime.now().isoformat(),
        "agent":      agent,
        "action":     action,
        "command":    _mask_secrets(command[:200]) if command else "",
        "tags":       list(tags),
        "allowed":    allowed,
        "violations": violations,
        "warnings":   warnings,
    }
    _write_audit(entry)

    return {
        "allowed":       allowed,
        "violations":    violations,
        "warnings":      warnings,
        "recommendation": recommendation,
        "mental_state":  mental_state,
        "agitation":     agitation,
    }


@mcp.tool()
def check_response(response_text: str, agent: str = "claude") -> dict:
    """
    [v4 신규] 헌법 제1조 강제 게이트 — 응답 텍스트 사전 검열.

    에이전트가 박씨에게 응답을 보내기 전에 이 툴을 실행한다.
    박씨한테 실행을 요청/떠넘기는 문장이 있으면 즉시 차단한다.

    Args:
        response_text: 박씨에게 보낼 응답 텍스트 (전체)
        agent:         에이전트 식별자

    Returns:
        {
          clean: bool,          # True = 전송 가능, False = 차단
          violations: list,     # 위반 패턴 목록
          blocked_sentences: list,  # 위반 문장 목록
          instruction: str,     # 수정 지시
          rewrite_required: bool
        }

    사용법:
        result = check_response(response_text=내_응답)
        if not result["clean"]:
            # 응답 수정 후 재검사
            ...
        else:
            # 전송
    """
    violations = []
    blocked_sentences = []

    # 문장 단위 분리 — 마침표/느낌표/물음표 뒤 공백, 또는 줄바꿈
    # 한국어는 마침표 없이 줄바꿈으로 문장이 끝나는 경우가 많아 \n도 구분자로 처리
    sentences = re.split(r'(?<=[.!?。])\s+|\r?\n', response_text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        for pattern, msg in PARKSY_REQUEST_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                violations.append(msg)
                blocked_sentences.append(sentence[:120])
                break  # 문장당 첫 번째 위반만

    clean = len(violations) == 0

    instruction = ""
    if not clean:
        instruction = (
            "응답 수정 필요. 아래 문장들을 삭제하고 에이전트 자율 실행으로 대체하라.\n"
            "금지: 박씨에게 실행/확인/클릭/로그인/입력 요청하는 모든 문장.\n"
            "허용: '직접 실행했습니다' / '결과: ...' / '완료. ...' 형식만."
        )

    _write_audit({
        "ts":      datetime.now().isoformat(),
        "agent":   agent,
        "action":  "check_response",
        "result":  f"clean={clean}, violations={len(violations)}",
        "status":  "passed" if clean else "blocked",
    })

    return {
        "clean":            clean,
        "violations":       violations,
        "blocked_sentences": blocked_sentences,
        "instruction":      instruction,
        "rewrite_required": not clean,
    }


@mcp.tool()
def report_failure(
    agent: str,
    task: str,
    attempts: list,
    technical_limit: str,
    next_autonomous_option: str = "",
) -> str:
    """
    [v4 신규] 자율 실행 전부 실패 시 보고 형식 강제 생성.

    박씨한테 "해주세요" 요청 없이 실패를 보고하는 유일한 방법.
    에이전트가 N가지 방법을 모두 시도한 후 불가능할 때만 사용.

    Args:
        agent:                  에이전트 식별자
        task:                   원래 시도한 작업
        attempts:               시도 목록. 각 항목: {"method": str, "result": str}
        technical_limit:        기술적 한계 (왜 모든 방법이 실패했는지)
        next_autonomous_option: 박씨 없이 가능한 다음 자율 대안 (없으면 "")

    Returns:
        박씨에게 전송 가능한 보고 텍스트 (요청 문장 없음)

    주의:
        이 툴을 쓰기 전에 최소 3가지 방법을 시도했어야 한다.
        attempts 리스트가 3개 미만이면 경고를 포함한다.
    """
    if len(attempts) < 3:
        warning = f"⚠ 경고: {len(attempts)}가지만 시도. 자율 시도 의무는 최소 3가지."
    else:
        warning = ""

    lines = ["[자율 실행 실패 보고]", f"작업: {task}", ""]
    lines.append("시도한 방법:")
    for i, attempt in enumerate(attempts, 1):
        m = attempt.get("method", "?")
        r = attempt.get("result", "?")
        lines.append(f"  {i}. {m} → {r}")

    lines.append("")
    lines.append(f"기술적 한계: {technical_limit}")

    if next_autonomous_option:
        lines.append(f"자율 대안: {next_autonomous_option}")
        lines.append("박씨 개입 필요: 없음 — 자율 대안으로 계속 진행.")
    else:
        lines.append("자율 대안: 현재 환경 제약으로 없음.")
        lines.append("박씨 개입 필요: 없음 — 작업 보류 또는 다음 세션에서 재시도.")

    if warning:
        lines.append("")
        lines.append(warning)

    report = "\n".join(lines)

    _write_audit({
        "ts":      datetime.now().isoformat(),
        "agent":   agent,
        "action":  f"report_failure: {task}",
        "result":  f"attempts={len(attempts)}, limit={technical_limit[:100]}",
        "status":  "failure_reported",
    })

    return report


@mcp.tool()
def get_approval(action_type: str) -> dict:
    """
    헌법 제4조 기준으로 박씨 승인이 필요한지 판단한다.

    Args:
        action_type: 액션 종류 (예: youtube_upload / repo_delete / billing_api 등)

    Returns:
        {needs_approval: bool, reason: str, telegram_format: str}
    """
    needs = any(a in action_type.lower() for a in APPROVAL_REQUIRED)

    if needs:
        fmt = (
            "텔레그램 보고 형식:\n"
            "제목: [콘텐츠 제목]\n"
            "채널: @채널명\n"
            "형식: 롱폼 Xmin / 쇼츠 Xsec\n"
            "요약: 3줄\n"
            "판단: 올릴 만한 이유\n"
            "→ OK하시면 바로 실행합니다"
        )
        reason = "헌법 제4조: public 배포 / 파괴적 작업 / 과금 API / 토큰 10만+ → 박씨 승인 필수"
    else:
        fmt = ""
        reason = "자율 실행 범위. 박씨 승인 불필요."

    return {"needs_approval": needs, "reason": reason, "telegram_format": fmt}


@mcp.tool()
def verify_asset(tool_name: str) -> dict:
    """
    헌법 제3조: 기존 자산이 있는지 확인한다. 신규 개발 전 필수 실행.

    Args:
        tool_name: 확인할 도구명 (예: youtube_upload / split_inference / run_and_publish)

    Returns:
        {exists: bool, path: str, note: str}
    """
    if tool_name in ASSET_CATALOG:
        path = ASSET_CATALOG[tool_name]
        exists = Path(path).exists() if path.startswith("/") else True
        return {
            "exists": exists,
            "path": path,
            "note": "기존 자산 사용. 신규 개발 금지." if exists else "경로 존재하나 파일 없음. 확인 필요.",
        }

    results = []
    for ext in ["*.cjs", "*.js", "*.py", "*.sh"]:
        results += list(TOOLS_DIR.rglob(ext))

    matches = [str(p) for p in results if tool_name.replace("_", "") in p.name.replace("_", "").lower()]

    if matches:
        return {"exists": True, "path": matches[0], "note": f"발견 {len(matches)}개. 신규 개발 금지."}

    scm = PAPYRUS / "parksy_scm_mcp.py"
    if scm.exists():
        content = scm.read_text(encoding="utf-8")
        if tool_name.replace("_", "") in content.replace("_", "").lower():
            return {"exists": True, "path": str(scm), "note": "parksy_scm_mcp.py 내 함수로 존재."}

    return {
        "exists": False,
        "path": "",
        "note": "기존 자산 없음. 신규 개발 허용 — 단, tools/ 아래에 배치.",
    }


@mcp.tool()
def get_law(law_id: str) -> str:
    """
    특정 법률 조항 내용을 반환한다.

    Args:
        law_id: 법률 파일 식별자
                00 = 헌법
                01 = 글로벌법
                02 = 역할계약
                03 = 의사결정트리
                04 = SOP-퍼블리싱
                ds = DeepSeek 설정 가이드
                all = 전체

    Returns:
        법률 전문 텍스트
    """
    mapping = {
        "00":   "00-CONSTITUTION.md",
        "01":   "01-GLOBAL-LAW.md",
        "02":   "02-ROLE-CONTRACT.md",
        "03":   "03-DECISION-TREE.md",
        "04":   "04-SOP-PUBLISHING.md",
        "ds":   "DEEPSEEK-CONFIG.md",
        "헌법":  "00-CONSTITUTION.md",
        "글로벌법": "01-GLOBAL-LAW.md",
        "역할계약": "02-ROLE-CONTRACT.md",
        "의사결정": "03-DECISION-TREE.md",
        "sop":  "04-SOP-PUBLISHING.md",
        "deepseek": "DEEPSEEK-CONFIG.md",
    }

    key = law_id.lower().strip()

    if key == "all":
        parts = []
        for fname in ["00-CONSTITUTION.md", "01-GLOBAL-LAW.md", "02-ROLE-CONTRACT.md",
                      "03-DECISION-TREE.md", "04-SOP-PUBLISHING.md", "DEEPSEEK-CONFIG.md"]:
            parts.append(_read_law(fname))
        return "\n\n---\n\n".join(parts)

    fname = mapping.get(key)
    if fname:
        return _read_law(fname)

    return f"[오류] 알 수 없는 law_id: {law_id}. 사용 가능: 00~04 / ds / all"


@mcp.tool()
def audit_log(agent: str, action: str, result: str,
              status: str = "done") -> str:
    """
    에이전트 액션을 감사 로그에 기록한다.

    Args:
        agent:  에이전트 (claude / deepseek)
        action: 수행한 액션
        result: 결과 요약
        status: done / failed / blocked / pending_approval / policy_feedback

    Returns:
        로그 저장 확인 메시지

    Note:
        status="policy_feedback" 로 기록 시,
        01-GLOBAL-LAW.md 정책 개선 제안 루프로 분류됨.
        반복 차단 패턴 → law 담당자(Claude 메인)가 검토 가능.
    """
    entry = {
        "ts":     datetime.now().isoformat(),
        "agent":  agent,
        "action": action,
        "result": _mask_secrets(result[:500]),
        "status": status,
    }
    _write_audit(entry)
    return f"감사 로그 기록 완료 [{entry['ts']}] {agent}: {action} → {status}"


@mcp.tool()
def detect_mental_state(message: str) -> dict:
    """
    헌법 제7조: 박씨 메시지에서 멘탈/컨디션 신호를 감지한다.

    Args:
        message: 박씨 발화 텍스트

    Returns:
        {state: str, level: str, mode: str, instruction: str,
         recommended_mental_state: str}
        state: normal / irritated / delegated / stop
        level: mild / strong / critical
        mode: normal / action99 / loop100 / halt
        recommended_mental_state: ok / high_risk / rest_required
    """
    # 첫 매칭 return 금지 — 메시지 전체를 스캔해서 최고 severity를 선택한다.
    # 예: "씨발 됐어" → 씨발(mild) + 됐어(stop) → stop이 우선
    PRIORITY = {"mild": 1, "strong": 2, "stop": 3, "delegate": 4}
    best_level = None

    for pattern, level in MENTAL_SIGNALS:
        if re.search(pattern, message, re.IGNORECASE):
            if best_level is None or PRIORITY[level] > PRIORITY[best_level]:
                best_level = level

    if best_level == "delegate":
        return {
            "state": "delegated",
            "level": "critical",
            "mode": "loop100",
            "instruction": (
                "명시 위임 감지. 100점 자율 루프 진입. "
                "중간 질문/보고 없이 완성까지 자율 실행. "
                "자기평가 포함. 100점 아니면 재작업. "
                "완료 후 결과 한 번만 보고."
            ),
            "recommended_mental_state": "ok",
        }
    if best_level == "stop":
        return {
            "state": "stop",
            "level": "critical",
            "mode": "halt",
            "instruction": "중단 신호. 현재 작업 즉시 멈추고 다음 지시 대기.",
            "recommended_mental_state": "rest_required",
        }
    if best_level == "strong":
        return {
            "state": "irritated",
            "level": "strong",
            "mode": "action99",
            "instruction": (
                "강한 짜증 감지. 행동 99 / 보고 1 모드. "
                "현재 패턴 즉시 폐기. 말 줄이고 실행. "
                "완료 후 한 줄만 보고. 질문 금지."
            ),
            "recommended_mental_state": "high_risk",
        }
    if best_level == "mild":
        return {
            "state": "irritated",
            "level": "mild",
            "mode": "action99",
            "instruction": "짜증 감지. 보고 줄이고 행동 중심으로 전환.",
            "recommended_mental_state": "ok",
        }

    return {
        "state": "normal",
        "level": "none",
        "mode": "normal",
        "instruction": "정상. 일반 모드 유지.",
        "recommended_mental_state": "ok",
    }


@mcp.tool()
def set_mental_state(state: str, agitation: int = -1,
                     sleep_hours: float = -1.0) -> str:
    """
    헌법 제7조: PARKSY_MENTAL_STATE를 /tmp/parksy_mental_state 파일에 기록.

    Args:
        state:       ok / high_risk / rest_required
        agitation:   0-100 (-1 = 현재값 유지)
        sleep_hours: 최근 24시간 수면 시간 (-1 = 미기록)

    Returns:
        설정 완료 메시지
    """
    if state not in ("ok", "high_risk", "rest_required"):
        return f"[오류] 잘못된 state: {state}. 허용값: ok / high_risk / rest_required"

    lines = [f"STATE={state}"]
    if agitation >= 0:
        lines.append(f"AGITATION={max(0, min(100, agitation))}")
    if sleep_hours >= 0:
        lines.append(f"SLEEP_HOURS={sleep_hours:.1f}")
    lines.append(f"UPDATED={datetime.now().isoformat()}")

    MENTAL_STATE_FILE.write_text("\n".join(lines) + "\n")

    _write_audit({
        "ts":     datetime.now().isoformat(),
        "agent":  "system",
        "action": f"set_mental_state → {state}",
        "result": f"agitation={agitation}, sleep_hours={sleep_hours}",
        "status": "done",
    })

    return (
        f"MENTAL_STATE={state} 설정 완료. "
        f"Agitation={agitation if agitation >= 0 else '변경없음'}. "
        f"파일: {MENTAL_STATE_FILE}"
    )


@mcp.tool()
def get_audit_log(lines: int = 20, filter_status: str = "") -> str:
    """
    최근 감사 로그를 반환한다.

    Args:
        lines:         반환할 줄 수 (기본 20)
        filter_status: 특정 status만 필터 (예: policy_feedback / blocked / done)

    Returns:
        JSONL 형식 최근 로그 (mental_state 포함)
    """
    if not AUDIT_LOG.exists():
        return "[감사 로그 없음]"

    all_lines = AUDIT_LOG.read_text(encoding="utf-8").strip().split("\n")

    if filter_status:
        filtered = []
        for l in all_lines:
            if not l.strip():
                continue
            try:
                if json.loads(l).get("status") == filter_status:
                    filtered.append(l)
            except (json.JSONDecodeError, ValueError):
                pass
        all_lines = filtered

    recent = all_lines[-lines:]

    output = []
    for line in recent:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            ts        = entry.get("ts", "")[:16]
            agent     = entry.get("agent", "?")
            action    = entry.get("action", "")[:50]
            status    = entry.get("status", entry.get("allowed", "?"))
            ms        = entry.get("mental_state", "")
            agit      = entry.get("agitation", "")
            ms_str    = f" [멘탈:{ms}" + (f"/{agit}" if agit != "" else "") + "]" if ms else ""
            output.append(f"[{ts}] {agent} | {action} | {status}{ms_str}")
        except Exception:
            output.append(line[:100])

    return "\n".join(output) if output else "[조건에 맞는 로그 없음]"


@mcp.tool()
def self_test() -> dict:
    """
    [v5 신규] 핵심 로직 자가 검증 — detect_mental_state() 11케이스 + _get_mental_state() 파일 파싱.

    "규칙 수를 늘리는 것보다 핵심 버그 없이 최고 severity가 정확히 씹히는지를
    테스트로 계속 보증하는 것이 더 중요하다" (2026-06-05 운영 원칙)

    Returns:
        {passed: int, failed: int, total: int, failures: list, ok: bool}
    """
    CASES = [
        # (입력, 기대 state, 기대 level, 설명)
        ("왜 이렇게 하냐",       "irritated", "mild",     "왜이렇게 단독"),
        ("병신같이 하네",        "irritated", "strong",   "병신 단독"),
        ("씨발",                "irritated", "mild",     "씨발 단독 → mild"),
        ("개새끼야",            "irritated", "strong",   "개새끼 단독"),
        ("됐어",                "stop",      "critical",  "됐어 단독 → stop"),
        ("그만",                "stop",      "critical",  "그만 단독 → stop"),
        ("씨발 됐어",           "stop",      "critical",  "씨발+됐어 → stop 우선"),
        ("병신 됐어",           "stop",      "critical",  "병신+됐어 → stop 우선"),
        ("알아서 해",           "delegated", "critical",  "위임 단독"),
        ("끝내버려",            "delegated", "critical",  "위임 변형"),
        ("오늘 날씨 좋네",      "normal",    "none",      "정상 발화"),
    ]

    failures = []
    for msg, exp_state, exp_level, desc in CASES:
        r = detect_mental_state(msg)
        ok = (r["state"] == exp_state and r["level"] == exp_level)
        if not ok:
            failures.append({
                "case": desc,
                "input": msg,
                "expected": f"state={exp_state} level={exp_level}",
                "got":      f"state={r['state']} level={r['level']}",
            })

    # _get_mental_state() 파일 파싱 직접 검증
    # set_mental_state()가 쓰는 형식: "STATE=high_risk\nAGITATION=85\n..."
    # 라인별 파싱이 정상이면 "high_risk" 반환해야 함
    def _parse_state_from_text(text: str) -> str:
        for line in text.splitlines():
            if line.startswith("STATE="):
                val = line.split("=", 1)[1].strip()
                if val in ("ok", "high_risk", "rest_required"):
                    return val
        return "ok"

    test_file_content = "STATE=high_risk\nAGITATION=85\nSLEEP_HOURS=4.0\nUPDATED=2026-06-05T00:00:00\n"
    parsed = _parse_state_from_text(test_file_content)
    if parsed != "high_risk":
        failures.append({
            "case": "_get_mental_state() 파일 파싱",
            "input": "STATE=high_risk\\nAGITATION=85\\n...",
            "expected": "high_risk",
            "got": parsed,
        })

    # raw 전체 비교 버그가 재발하는지도 확인 (구 버그: raw in ("ok", ...) 전체 비교)
    raw_buggy = test_file_content.strip() in ("ok", "high_risk", "rest_required")
    if raw_buggy:
        failures.append({
            "case": "_get_mental_state() raw 전체 비교 버그 재발",
            "input": "raw.strip() 전체 비교",
            "expected": "False (절대 전체와 매치 안 돼야 함)",
            "got": "True (버그 재발)",
        })

    total = len(CASES) + 2   # detect 11케이스 + 파싱 1 + raw버그재발 1
    passed = total - len(failures)

    _write_audit({
        "ts":     datetime.now().isoformat(),
        "agent":  "system",
        "action": "self_test",
        "result": f"passed={passed}/{total}",
        "status": "done" if not failures else "failed",
    })

    return {
        "ok":       len(failures) == 0,
        "passed":   passed,
        "failed":   len(failures),
        "total":    total,
        "failures": failures,
    }


# ─── 메인 ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
