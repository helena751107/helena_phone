"""한국어 TTS 종합 텍스트 정규화 엔진 v2.

처리 순서: 음수 → 화폐 → 퍼센트 → 숫자+단위 → 버전 → 소수
         → snake_case → 영어사전 → 순수숫자 → ALL_CAPS → 남은영어
"""
from __future__ import annotations
import re

_LETTER_KO = {
    "A": "에이", "B": "비", "C": "씨", "D": "디", "E": "이",
    "F": "에프", "G": "지", "H": "에이치", "I": "아이", "J": "제이",
    "K": "케이", "L": "엘", "M": "엠", "N": "엔", "O": "오",
    "P": "피", "Q": "큐", "R": "알", "S": "에스", "T": "티",
    "U": "유", "V": "브이", "W": "더블유", "X": "엑스", "Y": "와이",
    "Z": "제트",
}

_EN_WORD_MAP: dict[str, str] = {
    # 플랫폼·서비스
    "YouTube": "유튜브", "Instagram": "인스타그램", "TikTok": "틱톡",
    "Twitter": "트위터", "Facebook": "페이스북", "WhatsApp": "왓츠앱",
    "Telegram": "텔레그램", "Discord": "디스코드", "LinkedIn": "링크드인",
    "Pinterest": "핀터레스트", "Snapchat": "스냅챗", "Reddit": "레딧",
    "Netflix": "넷플릭스", "Spotify": "스포티파이", "Twitch": "트위치",
    "Notion": "노션", "Slack": "슬랙", "Zoom": "줌", "Figma": "피그마",
    # AI·LLM
    "ChatGPT": "챗지피티", "OpenAI": "오픈에이아이", "Anthropic": "앤쓰로픽",
    "DeepSeek": "딥시크", "Gemini": "제미나이", "Mistral": "미스트랄",
    "Perplexity": "퍼플렉시티", "HuggingFace": "허깅페이스", "Hugging": "허깅",
    "Claude": "클로드", "Grok": "그록", "Llama": "라마", "Whisper": "위스퍼",
    "Stable": "스테이블", "Diffusion": "디퓨전", "ComfyUI": "콤피유아이",
    "FLUX": "플럭스", "Chatterbox": "채터박스",
    # 클라우드·인프라
    "RunPod": "런팟", "Runpod": "런팟", "Vast": "배스트", "Colab": "콜랩",
    "Vercel": "버셀", "Netlify": "넷리파이", "Heroku": "헤로쿠",
    "Docker": "도커", "Kubernetes": "쿠버네티스", "Terraform": "테라폼",
    "Ansible": "앤서블", "AWS": "에이더블유에스", "GCP": "지씨피",
    "Azure": "애저", "Ubuntu": "우분투", "Linux": "리눅스", "Debian": "데비안",
    "Arch": "아치", "Termux": "터뮤엑스", "Tailscale": "테일스케일",
    # 개발 도구·언어
    "GitHub": "깃허브", "GitLab": "깃랩", "Bitbucket": "빗버킷",
    "Python": "파이썬", "JavaScript": "자바스크립트", "TypeScript": "타입스크립트",
    "Rust": "러스트", "Golang": "고랭", "Kotlin": "코틀린", "Swift": "스위프트",
    "React": "리액트", "Next": "넥스트", "Vue": "뷰", "Angular": "앵귤러",
    "FastAPI": "패스트에이피아이", "Flask": "플라스크", "Django": "장고",
    "PyTorch": "파이토치", "TensorFlow": "텐서플로우", "Numpy": "넘파이",
    "Pandas": "판다스", "Scipy": "사이파이", "Librosa": "라이브로사",
    "Gradio": "그래디오", "Streamlit": "스트림릿", "Playwright": "플레이라이트",
    "Selenium": "셀레니움", "Jupyter": "주피터", "Notebook": "노트북",
    "ffmpeg": "에프에프엠펙", "FFmpeg": "에프에프엠펙",
    "REAPER": "리퍼", "Reaper": "리퍼",
    "SoVITS": "소비츠", "sovits": "소비츠",
    # git 동사·개발 용어
    "push": "푸시", "pull": "풀", "commit": "커밋", "merge": "머지",
    "branch": "브랜치", "checkout": "체크아웃", "rebase": "리베이스",
    "clone": "클론", "fork": "포크", "deploy": "디플로이", "build": "빌드",
    "install": "인스톨", "import": "임포트", "export": "익스포트",
    "download": "다운로드", "upload": "업로드", "update": "업데이트",
    "release": "릴리즈", "debug": "디버그", "test": "테스트",
    "render": "렌더", "inference": "인퍼런스", "train": "트레인",
    "fine-tune": "파인튠", "finetune": "파인튠", "checkpoint": "체크포인트",
    "pipeline": "파이프라인", "sample": "샘플", "samples": "샘플",
    "steps": "스텝", "step": "스텝", "epoch": "에포크", "batch": "배치",
    "model": "모델", "weight": "웨이트", "weights": "웨이트",
    "token": "토큰", "tokens": "토큰", "prompt": "프롬프트",
    "output": "아웃풋", "input": "인풋", "stream": "스트림",
    "log": "로그", "logs": "로그", "server": "서버", "client": "클라이언트",
    "proxy": "프록시", "tunnel": "터널", "widget": "위젯", "script": "스크립트",
    "config": "컨피그", "setup": "셋업", "demo": "데모", "beta": "베타",
    "alpha": "알파", "stable": "스테이블",
    "Pro": "프로", "pro": "프로", "ProPlus": "프로플러스",
    "Plus": "플러스", "plus": "플러스", "Max": "맥스", "max": "맥스",
    "mini": "미니", "nano": "나노", "lite": "라이트",
    # ML 파라미터
    "top": "탑", "size": "사이즈", "rate": "레이트", "learning": "러닝",
    "loss": "로스", "grad": "그래드", "clip": "클립", "warmup": "웜업",
    "dropout": "드롭아웃", "hidden": "히든", "layer": "레이어", "head": "헤드",
    "dim": "딤", "vocab": "보캡", "embed": "임베드", "attention": "어텐션",
    "encoder": "인코더", "decoder": "디코더", "latent": "레이턴트",
    "noise": "노이즈", "seed": "시드", "interval": "인터벌",
    "threshold": "쓰레숄드", "duration": "듀레이션", "fragment": "프래그먼트",
    "parallel": "패러렐", "bucket": "버킷", "streaming": "스트리밍",
    # 웹·네트워크
    "request": "리퀘스트", "response": "리스폰스", "endpoint": "엔드포인트",
    "header": "헤더", "payload": "페이로드", "callback": "콜백",
    "webhook": "웹훅", "timeout": "타임아웃", "retry": "리트라이",
    "cache": "캐시", "port": "포트", "host": "호스트", "path": "패스",
    "query": "쿼리", "session": "세션", "cookie": "쿠키",
    "auth": "오스", "status": "스테이터스", "error": "에러",
    "warning": "워닝", "info": "인포",
    # 기기·OS
    "Android": "안드로이드", "iPhone": "아이폰", "iPad": "아이패드",
    "macOS": "맥오에스", "Windows": "윈도우즈", "Galaxy": "갤럭시",
    "Pixel": "픽셀", "AirPods": "에어팟", "Bluetooth": "블루투스",
    "WiFi": "와이파이", "Wi-Fi": "와이파이",
    # 단위 (숫자+단위 패턴에서 먼저 처리됨)
    "TB": "테라바이트", "GB": "기가바이트", "MB": "메가바이트", "KB": "킬로바이트",
    "GHz": "기가헤르츠", "MHz": "메가헤르츠", "kHz": "킬로헤르츠", "Hz": "헤르츠",
    "dBFS": "디비에프에스", "dB": "데시벨",
    "fps": "에프피에스", "FPS": "에프피에스",
    "bps": "비피에스", "Kbps": "킬로비피에스", "Mbps": "메가비피에스", "Gbps": "기가비피에스",
    # 약어
    "AI": "에이아이", "TTS": "티티에스", "GPT": "지피티", "API": "에이피아이",
    "STT": "에스티티", "RVC": "알브이씨", "GPU": "지피유", "CPU": "씨피유",
    "LLM": "엘엘엠", "MCP": "엠씨피", "SDK": "에스디케이", "VPN": "브이피엔",
    "URL": "유알엘", "IT": "아이티", "UI": "유아이", "UX": "유엑스",
    "ML": "엠엘", "SSH": "에스에스에이치", "HTTP": "에이치티티피",
    "HTTPS": "에이치티티피에스", "SCP": "에스씨피",
    "WAV": "웨이브", "MP3": "엠피쓰리", "MP4": "엠피포",
    "PDF": "피디에프", "CSV": "씨에스브이", "DB": "디비",
    "PC": "피씨", "TV": "티비", "SNS": "에스엔에스",
    "ONNX": "온엑스", "DPO": "디피오", "LoRA": "로라",
    "MIDI": "미디", "DAW": "디에이더블유", "VST": "브이에스티",
    "SSD": "에스에스디", "HDD": "에이치디디", "RAM": "램", "ROM": "롬",
    "USB": "유에스비", "HDMI": "에이치디엠아이",
    "RTX": "알티엑스", "GTX": "지티엑스", "VRAM": "브이램",
    "WSL": "더블유에스엘", "ADB": "에이디비", "OTA": "오티에이",
    "PR": "피알", "CLI": "씨엘아이", "IDE": "아이디이", "CI": "씨아이",
    "RESTful": "레스트풀", "REST": "레스트", "JSON": "제이슨",
    "YAML": "야믈", "XML": "엑스엠엘", "HTML": "에이치티엠엘", "CSS": "씨에스에스",
    "JWT": "제이더블유티", "OAuth": "오오스",
    "SaaS": "사스", "PaaS": "파스", "IaaS": "이아스",
    "OCR": "오씨알", "NLP": "엔엘피", "ASR": "에이에스알", "VAD": "브이에이디",
    "BERT": "버트", "ViT": "브이아이티", "GAN": "갠", "VAE": "브이에이이",
    "RLHF": "알엘에이치에프",
}

