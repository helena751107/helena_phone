"""한국어 TTS 텍스트 정규화 — 영어 약어를 한국어 발음으로 변환."""
from __future__ import annotations
import re

_KO_ACRONYM_MAP: dict[str, str] = {
    "AI": "에이아이",
    "TTS": "티티에스",
    "GPT": "지피티",
    "API": "에이피아이",
    "STT": "에스티티",
    "RVC": "알브이씨",
    "GPU": "지피유",
    "CPU": "씨피유",
    "LLM": "엘엘엠",
    "MCP": "엠씨피",
    "SDK": "에스디케이",
    "VPN": "브이피엔",
    "URL": "유알엘",
    "IT": "아이티",
    "UI": "유아이",
    "UX": "유엑스",
    "ML": "엠엘",
    "SSH": "에스에스에이치",
    "HTTP": "에이치티티피",
    "SCP": "에스씨피",
    "WAV": "웨이브",
    "MP3": "엠피쓰리",
    "MP4": "엠피포",
    "PDF": "피디에프",
    "CSV": "씨에스브이",
    "DB": "디비",
    "PC": "피씨",
    "TV": "티비",
    "SNS": "에스엔에스",
    "MIDI": "미디",
    "DAW": "디에이더블유",
    "VST": "브이에스티",
}

_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])("
    + "|".join(re.escape(k) for k in sorted(_KO_ACRONYM_MAP, key=len, reverse=True))
    + r")(?![A-Za-z0-9])"
)


def normalize_ko(text: str) -> str:
    """한국어 문장의 영어 약어를 발음대로 변환."""
    return _PATTERN.sub(lambda m: _KO_ACRONYM_MAP[m.group(0)], text)
