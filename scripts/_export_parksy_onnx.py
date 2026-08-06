#!/usr/bin/env python3
"""ParkSyTTS ONNX Export — 박씨 목소리(GPT-SoVITS v2Pro) → ONNX 변환

용도: S21 폰에서 onnxruntime CPU NEON 가속으로 추론 속도 개선
      (향후 NPU/NNAPI delegate로 추가 가속)

출력: voice_models/parksy_v2/
  ├── parksy_v2_t2s_encoder.onnx    (text+ref → latent)
  ├── parksy_v2_t2s_fsdec.onnx      (first-stage decoder)
  ├── parksy_v2_t2s_sdec.onnx       (stage decoder — autoregressive loop body)
  └── parksy_v2_vits.onnx           (semantic tokens → audio waveform)

사용법:
  cd /root/GPT-SoVITS
  python3 /root/work/scripts/_export_parksy_onnx.py
"""
from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path

import torch

# ── GPT-SoVITS path setup ──
GPT_SOVITS_DIR = Path(os.environ.get("GPT_SOVITS_DIR", "/root/GPT-SoVITS"))
GS = GPT_SOVITS_DIR / "GPT_SoVITS"
for p in [str(GPT_SOVITS_DIR), str(GS), str(GS / "eres2net")]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.chdir(str(GPT_SOVITS_DIR))

# ── ParksyTTS model paths ──
PARKSY_DIR = Path("/root/work/helena-programming/parksy-tts-v1/models")
GPT_CKPT = PARKSY_DIR / "gpt/parksy_v2-e15.ckpt"
SOVITS_CKPT = PARKSY_DIR / "sovits/parksy_v2_e8_s256.pth"
OUT_DIR = Path("/root/work/voice_models/parksy_v2")


