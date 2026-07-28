# 초심자 설치 — 딱 3화면

> **리버스 엔지니어링 결론:**  
> 초심자가 막히는 지점은 “변수·OWNER/WORK·두 번 설치·선택지”다.  
> **앱 2개 → 붙여넣기 1번 → 브라우저로 확인** 이 최단 경로다.

명의 기본값: `helena751107`  
스크립트: `g/easy.sh` (쉬움) · `g/install.sh` (고급)

> 🔧 **다른 사람 계정으로 설치할 때:**  
> `OWNER_GITHUB=클라이언트명 bash <(curl -sL ...)`  
> 이렇게 env만 앞에 붙이면 `S21-START.txt`와 Pages 주소가 그 사람 명의로 바뀐다.  
> 토큰 없이 public clone만 하니까 키 발급 불필요.

---

## 화면 1 — 앱 두 개만

1. 폰 브라우저에서 **F-Droid** 설치  
   https://f-droid.org/
2. F-Droid 앱 열고 검색:
   - **Termux** 설치  
   - **Termux:API** 설치 (이름 비슷, **둘 다**)
3. **Termux** 아이콘 눌러 실행 (검은 화면 = 정상)

☐ 여기까지 됐으면 화면 2

---

## 화면 2 — 한 줄만 붙여넣기

Termux 검은 화면에 **아래 전체를 길게 눌러 붙여넣기** 후 Enter.

```bash
bash <(curl -sL https://raw.githubusercontent.com/helena751107/helena_phone/main/g/easy.sh)
```

- 처음이면 Ubuntu 깔리면서 **몇 분** 걸림. 가만히 둔다.  
- `✅ 쉬운 설치 끝` 이 보이면 성공.  
- 중간에 저장소 권한 팝업 → **허용**.

☐ 성공 문구 봤으면 화면 3

---

## 화면 3 — 됐는지 확인

### A) 터미널 (매일 쓰는 주문)

```bash
proot-distro login ubuntu
cd /root/work
cat S21-START.txt
```

`S21-START.txt` 가 읽히면 워크스페이스 준비 완료.

### B) 브라우저 (눈으로 확인)

폰 브라우저 주소창:

```
https://helena751107.github.io/helena_phone/
```

페이지가 열리면 **설치 성공**이다.  
(위성)  
https://helena751107.github.io/helana_log/  
https://helena751107.github.io/helana-faith/  
https://helena751107.github.io/helena-piano/  
https://helena751107.github.io/helena-psycare/

---

## 끝. 오늘은 여기까지.

키 발급, 토큰, Claude, Grok, 푸시는 **오늘 안 해도 됨.**  
사이트만 보이면 1단계 통과.

---

## (나중) 필요할 때만 — 고급

푸시·에이전트·텔레그램이 필요해지면:

```bash
proot-distro login ubuntu
cd /root/work
export GITHUB_USER="작업계정"
export GITHUB_TOKEN="ghp_xxx"
export DEEPSEEK_API_KEY="sk-xxx"
bash g/install.sh
```

변수 설명:

| 이름 | 뜻 | 초심자 |
|------|-----|--------|
| `OWNER_GITHUB` | 명의·공개 주인 | 기본 `helena751107` (안 바꿔도 됨) |
| `GITHUB_USER` | 푸시하는 손 | 나중에 |
| `GITHUB_TOKEN` | 비밀번호 대신 | 나중에 |
| `TEMPLATE_REPO` | 클론 원본 | 기본 그대로 |

---

## 🔧 설치자용 체크리스트 (사회복지사·가족)

> 남의 폰에 깔아줄 때 — **설치 전** 확인 4가지:

```
☐ Android 버전: 10 이상 (설정 → 휴대전화 정보 → 소프트웨어 정보)
☐ 저장공간: 5GB 이상 여유 (설정 → 디바이스 케어 → 저장공간)
☐ Wi-Fi: 연결됨 (Ubuntu 200MB+ 다운로드)
☐ F-Droid APK: https://f-droid.org/ 에서 미리 받아둘 것
```

설치 중 주의:
- **Ubuntu 다운로드 3~7분** — 이 구간은 가만히. "멈췄다"고 끄면 안 됨.
- **저장소 권한 팝업** — 반드시 **허용**. 안 뜨면 괜찮음.
- **끝난 후:** `pkg install termux-api -y` 한 번 더 (MCP 도구용 — devlog §16)

---

## 고장 표 (짧게)

| 보이면 | 할 일 |
|--------|--------|
| curl: not found | `pkg install curl` 후 easy 한 줄 다시 |
| proot-distro 없음 | `pkg install proot-distro` |
| 저장 공간 | 사진/앱 지워 5GB 확보 |
| 클론 실패 | Wi-Fi 확인 후 easy 한 줄 다시 |
| Pages 안 열림 | 주소 오타 · 나중에 다시 |
| termux-api ENOENT | `pkg install termux-api -y` (devlog §16)

---

## 왜 이렇게 짧아졌나 (리버스)

| 예전 | 문제 | 지금 |
|------|------|------|
| 변수 잔뜩 | 초심자 포기 | easy는 **질문 없음** |
| Termux / Ubuntu 두 번 설치 | 어디서 치는지 모름 | **한 줄이 알아서 넘김** |
| OWNER/WORK 설명 먼저 | 개념 과부하 | **사이트 연 다음에** 설명 |
| install.sh 만 | 선택지 많음 | **easy → 성공 경험 먼저** |

---

## 관련 링크

| 무엇 | URL |
|------|-----|
| 이 매뉴얼 | https://helena751107.github.io/helena_phone/install-guide.html |
| 랜딩 Install | https://helena751107.github.io/helena_phone/#install |
| easy 소스 | https://raw.githubusercontent.com/helena751107/helena_phone/main/g/easy.sh |
| 허브 | https://helena751107.github.io/helena_phone/ |

*초심자 3화면 · agent _Grok · 2026-07-27*
