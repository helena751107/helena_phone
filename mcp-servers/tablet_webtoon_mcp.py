#!/usr/bin/env python3
"""
tablet-webtoon MCP (구 parksy-gallery 개명) — 태블릿 웹툰: 삼성 그리기 어시스트
전자동 생성 + 웹툰 연출·조립 통합.

2026-09-13 통합판:
  A) 이미지 생성 로직 — 태블릿 최신본(uiautomator dump 동적탐색, 522줄/7툴)
     기준으로 좌표 하드코딩판(이 파일의 구버전, restyle_image가 photo_index
     고정좌표를 썼음)을 교체 + CLI(~/parksy-image/scripts/drawing_assist.py)
     에서 같은 날 실측 확정한 4개 수정 반영:
       1. 프롬프트 100자 하드리밋 실측 확정(한/영 동일 코드포인트) →
          compress_prompt(): 쉼표>공백>하드컷 순 자동 압축
       2. 한글 `adb shell input text` NullPointerException →
          ADBKeyboard IME + ADB_INPUT_TEXT broadcast 우회
       3. preflight_hard_reset() — 세로모드강제+절전해제+IME전환+앱재시작을
          모든 생성 호출 앞에 무조건 실행(옵션 없음)
       4. check_token_alive() — 삼성 SAccountTokenManager 토큰 만료(가장 흔한
          "자동화는 되는데 이미지가 안 나옴" 원인)를 logcat으로 감지
  B) 웹툰 연출·조립 — 폰 `phone-webtoon-make`(phone_webtoon_make_mcp.py)의
     webtoon_direct(BLIP눈+텔레그램)/webtoon_assemble(식자+HTML조립)을 이식.
     구판의 "소스 내용 무관 하드코딩 4컷" 버그를 소스 gist 반영 동적설계로 교체.
  C) 신설 webtoon_generate(cuts) — 폰이 설계한 컷을 이 태블릿에서 전자동으로
     직접 생성(restyle_image 반복 호출). 폰 레인이 "화면 뺏기지 않으려고"
     일부러 반자동(박씨가 직접 붙여넣기)으로 남겨뒀던 단계를 대체하는 옵션 —
     강제 아님, 박씨가 "자동으로 해" 라고 할 때만 씀.

★ 작업 조건 (2026-09-15 재확인 — 이 MCP의 정체):
    지휘 = WSL / 랩탑 (이 MCP가 도는 곳. 여기서 adb로 태블릿을 조종한다)
    실행 = 태블릿 SM-X716N (100.86.15.50:5900) 삼성 갤러리/그리기 어시스트
    매개 = ADB (uiautomator dump → bounds → input tap). 루팅 불필요.
    산출 = 태블릿 컷 → WSL 회수 → 조립 → GitHub Pages + 티스토리 발행

★ 콜드스타트 조건 (이번에 영구 저장, 2026-09-15 박씨 지시):
    ① 태블릿 기초 IME는 언제나 '삼성 키보드'. ADBKeyboard는 입력 순간에만
       켜고 finally에서 원복한다 — 태블릿 기초값을 오염시키지 않는다.
       → webtoon_env_apply()가 이 기초값을 저장, webtoon_env_status()가 검증.
    ② 프리셋 얼굴 9종(parksy_40s 등)은 parksy-faces canonical이 정본.
       → preset_faces(sync=True, clean=True)로 대조·동기화·격리.
    ③ 발행 타깃은 '변수'다 — 박씨가 매번 옮겨 다닌다.
       → set_publish_target()/get_publish_target(), 호출 인자로도 덮어씀.
    ④ 발행은 3단계다: #publish-layer-btn → basicSet 공개선택 → #publish-btn.
       middle 단계를 빼면 발행 버튼이 렌더되지 않는다.

트릴로지 위치: 박씨 티칭(parksy-teaching)·판서튜토리얼(po-tutorial)과 같은
"태블릿" 워크센터. 코드 위치는 parksy-image(WSL 원본) + 태블릿 로컬 사본
(/root/work/mcp-servers/) 양쪽 동기화 유지.

의존: 태블릿 ADB 연결(100.86.15.50:5900), ADBKeyboard 사전설치
     (com.android.adbkeyboard), Pillow(워터마크 크롭),
     프리셋(/sdcard/DCIM/박씨 갤러리/프리셋/parksy_30s.png 등)
결과: /sdcard/DCIM/박씨 갤러리/Drawing_assist_*.jpg
      웹툰 HTML: ~/parksy-webzine/webtoon/index.html
"""
import glob
import os
import re
import shutil
import subprocess
import time

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("tablet-webtoon")  # 태블릿 웹툰 (구 parksy-gallery)

TAB = "100.86.15.50:5900"
PKG = "com.samsung.android.app.sketchbook"
ACT = "com.samsung.android.app.sketchbook.application.DrawingActivity"
ADB_IME = "com.android.adbkeyboard/.AdbIME"
# ★ 콜드스타트 조건(2026-09-15 박씨 지시): 태블릿의 '기초값' IME는 언제나
# 삼성 키보드다. ADBKeyboard는 입력하는 그 순간에만 켜고 반드시 되돌린다.
# (구판은 preflight마다 ADBKeyboard를 기본 IME로 박아놔서, 박씨가 태블릿을
#  직접 쓸 때마다 ADB 키보드가 튀어나왔다 — "기초값으로 하라" 지시의 원인.)
SAMSUNG_IME = "com.samsung.android.honeyboard/.service.HoneyBoardService"

# 2026-09-13 실측 확정 — 삼성 그리기 어시스트 프롬프트 입력창 하드 리밋.
# 한/영 동일 (코드포인트 기준). 이 값 넘으면 삼성 EditText가 조용히 잘라버림.
PROMPT_MAX_CHARS = 100

STYLES = {
    "아르 누보": (273, 357), "아르누보": (273, 357),
    "웹툰": (624, 357),
    "소프트 일러스트": (975, 357),
    "인스타툰": (1326, 357),
    "수채화": (273, 625),
    "일러스트": (624, 625),
    "팝아트": (975, 625),
    "스케치": (1326, 625),
    "3D 카툰": (273, 893), "3D카툰": (273, 893),
    "유화": (624, 893),
}

STYLE_USE = {
    "아르 누보": "기본값 (전체 기본)",
    "일러스트": "매뉴얼·설명서",
    "스케치": "실사 (사진 업로드 베이스)",
    "소프트 일러스트": "캐릭터 추출 (배경 없음 → 누끼)",
    "웹툰": "웹툰",
    "수채화": "삽화 (문학 작품 등)",
    "팝아트": "포스터·일본 잡지 느낌",
    "3D 카툰": "픽사 느낌",
    "유화": "유화",
    "인스타툰": "❌ 사용 안 함 (버림)",
}

SUGGEST = {
    "기본": "아르 누보", "아르누보": "아르 누보",
    "매뉴얼": "일러스트", "설명서": "일러스트",
    "실사": "스케치", "사진": "스케치", "리얼": "스케치",
    "캐릭터": "소프트 일러스트", "누끼": "소프트 일러스트", "추출": "소프트 일러스트",
    "삽화": "수채화", "문학": "수채화",
    "포스터": "팝아트", "잡지": "팝아트",
    "픽사": "3D 카툰", "3d": "3D 카툰", "3D": "3D 카툰",
    "웹툰": "웹툰", "만화": "웹툰",
}

