#!/usr/bin/env python3
"""
Voice engine — community A-bar (Purple Owl / playwright-recast style).

Priority (auto):
  1) Grok / xAI TTS (ara/eve/…) — SuperGrok 성우 본체
  2) local — ParksyTTS v1 (GPT-SoVITS) → Sherpa-ONNX (Kokoro) 폴백
  3) OpenAI tts-1-hd  if OPENAI_API_KEY set
  4) edge-tts + broadcast humanize — last-resort fallback only

TTS_ENGINE=local → 오프라인 전용 (ParksyTTS 우선, Sherpa 폴백)
TTS_ENGINE=grok|openai|edge → 해당 엔진만 사용

Also: multi-click pad, loudnorm chain.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

VOICE_DEFAULT = "ko-KR-SunHiNeural"
OPENAI_VOICE_DEFAULT = "nova"  # multilingual OK for short KO lines
GROK_VOICE_DEFAULT = os.environ.get("GROK_TTS_VOICE", "ara")


def ffprobe_duration(path: Path) -> float:
    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip() or "0")


def humanize_tts(src: Path, dest: Path) -> None:
    """Broadcast chain — edge-tts 기계음 완화."""
    af = (
        "highpass=f=90,"
        "equalizer=f=2800:t=q:w=1.1:g=2.4,"
        "equalizer=f=6500:t=q:w=1.0:g=1.6,"
        "acompressor=threshold=-20dB:ratio=3.5:attack=5:release=70:makeup=2.2,"
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    )
    r = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src), "-af", af,
            "-ar", "24000", "-ac", "1",
            "-c:a", "libmp3lame", "-q:a", "3", str(dest),
        ],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not dest.exists() or dest.stat().st_size < 200:
        shutil.copy(src, dest)


async def tts_edge(text: str, voice: str, dest: Path, retries: int = 4) -> float:
    import edge_tts

    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            if dest.exists():
                dest.unlink()
            # rate slightly slower = more natural product-demo cadence
            communicate = edge_tts.Communicate(text, voice, rate="-8%")
            await communicate.save(str(dest))
            if dest.stat().st_size < 100:
                raise RuntimeError(f"TTS empty: {dest}")
            return ffprobe_duration(dest)
        except Exception as e:
            last_err = e
            await asyncio.sleep(min(8, attempt * 2))
    raise RuntimeError(f"edge-tts failed: {last_err}")


def tts_openai(text: str, dest: Path, voice: str | None = None) -> float:
    """OpenAI Audio Speech API — A-bar voice when key present."""
    import urllib.request
    import json

    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not key:
        raise RuntimeError("no OPENAI_API_KEY")
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({
        "model": os.environ.get("OPENAI_TTS_MODEL", "tts-1-hd"),
        "voice": voice or os.environ.get("OPENAI_TTS_VOICE", OPENAI_VOICE_DEFAULT),
        "input": text,
        "response_format": "mp3",
        "speed": float(os.environ.get("OPENAI_TTS_SPEED", "0.95")),
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        dest.write_bytes(resp.read())
    if dest.stat().st_size < 200:
        raise RuntimeError("openai tts empty")
    return ffprobe_duration(dest)


def tts_grok(text: str, dest: Path, voice: str | None = None) -> float:
    """Grok xAI TTS — scripts/grok_tts.py (session JWT or XAI_API_KEY)."""
    root = Path(__file__).resolve().parents[1]  # /root/work
    script = root / "scripts" / "grok_tts.py"
    if not script.exists():
        raise RuntimeError("grok_tts.py not found")
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(script),
        "--text",
        text,
        "--out",
        str(dest),
        "--voice",
        voice or GROK_VOICE_DEFAULT,
        "--lang",
        os.environ.get("GROK_TTS_LANG", "ko"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not dest.exists() or dest.stat().st_size < 200:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip() or "grok tts failed")
    return ffprobe_duration(dest)


# ── local / offline providers ──────────────────────────────────────────


def _find_parksytts_root() -> Path | None:
    """ParksyTTS v1 설치 경로 자동 탐지."""
    candidates = [
        Path("/root/work/helena-programming/parksy-tts-v1"),
        Path("/root/work/parksy-tts-v1/helena-programming/parksy-tts-v1"),
        Path("/root/work/parksy-tts-v1"),
        Path.home() / "parksy-tts-v1",
    ]
    for c in candidates:
        if (c / "say.py").exists() or (c / "core" / "engine.py").exists():
            return c
    return None


def _find_sherpa_model() -> Path | None:
    """voice_models/ 에서 .onnx 모델 자동 탐지."""
    model_env = os.environ.get("LOCAL_VOICE_MODEL", "")
    if model_env and Path(model_env).exists():
        return Path(model_env)
    candidates = [
        Path("/root/work/helena-programming/voice_models"),
        Path("/root/work/voice_models"),
        Path(__file__).resolve().parents[1] / "voice_models",
    ]
    for d in candidates:
        if d.is_dir():
            onnx_files = sorted(d.glob("*.onnx"))
            if onnx_files:
                return onnx_files[0]
    return None


def _tts_local_parksy(text: str, dest: Path) -> float:
    """ParksyTTS v1 — GPT-SoVITS v2Pro 기반 박씨 목소리.

    parksy-tts-v1/say.py 를 호출. 설치돼 있지 않으면 RuntimeError.
    say.py API: python3 say.py "text" --out output.wav
    """
    root = _find_parksytts_root()
    if root is None:
        raise RuntimeError(
            "ParksyTTS v1 not found. "
            "Clone gift/parksy-tts-v1 or run install.sh first."
        )
    say_py = root / "say.py"
    if not say_py.exists():
        raise RuntimeError(f"ParksyTTS entrypoint missing: {root}/say.py")

    dest.parent.mkdir(parents=True, exist_ok=True)
    wav_dest = dest.with_suffix(".wav")

    # ParksyTTS는 GPT-SoVITS venv Python을 써야 함 (의존성: torch, ffmpeg 등)
    venv_python = root.parent / "GPT-SoVITS" / ".venv" / "bin" / "python3"
    if not venv_python.exists():
        venv_python = Path.home() / "GPT-SoVITS" / ".venv" / "bin" / "python3"
    python_exe = str(venv_python) if venv_python.exists() else sys.executable

    cmd = [
        python_exe, str(say_py),
        text,
        "--out", str(wav_dest),
        "--lang", os.environ.get("PARKSY_TTS_LANG", "ko"),
        "--speed", os.environ.get("PARKSY_TTS_SPEED", "1.0"),
    ]

    env = os.environ.copy()
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(root),
                       timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"ParksyTTS failed: {r.stderr.strip() or r.stdout.strip()}")

    # say.py --out 으로 직접 WAV 출력 → WAV → MP3 변환
    if not wav_dest.exists() or wav_dest.stat().st_size < 100:
        # fallback: /tmp/parksy_say.wav (say.py 기본 출력)
        default_wav = Path("/tmp/parksy_say.wav")
        if default_wav.exists() and default_wav.stat().st_size > 100:
            wav_dest = default_wav
        else:
            raise RuntimeError("ParksyTTS produced no output file")

    r2 = subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_dest),
         "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-q:a", "3", str(dest)],
        capture_output=True, text=True, timeout=60,
    )
    if r2.returncode != 0 or not dest.exists() or dest.stat().st_size < 200:
        raise RuntimeError(f"ParksyTTS wav→mp3 failed: {r2.stderr}")
    return ffprobe_duration(dest)


def _tts_local_sherpa(text: str, dest: Path,
                       model_path: Path | None = None) -> float:
    """Sherpa-ONNX 로컬 추론 — CPU NEON 가속, 오프라인.

    Kokoro (한국어) / VITS 모델 지원.
    voice_models/*.onnx 자동 탐지.
    """
    model_file = model_path or _find_sherpa_model()
    if model_file is None:
        raise RuntimeError(
            "No .onnx model found in voice_models/. "
            "Place a Sherpa-ONNX model or set LOCAL_VOICE_MODEL env."
        )

    tokens_file = model_file.with_suffix(".json")
    if not tokens_file.exists():
        # Kokoro 모델은 .json 토크나이저가 필요
        tokens_file_candidates = list(model_file.parent.glob("*.json"))
        if tokens_file_candidates:
            tokens_file = tokens_file_candidates[0]
        else:
            raise RuntimeError(
                f"No tokens file found for {model_file.name}. "
                "Place a .json tokens file alongside the .onnx model."
            )

    import sherpa_onnx

    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Kokoro 모델 설정
        tts_config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                    model=str(model_file),
                    tokens=str(tokens_file),
                    data_dir=str(model_file.parent),
                ),
            ),
        )
        tts = sherpa_onnx.OfflineTts(tts_config)
    except Exception:
        # VITS / 기타 모델 폴백
        tts_config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=str(model_file),
                    tokens=str(tokens_file),
                    data_dir=str(model_file.parent),
                ),
            ),
        )
        tts = sherpa_onnx.OfflineTts(tts_config)

    speed = float(os.environ.get("LOCAL_VOICE_SPEED", "0.95"))
    audio = tts.generate(text, sid=0, speed=speed)

    # sherpa_onnx 출력 → WAV 저장 → FFmpeg MP3
    import soundfile as sf
    wav_tmp = dest.with_suffix(".wav")
    sf.write(str(wav_tmp), audio.samples, audio.sample_rate)

    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_tmp),
         "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-q:a", "3", str(dest)],
        capture_output=True, text=True,
    )
    if wav_tmp.exists():
        wav_tmp.unlink()
    if r.returncode != 0 or not dest.exists() or dest.stat().st_size < 200:
        raise RuntimeError(f"Sherpa wav→mp3 failed: {r.stderr}")
    return ffprobe_duration(dest)


def tts_local(text: str, dest: Path, *,
              model_path: Path | None = None) -> tuple[float, str]:
    """로컬 TTS 디스패처 — ParksyTTS 우선, Sherpa-ONNX 폴백.

    Returns (duration_sec, provider_id).
    """
    # 1) ParksyTTS v1 (GPT-SoVITS 박씨 목소리)
    parksy_root = _find_parksytts_root()
    if parksy_root is not None:
        try:
            dur = _tts_local_parksy(text, dest)
            return dur, "local/parksytts-v1"
        except Exception as e:
            print(f"  ! local/parksytts failed, falling back to sherpa: {e}", flush=True)

    # 2) Sherpa-ONNX (Kokoro / VITS)
    dur = _tts_local_sherpa(text, dest, model_path=model_path)
    model_name = (model_path or _find_sherpa_model()).stem if (
        model_path or _find_sherpa_model()
    ) else "unknown"
    return dur, f"local/sherpa-{model_name}"


async def synthesize_beat(
    text: str,
    *,
    dest: Path,
    raw_dest: Path,
    edge_voice: str = VOICE_DEFAULT,
    prefer: str = "auto",
) -> tuple[float, str]:
    """
    Returns (duration_sec, provider_id).
    prefer: auto | grok | local | openai | edge
    """
    order: list[str]
    if prefer == "auto":
        # TTS_ENGINE 환경변수로 기본 엔진 지정 가능
        engine_env = os.environ.get("TTS_ENGINE", "")
        if engine_env:
            order = [engine_env]
        else:
            order = ["local", "grok", "openai", "edge"]
    else:
        order = [prefer]

    last_err: Exception | None = None
    for provider in order:
        try:
            if provider == "grok":
                dur = await asyncio.to_thread(tts_grok, text, raw_dest)
                # light polish only — Grok already broadcast-grade
                humanize_tts(raw_dest, dest)
                return ffprobe_duration(dest), f"grok-tts/{GROK_VOICE_DEFAULT}"
            if provider == "local":
                dur, prov_id = await asyncio.to_thread(tts_local, text, raw_dest)
                humanize_tts(raw_dest, dest)
                return ffprobe_duration(dest), prov_id
            if provider == "openai":
                if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")):
                    continue
                dur = await asyncio.to_thread(tts_openai, text, raw_dest)
                humanize_tts(raw_dest, dest)
                return ffprobe_duration(dest), "openai-tts-1-hd"
            if provider == "edge":
                dur = await tts_edge(text, edge_voice, raw_dest)
                humanize_tts(raw_dest, dest)
                return ffprobe_duration(dest), "edge+humanize"
        except Exception as e:
            last_err = e
            print(f"  ! tts {provider} failed: {e}", flush=True)
            continue
    raise RuntimeError(f"all tts providers failed: {last_err}")


def synthesize(text: str, dest: Path, engine: str = "auto") -> tuple[float, str]:
    """간편 진입점 — produce_pd.sh 등에서 호출.

    Returns (duration_sec, provider_id).
    engine: auto | grok | local | openai | edge

    내부적으로 synthesize_beat() 에 위임.
    """
    import tempfile

    dest.parent.mkdir(parents=True, exist_ok=True)
    raw_dest = Path(tempfile.mktemp(suffix=".mp3", prefix="voice_raw_"))

    try:
        dur, prov = asyncio.run(synthesize_beat(
            text,
            dest=dest,
            raw_dest=raw_dest,
            prefer=engine,
        ))
        return dur, prov
    finally:
        if raw_dest.exists():
            raw_dest.unlink(missing_ok=True)


def multi_click_pad(n_clicks: int, base_hold_ms: int = 400) -> float:
    """Airtime so act never drops 2nd click — pro: breath room without 2× overshoot."""
    pad = base_hold_ms / 1000.0
    if n_clicks >= 2:
        return max(pad, 0.55 + (n_clicks - 1) * 1.35)
    if n_clicks == 1:
        return max(pad, 0.65)
    return max(pad, 0.4)
