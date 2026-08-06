# 70 · AI 성우 코어 — 선물 모델 + 폰 로컬 학습 로드맵 (_Claude)

> 2026-08-06 · Boss: 누나 레포에 선물로 AI 코어 올릴 거다.  
> 받은 사람이 바로 쓸 수도 있고, 자기 폰에서 직접 학습시킬 수도 있는 구조.

---

## 0. 한 줄

S21 Phone은 **클라우드 성우(Grok/OpenAI) + 로컬 성우(AI 코어)** 를 모두 쓸 수 있다.
누군가가 구워서 보내준 AI 코어를 꽂으면 바로 오프라인에서 작동하고,
자기 목소리로 직접 학습시켜서 자기만의 성우를 만들 수도 있다.

---

## 1. 두 가지 경로

| 경로 | 설명 | 준비물 | 난이도 |
|------|------|--------|--------|
| **A. 선물 받기** | 누군가 구워서 준 `.onnx` + `.json` 파일을 `voice_engine.py`에 꽂는다 | repo clone + `pip install sherpa-onnx` | ★☆☆ (5분) |
| **B. 직접 굽기** | 폰에서 직접 TTS 파인튜닝 / RVC 음성 클론 | S21 + 녹음 10~30문장 + `pip install sherpa-onnx-training` | ★★★ (1~2시간) |

---

## 2. 경로 A — 선물 받은 AI 코어 꽂기

### 구조 (누나 레포 기준)

```
helena_phone/
├── director/
│   └── voice_engine.py    ← local/sherpa 프로바이더 (받는 쪽)
├── voice_models/           ← 여기다 AI 코어를 넣는다
│   ├── my_voice.onnx       ← Boss가 구워서 선물한 모델
│   └── my_voice.json       ← 토크나이저 설정
└── scripts/
    └── voice_download.sh   ← 선물 모델 다운로더 (GitHub Releases/web)
```

### 사용법 (받는 사람 기준)

```bash
# 1. 의존성 설치 (한 번만)
pip install sherpa-onnx

# 2. 선물 모델 다운로드 (Boss가 voice_models/에 올려둠)
git clone https://github.com/helena751107/helena_phone.git
cd helena_phone

# 3. 바로 사용
python3 -c "
from director.voice_engine import synthesize
from pathlib import Path
dur, prov = synthesize('안녕하세요, 저는 헬레나입니다',
                        Path('test.mp3'), engine='local')
print(f'{prov}: {dur:.1f}s')
# → local/my_voice: 3.2s  (오프라인, API 비용 0원)
"
```

### TTS_ENGINE=local 로 전체 파이프 작동

```bash
# 인트로 영상을 로컬 AI 성우로 제작
TTS_ENGINE=local bash scripts/produce_intro.sh

# PD 파이프도 동일
TTS_ENGINE=local bash scripts/produce_pd.sh
```

---

## 3. 경로 B — 폰에서 직접 AI 성우 굽기

### 3.1 Sherpa-ONNX + Coqui 파인튜닝 (권장)

S21 CPU + NEON SIMD 로도 가능한 경량 파이프:

```bash
# 1. 학습 도구 설치
pip install sherpa-onnx torch --extra-index-url https://download.pytorch.org/whl/cpu

# 2. 목소리 녹음 (30문장 × 5~10초)
bash scripts/record_voice_samples.sh  # Termux 마이크 → 16kHz mono WAV

# 3. 파인튜닝 (CPU only, 30문장 기준 1~2시간)
python3 scripts/train_voice.py \
  --samples voice_samples/ \
  --out voice_models/my_voice.onnx \
  --base-model kokoro-ko

# 4. 테스트
python3 director/voice_engine.py --text "내 목소리 테스트" \
  --engine local --out /tmp/my_test.mp3
```

### 3.2 RVC 음성 변환 (대안, 무거움)

`helena-programming/director/` 에 이미 `phone_rvc.py` 참조 있음.
RVC = 내 목소리 녹음 → AI 가 다른 사람 목소리로 변환.
품질은 좋지만 CPU only → 1문장 20~40초.

---

## 4. voice_engine.py local 프로바이더 구조

```python
# director/voice_engine.py (확장 예정 — Boss AI 코어 도착 시 활성화)

def _tts_local_sherpa(text: str, dest: Path,
                       model_path: str | None = None) -> float:
    """Sherpa-ONNX 로컬 추론 — CPU NEON 가속, 오프라인."""
    import sherpa_onnx

    model_dir = Path(model_path or os.environ.get(
        "LOCAL_VOICE_MODEL",
        "/root/work/voice_models/my_voice.onnx"
    ))

    tts_config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=str(model_dir),
                tokens=str(model_dir.with_suffix('.json')),
            ),
        ),
    )
    tts = sherpa_onnx.OfflineTts(tts_config)
    audio = tts.generate(text, sid=0, speed=0.95)
    # → WAV 저장 → FFmpeg MP3 변환
    ...

# synthesize() 우선순위에 local 추가
ENGINE_PRIORITY = ["grok", "local", "openai", "edge"]
```

