# 🎙 ParkSyTTS v1 — 박씨 목소리 선물

> Galaxy S21 proot-Ubuntu에서 동작하는 AI 성우 패키지
> 오빠 목소리로 뭐든 읽어주는 TTS 시스템

---

## 빠른 시작

### 1단계: 설치 (한 번만)
```bash
bash install.sh
```

### 2단계: 모델 받기
오빠한테 모델 파일 보내달라고 하면 됨.  
오빠가 WSL에서 실행:
```bash
bash send_models.sh 헬레나폰IP
```

### 3단계: 사용
```bash
source activate.sh
python3 say.py "안녕 헬레나!"
python3 say.py "오늘 날씨가 좋아요" --out 날씨.wav
python3 say.py --file 대본.txt --out 나레이션.wav --speed 1.2
```

---

## 파일 구조

```
parksy-tts-v1/
├── say.py          ← 여기만 쓰면 됨
├── install.sh      ← 처음 한 번만
├── activate.sh     ← 매번 실행 전
├── send_models.sh  ← 오빠가 모델 보낼 때
├── requirements.txt
└── core/
    ├── engine.py   ← 추론 엔진
    └── normalize.py← 한국어 텍스트 처리
```

---

## 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--out` | 저장 파일 이름 | `/tmp/parksy_say.wav` |
| `--speed` | 속도 (1.2=빠름) | `1.0` |
| `--play` | 합성 후 자동 재생 | 꺼짐 |
| `--file` | 텍스트 파일 읽기 | - |

---

## 동작 원리

```
텍스트
  → AI→에이아이 변환 (자동)
  → GPT-SoVITS v2Pro 추론 (박씨 학습 모델)
  → peak -1.1dBFS 정규화
  → WAV 저장
```

---

## 버전 히스토리

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-08-06 | 최초 선물 배포 |

*더 좋은 버전 나오면 오빠가 업데이트해줄게* 💌