def _load_ckpt(p: Path):
    """GPT-SoVITS .ckpt/.pth 로더 — 헤더 trim + weights_only=False (PyTorch 2.6+)"""
    with open(p, "rb") as f:
        meta = f.read(2)
        if meta != b"PK":
            data = b"PK" + f.read()
            return torch.load(BytesIO(data), map_location="cpu", weights_only=False)
    return torch.load(p, map_location="cpu", weights_only=False)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== ParkSyTTS ONNX Export ===\n  → {OUT_DIR}")

    # ── Import GPT-SoVITS internals ──
    from AR.models.t2s_lightning_module_onnx import Text2SemanticLightningModule
    from module.models_onnx import SynthesizerTrn, symbols_v2
    from text import cleaned_text_to_sequence

    print("  imports OK")

    # ── Load SoVITS (VITS decoder) ──
    print(f"\n[1/4] Loading SoVITS: {SOVITS_CKPT.name}")
    dict_s2 = _load_ckpt(SOVITS_CKPT)
    hps_dict = dict_s2["config"]
    version = "v2"
    print(f"  version={version}  embedding_dim={dict_s2['weight']['enc_p.text_embedding.weight'].shape[0]}")

    # DictToAttrRecursive
    class DictToAttrRecursive(dict):
        def __init__(self, d):
            super().__init__(d)
            for k, v in d.items():
                if isinstance(v, dict):
                    v = DictToAttrRecursive(v)
                self[k] = v
                setattr(self, k, v)

    hps = DictToAttrRecursive(hps_dict)
    hps.model.semantic_frame_rate = "25hz"

    # Build SynthesizerTrn (VITS decoder)
    vq_model = SynthesizerTrn(
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        n_speakers=hps.data.n_speakers,
        **hps.model,
    )
    vq_model.eval()
    vq_model.load_state_dict(dict_s2["weight"], strict=False)
    print(f"  SoVITS params: {sum(p.numel() for p in vq_model.parameters()):,}")

    # VITS wrapper (spectrogram + decoder)
    class VitsModel(torch.nn.Module):
        def __init__(self, vq, hps_cfg):
            super().__init__()
            self.vq_model = vq
            self.hps = hps_cfg

        def forward(self, text_seq, pred_semantic, ref_audio):
            # Spectrogram from reference audio
            n_fft = self.hps.data.filter_length
            hop = self.hps.data.hop_length
            win = self.hps.data.win_length
            hann = torch.hann_window(win).to(dtype=ref_audio.dtype, device=ref_audio.device)
            y = torch.nn.functional.pad(
                ref_audio.unsqueeze(1),
                (int((n_fft - hop) / 2), int((n_fft - hop) / 2)),
                mode="reflect",
            ).squeeze(1)
            spec = torch.stft(y, n_fft, hop_length=hop, win_length=win,
                              window=hann, center=False, pad_mode="reflect",
                              normalized=False, onesided=True, return_complex=False)
            refer = torch.sqrt(spec.pow(2).sum(-1) + 1e-6)
            return self.vq_model(pred_semantic, text_seq, refer)[0, 0]

    vits = VitsModel(vq_model, hps)

    # ── Load GPT (t2s) ──
    print(f"\n[2/4] Loading GPT: {GPT_CKPT.name}")
    dict_s1 = _load_ckpt(GPT_CKPT)
    t2s_config = dict_s1["config"]
    t2s_model = Text2SemanticLightningModule(t2s_config, "parksy_v2", is_train=False)
    t2s_model.load_state_dict(dict_s1["weight"])
    t2s_model.eval()
    t2s_model.model.top_k = torch.LongTensor([t2s_config.get("inference", {}).get("top_k", 15)])
    t2s_model.model.early_stop_num = torch.LongTensor([50 * t2s_config.get("data", {}).get("max_sec", 54)])
    t2s_model = t2s_model.model
    t2s_model.init_onnx()
    print(f"  GPT params: {sum(p.numel() for p in t2s_model.parameters()):,}")

    # T2S Encoder
    class T2SEncoder(torch.nn.Module):
        def __init__(self, t2s_enc, vq):
            super().__init__()
            self.encoder = t2s_enc.onnx_encoder
            self.vq = vq

        def forward(self, ref_seq, text_seq, ref_bert, text_bert, ssl_content):
            codes = self.vq.extract_latent(ssl_content)
            prompt_semantic = codes[0, 0]
            bert = torch.cat([ref_bert.transpose(0, 1), text_bert.transpose(0, 1)], 1)
            all_phoneme_ids = torch.cat([ref_seq, text_seq], 1)
            bert = bert.unsqueeze(0)
            prompt = prompt_semantic.unsqueeze(0)
            return self.encoder(all_phoneme_ids, bert), prompt

    t2s_encoder = T2SEncoder(t2s_model, vq_model)

    # ── Dummy data (shapes only — actual values don't matter for export) ──
    print(f"\n[3/4] Creating dummy data...")
    # Korean phonemes via v2 symbol set
    dummy_seq = [cleaned_text_to_sequence(
        ["n", "a", "n", "n", "e", "u", "n",
         "h", "e", "r", "r", "e", "n", "a"], version=version)]  # dummy ref
    ref_seq = torch.LongTensor(dummy_seq)
    text_seq = torch.LongTensor(dummy_seq)
    ref_seq_len = ref_seq.shape[1]
    text_seq_len = text_seq.shape[1]

    # BERT: Korean uses zero vectors (no Chinese BERT) — but shapes must match
    ref_bert = torch.zeros(ref_seq_len, 1024).float()
    text_bert = torch.zeros(text_seq_len, 1024).float()

    # Reference audio: dummy 5s @ 48kHz
    ref_audio = torch.randn(1, 48000 * 5).float()

    # SSL content: dummy [1, 768, N] (from hubert feature extractor)
    ssl_content = torch.randn(1, 768, 200).float()

    print(f"  ref_seq={ref_seq.shape}  text_seq={text_seq.shape}")
    print(f"  ref_bert={ref_bert.shape}  text_bert={text_bert.shape}")
    print(f"  ssl_content={ssl_content.shape}  ref_audio={ref_audio.shape}")

    # ── Export ONNX ──
    print(f"\n[4/4] Exporting ONNX...")

    # 4a. T2S Encoder
    onnx_enc = OUT_DIR / "parksy_v2_t2s_encoder.onnx"
    print(f"  → {onnx_enc.name}")
    torch.onnx.export(
        t2s_encoder,
        (ref_seq, text_seq, ref_bert, text_bert, ssl_content),
        str(onnx_enc),
        input_names=["ref_seq", "text_seq", "ref_bert", "text_bert", "ssl_content"],
        output_names=["x", "prompts"],
        dynamic_axes={
            "ref_seq": {1: "ref_length"},
            "text_seq": {1: "text_length"},
            "ref_bert": {0: "ref_length"},
            "text_bert": {0: "text_length"},
            "ssl_content": {2: "ssl_length"},
        },
        opset_version=16,
    )

    # 4b. First-stage decoder
    x, prompts = t2s_encoder(ref_seq, text_seq, ref_bert, text_bert, ssl_content)
    onnx_fsdec = OUT_DIR / "parksy_v2_t2s_fsdec.onnx"
    print(f"  → {onnx_fsdec.name}")
    torch.onnx.export(
        t2s_model.first_stage_decoder,
        (x, prompts),
        str(onnx_fsdec),
        input_names=["x", "prompts"],
        output_names=["y", "k", "v", "y_emb", "x_example"],
        dynamic_axes={
            "x": {1: "x_length"},
            "prompts": {1: "prompts_length"},
        },
        opset_version=16,
    )

    # 4c. Stage decoder (the heavy one — runs 1500 iterations)
    y, k, v, y_emb, x_example = t2s_model.first_stage_decoder(x, prompts)
    onnx_sdec = OUT_DIR / "parksy_v2_t2s_sdec.onnx"
    print(f"  → {onnx_sdec.name}")
    torch.onnx.export(
        t2s_model.stage_decoder,
        (y, k, v, y_emb, x_example),
        str(onnx_sdec),
        input_names=["iy", "ik", "iv", "iy_emb", "ix_example"],
        output_names=["y", "k", "v", "y_emb", "logits", "samples"],
        dynamic_axes={
            "iy": {1: "iy_length"},
            "ik": {1: "ik_length"},
            "iv": {1: "iv_length"},
            "iy_emb": {1: "iy_emb_length"},
            "ix_example": {1: "ix_example_length"},
        },
        opset_version=16,
    )

    # 4d. VITS decoder (semantic tokens → audio)
    pred_semantic = y[:, -30:].unsqueeze(0)  # dummy from GPT output
    # Resample ref_audio to model SR
    sr = hps.data.sampling_rate
    ref_audio_sr = torch.nn.functional.interpolate(
        ref_audio.unsqueeze(0), size=int(5 * sr), mode="linear", align_corners=False
    ).squeeze(0)
    onnx_vits = OUT_DIR / "parksy_v2_vits.onnx"
    print(f"  → {onnx_vits.name}")
    torch.onnx.export(
        vits,
        (text_seq, pred_semantic, ref_audio_sr),
        str(onnx_vits),
        input_names=["text_seq", "pred_semantic", "ref_audio"],
        output_names=["audio"],
        dynamic_axes={
            "text_seq": {1: "text_length"},
            "pred_semantic": {2: "pred_length"},
            "ref_audio": {1: "audio_length"},
        },
        opset_version=17,
    )

    # ── Metadata ──
    import json
    meta = {
        "project": "parksy_v2",
        "type": "GPT-SoVITS",
        "version": "v2Pro",
        "sample_rate": hps.data.sampling_rate,
        "gpt_ckpt": str(GPT_CKPT),
        "sovits_ckpt": str(SOVITS_CKPT),
        "onnx_files": [p.name for p in sorted(OUT_DIR.glob("*.onnx"))],
        "note": "박씨 목소리 — onnxruntime CPU NEON 가속용. NPU delegate 대기 중.",
    }
    (OUT_DIR / "parksy_v2.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  ✅ metadata: parksy_v2.json")

    # ── Summary ──
    total_mb = sum(p.stat().st_size for p in OUT_DIR.glob("*.onnx")) / 1024 / 1024
    print(f"\n{'='*50}")
    print(f"✅ ONNX export 완료: {OUT_DIR}")
    print(f"   총 {len(list(OUT_DIR.glob('*.onnx')))}개 파일, {total_mb:.1f}MB")
    print(f"   parksy_v2_vits.onnx → onnxruntime CPU 추론 준비 완료")
    print(f"   parksy_v2_t2s_sdec.onnx → GPT autoregressive loop (NPU 대기)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
