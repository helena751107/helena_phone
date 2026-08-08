#!/usr/bin/env python3
"""ParkSyTTS VITS Decode Core ONNX Export — spectrogram → audio 디코더

TTS 파이프라인에서 `vits_model.decode(codes, text, refer, sv_emb)` 호출을
ONNX로 대체. ge(ref_enc+sv_emb) 계산만 PyTorch로 유지하고,
quantizer.decode → enc_p → flow → dec 체인을 ONNX 그래프 하나로 내보냄.

입력:
  codes: [1, T_codes] int64 — GPT stage semantic tokens
  text:  [1, T_text] int64  — phoneme IDs
  ge:    [1, 512, T_spec] float32 — pre-computed global embedding (ref_enc + sv_emb)

출력:
  audio: [1, 1, T_audio] float32 — raw waveform @ 32000Hz

사용법:
  cd /root/GPT-SoVITS
  python3 /root/work/scripts/_export_parksy_vits_decode_onnx.py
"""
from __future__ import annotations

import os, sys, json
from io import BytesIO
from pathlib import Path

import torch
import torch.nn.functional as F
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
    print(f"=== ParkSyTTS VITS decode core → ONNX ===\n  out: {OUT_DIR}")

    from module.models import SynthesizerTrn
    from module import commons

    # ── Load SoVITS checkpoint ──
    print(f"\nLoading {SOVITS_CKPT.name}...")
    dict_s2 = _load_ckpt(SOVITS_CKPT)
    hps = dict_s2["config"]
    version = "v2"
    sr = hps["data"]["sampling_rate"]
    print(f"  version={version}  sr={sr}")

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
    n_params = sum(p.numel() for p in vq.parameters())
    print(f"  params: {n_params:,}")

    # ── ONNX-exportable decode core (steps after ge computation) ──
    class VitsDecodeCore(torch.nn.Module):
        """ge가 이미 계산된 상태에서 codes+text+ge → audio.

        TTS.decode() 메서드에서 ge 계산 후 내부 체인과 동일.
        """
        def __init__(self, vq_model):
            super().__init__()
            self.quantizer = vq_model.quantizer
            self.enc_p = vq_model.enc_p
            self.flow = vq_model.flow
            self.dec = vq_model.dec
            self.ge_to512 = vq_model.ge_to512
            self.is_v2pro = vq_model.is_v2pro
            self.semantic_frame_rate = vq_model.semantic_frame_rate

        def forward(self, codes, text, ge):
            # codes: [1, T_codes] int64
            # text:  [1, T_text] int64
            # ge:    [1, 512, T_spec] float32

            y_lengths = torch.LongTensor([codes.size(2) * 2]).to(codes.device)
            text_lengths = torch.LongTensor([text.size(-1)]).to(text.device)

            quantized = self.quantizer.decode(codes)
            if self.semantic_frame_rate == "25hz":
                quantized = F.interpolate(
                    quantized, size=int(quantized.shape[-1] * 2), mode="nearest"
                )

            if self.is_v2pro:
                ge_for_enc = self.ge_to512(ge.transpose(2, 1)).transpose(2, 1)
            else:
                ge_for_enc = ge

            x, m_p, logs_p, y_mask, _, _ = self.enc_p(
                quantized, y_lengths, text, text_lengths, ge_for_enc, torch.tensor([1.0])
            )
            z_p = m_p + torch.randn_like(m_p) * torch.exp(logs_p) * 0.5
            z = self.flow(z_p, y_mask, g=ge, reverse=True)
            o = self.dec((z * y_mask)[:, :, :], g=ge)
            return o

    model = VitsDecodeCore(vq)
    model.eval()

    # ── Dummy inputs ──
    codes = torch.randint(0, 1024, (1, 1, 60), dtype=torch.long)
    text = torch.randint(0, 500, (1, 30), dtype=torch.long)
    ge = torch.randn(1, 1024, 1).float()  # global style vector — temporal dim=1, broadcasts

    print(f"  codes={list(codes.shape)}  text={list(text.shape)}  ge={list(ge.shape)}")

    # ── Sanity check: PyTorch forward ──
    print("\n[Sanity] PyTorch forward...")
    with torch.no_grad():
        audio = model(codes, text, ge)
    print(f"  output shape={list(audio.shape)}  peak={float(audio.abs().max()):.4f}")

    # ── Export ONNX ──
    onnx_path = OUT_DIR / "parksy_v2_vits_decode.onnx"
    print(f"\n[Export] → {onnx_path.name}")

    torch.onnx.export(
        model,
        (codes, text, ge),
        str(onnx_path),
        input_names=["codes", "text", "ge"],
        output_names=["audio"],
        dynamic_axes={
            "codes": {2: "code_len"},
            "text": {1: "text_len"},
            # ge temporal dim is always 1 (global style vector)
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
        "codes": codes.numpy(),
        "text": text.numpy(),
        "ge": ge.numpy(),
    }
    ort_audio = sess.run(None, ort_inputs)[0]
    print(f"  output shape={list(ort_audio.shape)}  peak={float(np.abs(ort_audio).max()):.4f}")

    diff = np.abs(audio.numpy() - ort_audio).mean()
    print(f"  torch-vs-onnx MAE: {diff:.6f} {'✅' if diff < 0.01 else '⚠️'}")

    # ── Metadata ──
    meta = {
        "project": "parksy_v2",
        "voice": "박씨 목소리",
        "type": "GPT-SoVITS v2Pro → VITS Decode Core ONNX",
        "sample_rate": sr,
        "inputs": {
            "codes": "semantic tokens [1, code_len] int64",
            "text": "phoneme IDs [1, text_len] int64",
            "ge": "global embedding [1, 512, ge_len] float32 (ref_enc+sv_emb, pre-computed)",
        },
        "output": "audio waveform [1, 1, T_audio] float32",
        "note": "TTS.decode()의 ge 이후 내부 체인. ge 계산은 PyTorch에서 하고 나머지만 ONNX.",
    }
    (OUT_DIR / "parksy_v2_decode.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n{'='*50}")
    print(f"✅ 완료: {onnx_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