NEW = (1443, 119)
TEXT_INPUT = (500, 1896)
VIEW_ALL = (1287, 2114)
GENERATE = (800, 2276)
SAVE = (851, 270)
PHOTO_ATTACH = (242, 1897)

DEFAULT_SOURCE = "parksy_30s.png"

GALLERY_DIR = "/sdcard/DCIM/박씨 갤러리"
DRAWING_DIR = "/sdcard/DCIM/Drawing assist"
PRESET_DIR = GALLERY_DIR + "/프리셋"
STAGE_DIR = "/sdcard/Pictures/parksy_stage"
STAGE_ALBUM_NAME = "parksy_stage"
# 정본 얼굴이 아닌 파일의 격리소 — ★ DCIM 밖이어야 한다(앨범 안 하위폴더는
# 삼성 갤러리 피커가 별도 앨범으로 노출하므로 AI 입력 경로에 남는다).
MISC_QUARANTINE = "/sdcard/Documents/parksy_preset_misc"

_DUMP_REMOTE = "/sdcard/_pw_dump.xml"
_DUMP_LOCAL = "/tmp/_pw_dump.xml"

WEBTOON_DIR = os.path.expanduser("~/parksy-webzine/webtoon")
ASSET_DIR = os.path.join(WEBTOON_DIR, "cuts")
VISION_SCRIPT = "/root/vision/see.py"  # BLIP 눈 — 이 기기엔 없을 수 있음, 없으면 폴백
TG_SCRIPT = os.path.expanduser("~/work/tg.sh")


# ── ADB 저수준 ──────────────────────────────────────────────────────────────

def _adb(*args):
    return subprocess.run(["adb", "-s", TAB, *args], capture_output=True, text=True, timeout=60)


def _tap(x, y):
    _adb("shell", "input", "tap", str(x), str(y))


