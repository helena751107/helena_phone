# 🔥 PC 삽질 포스트모템 — 왜 폰 하나로 다 하는가

> 2026-08-05. Boss + Claude Code 4시간 논쟁의 기록.
> 결론: proot Ubuntu 하나면 된다. 이 과정 자체가 증명이다.

---

## 우리가 한 삽질 (순서대로)

### 1. "PC로 확장하자"
WSL2 + DeepSeek Aider + Tailscale + SSH. 폰의 작업반장을 PC로 확장.
**문제: PC 사양 확인도 안 하고 설계부터 함.**

### 2. "Celeron 3855U + 4GB DDR3"
누나 PC 실사양 확인. 2코어 1.6GHz, 4GB RAM.
**WSL2 최소 2GB 필요. Windows 10 혼자 2GB. 같이 못 돌림. 불가.**

### 3. "GitHub Actions가 공짜 서버다"
2000분/월 + 7GB RAM + Ubuntu 24.04. Public repo = 무제한.
APK·오디오·CAD 전부 Actions로 돌리기로 함.
**맞는 판단. 아직 유효.**

### 4. "Oracle Cloud Always Free"
ARM 4코어 24GB RAM 평생 공짜.
**문제: 가입 당첨이 거의 불가능. 운빨.**

### 5. "Hetzner ₩5,500/월"
2vCPU 4GB. 제일 싼 유료 VPS.
**문제: 4GB로 Gradle APK 빌드 빠듯. Actions 7GB가 더 나음.**

### 6. "Vercel + GitHub Pages + Actions"
공짜 풀스택 조합. 정적 + 서버리스 + CI/CD.
**맞는 판단. 지금도 이걸로 감.**

### 7. "중국 CPU 클라우드"
DeepSeek처럼 공짜 CPU 없냐.
**결론: 없다. DeepSeek는 API가 훈련 데이터 수집용이라 가능한 거. CPU는 실제 전기세 들어감.**

### 8. "GitHub Team ₩4,000"
Private repo Actions 3000분.
**결론: 이미 public이라 무제한. 낼 필요 없음.**

### 9. "ADB 때문에 PC 필요"
Actions는 휘발성. ADB는 계속 폰에 붙어있어야 함.
로컬 머신 필수 → Celeron PC 다시 꺼냄.
**맞는 지적. Actions의 한계.**

### 10. "WSL 포기, Windows만"
Celeron에 Windows Native 앱 4개(Tailscale, SSH, ADB, Git).
연결 허브로만 쓰기로.
**의미 있는 타협. RAM 충분.**

### 11. 🔥 "프루트에 다 있잖아"
**확인 결과:**
- FFmpeg → arm64 네이티브, 이미 깔림
- **Ardour** → Reaper 대체 DAW, arm64 있음
- Audacity → arm64 있음
- FluidSynth → MIDI 신디
- JACK → 저지연 오디오
- ADB → Termux pkg

**PC 필요 없음. 처음으로 돌아옴.**

---

## 최종 구도

```
📱 S21 Phone (Exynos 2100 / 8GB / proot Ubuntu)
   │
   ├── Claude Code (cc)     → AI 기획·감사
   ├── Aider + DeepSeek     → 작업반장
   ├── Grok CLI             → GPU·이미지·영상
   ├── Ardour               → DAW
   ├── FFmpeg + Audacity    → 오디오
   ├── ADB                  → APK 디버깅
   ├── Git                  → 모든 레포
   └── MCP 18 tools         → 센서·시스템

☁️  GitHub Actions (공짜)
   ├── APK 빌드 (7GB RAM)
   ├── 오디오 렌더링
   └── CAD·범용 컴퓨트

🖥️  Celeron PC (필요 없음)
   → 버리거나 Thin Client로만
```

---

## 왜 이게 중요한가

| 의문 | 답변 |
|------|------|
| PC 없이 개발 가능? | **가능.** proot Ubuntu = 풀 리눅스 |
| DAW 가능? | **Ardour arm64.** Reaper 대체 |
| APK 빌드? | **Actions 7GB**가 로컬보다 나음 |
| GPU 작업? | **Grok + RunPod** |
| DB·도커 없이? | **JSON 파일 + Actions** |
| 공인 IP 없이? | **Tailscale + Pages** |

---

## 이 글을 쓰는 이유

많은 사람이 "개발은 PC로 해야 한다"고 생각한다.
우리는 **4시간 동안 PC→클라우드→PC→폰으로 돌아오는** 전 과정을 겪었다.
그리고 결론은 **폰 하나로 충분하다**는 것.

이 삽질이 누군가에게 "PC 없이도 된다"는 증명이 되길.

---

_2026-08-05. S21 Phone + Claude Code + DeepSeek._
_헬레나 프로젝트 — 대필작가-간병인의 AI 워크스테이션._
