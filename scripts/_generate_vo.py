#!/usr/bin/env python3
"""P0.5 VO Generator — shot_bible 기반 한국어 내레이션 초안 생성

각 beat의 caption + context를 읽고 자연스러운 한국어 VO 문장을 생성합니다.
Grok API가 사용 가능하면 LLM 기반 생성, 없으면 템플릿 기반 fallback.

Usage:
  python3 scripts/_generate_vo.py <OUTDIR>
  python3 scripts/_generate_vo.py /root/work/out/pd_tistory_v2
"""
from __future__ import annotations

import json, os, sys, subprocess
from pathlib import Path


def grok_generate(prompt: str) -> str | None:
    """Try Grok CLI for VO generation. Returns None if unavailable."""
    try:
        r = subprocess.run(
            ["grok", "한국어로 2-3문장의 짧은 내레이션을 만들어줘. " + prompt],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            text = r.stdout.strip()
            if text and len(text) > 5:
                return text[:200]
    except Exception:
        pass
    return None


def template_vo(beat: dict, bible: dict) -> str:
    """Template-based VO generation when LLM is unavailable."""
    role = beat.get("role", "build")
    caption = beat.get("caption", "")
    context = beat.get("vo", "")  # P0 puts raw context in vo field
    title = bible.get("title", "")

    # Clean context: remove heading repetition
    if context.startswith(caption):
        context = context[len(caption):].strip()
        if context.startswith("."):
            context = context[1:].strip()

    # Extract key sentence (first meaningful sentence)
    sentences = [s.strip() for s in context.replace("\n", " ").split(".") if len(s.strip()) > 10]
    key_sentence = sentences[0] if sentences else context[:80]

    templates = {
        "hook": [
            f"지금 보시는 건 {title or caption}입니다. {key_sentence}.",
            f"{caption}. {key_sentence} — 이게 핵심입니다.",
        ],
        "build": [
            f"{caption}. {key_sentence}.",
            f"{caption}에 대해 알려드릴게요. {key_sentence}.",
        ],
        "climax": [
            f"여기가 중요합니다. {caption} — {key_sentence}.",
            f"핵심은 {caption}입니다. {key_sentence}.",
        ],
        "resolve": [
            f"정리하면 {key_sentence}. {caption}.",
            f"{key_sentence}. 이것이 {title or caption}의 전부입니다.",
        ],
    }

    options = templates.get(role, templates["build"])
    # Pick the option that best fits the context length
    if len(key_sentence) > 50:
        vo = options[0]
    else:
        vo = options[1] if len(options) > 1 else options[0]

    # Trim to reasonable length (Edge TTS handles long text but shorter = better pacing)
    if len(vo) > 150:
        vo = vo[:147] + "..."

    return vo


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 _generate_vo.py <OUTDIR>")
        return 1

    outdir = Path(sys.argv[1])
    bible_path = outdir / "shot_bible.json"

    if not bible_path.exists():
        print(f"❌ No shot_bible.json in {outdir}")
        return 1

    bible = json.loads(bible_path.read_text(encoding="utf-8"))
    beats = bible.get("beats") or []

    if not beats:
        print("⚠️  No beats in shot_bible — skip VO generation")
        return 0

    print(f"🎙  P0.5 VO Generator — {len(beats)} beats")

    # ── Try Grok first ──
    use_llm = False
    for beat in beats:
        caption = beat.get("caption", "")
        context_raw = beat.get("vo", "")
        prompt = f"제목: {caption}. 내용: {context_raw[:200]}"

        vo = grok_generate(prompt)
        if vo:
            use_llm = True
            beat["vo"] = vo
        else:
            beat["vo"] = template_vo(beat, bible)

    if use_llm:
        print("  🤖 VO generated via Grok LLM")
    else:
        print("  📝 VO generated via template (Grok unavailable)")

    # ── Save ──
    bible_path.write_text(
        json.dumps(bible, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for b in beats:
        print(f"  {b['id']:25s} | {b['vo'][:70]}...")

    print(f"  ✅ shot_bible updated — Next: python3 scripts/_direct_map.py {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