def _dump_ui() -> str:
    _adb("shell", "uiautomator", "dump", _DUMP_REMOTE)
    r = _adb("pull", _DUMP_REMOTE, _DUMP_LOCAL)
    if r.returncode != 0:
        return ""
    try:
        with open(_DUMP_LOCAL, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _node_center(xml_text: str, text: str, resource_id: str = None):
    for m in re.finditer(r"<node ([^>]*?)/?>", xml_text):
        attrs = m.group(1)
        if f'text="{text}"' not in attrs:
            continue
        if resource_id and f'resource-id="{resource_id}"' not in attrs:
            continue
        b = re.search(r'bounds="(\[[0-9,\[\]]+\])"', attrs)
        if not b:
            continue
        x1, y1, x2, y2 = map(int, re.findall(r"\d+", b.group(1)))
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    return None


def _first_thumbnail(xml_text: str):
    best = None
    for m in re.finditer(r"<node ([^>]*?)/?>", xml_text):
        attrs = m.group(1)
        cls_m = re.search(r'class="([^"]*)"', attrs)
        if not cls_m or "ImageView" not in cls_m.group(1):
            continue
        b = re.search(r'bounds="(\[[0-9,\[\]]+\])"', attrs)
        if not b:
            continue
        x1, y1, x2, y2 = map(int, re.findall(r"\d+", b.group(1)))
        if best is None or (y1, x1) < (best[1], best[0]):
            best = (x1, y1, x2, y2)
    if best is None:
        return None
    x1, y1, x2, y2 = best
    return ((x1 + x2) // 2, (y1 + y2) // 2)


# ── 압축·입력·프리플라이트·토큰체크 (2026-09-13 실측 확정 로직) ──────────────

def compress_prompt(prompt: str, max_chars: int = PROMPT_MAX_CHARS) -> str:
    """삼성 100자 한도에 맞춰 프롬프트를 압축한다 (실측 확정: 한/영 동일 100자).

    쉼표 경계 > 공백(단어) 경계 > 하드컷 순으로 시도. 말줄임표는 안 붙인다
    (그 글자수만큼 원문이 더 잘려나가는 손해가 더 큼 — 삼성이 알아서 자른다).
    """
    prompt = prompt.strip()
    if len(prompt) <= max_chars:
        return prompt
    truncated = prompt[:max_chars]
    last_comma = truncated.rfind(",")
    if last_comma > max_chars * 0.5:
        return truncated[:last_comma].strip()
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.5:
        return truncated[:last_space].strip()
    return truncated


def _ime_default() -> str:
    """현재 태블릿의 기본 IME(기초값)를 읽는다."""
    return _adb("shell", "settings", "get", "secure", "default_input_method").stdout.strip()


def _ime_set(ime: str):
    _adb("shell", "ime", "set", ime)


def _input_text_unicode(text: str):
    """한글 포함 유니코드 텍스트를 ADBKeyboard broadcast로 입력한다.

    `adb shell input text`는 한글에 NullPointerException(Android 셸 키맵 한계,
    영어는 정상). ADBKeyboard로 IME 전환 후 ADB_INPUT_TEXT 브로드캐스트 사용.
    로컬+원격 이중 따옴표 필수 — 안 하면 공백에서 인자가 쪼개짐(실측 확인).

    ★ 2026-09-15 박씨 지시: 입력 '그 순간에만' ADBKeyboard로 바꾸고 finally에서
    반드시 원래 기본 IME(삼성 키보드)로 되돌린다. 태블릿의 기초값을 절대
    오염시키지 않는다 — 박씨가 태블릿을 직접 쓸 때 ADB 키보드가 뜨면 안 됨.
    """
    prev = _ime_default() or SAMSUNG_IME
    if prev == ADB_IME:
        prev = SAMSUNG_IME
    _adb("shell", "ime", "enable", ADB_IME)
    _ime_set(ADB_IME)
    time.sleep(0.6)
    try:
        escaped = text.replace("'", "'\\''")
        _adb("shell", f"am broadcast -a ADB_INPUT_TEXT --es msg '{escaped}'")
        time.sleep(1.2)
    finally:
        _adb("shell", "ime", "disable", ADB_IME)
        _ime_set(prev)
        time.sleep(0.4)


def check_token_alive() -> dict:
    """삼성 계정(SAccountTokenManager) 액세스 토큰 생존 여부를 logcat으로 확인.

    토큰 만료 시 `Token length : 0`으로 찍히고 생성 요청은 에러 팝업도 없이
    조용히 실패한다(2026-09-13 실측 확정 — 가장 흔한 실패 원인). 재부팅하면
    재발급됨(길이 25로 정상화 실측). ADB로는 복구 불가 — 재부팅만이 해법.
    """
    r = subprocess.run(
        ["adb", "-s", TAB, "logcat", "-d", "-s", "SketchBook:I"],
        capture_output=True, text=True, timeout=30
    )
    lines = [l for l in r.stdout.splitlines() if "SAccountTokenManager" in l and "Token length" in l]
    if not lines:
        return {"checked": False, "reason": "로그에 토큰 발급 기록 없음 (앱을 아직 안 띄웠을 수 있음)"}
    last = lines[-1]
    m = re.search(r"Token length\s*:\s*(\d+)", last)
    length = int(m.group(1)) if m else -1
    alive = length > 0
    return {
        "checked": True, "alive": alive, "token_length": length, "raw": last.strip(),
        "advice": None if alive else "토큰 길이 0 — 태블릿 재부팅 필요 (삼성 서버 세션 만료, ADB로 복구 불가)",
    }


def preflight_hard_reset():
    """모든 생성 호출 전 무조건 강제 실행 — 옵션으로 끌 수 없음(박씨 지시).

    세로모드 강제(가로면 좌표 전부 어긋남) → 절전 해제(커버닫힘 등으로
    Dozing 고착 시 WAKEUP 키만으론 안 깨어남, svc power stayon 필수) →
    ADBKeyboard 활성화만(기본 IME는 건드리지 않는다 — 입력 순간에 _input_text_unicode가
    켜고 되돌린다) → 앱 강제 재시작(잔여 상태 제거).
    """
    _adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
    _adb("shell", "settings", "put", "system", "user_rotation", "0")
    _adb("shell", "svc", "power", "stayon", "true")
    _adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    # IME는 여기서 '기본'으로 박지 않는다 — 입력 순간에만 켜고 원복한다.
    _adb("shell", "ime", "enable", ADB_IME)
    time.sleep(0.5)
    _adb("shell", "am", "force-stop", PKG)
    time.sleep(1)
    _adb("shell", "am", "start", "-n", f"{PKG}/{ACT}")
    time.sleep(4)


def _stage_preset_for_picker(source: str):
    preset_path = f"{PRESET_DIR}/{source}"
    existing_path = f"{GALLERY_DIR}/{source}"
    r = _adb("shell",
             f"if [ -f '{preset_path}' ]; then echo PRESET; "
             f"elif [ -f '{existing_path}' ]; then echo EXISTING; "
             f"else echo NONE; fi")
    kind = r.stdout.strip()
    if kind == "NONE":
        return None
    src = preset_path if kind == "PRESET" else existing_path
    _adb("shell", f"mkdir -p '{STAGE_DIR}'")
    _adb("shell", f"rm -f '{STAGE_DIR}'/*")
    dst = f"{STAGE_DIR}/stage.jpg"
    _adb("shell", f"cp '{src}' '{dst}'")
    _adb("shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
         "-d", "file://" + dst)
    time.sleep(1)
    return dst


def _move_latest_to_gallery():
    _adb("shell", "mkdir", "-p", GALLERY_DIR)
    script = (
        f"latest=$(ls -t '{DRAWING_DIR}/'Drawing_assist_*.jpg 2>/dev/null | head -1); "
        f"if [ -n \"$latest\" ]; then mv \"$latest\" '{GALLERY_DIR}/'; fi; "
        f"echo \"$latest\""
    )
    r = _adb("shell", script)
    moved = r.stdout.strip()
    _adb("shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
         "-d", "file://" + GALLERY_DIR)
    if not moved:
        return None
    return GALLERY_DIR + "/" + moved.split("/")[-1]


def _crop_bottom_watermark(path: str, crop_bottom: float = 8.0) -> str:
    from PIL import Image

    local = "/tmp/pg_crop.jpg"
    if os.path.isdir(local):
        shutil.rmtree(local, ignore_errors=True)
    elif os.path.isfile(local):
        os.remove(local)
    subprocess.run(["adb", "-s", TAB, "pull", path, local], capture_output=True, text=True, timeout=60)
    if not os.path.isfile(local):
        return path
    im = Image.open(local)
    w, h = im.size
    new_h = int(h * (1.0 - crop_bottom / 100.0))
    im.crop((0, 0, w, new_h)).save(local, quality=95)
    subprocess.run(["adb", "-s", TAB, "push", local, path], capture_output=True, text=True, timeout=60)
    return path


# ── 툴: 생성 (제너레이트 / 리스타일) ──────────────────────────────────────

@mcp.tool()
def generate_image(prompt: str, style: str = "아르 누보", wait: int = 20, crop_bottom: float = 8.0) -> dict:
    """프롬프트로 이미지를 생성해 갤러리(박씨 갤러리)에 저장한다. 100자 초과시 자동 압축.

    프리플라이트(세로고정/절전해제/한글IME전환/앱재시작)를 무조건 먼저 실행하고,
    저장 직전 삼성 서버 토큰 생존을 확인해 만료 시 재부팅 필요를 명확히 알린다.
    """
    if style not in STYLES:
        return {"ok": False, "error": f"지원하지 않는 스타일: {style}", "styles": list(STYLES)}

    original_prompt = prompt
    prompt = compress_prompt(prompt)
    compressed = prompt != original_prompt

    preflight_hard_reset()
    _tap(*NEW)
    time.sleep(2)
    _tap(*TEXT_INPUT)
    time.sleep(1.2)
    _input_text_unicode(prompt)
    time.sleep(1.2)
    _adb("shell", "input", "keyevent", "KEYCODE_BACK")
    time.sleep(1.5)
    _tap(*VIEW_ALL)
    time.sleep(2.0)
    _tap(*STYLES[style])
    time.sleep(1.5)
    _tap(*GENERATE)
    time.sleep(wait)

    token_status = check_token_alive()
    if token_status.get("checked") and not token_status.get("alive"):
        return {"ok": False, "error": "삼성 계정 토큰 만료 — 태블릿 재부팅 필요",
                "token_status": token_status, "prompt": prompt}

    _tap(*SAVE)
    time.sleep(4)
    path = _move_latest_to_gallery()
    if path is None:
        return {"ok": False, "error": "생성 실패 — 새 이미지가 저장되지 않음",
                "prompt": prompt, "style": style, "token_status": token_status}
    if crop_bottom > 0:
        path = _crop_bottom_watermark(path, crop_bottom)

    return {"ok": True, "prompt": prompt, "prompt_compressed": compressed,
            "original_prompt": original_prompt if compressed else None,
            "style": style, "path": path, "cropped": crop_bottom > 0}


@mcp.tool()
def restyle_image(source: str = DEFAULT_SOURCE, style: str = "아르 누보", prompt: str = "",
                  wait: int = 20, crop_bottom: float = 8.0) -> dict:
    """박씨 고정 프리셋(기본 parksy_30s, 전신크롭)을 업로드해 배경/화풍만 바꾼다.

    2026-09-13: 구판(photo_index 고정좌표)을 폐기하고 uiautomator dump 동적
    탐색으로 교체 — 삼성 갤러리 UI가 좌표 고정으로는 못 버틴다(실측 확인).
    source를 안 넘기면 항상 po-deepfake MCP와 동일한 고정 프리셋을 써서
    웹툰 컷마다 인물이 흔들리지 않게 한다.
    """
    if style not in STYLES:
        return {"ok": False, "error": f"지원하지 않는 스타일: {style}", "styles": list(STYLES)}

    original_prompt = prompt
    prompt = compress_prompt(prompt) if prompt else prompt
    compressed = bool(prompt) and prompt != original_prompt

    preflight_hard_reset()

    staged = _stage_preset_for_picker(source)
    if staged is None:
        return {"ok": False, "error": f"소스 파일을 못 찾음: {source} (프리셋/박씨갤러리 둘 다 없음)"}

    _tap(*PHOTO_ATTACH)
    time.sleep(2.5)

    xml = _dump_ui()
    album_tab = _node_center(xml, "앨범", resource_id="com.sec.android.gallery3d:id/title")
    if album_tab is None:
        _adb("shell", f"rm -f '{staged}'")
        return {"ok": False, "error": "사진피커에서 '앨범' 탭을 못 찾음 (uiautomator dump 실패)"}
    _tap(*album_tab)
    time.sleep(2)

    xml = _dump_ui()
    stage_album = _node_center(xml, STAGE_ALBUM_NAME, resource_id="com.sec.android.gallery3d:id/title")
    if stage_album is None:
        view_all = _node_center(xml, "모두 보기", resource_id="com.sec.android.gallery3d:id/view_all")
        if view_all is not None:
            _tap(*view_all)
            time.sleep(2)
            xml = _dump_ui()
            stage_album = _node_center(xml, STAGE_ALBUM_NAME, resource_id="com.sec.android.gallery3d:id/title")
    if stage_album is None:
        _adb("shell", f"rm -f '{staged}'")
        return {"ok": False, "error": f"앨범 목록에서 '{STAGE_ALBUM_NAME}'을 못 찾음 (미디어스캔 지연 가능)"}
    _tap(*stage_album)
    time.sleep(2)

    xml = _dump_ui()
    pos = _first_thumbnail(xml)
    if pos is None:
        _adb("shell", f"rm -f '{staged}'")
        return {"ok": False, "error": "parksy_stage 앨범 안에서 썸네일을 못 찾음"}
    _tap(*pos)
    time.sleep(3)

    if prompt:
        xml = _dump_ui()
        edit_tab = _node_center(xml, "", resource_id="com.samsung.android.app.sketchbook:id/text_thumbnail_view")
        _tap(*(edit_tab or (917, 1896)))
        time.sleep(1.5)
        for _ in range(PROMPT_MAX_CHARS + 10):
            _adb("shell", "input", "keyevent", "KEYCODE_DEL")
        _input_text_unicode(prompt)
        time.sleep(1)
        _adb("shell", "input", "keyevent", "KEYCODE_BACK")
        time.sleep(1.5)

    _tap(*VIEW_ALL)
    time.sleep(2)
    _tap(*STYLES[style])
    time.sleep(1.5)
    _tap(*GENERATE)
    time.sleep(wait)

    token_status = check_token_alive()
    if token_status.get("checked") and not token_status.get("alive"):
        _adb("shell", f"rm -f '{staged}'")
        return {"ok": False, "error": "삼성 계정 토큰 만료 — 태블릿 재부팅 필요",
                "token_status": token_status, "source": source, "prompt": prompt}

    _tap(*SAVE)
    time.sleep(4)
    path = _move_latest_to_gallery()
    _adb("shell", f"rm -f '{staged}'")
    if path is None:
        return {"ok": False, "error": "생성 실패 — 새 이미지가 저장되지 않음",
                "source": source, "token_status": token_status}
    if crop_bottom > 0:
        path = _crop_bottom_watermark(path, crop_bottom)

    return {"ok": True, "style": style, "source": source, "prompt": prompt,
            "prompt_compressed": compressed,
            "original_prompt": original_prompt if compressed else None,
            "path": path, "cropped": crop_bottom > 0}


@mcp.tool()
def extract_character(prompt: str, wait: int = 20, crop_bottom: float = 0.0) -> dict:
    """누끼(캐릭터 추출) — '소프트 일러스트' 스타일(배경 없음)로 생성."""
    return generate_image(prompt=prompt, style="소프트 일러스트", wait=wait, crop_bottom=crop_bottom)


@mcp.tool()
def check_token() -> dict:
    """삼성 계정 토큰 생존 여부만 확인한다 (이미지 생성 안 함). 자동화가 안 될 때 먼저 이걸로 진단."""
    return check_token_alive()


@mcp.tool()
def list_styles() -> dict:
    """지원 스타일 목록 + 용도 매뉴얼 + 프롬프트 글자수 한도를 반환한다."""
    return {"styles": STYLE_USE, "default": "아르 누보", "prompt_max_chars": PROMPT_MAX_CHARS}


@mcp.tool()
def suggest_style(need: str) -> dict:
    """용도(예: '포스터', '삽화', '실사', '캐릭터')를 보고 스타일을 역제안한다."""
    nl = need.strip().lower()
    for k, v in SUGGEST.items():
        if k in nl or nl in k:
            return {"need": need, "style": v, "use": STYLE_USE.get(v, "")}
    return {"need": need, "style": "아르 누보", "use": "기본값", "fallback": True}


@mcp.tool()
def list_presets() -> dict:
    """박씨 갤러리 프리셋 사진 목록(합성/재스타일용 참조 사진)을 반환한다.

    ⚠️ 이 폴더에 실물 신분증 등 민감사진이 섞여있던 사례가 있었음(2026-08-30).
    """
    r = _adb("shell", f"ls '{PRESET_DIR}/'")
    files = [f for f in r.stdout.strip().split("\n") if f]
    return {"preset_dir": PRESET_DIR, "count": len(files), "presets": files}


# ── 웹툰 연출·조립 (폰 phone-webtoon-make 이식 + 동적 설계로 교체) ──────────

def _fetch_text(source):
    if source.startswith("http"):
        try:
            r = subprocess.run(["curl", "-s", "-m", "20", source], capture_output=True, text=True, timeout=30)
            html = r.stdout
            title = re.search(r"<title>(.*?)</title>", html, re.S)
            title = title.group(1).strip() if title else source
            html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
            html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
            body = re.sub(r"<[^>]+>", " ", html)
            body = re.sub(r"\s+", " ", body).strip()
            return title, body[:1500]
        except Exception as e:
            return source, f"(fetch 오류: {e})"
    else:
        try:
            text = open(source).read()
            return os.path.basename(source), text[:1500]
        except Exception as e:
            return source, f"(읽기 오류: {e})"


def _screenshot(url):
    png = f"/tmp/wt_{int(time.time())}.png"
    code = f'''
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={{"width":1080,"height":1400}})
    pg.goto({url!r}, wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(2000)
    pg.screenshot(path={png!r})
    b.close()
'''
    try:
        subprocess.run(["python3", "-c", code], capture_output=True, timeout=90)
        return png if os.path.isfile(png) else None
    except Exception:
        return None


def _vision(image_path):
    """BLIP으로 이미지를 '본다'. 이 기기엔 없을 수 있음 — 실패해도 텍스트 폴백."""
    if not image_path or not os.path.isfile(VISION_SCRIPT):
        return "(비전 스크립트 없음 — 이 기기엔 BLIP 미설치)"
    try:
        r = subprocess.run(["python3", VISION_SCRIPT, image_path],
                           capture_output=True, text=True, timeout=120)
        lines = r.stdout.splitlines()
        for i, l in enumerate(lines):
            if "CAPTION" in l and i + 1 < len(lines):
                return lines[i + 1].strip()
        return r.stdout.strip()[-300:]
    except Exception as e:
        return f"(비전 오류: {e})"


def _design_dynamic(title, body, vision):
    """소스 내용을 반영한 4컷 연출 설계.

    구판(phone_webtoon_make_mcp.py)의 버그: gist를 계산만 하고 프롬프트엔
    한 글자도 안 씀 — 소스가 뭐든 컷 4개가 완전히 동일했음(2026-09-13 발견).
    이 버전은 hook/gist를 실제 프롬프트 문자열에 삽입한다.
    """
    words = [w.strip(".,!?") for w in body.split() if len(w) > 1][:12]
    gist = " ".join(words[:6]) if words else title[:40]
    hook = words[0] if words else "이야기"

    core = [
        ("앞에 서다", "정면. 두 손 뒤로. 대상을 바라보며 선다.",
         f"박씨 얼굴 합성, {hook} 주제 배경 앞 정면 전신, 두 손 뒤로 바라봄, 다크그린 황동 조명"),
        ("집어 눕히다", "손을 뻗어 핵심을 집는다 → 눕힌다.",
         f"박씨 얼굴 합성, 손 클로즈업, {gist} 관련 오브제를 테이블에 눕히는 순간, 측면 조명"),
        ("일으켜 세우다", "눕힌 것을 세운다 → 빛나는 결과로 변한다.",
         f"박씨 얼굴 합성, {hook} 오브제 세로로 세우며 빛나는 프레임으로 변하는 순간, 역동 구도"),
        ("돌아오다", "완성된 것을 끌어안듯 제자리로.",
         f"박씨 얼굴 합성, {gist} 완성물 안고 돌아와 미소, 전신 구도, 루프 완성"),
    ]
    cuts = [{"n": i + 1, "scene": sc, "motion": mo, "prompt": compress_prompt(pr)}
            for i, (sc, mo, pr) in enumerate(core)]
    return {"title": f"웹툰 — {title}", "source_gist": gist, "vision": vision, "cuts": cuts}


def _tg_send(text):
    try:
        with open("/tmp/wt_tg.txt", "w") as f:
            f.write(text)
        cmd = f'set -a; source {os.path.dirname(TG_SCRIPT)}/.secrets.env 2>/dev/null; set +a; bash {TG_SCRIPT} --no-button "$(cat /tmp/wt_tg.txt)"'
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=30)
        return "ok" if r.returncode == 0 else f"fail: {r.stderr[-120:]}"
    except Exception as e:
        return f"fail: {e}"


def _format_telegram(d, auto_available: bool):
    lines = [f"🎬 태블릿 웹툰 — 연출 기획", "", f"소스: {d['title']}", f"눈(BLIP): {d['vision']}", "",
             "━━━━━━━━━━━━━━━━"]
    for c in d["cuts"]:
        lines += [f"[컷 {c['n']}] {c['scene']}", f"몸동작: {c['motion']}", f"프롬프트:", f"「{c['prompt']}」", ""]
    lines += ["━━━━━━━━━━━━━━━━"]
    if auto_available:
        lines += ["'자동으로 해' 라고 하면 이 컷 그대로 태블릿에서 전자동 생성 (화면 잠깐 뺏김).",
                  "직접 하고 싶으면 갤러리(Drawing assist)에 프롬프트 붙여넣고 생성 후 조립 요청."]
    else:
        lines += ["갤러리(Drawing assist)에 프롬프트 붙여넣고 얼굴 합성 생성 → 저장하면 식자+조립"]
    return "\n".join(lines)


@mcp.tool()
def webtoon_direct(source: str) -> dict:
    """연출 기획 — 소스(URL/문서)를 BLIP 눈으로 본 뒤 4컷 설계(소스 내용 반영) → 텔레그램 전송.

    이후 두 갈래: (1) webtoon_generate 로 이 태블릿에서 바로 전자동 생성
    (2) 박씨가 직접 갤러리에 붙여넣고 생성(반자동, 화면 안 뺏김) — 둘 다 가능,
    강요하지 않는다. 어느 쪽이든 끝나면 webtoon_assemble 로 조립.
    """
    try:
        title, body = _fetch_text(source)
        vision = "(문서라 스크린샷 없음)"
        if source.startswith("http"):
            png = _screenshot(source)
            vision = _vision(png) if png else "(스크린샷 실패)"
        design = _design_dynamic(title, body, vision)
        msg = _format_telegram(design, auto_available=True)
        tg = _tg_send(msg)
        return {"ok": True, "title": title, "vision": vision, "cuts": design["cuts"],
                "telegram": tg, "design": design}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}


