"""ParkSyTTS v1 — 추론 엔진 (GPT-SoVITS v2ProPlus 래퍼).

S21 proot-Ubuntu CPU 전용. GPU 없어도 동작.
모델 경로: ~/parksy-tts-v1/models/
"""
from __future__ import annotations

import os
import sys
import threading
from io import BytesIO
from pathlib import Path
from typing import Optional

import numpy as np

_DEFAULT_MODEL_DIR = Path(os.environ.get(
    "PARKSY_MODEL_DIR",
    str(Path.home() / "parksy-tts-v1/models"),
))
_DEFAULT_GPT_SOVITS_DIR = Path(os.environ.get(
    "GPT_SOVITS_DIR",
    str(Path.home() / "GPT-SoVITS"),
))

_TARGET_PEAK = 0.88  # -1.1 dBFS


def _peak_normalize(audio: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(audio))
    if peak > _TARGET_PEAK and peak > 1e-6:
        audio = audio * (_TARGET_PEAK / peak)
    return audio


def _load_sovits(weights_path: str | Path):
    """GPT-SoVITS .pth 헤더 trim 우회 로더."""
    import torch
    p = str(weights_path)
    with open(p, "rb") as f:
        meta = f.read(2)
        if meta != b"PK":
            data = b"PK" + f.read()
            return torch.load(BytesIO(data), map_location="cpu", weights_only=False)
    return torch.load(p, map_location="cpu", weights_only=False)


class ParkSyTTS:
    """박씨 음성 합성기 — S21 proot 전용 경량 래퍼.

    사용법:
        tts = ParkSyTTS()
        tts.say("안녕 헬레나!", "/tmp/hello.wav")
    """

    GPT_CKPT    = "gpt/parksy_v2-e15.ckpt"
    SOVITS_CKPT = "sovits/parksy_v2_e8_s256.pth"
    REF_AUDIO   = "ref/seg004.wav"
    REF_TEXT    = "나만의 반복되는 어떤 것들 예를 들면 강의영상 같은 걸 만들 때"

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *a, **kw):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._ready = False
        return cls._instance

    def __init__(
        self,
        model_dir: Optional[Path] = None,
        gptsovits_dir: Optional[Path] = None,
    ):
        if self._ready:
            return
        self._ready = True
        self.model_dir = Path(model_dir or _DEFAULT_MODEL_DIR)
        self.gptsovits_dir = Path(gptsovits_dir or _DEFAULT_GPT_SOVITS_DIR)
        self._tts = None
        self._init_lock = threading.Lock()

    def _load(self):
        if self._tts is not None:
            return
        with self._init_lock:
            if self._tts is not None:
                return

            import torch
            gd = self.gptsovits_dir
            for p in (gd, gd / "GPT_SoVITS", gd / "GPT_SoVITS/eres2net"):
                sp = str(p)
                if sp not in sys.path:
                    sys.path.insert(0, sp)

            os.chdir(str(gd))
            os.environ.setdefault("version", "v2Pro")
            os.environ.setdefault("is_half", "False")
            torch.set_grad_enabled(False)

            from TTS_infer_pack.TTS import TTS, TTS_Config  # type: ignore

            cfg = TTS_Config(str(gd / "GPT_SoVITS/configs/tts_infer.yaml"))
            cfg.device = "cpu"
            cfg.is_half = False
            cfg.version = "v2Pro"
            cfg.t2s_weights_path = str(self.model_dir / self.GPT_CKPT)
            cfg.vits_weights_path = str(self.model_dir / self.SOVITS_CKPT)
            cfg.cnhuhbert_base_path = str(gd / "GPT_SoVITS/pretrained_models/chinese-hubert-base")
            # 한국어 전용 — BERT 0벡터 경로만 탐, chinese-roberta 불필요
            cfg.bert_base_path = str(gd / "GPT_SoVITS/pretrained_models/chinese-hubert-base")
            self._tts = TTS(cfg)

    def say(
        self,
        text: str,
        output_path: str | Path,
        *,
        lang: str = "ko",
        speed: float = 1.0,
        top_k: int = 5,
        temperature: float = 1.0,
        top_p: float = 1.0,
    ) -> Path:
        """텍스트를 박씨 목소리로 합성해 WAV로 저장."""
        import soundfile as sf
        from .normalize import normalize_ko_text

        self._load()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if lang == "ko":
            text = normalize_ko_text(text)

        inputs = {
            "text": text,
            "text_lang": lang,
            "ref_audio_path": str(self.model_dir / self.REF_AUDIO),
            "aux_ref_audio_paths": [],
            "prompt_text": self.REF_TEXT,
            "prompt_lang": "ko",
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "text_split_method": "cut5",
            "batch_size": 1,
            "speed_factor": speed,
            "ref_text_free": False,
            "split_bucket": True,
            "fragment_interval": 0.3,
            "seed": -1,
            "media_type": "wav",
            "streaming_mode": False,
            "parallel_infer": True,
            "repetition_penalty": 1.35,
            "sample_steps": 48,
            "super_sampling": False,
        }

        for sr, audio in self._tts.run(inputs):
            audio = _peak_normalize(audio)
            sf.write(str(out), audio, sr)
            return out

        raise RuntimeError("합성 실패 — 모델 파일 경로를 확인하세요.")