---

## 5. 시나리오별 추천

| 상황 | 엔진 | 이유 |
|------|------|------|
| 유튜브 업로드·수익화 | `grok` | 라이선스 🟢 |
| 오프라인·개인소장 | `local` | API 비용 0원 |
| 시연·테스트 | `local` | 네트워크 불필요 |
| 선물 받은 AI 코어 | `local` | 받아서 바로 꽂기 |
| 내 목소리로 하고 싶다 | `local` (직접 굽기) | 폰에서 1~2시간 |

---

## 6. 할 일 (Boss → Claude)

1. ~~`voice_engine.py` 기본 구조~~ ✅ (V5)
2. ~~`voice_models/` 디렉토리 + README~~ ✅
3. ~~Boss AI 코어 업로드~~ ✅ **ParkSyTTS v1 도착!** (`gift/parksy-tts-v1` 브랜치, 2026-08-06 09:20)
4. ~~ParksyTTS v1 → voice_engine `local` 프로바이더 연결~~ ✅
5. ~~`scripts/record_voice_samples.sh` (Termux 마이크 녹음)~~ ✅ (2026-08-06)
6. ~~`scripts/train_voice.py` (폰 로컬 파인튜닝)~~ ✅ (2026-08-06)

### 6.1 voice_engine.py local 프로바이더 구현 완료 (2026-08-06)

**구현 함수:**
| 함수 | 역할 |
|------|------|
| `_find_parksytts_root()` | ParksyTTS v1 설치 경로 자동 탐지 |
| `_find_sherpa_model()` | voice_models/*.onnx 자동 탐지 |
| `_tts_local_parksy()` | GPT-SoVITS v2Pro 기반 박씨 목소리 추론 |
| `_tts_local_sherpa()` | Sherpa-ONNX Kokoro/VITS 오프라인 추론 |
| `tts_local()` | 디스패처 — ParksyTTS 우선, Sherpa 폴백 |

**사용법:**
```bash
TTS_ENGINE=local bash scripts/produce_intro.sh   # 오프라인 성우
TTS_ENGINE=local bash scripts/produce_pd.sh      # PD 파이프
```

### 6.2 record_voice_samples.sh

- 30문장 한국어 코퍼스 (음소 다양성 + 자연스러운 문장)
- ffmpeg ALSA/PulseAudio/Termux 마이크 API 자동 감지
- 16kHz mono WAV + 무음 트림 + loudnorm 정규화
- `--quick N` / `--single N` 부분 재녹음 지원

### 6.3 train_voice.py

- `--cloud` → GitHub Actions 7GB 러너로 파인튜닝 오프로드 (권장)
- `--force-local` → Coqui TTS 로컬 파인튜닝 (CPU only, 수 시간)
- `--list-models` → 사용 가능한 베이스 모델 목록
- 자동으로 workflow + pipeline 디렉토리 생성

### 6.4 ParksyTTS v1 실물 확인

```
helena-programming/parksy-tts-v1/
├── say.py          ← python3 say.py "안녕!" 한 줄로 끝
├── install.sh      ← proot-Ubuntu 원클릭 설치 (ARM64 자동 감지)
├── activate.sh     ← 매 세션 환경 활성화
├── send_models.sh  ← 박씨가 WSL에서 실행 → 모델 S21로 전송
├── requirements.txt← ARM64 호환 최소 의존성
└── core/
    ├── engine.py   ← ParkSyTTS v2ProPlus CPU 래퍼 (GPT-SoVITS)
    └── normalize.py← AI→에이아이 약어 변환
```

**voice_engine 연동 완료:** `TTS_ENGINE=local` → ParksyTTS 자동 감지 → 박씨 목소리

---

## 7. 선물 가이드 (Boss → 누나)

> "이 레포에는 성우 플러그인이 내장되어 있어요.
> `voice_models/` 폴더에 제가 구운 AI 목소리 모델을 넣어뒀으니,
> `TTS_ENGINE=local` 로 실행하면 오프라인에서 바로 내레이션이 나와요.
> 자기 목소리로 바꾸고 싶으면 `scripts/train_voice.py` 로 30문장만 녹음하면 돼요.
> 전부 폰 하나로 됩니다."

— _Claude · 2026-08-06