@mcp.tool()
def webtoon_generate(cuts: list) -> dict:
    """webtoon_direct가 설계한 컷들을 이 태블릿에서 전자동으로 직접 생성한다.

    화면이 몇 분간 자동으로 움직인다(박씨가 그 시간 태블릿을 다른 용도로
    쓰려던 참이면 부르지 말 것 — 강제 아님, 옵션). 컷마다 restyle_image를
    고정 프리셋(parksy_30s.png)으로 순차 호출.

    Args:
        cuts: [{"prompt": "...", "style": "아르 누보"(생략시 기본)}, ...]
    """
    results = []
    for i, c in enumerate(cuts):
        prompt = c.get("prompt", "")
        style = c.get("style", "아르 누보")
        r = restyle_image(source=DEFAULT_SOURCE, style=style, prompt=prompt, wait=20)
        results.append({"cut": i + 1, "ok": r.get("ok"), "path": r.get("path"), "error": r.get("error")})
        if not r.get("ok") and r.get("token_status", {}).get("checked") and not r["token_status"].get("alive"):
            return {"ok": False, "error": "토큰 만료로 중단 — 태블릿 재부팅 필요",
                    "done": results, "remaining": len(cuts) - len(results)}
    return {"ok": all(x["ok"] for x in results), "n_cuts": len(results), "results": results}


