# Voice Models — AI 성우 코어

여기에 `.onnx` + `.json` 성우 모델을 넣으면 `voice_engine.py` 가 자동으로 인식합니다.

## 사용법

```bash
# 1. 모델 파일을 이 디렉토리에 복사
cp /path/to/my_voice.onnx voice_models/
cp /path/to/my_voice.json voice_models/

# 2. 바로 사용
python3 director/voice_engine.py --text "안녕하세요" --engine local --out test.mp3

# 3. 전체 파이프에서 사용
TTS_ENGINE=local bash scripts/produce_intro.sh
```

## 모델 형식

- **Sherpa-ONNX** 호환 `.onnx` 모델
- Kokoro 또는 VITS 아키텍처
- 한국어 TTS 권장
- 토크나이저는 `.json` 파일 (모델명과 동일한 이름)

## 선물 모델

Boss(헬레나)가 구워서 올려둔 AI 코어는 GitHub Releases 또는 이 디렉토리에 있습니다.
받은 모델을 이 폴더에 넣으면 `TTS_ENGINE=local` 로 바로 사용 가능합니다.

## 직접 학습

폰에서 직접 학습시키려면 `_notebook/70-ai-voice-core-gift-local-train_Grok.md` 참조.
