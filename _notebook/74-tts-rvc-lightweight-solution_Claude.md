# 🎤 경량 TTS + RVC 성우 더빙 솔루션 (2026-08-07, _Claude)

## 문제

ParksyTTS (GPT-SoVITS) CPU 추론이 471초 for 3.5초 음성으로 실사용 불가.
SoVITS 모델 포기하고 경량 TTS + RVC 조합으로 전환 결정.

## 핵심 아키텍처

```
[대본 텍스트]
    │
    ▼
NeuTTS Nano (GGUF, ARM64 CPU, ~2x 실시간)
  → 자연스러운 한국어 TTS 음성 (몇 초)
    │
    ▼
RVC ONNX INT8 (~380MB, ARM64 CPU, ~72ms)
  → 누나 목소리로 변환
    │
    ▼
ffmpeg 후처리 (노멀라이즈, EQ)
    │
    ▼
최종 WAV → 영상 더빙
```

**총 추론 시간 예상:** TTS 수 초 + RVC 0.1초 = **10초 내외** (기존 ParksyTTS 471초 대비 ~50배 단축)

## RVC on ARM64 — 완전 가능

| 항목 | 원본 RVC PyTorch | INT8 ONNX (모바일 최적화) |
|------|------------------|--------------------------|
| 모델 크기 | 2.3 GB | **380 MB** (83%↓) |
| 추론 지연 | 350 ms | **72 ms** (79%↓) |
| 메모리 | 1.8 GB | **420 MB** (77%↓) |
| CPU 사용률 | 95% | **45%** |

### export 경로
1. PyTorch `.pth` 모델 → `export_onnx()` → `.onnx`
2. ONNX Runtime graph optimize + INT8 양자화
3. `onnxruntime-android` / `onnxruntime` (proot glibc) 로 ARM64 추론

### 기존 pre-built 자산
- **HuggingFace:** `TigreGotico/voiceclonnx-rvc` — ContentVec encoder 91MB + RMVPE pitch 94MB (INT8)
- **라이브러리:** `vconnx` — `pip install` 한 줄로 RVC 추론
- **npm:** `rvc-onnx-web` — TypeScript로 pth→onnx 변환 (Python 불필요)

### ONNX Runtime 최적화
```bash
python -m onnxruntime.tools.optimize_onnx_model \
  --input model.onnx --output optimized.onnx
```
→ 20~30% 연산 감소

### 동적 양자화
- `torch.nn.Linear`, `Conv1d` → qint8
- LSTM 레이어는 별도 qconfig
- 결과: **72% 크기 감소, 3.2× 추론 가속, <2% 품질 손실**

---

## TTS 엔진 비교

| 모델 | 크기 | 한국어 | Voice Cloning | 포맷 | CPU 추론 | 비고 |
|------|------|--------|---------------|------|----------|------|
| **NeuTTS Nano** | ~120M params | ✅ | ✅ Instant | GGUF | ✅ ~2x RTF | 🔥 1순위 |
| **Chatterbox-LiteRT** | ~500MB INT8 | ✅ | ✅ Zero-shot | TFLite | ✅ ~0.95 RTF | 실험적 |
| VoxCPM2-LiteRT | 8.7GB FP16 | ✅ | ✅ Zero-shot | TFLite | ❌ 무거움 | S21 부적합 |
| Sherpa-ONNX Kokoro | ~300MB | ⚠️ 확인 필요 | ❌ 미지원 | ONNX | ✅ | Voice cloning 안 됨 |
| GPT-SoVITS | ~2GB+ | ✅ | ✅ Few-shot | PyTorch | ❌ 471초 | 포기 확정 |

### 1순위: NeuTTS Nano
- GitHub 6,178 stars, 2026년 7월 기준 트렌딩
- GGUF 포맷 → ARM64 CPU 네이티브, Snapdragon/Exynos 최적화
- 9개 언어(한국어 포함), instant voice cloning
- 120M active parameters → S21에서 충분히 구동