# ── 필름 스프로켓홀 (폰 2026-09-13 완성, 변수화) ──
FILM_STRIP_W = 52
FILM_HOLE_W = 24
FILM_HOLE_H = 18
FILM_HOLE_GAP = 30
FILM_STRIP_COLOR = (14, 26, 20)
FILM_HOLE_COLOR = (236, 231, 208)

# ── 식자 말풍선 위치/크기 (변수화) ──
BUBBLE_LEFT = 60
BUBBLE_RIGHT = 60
BUBBLE_BOTTOM = 14
BUBBLE_FONT = 13

# ── 인터랙티브 (폰 2026-09-14 최종판 — 셀프컨테인드, 모바일 표준) ──
# 2026-09-13~14 폰(kr-merit-aggro.tistory.com/4) 실측 디버깅 이력:
#   1) window scroll 이벤트 방식 → #wrap 내부 스크롤(스킨 position:fixed 프레임)
#      에서 window가 안 스크롤돼 무동작 → IntersectionObserver로 교체
#   2) PC(/4)는 되는데 모바일(/m/4)에서 재현 안 됨 → 티스토리 /m/ 은 스킨 레벨
#      전역 CSS/JS를 걷어내는 별개 레거시 렌더링 경로가 원인 → 포스트 본문
#      안에 직접 셀프컨테인드로 넣으면 /m/ 에서도 그대로 서빙·실행됨(확인)
#   3) requestAnimationFrame 루프로 뷰포트 중앙까지 거리 기반 스케일(0.95~1.08)
#      + sway + 클릭시 shake를 한 애니메이션 루프에 통합(개별 CSS keyframe
#      토글보다 매끄러움) — 최종 완성판
INTERACTIVE_CSS = """
.wt-bubble{opacity:0;transition:opacity .4s;will-change:transform}
.wt-bubble.wt-in{opacity:1}
.wt-char{display:inline-block;opacity:0}
.wt-in .wt-char{animation:wttype .4s cubic-bezier(.34,1.56,.64,1) forwards}
@keyframes wttype{0%{opacity:0;transform:translateY(6px) scale(1.4)}100%{opacity:1;transform:translateY(0) scale(1)}}
.wt-bubble:hover{box-shadow:0 10px 32px rgba(0,0,0,.72),0 0 0 2px rgba(160,138,76,.55)}
"""
INTERACTIVE_JS = """<script>
(function(){var bs=document.querySelectorAll('.wt-bubble');if(!bs.length)return;for(var i=0;i<bs.length;i++){var b=bs[i];var t=b.textContent;b.innerHTML=t.split('').map(function(c,j){return '<span class="wt-char" style="animation-delay:'+(j*0.04).toFixed(3)+'s">'+(c===' '?'&nbsp;':c)+'</span>';}).join('');}var shakes={};for(var k=0;k<bs.length;k++){(function(el){el.addEventListener('click',function(){shakes[el]=Date.now()+450;});})(bs[k]);}if('IntersectionObserver'in window){var io=new IntersectionObserver(function(es){for(var j=0;j<es.length;j++){if(es[j].isIntersecting)es[j].target.classList.add('wt-in');else es[j].target.classList.remove('wt-in');}},{threshold:0.3});for(var l=0;l<bs.length;l++)io.observe(bs[l]);}else{for(var m=0;m<bs.length;m++)bs[m].classList.add('wt-in');}function tick(){var now=Date.now(),vh=innerHeight;for(var j=0;j<bs.length;j++){var b=bs[j];if(!b.classList.contains('wt-in'))continue;var r=b.getBoundingClientRect(),c=r.top+r.height/2,d=Math.abs(c-vh/2);var kk=Math.max(0,1-d/(vh/2)),s=0.95+kk*0.13;var sway=Math.sin(now/800+j*1.3)*5;var sh=0;if(shakes[b]&&now<shakes[b]){var tt=(shakes[b]-now)/450;sh=Math.sin(now/40)*9*tt;}b.style.transform='scale('+s.toFixed(3)+') translateX('+(sway+sh).toFixed(1)+'px)';}requestAnimationFrame(tick);}requestAnimationFrame(tick);})();
</script>"""