_WORD_PAT = re.compile(
    r"(?<![A-Za-z0-9])("
    + "|".join(re.escape(k) for k in sorted(_EN_WORD_MAP, key=len, reverse=True))
    + r")(?![A-Za-z0-9])",
    re.IGNORECASE,
)

_NUM_UNIT_PAT = re.compile(
    r"(\d+(?:\.\d+)?)\s*(TB|GB|MB|KB|GHz|MHz|kHz|Hz|dBFS|dB|fps|FPS|Kbps|Mbps|Gbps|bps)(?![A-Za-z])"
)
_CURRENCY_PAT = re.compile(r"\$(\d+(?:\.\d+)?)")
_WON_PAT      = re.compile(r"₩(\d+(?:,\d{3})*)")
_PCT_PAT      = re.compile(r"(\d+(?:\.\d+)?)%")
_VERSION_PAT  = re.compile(r"\bv(\d+(?:\.\d+)*(?:[A-Za-z]\w*)?)\b")
_NUM_PAT      = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d+)(?!\.\d)(?![A-Za-z])")
_DECIMAL_PAT  = re.compile(r"(?<!\d)(\d+)\.(\d+)(?!\d)")
_SNAKE_PAT    = re.compile(r"([A-Za-z]+)_([A-Za-z]+(?:_[A-Za-z]+)*)")
_ALLCAPS_PAT  = re.compile(r"(?<![A-Za-z])([A-Z]{2,})(?![a-z])")
_ENG_FALLBACK = re.compile(r"[A-Za-z][a-z]*(?:[A-Z][a-z]*)*")