### 폴백: Sherpa-ONNX Kokoro
- 이미 S21에 설치·검증 완료
- 한국어 모델 실제 지원 여부 확인 필요
- Voice cloning 안 되므로 RVC 변환 필수

---

## 누나 목소리 RVC 모델 만들기

### 학습
- 필요 데이터: 누나 목소리 10~30분 clean 음성
- GitHub Actions에서 RVC 학습 1회 실행 (로컬 CPU 부담 없음)
- 사전 녹음 스크립트: `scripts/record_voice_samples.sh` 이미 있음

### 커뮤니티 레퍼런스
voice-models.com에 한국어 여성 RVC 모델 다수:
- **NELL 시리즈** — 310분 데이터셋, V11까지 실험 완료
- **Harang (하랑)** — BOOTH 판매, 부드러운 여성 목소리
- **Jane** — 실시간 보이스 체인저 특화

### 학습 후 추론
1. `.pth` → ONNX export
2. INT8 양자화 → ~380MB
3. S21 proot에 배치
4. `vconnx`로 추론

---

## Grok TTS 라이선스

Grok TTS는 현재 SuperGrok 구독에 포함 안 됨 (403). 그러나 추후 사용 가능해질 경우:
- xAI ToS 상 생성된 음성에 대한 저작권 제한 없음 (오픈소스 출력물로 간주)
- 상업적 사용 가능
- 다만 현재는 미사용 — TTS_ENGINE=local 유지

---

## 실행 계획

| 순위 | 작업 | 예상 시간 | 난이도 |
|------|------|----------|--------|
| 🔴 1 | `pip install vconnx onnxruntime` → RVC ONNX 추론 테스트 | 20분 | 쉬움 |
| 🔴 2 | Sherpa-ONNX Kokoro 한국어 모델 존재 확인 | 10분 | 쉬움 |
| 🟡 3 | NeuTTS Nano GGUF 다운로드 → S21에서 TTS 테스트 | 30분 | 중간 |
| 🟡 4 | TTS 출력 → RVC 변환 파이프 검증 | 30분 | 중간 |
| 🟢 5 | 누나 목소리 샘플 수집 (10~30분) | 수동 | - |
| 🟢 6 | GitHub Actions RVC 학습 워크플로우 | 1시간 | 중간 |
| 🟢 7 | voice_engine.py에 `tts_rvc` 프로바이더 추가 | 30분 | 쉬움 |

---

## 예상 효과

| 지표 | 현재 (ParksyTTS) | 목표 (NeuTTS+RVC) |
|------|-----------------|-------------------|
| 3.5초 음성 생성 | 471초 | ~10초 |
| 실시간 대비 | 135배 느림 | ~3배 |
| 메모리 | 2GB+ | ~500MB |
| 모델 파일 크기 | 314MB 체크포인트 | ~500MB ONNX 총합 |
| 품질 | ParksyTTS v1 양호 | TTS 자연스러움 + RVC 개성 |
| 확장성 | CPU-only 한계 | ONNX 생태계 (모바일·서버·브라우저) |

---

## 레퍼런스

- RVC ONNX HuggingFace: https://huggingface.co/TigreGotico/voiceclonnx-rvc
- vconnx 라이브러리: `pip install vconnx`
- rvc-onnx-web (npm): https://www.npmjs.com/package/rvc-onnx-web
- NeuTTS Nano: https://www.neuphonic.com/models/neutts-nano
- Chatterbox-LiteRT: https://huggingface.co/soniqo/Chatterbox-LiteRT
- Sherpa-ONNX: https://github.com/k2-fsa/sherpa-onnx
- 한국어 RVC 모델: https://voice-models.com (NELL, Jane, Harang 등)

---

> **결론:** SoVITS는 포기. TTS(NeuTTS Nano 또는 Sherpa-ONNX Kokoro) + RVC ONNX = S21에서 실사용 가능한 성우 더빙 파이프.
> Grok TTS는 저작권 문제 없으나 현재 403. local 프로바이더에 이 파이프를 추가하는 게 정답.