def _crop_disclaimer(src, dst):
    try:
        from PIL import Image
        img = Image.open(src)
        w, h = img.size
        img.crop((0, 0, w, int(h * (1 - 0.08)))).save(dst)
    except Exception:
        shutil.copy(src, dst)


def _add_film_sprocket(path):
    """필름 스프로켓홀 효과 — 좌우 다크그린 스트립 + 흰색 구멍 (폰 2026-09-13 완성)."""
    try:
        from PIL import Image, ImageDraw
        img = Image.open(path).convert('RGB')
        w, h = img.size
        new_w = w + 2 * FILM_STRIP_W
        out = Image.new('RGB', (new_w, h), FILM_STRIP_COLOR)
        out.paste(img, (FILM_STRIP_W, 0))
        d = ImageDraw.Draw(out)
        y = FILM_HOLE_GAP // 2
        while y + FILM_HOLE_H < h:
            cx_l = FILM_STRIP_W // 2; cx_r = new_w - FILM_STRIP_W // 2
            d.rectangle([cx_l - FILM_HOLE_W // 2, y, cx_l + FILM_HOLE_W // 2, y + FILM_HOLE_H], fill=FILM_HOLE_COLOR)
            d.rectangle([cx_r - FILM_HOLE_W // 2, y, cx_r + FILM_HOLE_W // 2, y + FILM_HOLE_H], fill=FILM_HOLE_COLOR)
            y += FILM_HOLE_GAP + FILM_HOLE_H
        out.save(path, quality=92)
    except Exception:
        pass


def _compose(title, cut_rel, dialogue):
    """폰(phone_webtoon_make_mcp.py) 2026-09-14 최종판과 동기화.

    말풍선은 컷 이미지 위에 겹쳐서(absolute, 이미지 하단 중앙 오버레이)
    배치하고 class="bubble wt-bubble"로 INTERACTIVE_CSS/JS와 연결한다.
    """
    panels = []
    for i, (cut, text) in enumerate(zip(cut_rel, dialogue), 1):
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        panels.append(f'<section class="panel"><div class="cut"><img src="{cut}" alt="컷 {i}">'
                      f'<div class="bubble wt-bubble"><span class="txt">{safe}</span></div></div></section>')
    return f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — PARKSY 웹툰</title>
<style>:root{{--paper:#0c1710;--ink:#e9e5cf;--brass:#a08a4c}}*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font-family:"Nanum Myeongjo",serif;line-height:1.6}}
.wrap{{max-width:720px;margin:0 auto;padding:20px 16px 80px}}
.mast{{text-align:center;padding:18px 0 26px;border-bottom:1px solid rgba(160,138,76,.3)}}
.mast h1{{font-family:Georgia,serif;font-weight:900;font-size:26px}}.mast .sub{{font-size:11px;letter-spacing:.3em;color:var(--brass);margin-top:6px}}
.panel{{margin:26px 0}}.cut{{position:relative}}.cut img{{width:100%;display:block;border-radius:4px;box-shadow:0 14px 30px rgba(0,0,0,.5)}}
.bubble{{position:absolute;left:{BUBBLE_LEFT}px;right:{BUBBLE_RIGHT}px;bottom:{BUBBLE_BOTTOM}px;background:rgba(233,229,207,.96);color:#1a120c;padding:12px 16px;border-radius:14px;font-size:{BUBBLE_FONT}px;font-weight:700;box-shadow:0 4px 14px rgba(0,0,0,.45);text-align:center}}
footer{{text-align:center;color:var(--brass);font-size:12px;letter-spacing:.2em;padding:30px 0}}{INTERACTIVE_CSS}</style></head><body>
<div class="wrap"><div class="mast"><h1>{title}</h1><div class="sub">PARKSY WEBTOON</div></div>
{''.join(panels)}<footer>PARKSY · 박씨 종합잡지사</footer></div>{INTERACTIVE_JS}</body></html>'''


@mcp.tool()
def webtoon_assemble(dialogue: list, title: str = "웹툰") -> dict:
    """[태블릿 웹툰 메이크] 식자·조립 — 갤러리 최신 컷을 읽어 말풍선을 식자하고
    세로 웹툰 HTML로 조립한다.

    2026-09-14: 폰(kr-merit-aggro.tistory.com/4)이 완성한 최종판 —
    필름 스프로켓홀(좌우 다크그린 필름 프레임) + 인터랙티브 말풍선(타이핑
    pop-in + 뷰포트 중앙 거리기반 스케일/sway + 탭 shake, PC/모바일 /m/ 둘 다
    검증됨)이 _compose()/_add_film_sprocket()에 기본 내장됨 — 여기서 조립하는
    모든 웹툰이 자동으로 이 효과를 갖는다. 별도 옵션/설정 불필요.
    """
    try:
        if not dialogue or not isinstance(dialogue, list):
            return {"ok": False, "error": "dialogue 필요 (대사 리스트)"}
        pats = sorted(glob.glob(os.path.join(GALLERY_DIR, "*.jpg")) + glob.glob(os.path.join(GALLERY_DIR, "*.png")), reverse=True)
        if not pats:
            return {"ok": False, "error": f"갤러리에 컷 없음: {GALLERY_DIR}"}
        n = min(len(pats), len(dialogue))
        os.makedirs(ASSET_DIR, exist_ok=True)
        cut_rel = []
        for i in range(n):
            ext = os.path.splitext(pats[i])[1]
            dst = os.path.join(ASSET_DIR, f"cut_{i+1:02d}{ext}")
            _crop_disclaimer(pats[i], dst)
            _add_film_sprocket(dst)
            cut_rel.append(f"cuts/cut_{i+1:02d}{ext}")
        html = _compose(title, cut_rel, dialogue[:n])
        out = os.path.join(WEBTOON_DIR, "index.html")
        os.makedirs(WEBTOON_DIR, exist_ok=True)
        open(out, "w").write(html)
        return {"ok": True, "n_cuts": n, "html": out, "cuts": cut_rel}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}


# ══════════════════════════════════════════════════════════════════════════
# 환경 기초값 영구 저장 + 발행 타깃 변수화 (2026-09-15 박씨 지시)
# ══════════════════════════════════════════════════════════════════════════
#
# ★ 작업 조건 (재확인 — 이 MCP의 존재 이유):
#     지휘 = WSL / 랩탑  (이 MCP가 도는 곳. 여기서 adb로 태블릿을 조종한다)
#     실행 = 태블릿 SM-X716N (100.86.15.50:5900) — 삼성 갤러리/그리기 어시스트
#     매개 = ADB (uiautomator dump → bounds → input tap). 루팅·앱데이터 접근 불필요.
#     산출 = 태블릿 갤러리 컷 → WSL 회수 → 조립(필름+식자) → GitHub Pages + 티스토리
#
# ★ 발행 타깃은 변수다 — 박씨가 매번 여기저기 옮겨 다닌다. config에 저장되고
#   호출 때 인자로 덮어쓸 수 있다. 하드코딩 금지.

CONFIG_PATH = os.path.expanduser("~/parksy-image/mcp-servers/tablet_webtoon.config.json")
FACES_SRC = os.path.expanduser("~/parksy-faces/canonical")
CANONICAL_FACES = [
    "parksy_40s.png", "parksy_30s.png", "parksy_50s.png", "parksy_casual.jpg",
    "mom.png", "father.png", "elder_sister.png", "2nd_elder_sister.png", "dog.jpg",
]
TISTORY_TOOLS = os.path.expanduser("~/dtslib-papyrus/tools/tistory")

PUBLISH_DEFAULTS = {
    "blog": "kr-merit-aggro",
    "account": "dtslib2k",
    "cdp_socket": "chrome_devtools_remote",   # 태블릿 크롬 (본사그룹은 Terrace)
    "adb_serial": TAB,
}


def _load_config() -> dict:
    import json
    if os.path.isfile(CONFIG_PATH):
        try:
            return json.load(open(CONFIG_PATH, encoding="utf-8"))
        except Exception:
            pass
    return {"publish": dict(PUBLISH_DEFAULTS)}


def _save_config(cfg: dict):
    import json
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    json.dump(cfg, open(CONFIG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _md5_local(p: str) -> str:
    import hashlib
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _md5_remote(p: str) -> str:
    out = _adb("shell", f"md5sum '{p}' 2>/dev/null").stdout.strip()
    return out.split()[0] if out else ""


@mcp.tool()
def webtoon_env_apply() -> dict:
    """[태블릿 웹툰] 태블릿 환경 '기초값'을 지금 이 상태로 확정 저장한다.

    콜드스타트마다 손으로 되돌리던 것들을 한 번에 박는다:
      ① 기본 IME = 삼성 키보드 (ADBKeyboard는 기본에서 제거 — 입력 순간에만 씀)
      ② 세로 고정 (user_rotation=0, accelerometer_rotation=0)
      ③ 절전 해제 (stay_on_while_plugged_in=15, svc power stayon true)
      ④ 프리셋 얼굴 9종 존재 확인 + parksy_stage 앨범 준비
    반환값이 곧 '저장된 기초값' — 다음 콜드스타트에 이 값을 기준으로 검증한다.
    """
    res = {}
    # ① IME — 삼성 키보드가 기초값. ADBKeyboard는 기본 후보에서 내린다.
    prev = _ime_default()
    _adb("shell", "ime", "enable", SAMSUNG_IME)
    _ime_set(SAMSUNG_IME)
    _adb("shell", "ime", "disable", ADB_IME)
    time.sleep(0.5)
    res["ime_prev"] = prev
    res["ime_now"] = _ime_default()
    res["ime_ok"] = res["ime_now"] == SAMSUNG_IME
    # ② 세로 고정
    _adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
    _adb("shell", "settings", "put", "system", "user_rotation", "0")
    res["user_rotation"] = _adb("shell", "settings", "get", "system", "user_rotation").stdout.strip()
    # ③ 절전 해제
    _adb("shell", "settings", "put", "global", "stay_on_while_plugged_in", "15")
    _adb("shell", "svc", "power", "stayon", "true")
    res["stay_on"] = _adb("shell", "settings", "get", "global", "stay_on_while_plugged_in").stdout.strip()
    # ④ 스테이지 앨범
    _adb("shell", f"mkdir -p '{STAGE_DIR}'")
    _adb("shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
         "-d", "file://" + STAGE_DIR)
    # ⑤ 프리셋 얼굴 현황
    res["faces"] = preset_faces()["faces"]
    res["staged_to"] = "settings://tablet (ADB 설정 자체에 영구 저장됨 — 재부팅에도 유지)"
    return {"ok": res.get("ime_ok", False) and res["user_rotation"] == "0", "applied": res}


@mcp.tool()
def webtoon_env_status() -> dict:
    """[태블릿 웹툰] 태블릿 기초값을 읽어서 '작업 가능 상태'인지 판정한다.

    webtoon_env_apply()로 저장한 조건과 대조. 하나라도 어긋나면 그 항목이
    warning으로 뜬다 — 생성 전에 이걸 먼저 본다.
    """
    d = _ime_default()
    rot = _adb("shell", "settings", "get", "system", "user_rotation").stdout.strip()
    stay = _adb("shell", "settings", "get", "global", "stay_on_while_plugged_in").stdout.strip()
    adb_default = (d == ADB_IME)
    warn = []
    if d != SAMSUNG_IME:
        warn.append(f"기본 IME가 삼성 키보드가 아님 (now={d})")
    if adb_default:
        warn.append("ADBKeyboard가 기본 IME로 남아 있음 — 태블릿 직접 사용 시 튀어나옴")
    if rot != "0":
        warn.append(f"세로 고정 아님 (user_rotation={rot})")
    if stay not in ("15", "7", "1"):
        warn.append(f"절전 해제 아님 (stay_on={stay})")
    tk = check_token_alive()
    if tk.get("checked") and not tk.get("alive"):
        warn.append("삼성 계정 토큰 만료 — 태블릿 재부팅 필요")
    return {
        "ok": not warn,
        "device": TAB,
        "role": "실행기 — WSL/랩탑(지휘)이 ADB로 조종하는 삼성 갤러리 자동화",
        "default_ime": d,
        "user_rotation": rot,
        "stay_on_while_plugged_in": stay,
        "token": tk,
        "warnings": warn,
    }


@mcp.tool()
def preset_faces(sync: bool = False, clean: bool = False) -> dict:
    """[태블릿 웹툰] 프리셋 얼굴 9종을 태블릿과 대조한다 (md5).

    sync=True  → WSL 정본(~/parksy-faces/canonical)에서 빠진/다른 얼굴을 태블릿
                 PRESET_DIR로 밀어넣고 MediaScanner를 돌린다.
    clean=True → 정본 9종이 아닌 파일을 '갤러리 앨범 밖'(MISC_QUARANTINE)으로
                 내보낸다. ★ 앨범 안 하위폴더(_misc)로는 부족하다 — 삼성 갤러리
                 피커는 하위폴더도 별도 앨범으로 노출하므로 AI 입력 경로에 남는다.
                 DCIM 밖으로 빼야 피커에서 사라진다. (주민등록증 등 신분증이
                 프리셋에 섞이면 삼성 클라우드 AI로 새어나갈 수 있다.)
    """
    if not os.path.isdir(FACES_SRC):
        return {"ok": False, "error": f"정본 얼굴 폴더 없음: {FACES_SRC}"}
    remote_names = set(_adb("shell", f"ls -1 '{PRESET_DIR}' 2>/dev/null").stdout.split())
    faces, missing, stale = {}, [], []
    for name in CANONICAL_FACES:
        lp = os.path.join(FACES_SRC, name)
        if not os.path.isfile(lp):
            faces[name] = "정본에 없음"
            continue
        lmd5 = _md5_local(lp)
        if name in remote_names:
            rmd5 = _md5_remote(f"{PRESET_DIR}/{name}")
            if rmd5 == lmd5:
                faces[name] = "OK"
            else:
                faces[name] = "다름"
                stale.append(name)
        else:
            faces[name] = "없음"
            missing.append(name)
    if sync and (missing or stale):
        for name in missing + stale:
            _adb("push", os.path.join(FACES_SRC, name), f"{PRESET_DIR}/{name}")
            faces[name] = "동기화됨"
        _adb("shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
             "-d", "file://" + PRESET_DIR)
    extras = sorted(remote_names - set(CANONICAL_FACES))
    moved = []
    if clean and extras:
        _adb("shell", f"mkdir -p '{MISC_QUARANTINE}'")
        for e in extras:
            _adb("shell", f"mv '{PRESET_DIR}/{e}' '{MISC_QUARANTINE}/' 2>/dev/null")
            moved.append(e)
        _adb("shell", "rmdir", f"{PRESET_DIR}/_misc")
        _adb("shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
             "-d", "file://" + PRESET_DIR)
        _adb("shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
             "-d", "file://" + MISC_QUARANTINE)
    return {
        "ok": not missing and not stale,
        "src": FACES_SRC,
        "preset_dir": PRESET_DIR,
        "faces": faces,
        "missing": missing, "stale": stale,
        "extras_moved_to_misc": moved if clean else [],
        "extras_count": 0 if clean else len(extras),
    }


@mcp.tool()
def set_publish_target(blog: str = "", account: str = "", cdp_socket: str = "",
                       adb_serial: str = "") -> dict:
    """[태블릿 웹툰] 티스토리 발행 타깃을 변수로 바꾼다 (박씨가 매번 옮겨 다님).

    blog(블로그 슬러그) / account(계정 id) / cdp_socket(세션을 빌려올 브라우저) /
    adb_serial(세션을 가진 기기). 빈 값은 기존 유지. config에 영구 저장된다.
    """
    cfg = _load_config()
    pub = {**PUBLISH_DEFAULTS, **cfg.get("publish", {})}
    if blog:       pub["blog"] = blog
    if account:    pub["account"] = account
    if cdp_socket: pub["cdp_socket"] = cdp_socket
    if adb_serial: pub["adb_serial"] = adb_serial
    cfg["publish"] = pub
    _save_config(cfg)
    return {"ok": True, "publish": pub, "config": CONFIG_PATH}


@mcp.tool()
def get_publish_target() -> dict:
    """[태블릿 웹툰] 현재 발행 타깃 + config 경로를 반환한다."""
    cfg = _load_config()
    return {"publish": {**PUBLISH_DEFAULTS, **cfg.get("publish", {})}, "config": CONFIG_PATH}


@mcp.tool()
def publish_webtoon(title: str, content: str, tags: list = None,
                    blog: str = "", account: str = "", visibility: str = "public") -> dict:
    """[태블릿 웹툰] 완성 웹툰을 티스토리에 공개 발행한다 (타깃은 변수).

    2026-09-15 실증 파이프라인을 그대로 쓴다:
      ① 태블릿 브라우저(기본 크롬, cdp_socket=chrome_devtools_remote)의 살아있는
         티스토리 세션을 CDP로 대여 → Playwright 프로필에 주입 (캡차 우회)
         · 세션 토큰은 1회용에 가깝다 — 반드시 '발행 직전에' 뽑아 바로 쓴다.
      ② post.py 발행 3단계: #publish-layer-btn(완료) → input[name=basicSet]
         공개선택 → #publish-btn. ★ ②를 빠뜨리면 #publish-btn이 아예 안 뜬다
         (오랫동안 '발행 버튼 없음'으로 죽던 진짜 원인).
      ③ WSL엔 X서버가 없어 post.py(창 띄움)가 TargetClosedError → xvfb-run으로 감싼다.
    """
    import json
    cfg = _load_config()
    pub = {**PUBLISH_DEFAULTS, **cfg.get("publish", {})}
    blog = blog or pub["blog"]
    account = account or pub["account"]
    socket = pub["cdp_socket"]
    serial = pub["adb_serial"]
    tags = tags or []

    if not os.path.isdir(TISTORY_TOOLS):
        return {"ok": False, "error": f"티스토리 툴 없음: {TISTORY_TOOLS}"}

    # ① 세션 대여 (지금 이 순간에 뽑는다)
    env = {**os.environ, "TISTORY_CDP_SOCKET": socket}
    lend = subprocess.run(
        ["python3", "cdp_session_lend.py", "--adb-serial", serial,
         "--profile", f"cookies/{account}",
         "--check-url", f"https://{blog}.tistory.com/manage", "--local-port", "9446"],
        cwd=TISTORY_TOOLS, env=env, capture_output=True, text=True, timeout=180)
    lend_out = (lend.stdout + lend.stderr).strip().splitlines()[-1:] or [""]
    if "성공" not in lend_out[-1]:
        return {"ok": False, "stage": "session_lend", "error": lend_out[-1][:200],
                "hint": f"태블릿 크롬에 {blog} 로그인 탭이 열려 있는지 확인"}

    # ② 포스트 JSON 작성
    posts_dir = os.path.join(TISTORY_TOOLS, "posts")
    os.makedirs(posts_dir, exist_ok=True)
    slug = blog.replace("/", "-")
    pf = os.path.join(posts_dir, f"webtoon_{slug}.json")
    json.dump({"account": account, "blog": blog, "title": title, "content": content,
               "tags": tags, "category": "", "visibility": visibility},
              open(pf, "w", encoding="utf-8"), ensure_ascii=False)

    # ③ 발행 (X서버 없음 → xvfb-run)
    cmd = ["xvfb-run", "-a", "python3", "post.py", "--post", pf]
    if not shutil.which("xvfb-run"):
        cmd = ["python3", "post.py", "--post", pf]
    r = subprocess.run(cmd, cwd=TISTORY_TOOLS, capture_output=True, text=True, timeout=300)
    out = (r.stdout or "") + (r.stderr or "")
    ok = "성공: 1개" in out
    log_tail = [l for l in out.splitlines() if "[kr" in l or "성공:" in l or "실패:" in l][-6:]
    return {"ok": ok, "blog": blog, "account": account, "url": f"https://{blog}.tistory.com",
            "post_json": pf, "log": log_tail}


if __name__ == "__main__":
    mcp.run()
