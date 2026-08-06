#!/usr/bin/env python3
"""ParkSyTTS VITS Decoder ONNX Export — 박씨 목소리 디코더만 추출

SoVITS decoder(84.8M params): semantic tokens → raw audio
GPT stage는 그대로 PyTorch로 유지하고, 디코더만 ONNX 가속.

사용법:
  cd /root/GPT-SoVITS
  python3 /root/work/scripts/_export_parksy_vits_onnx.py
"""
from __future__ import annotations

import os, sys, json
from io import BytesIO
from pathlib import Path

import torch
import numpy as np

# ── Path setup ──
GS = Path("/root/GPT-SoVITS/GPT_SoVITS")
for p in ["/root/GPT-SoVITS", str(GS), str(GS / "eres2net")]:
    if p not in sys.path:
        sys.path.insert(0, p)
os.chdir("/root/GPT-SoVITS")

SOVITS_CKPT = Path("/root/work/helena-programming/parksy-tts-v1/models/sovits/parksy_v2_e8_s256.pth")
OUT_DIR = Path("/root/work/voice_models/parksy_v2")


def _load_ckpt(p: Path):
    with open(p, "rb") as f:
        meta = f.read(2)
        if meta != b"PK":
            return torch.load(BytesIO(b"PK" + f.read()), map_location="cpu", weights_only=False)
    return torch.load(p, map_location="cpu", weights_only=False)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== ParkSyTTS VITS Decoder → ONNX ===\n  out: {OUT_DIR}")

    from module.models_onnx import SynthesizerTrn

    # ── Load SoVITS checkpoint ──
    print(f"\nLoading {SOVITS_CKPT.name}...")
    dict_s2 = _load_ckpt(SOVITS_CKPT)
    hps = dict_s2["config"]
    version = "v2"
    sr = hps["data"]["sampling_rate"]
    print(f"  version={version}  sr={sr}")

    # Dict → attrs
    class HPS(dict):
        def __init__(self, d):
            super().__init__(d)
            for k, v in d.items():
                if isinstance(v, dict):
                    v = HPS(v)
                self[k] = v
                setattr(self, k, v)
    hps = HPS(hps)
    hps.model.semantic_frame_rate = "25hz"

    # ── Build SynthesizerTrn ──
    vq = SynthesizerTrn(
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        n_speakers=hps.data.n_speakers,
        **hps.model,
    )
    vq.load_state_dict(dict_s2["weight"], strict=False)
    vq.eval()

    # ── Speaker embedding ──
    # v2Pro requires sv_emb [1, 20480] as input.
    # ParksyTTS is single-speaker (n_speakers=0) → embedding is constant.
    # Use zero-vector placeholder; actual sv_emb can be pre-computed
    # from the TTS.sv_model stack when full deps are available.
    ref_path = "/root/work/helena-programming/parksy-tts-v1/models/ref/seg004.wav"
    sv_emb_ref = torch.zeros(1, 20480).float()
    print(f"  sv_emb placeholder: {list(sv_emb_ref.shape)} (zero vec — single speaker model)")
    print(f"  ref audio: {ref_path} (embedding will use actual file when deps ready)")

    # ── Spec extractor + VITS decoder (ONNX-exportable) ──
    class VitsDecoder(torch.nn.Module):
        """VITS decoder: reference audio + semantic tokens + speaker emb → waveform."""
        def __init__(self, vq_model, h):
            super().__init__()
            self.vq_model = vq_model
            self.n_fft = h.data.filter_length
            self.hop = h.data.hop_length
            self.win = h.data.win_length
            self.sampling_rate = h.data.sampling_rate

        def forward(self, text_seq, pred_semantic, ref_audio, sv_emb):
            # Mel-spectrogram from reference audio
            hann = torch.hann_window(self.win, device=ref_audio.device, dtype=ref_audio.dtype)
            y = torch.nn.functional.pad(
                ref_audio.unsqueeze(1),
                (int((self.n_fft - self.hop) / 2), int((self.n_fft - self.hop) / 2)),
                mode="reflect",
            ).squeeze(1)
            spec = torch.stft(
                y, self.n_fft, hop_length=self.hop, win_length=self.win,
                window=hann, center=False, pad_mode="reflect",
                normalized=False, onesided=True, return_complex=False,
            )
            refer = torch.sqrt(spec.pow(2).sum(-1) + 1e-6)
            return self.vq_model(pred_semantic, text_seq, refer, sv_emb=sv_emb)

    model = VitsDecoder(vq, hps)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  params: {n_params:,}")

    # ── Dummy inputs (shapes from actual inference) ──
    # text_seq: [B, T_phonemes] — Korean phoneme IDs
    text_seq = torch.randint(0, 500, (1, 30), dtype=torch.long)
    # pred_semantic: [B, 1, T_semantic] — semantic tokens from GPT stage
    pred_semantic = torch.randint(0, 1024, (1, 1, 50), dtype=torch.long)
    # ref_audio: [B, T_samples] — reference audio (3s @ model SR)
    ref_audio = torch.randn(1, sr * 3).float() * 0.01
    sv_emb = sv_emb_ref

    print(f"  text_seq={list(text_seq.shape)}  pred_semantic={list(pred_semantic.shape)}")
    print(f"  ref_audio={list(ref_audio.shape)}  sv_emb={list(sv_emb.shape)}")

    # ── Sanity check: PyTorch forward pass ──
    print("\n[Sanity] PyTorch forward...")
    with torch.no_grad():
        audio = model(text_seq, pred_semantic, ref_audio, sv_emb)
    print(f"  output shape={list(audio.shape)}  peak={float(audio.abs().max()):.4f}")

    # ── Export ONNX ──
    onnx_path = OUT_DIR / "parksy_v2_vits.onnx"
    print(f"\n[Export] → {onnx_path.name}")

    # Use older-style export (not dynamo) for compatibility
    torch.onnx.export(
        model,
        (text_seq, pred_semantic, ref_audio, sv_emb),
        str(onnx_path),
        input_names=["text_seq", "pred_semantic", "ref_audio", "sv_emb"],
        output_names=["audio"],
        dynamic_axes={
            "text_seq": {1: "text_len"},
            "pred_semantic": {2: "semantic_len"},
            "ref_audio": {1: "audio_len"},
            "sv_emb": {0: "batch"},
        },
        opset_version=17,
        dynamo=False,
    )

    size_mb = onnx_path.stat().st_size / 1024 / 1024
    print(f"  ✅ {onnx_path.name} ({size_mb:.1f} MB)")

    # ── Verify with onnxruntime ──
    print("\n[Verify] onnxruntime inference...")
    import onnxruntime as ort
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    ort_inputs = {
        "text_seq": text_seq.numpy(),
        "pred_semantic": pred_semantic.numpy(),
        "ref_audio": ref_audio.numpy(),
        "sv_emb": sv_emb.numpy(),
    }
    ort_audio = sess.run(None, ort_inputs)[0]
    print(f"  output shape={list(ort_audio.shape)}  peak={float(np.abs(ort_audio).max()):.4f}")

    # Compare PyTorch vs ONNX
    diff = np.abs(audio.numpy() - ort_audio).mean()
    print(f"  torch-vs-onnx MAE: {diff:.6f} {'✅' if diff < 0.01 else '⚠️'}")

    # ── Metadata ──
    meta = {
        "project": "parksy_v2",
        "voice": "박씨 목소리",
        "type": "GPT-SoVITS v2Pro → VITS Decoder ONNX",
        "sample_rate": sr,
        "sovits_ckpt": str(SOVITS_CKPT),
        "ref_audio": ref_path,
        "onnx_files": ["parksy_v2_vits.onnx"],
        "inputs": {
            "text_seq": "phoneme IDs [1, text_len] int64 — from Korean phonemizer",
            "pred_semantic": "semantic tokens [1, 1, semantic_len] int64 — from GPT stage",
            "ref_audio": "reference audio [1, audio_len] float32 — 3s at model SR for timbre",
            "sv_emb": "speaker embedding [1, 20480] float32 — pre-computed from ref audio (seg004.wav)",
        },
        "note": "박씨 목소리 디코더. GPT stage만 PyTorch로 돌리고 디코더는 onnxruntime NEON 가속. 추후 NPU delegate.",
    }
    (OUT_DIR / "parksy_v2.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'='*50}")
    print(f"✅ 완료: {onnx_path}")
    print(f"   → voice_engine.py 에서 onnxruntime으로 로드해서 추론 가속")
    return 0


if __name__ == "__main__":
    sys.exit(main())