_KO_ONES  = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
_KO_UNITS = ["", "십", "백", "천"]
_KO_BIG   = ["", "만", "억", "조", "경"]


def _int_to_ko(n: int) -> str:
    if n == 0:
        return "영"
    if n < 0:
        return "마이너스 " + _int_to_ko(-n)
    result = ""
    big_idx = 0
    while n > 0:
        chunk = n % 10000
        if chunk:
            chunk_str = ""
            for i, d in enumerate(reversed(str(chunk))):
                d = int(d)
                if d:
                    one = _KO_ONES[d] if d != 1 or i == 0 else ""
                    chunk_str = one + _KO_UNITS[i] + chunk_str
            result = chunk_str + _KO_BIG[big_idx] + result
        big_idx += 1
        n //= 10000
    return result


def _num_to_ko(s: str) -> str:
    s = s.replace(",", "")
    try:
        return _int_to_ko(int(s))
    except ValueError:
        return s


def normalize_ko_text(text: str) -> str:
    """한국어 TTS 종합 텍스트 정규화 v2."""

    # 0. 음수
    text = re.sub(r"(?<![A-Za-z0-9])-(\d+(?:\.\d+)?)",
                  lambda m: "마이너스 " + m.group(1), text)

    # 1. 화폐
    text = _CURRENCY_PAT.sub(lambda m: _num_to_ko(m.group(1)) + "달러", text)
    text = _WON_PAT.sub(lambda m: _num_to_ko(m.group(1).replace(",", "")) + "원", text)

    # 2. 퍼센트
    text = _PCT_PAT.sub(lambda m: _num_to_ko(m.group(1)) + "퍼센트", text)

    # 3. 숫자+단위
    def _num_unit(m: re.Match) -> str:
        num, unit = m.group(1), m.group(2)
        ko_unit = _EN_WORD_MAP.get(unit, unit)
        if "." not in num:
            num_ko = _num_to_ko(num)
        else:
            i_part, d_part = num.split(".", 1)
            d_part = d_part.rstrip("0") or "0"
            num_ko = _num_to_ko(i_part) + "점" + "".join(_KO_ONES[int(c)] or "영" for c in d_part)
        return num_ko + " " + ko_unit
    text = _NUM_UNIT_PAT.sub(_num_unit, text)

    # 4. 버전 번호
    def _verpart(s: str) -> str:
        if s.isdigit():
            return _num_to_ko(s)
        chunks = re.split(r"(\d+)", s)
        result = []
        for ch in chunks:
            if not ch:
                continue
            if ch.isdigit():
                result.append(_num_to_ko(ch))
            else:
                words = re.sub(r"([A-Z][a-z]+)", r" \1",
                               re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", ch)).split()
                for w in words:
                    ko = _EN_WORD_MAP.get(w) or _EN_WORD_MAP.get(w.lower()) or _EN_WORD_MAP.get(w.capitalize())
                    result.append(ko if ko else "".join(_LETTER_KO.get(c.upper(), c) for c in w))
        return "".join(result)

    def _ver(m: re.Match) -> str:
        parts = re.split(r"([.\-])", m.group(1))
        out = []
        for p in parts:
            out.append("점" if p in (".", "-") else _verpart(p))
        return "버전 " + "".join(out)
    text = _VERSION_PAT.sub(_ver, text)

    # 5. 소수
    def _decimal(m: re.Match) -> str:
        i, d = m.group(1), m.group(2).rstrip("0") or "0"
        return _num_to_ko(i) + "점" + "".join(_KO_ONES[int(c)] or "영" for c in d)
    text = _DECIMAL_PAT.sub(_decimal, text)

    # 6-a. snake_case (사전 적용 전에 분해)
    def _snake(m: re.Match) -> str:
        parts = m.group(0).split("_")
        result = []
        for p in parts:
            ko = _EN_WORD_MAP.get(p) or _EN_WORD_MAP.get(p.lower()) or _EN_WORD_MAP.get(p.capitalize())
            if ko:
                result.append(ko)
            elif len(p) == 1:
                result.append(_LETTER_KO.get(p.upper(), p))
            else:
                result.append(p)
        return " ".join(result)
    text = _SNAKE_PAT.sub(_snake, text)

    # 6-b. 영어 단어 사전
    def _word(m: re.Match) -> str:
        w = m.group(1)
        return _EN_WORD_MAP.get(w) or _EN_WORD_MAP.get(w.upper()) or _EN_WORD_MAP.get(w.lower()) or w
    text = _WORD_PAT.sub(_word, text)

    # 7. 순수 숫자
    text = _NUM_PAT.sub(lambda m: _num_to_ko(m.group(1)), text)

    # 8. 남은 ALL_CAPS
    text = _ALLCAPS_PAT.sub(
        lambda m: "".join(_LETTER_KO.get(c, c) for c in m.group(1)), text)

    # 9. 혹시 남은 밑줄 제거
    text = re.sub(r"(?<=[가-힣A-Za-z])_(?=[가-힣A-Za-z])", " ", text)

    # 10. 남은 영어 → CamelCase 분리 + 자모 폴백
    def _eng_fallback(m: re.Match) -> str:
        w = m.group(0)
        if len(w) == 1:
            return _LETTER_KO.get(w.upper(), w)
        if len(w) == 2:
            ko = _EN_WORD_MAP.get(w) or _EN_WORD_MAP.get(w.upper())
            return ko if ko else "".join(_LETTER_KO.get(c.upper(), c) for c in w)
        parts = re.sub(r"([A-Z][a-z]+)", r" \1",
                       re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", w)).split()
        result = []
        for p in parts:
            ko = _EN_WORD_MAP.get(p) or _EN_WORD_MAP.get(p.upper())
            result.append(ko if ko else "".join(_LETTER_KO.get(c.upper(), c) for c in p))
        return " ".join(result)
    text = _ENG_FALLBACK.sub(_eng_fallback, text)

    return text


# 하위 호환성 alias
normalize_ko = normalize_ko_text
