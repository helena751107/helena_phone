# 첫 설치 케이스 스터디 — 형 폰에 직접 설치 (_Boss)

> 2026-07-28 · 내일 미팅 · 형(CS 박사) 폰에 helena_phone 수동 설치  
> 이 기록 → 사회복지사 교육자료 1챕터로 전환 예정

---

## 1. 배경

**Boss 구상:**
사회복지사·공무원한테 가르쳐서 그 사람들이 클라이언트 폰에 설치해주는 모델.

**첫 실전:** 내일 형(CS 박사) 미팅에서 직접 깔아주기.

**왜 형이 먼저냐:**
- CS 박사 → 기술적 질문이 사회복지사보다 깊을 것
- 형 폰에서 막히는 지점 = 사회복지사가 막힐 지점의 상위집합
- 형이 납득하면 시스템 검증 완료

---

## 2. 사전 준비

### 형이 오늘 할 것 (연락)

```
☐ 폰 저장공간 5GB 이상 확보 (사진·앱 정리)
☐ Wi-Fi 연결된 상태로 오기
☐ F-Droid APK 미리 설치: https://f-droid.org/
   → F-Droid에서 "Termux" + "Termux:API" 검색해서 미리 설치
   → ⚠ Play Store 말고 F-Droid. Play Store 버전은 업데이트 중단됨.
☐ 네이버 계정 있는지 확인
☐ GitHub 계정 있는지 확인 (없으면 현장 생성)
```

### Boss 챙겨갈 것

```
☐ git pull 최신 (easy.sh 검증)
☐ install-guide.html 링크 작동 확인
☐ DeepSeek API 키 준비
☐ phone-health.sh 실행 가능한지 포트 3456 확인
☐ 형 폰 모델 확인 (S21 아니어도 Android 10+면 OK)
```

---

## 3. 설치 시퀀스 (3+1 화면)

### 화면 1 — 앱 확인 (5분)
```
Termux 열림? → 검은 화면 정상 → OK
Termux:API 설치됐는지: pkg list | grep termux-api
```

### 화면 2 — 한 줄 (10~20분)
```bash
bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/g/easy.sh)
```
- Ubuntu 다운로드 3~7분. 이 구간 침묵 → "멈춘 거 아님" 미리 말해둘 것
- 저장소 권한 팝업 뜨면 허용

### 화면 3 — 확인 (5분)
```bash
proot-distro login ubuntu
cd /root/work
cat S21-START.txt
```
브라우저로 `helena751107.github.io/helena_phone/` 열리면 성공.

### 화면 4 — 고급 (형 전용, 15분)
```bash
export GITHUB_USER="형계정"
export GITHUB_TOKEN="ghp_..."
export DEEPSEEK_API_KEY="sk-..."
bash g/install.sh
```
CS 박사니까 여기까지. `claude` 명령어로 Claude Code 실행되는 것까지 보여주면 감동 포인트.

---

## 4. 예상 장애

| 장애 | 대처 |
|------|------|
| curl: not found | `pkg install curl` |
| proot-distro 설치 중 멈춤 | 인내. 200MB+. 몇 분 걸림 |
| 저장공간 부족 | 5GB 미만 시 실패 |
| termux-api ENOENT | `pkg install termux-api -y` (§16) |
| Pages 안 열림 | DNS 지연. 1분 후 새로고침 |
| Android 9 이하 | proot-distro 불가능 가능성 |

---

## 5. 기록 템플릿 (현장에서 채울 것)

```
☐ 형 폰 기종 / Android 버전:
☐ easy.sh 시작 시각:
☐ easy.sh 완료 시각:
☐ 총 소요 시간:
☐ 막힌 지점 (뭐 때문에 / 어떻게 해결):
☐ 형이 한 질문:
☐ 성공 후 형 반응:
☐ 개선할 점:
```

---

## 6. 이 케이스의 의미

| 관점 | 의미 |
|------|------|
| **기술 검증** | easy.sh가 남의 폰에서도 도는가 |
| **UX 검증** | 3화면으로 실제 비전문가가 따라 할 수 있는가 |
| **교육자료** | 이 기록 = 사회복지사 트레이닝 1챕터 |
| **비즈니스** | 첫 설치가 10분 안에 되면 용역 모델 증명 |

---

## 7. 용역비 참고 (사회복지사 설치 모델)

| 타입 | 가격 | 대상 |
|------|------|------|
| A: 설치만 | 15~20만원 | 개발자 |
| **B: 워크스테이션 구축** | **40~60만원** | 비개발자 창작자 |
| C: 돌봄 패키지 | 80~120만원 | 노인/장애인 가족 |

**핵심:** 니가 파는 건 "설치"가 아니라 **AI 워크스테이션 구축 컨설팅**이다.  
easy.sh가 10분이니까 15만원 받으면 안 된다. 설계·판단·구조가 상품이다.

---

*첫 설치 케이스 스터디 · _Boss · 2026-07-28*
