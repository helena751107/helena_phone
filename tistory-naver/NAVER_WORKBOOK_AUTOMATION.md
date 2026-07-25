# 네이버 업무수첩 회의록 자동화 백서
> Claude Code 스터디 노트 | 2026-06-19
> 오늘 파싱하고 분석한 전체 내용 저장

---

## 1. 핵심 발견 — 오늘 세션에서 얻어걸린 것

오늘 parksy-logs 레포 소개 작업 중 우연히 발견했다.

터미널에서 Claude Code와 주고받는 대화 자체가, 아무 가공 없이 네이버 업무수첩 포스트가 된다는 것을.

동시에 옆 tmux 세션에서 DeepSeek Aider가 같은 작업을 다른 각도로 보조하면서, 두 세션을 서로 모니터링하며 협업하는 장면이 만들어졌다.

### 왜 이게 포맷이 되는가

- 일반 회의록: 사람이 쓴다
- AI 에이전트 작업 회의록: Claude + DeepSeek이 작업하는 동안 자동으로 쌓인다
- 발행: post.cjs(Playwright)가 네이버 SmartEditor를 조작해서 포스트 업로드
- 피드백 루프: 발행된 포스트를 다음 세션 Claude가 RSS로 파싱해서 컨텍스트 복원

```
작업 → 자동 기록 → 네이버 발행 → RSS 파싱 → 다음 세션 컨텍스트
```

---

## 2. post.cjs 코드 분석 (핵심 로직)

**파일 위치**: `~/dtslib-papyrus/tools/naver/post.cjs`

### 실행 방식
```bash
node post.cjs [계정id]          # posts/*.json 전체 처리
node post.cjs [계정id] [파일명] # 특정 파일만
```

### 포스트 JSON 스펙
```json
{
  "account": "eae_kr",
  "title": "제목",
  "content": "<p>HTML 본문</p>",
  "images": ["/mnt/c/Temp/screenshot.png"],
  "tags": ["태그1", "태그2"],
  "visibility": "public"
}
```

### 핵심 흐름
1. `accounts/credentials.json`에서 naver_id 조회
2. `accounts/cookies/{account}_state.json`에서 Playwright storageState 로드
3. `headless: false, channel: 'chrome'` — Windows Chrome 직접 실행
4. `https://blog.naver.com/{naverId}/postwrite` 열기
5. 제목 → 이미지 업로드 → SE3 본문 입력 → 태그 → 발행 버튼 클릭
6. 완료 파일 → `posts/done/` 이동

### 이미지 업로드 3단계 폴백
1. `input[type="file"]` 직접 setInputFiles
2. filechooser 이벤트 방식 (버튼 클릭)
3. contenteditable에 `<img>` 직접 삽입

### SE3 에디터 입력 방식
```javascript
document.execCommand('selectAll');
document.execCommand('insertHTML', false, htmlContent);
```
- iframe 내부 우선 시도 → 메인 페이지 fallback

---

## 3. DeepSeek v1.1 백서 파싱 분석

**파일 위치**: `~/dtslib-papyrus/tools/naver/whitepaper_v1.1.md`

### 내 v1 vs DeepSeek v1.1 비교

| 항목 | Claude v1 (msg_id 72) | DeepSeek v1.1 (msg_id 286) |
|------|----------------------|---------------------------|
| 서사 | 문학적, 발견 감동 중심 | 짧고 기술적 |
| 파이프라인 | 텍스트 설명 | 3레이어 ASCII 다이어그램 |
| 장애 분석 | 없음 | RustDesk 캡차 경로 명시 |
| 실행 항목 | 없음 | TODO 5개 구체적 명시 |
| RustDesk | 언급 없음 | 캡차 우회 게이트웨이로 설계 |

### DeepSeek이 발견한 것 (내가 못 본 것)

**RustDesk 캡차 우회 경로**:
```
login.cjs 실행 → ncaptcha 발생
  → RustDesk(위젯 5번)로 폰에서 PC Chrome 화면 확인
  → 캡차 직접 입력 (폰에서)
  → 쿠키 갱신 완료 → post.cjs 실행
```

**장애물 정확히 찾아냄**:
- Windows RustDesk: ✅ 실행 중
- 폰 RustDesk APK: ❌ 미설치 ← 유일한 차단 지점

**Termux 위젯 8개 상태 파악**:
```
5.rustdesk.sh — 현재 무효 (APK 미설치)
```

### DeepSeek 파이프라인 다이어그램 (원문 재현)
```
INPUT:  tmux claude-main + tmux phone_aider + tmux tg-audio/tg-image
          ↓ capture-pane + 로그
PROCESS: Claude → 작업 완료 단위 선별 → 제목/본문/스크린샷 변환
          → post.cjs 호출
          ↓ Playwright
DELIVERY: 네이버 업무수첩 발행 (dtslib / eae_kr / parksy_kr)
          ↔ RSS 피드 → 다음 세션 Claude 자동 감지
```

---

## 4. session_post.py 설계 원리

**파일 위치**: `~/dtslib-papyrus/tools/naver/session_post.py`

### 왜 PowerShell 스크린샷인가

DeepSeek은 RustDesk 경유 스크린샷을 시도했다. 근데 PowerShell이 더 직접적이다:

```powershell
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b=[System.Drawing.Bitmap]::new([Screen]::PrimaryScreen.Bounds.Width, ...)
$g=[System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen([Point]::Empty,[Point]::Empty,$b.Size)
$b.Save('C:\Temp\session_screenshot.png')
```

WSL에서 `powershell.exe -Command` 로 바로 실행 → `C:\Temp\` 저장 → WSL이 `/mnt/c/Temp/`로 접근.

### 이미지 경로 규칙

post.cjs는 Node.js(Windows Chrome Playwright)에서 실행되므로:
- WSL 경로 `/tmp/xxx.png` → 사용 불가
- Windows 경로 `C:\Temp\xxx.png` → 사용 가능

스크린샷: WSL `/tmp/session_screenshot.png` 에 복사 + `C:\Temp\session_screenshot.png` Windows 경로로 post.cjs에 전달.

### 텔레그램 이미지 수집 로직

```python
# getUpdates → photo 있는 메시지 → 최대 해상도 file_id 선택
# getFile → file_path → 다운로드 URL
# WSL /tmp/ 에 저장 → Windows C:\Temp\ 에 복사
```

### 사용법
```bash
# 기본
python3 ~/dtslib-papyrus/tools/naver/session_post.py eae_kr "오늘 작업 제목"

# 텔레그램 최근 이미지 3장 포함
python3 ~/dtslib-papyrus/tools/naver/session_post.py eae_kr "오늘 작업" --tg
```

---

## 5. 네이버 RSS 파싱 구조

### 확인된 RSS URL
```
https://rss.blog.naver.com/eae_kr.xml
https://rss.blog.naver.com/dtslib.xml
https://rss.blog.naver.com/parksy-kr.xml
```

### 파싱 코드
```python
import urllib.request
import xml.etree.ElementTree as ET

url = "https://rss.blog.naver.com/eae_kr.xml"
with urllib.request.urlopen(url) as resp:
    tree = ET.parse(resp)
channel = tree.getroot().find("channel")
items = channel.findall("item")
for item in items[:5]:
    print(item.find("title").text)
    print(item.find("pubDate").text)
    print(item.find("link").text)
```

### 한계
- 최신 5개만 제공
- 본문 전체 파싱 불가 (제목/날짜/링크만)
- 비공개 포스트 제외

### 상위 장부 트리거 방식
박씨가 포스트에 `[★]` 또는 `[우선]` 태그 달면 Claude가 우선순위 판단 가능

---

## 6. 계정별 쿠키 현황

```
accounts/cookies/
├── eae_kr.json         ← 쿠키 JSON
├── eae_kr_state.json   ← Playwright storageState (발행에 사용)
├── dtslib.json
└── dtslib_state.json
```

`parksy_kr` 쿠키 없음 → login.cjs 실행 필요

### 쿠키 갱신 명령
```bash
node ~/dtslib-papyrus/tools/naver/login.cjs eae_kr
node ~/dtslib-papyrus/tools/naver/login.cjs dtslib
node ~/dtslib-papyrus/tools/naver/login.cjs parksy_kr
```

캡차 발생 시: RustDesk로 PC Chrome 화면 보고 폰에서 직접 입력

---

## 7. 두 에이전트 협업 패턴 분석

### 오늘 관찰된 역할 분담

| | Claude (claude-main) | DeepSeek (phone_aider) |
|--|--|--|
| 모델 | Sonnet 4.6 | DeepSeek V4 Flash |
| 강점 | 서사/콘텐츠/파이프라인 설계 | 인프라 진단/상태 파악 |
| 오늘 한 것 | 백서 v1 / session_post.py / 레포 소개 | 백서 v1.1 / RustDesk 진단 / 위젯 파악 |
| 컨텍스트 | 세션 내내 유지 | 100% 찼다 → 새 세션 시작 |

### tmux 세션 구조
```
claude-main  ← 이 세션 (Claude Code)
phone_aider  ← DeepSeek Aider (ccr 브릿지)
phone_claude ← 폰 Claude
tab_aider    ← 탭 DeepSeek
tab_claude   ← 탭 Claude
tg-audio     ← 텔레그램 오디오 브릿지
tg-image     ← 텔레그램 이미지 브릿지
watchdog     ← 감시 프로세스
```

### 상호 모니터링 방법
```bash
# Claude가 DeepSeek 세션 보기
tmux capture-pane -t phone_aider -p | tail -30

# DeepSeek이 Claude 세션에 입력 보내기
tmux send-keys -t claude-main '0' Enter  # dismiss
```

---

## 8. 전체 파일 맵

```
~/dtslib-papyrus/tools/naver/
├── login.cjs                      — 로그인 + 쿠키 추출
├── post.cjs                       — 포스팅 자동화 (핵심)
├── session_post.py                — 터미널→네이버 원클릭 파이프라인 [2026-06-19 신규]
├── reconnect.sh                   — 쿠키 재연결
├── setup.sh                       — 초기 설정
├── whitepaper_v1.1.md             — DeepSeek 작성 v1.1 백서
├── NAVER_WORKBOOK_AUTOMATION.md   — 이 문서 (Claude 스터디 노트) [2026-06-19 신규]
├── accounts/
│   ├── credentials.json           — 3개 계정 (eae_kr, dtslib, parksy_kr)
│   ├── blogs.json
│   ├── cookies/                   — Playwright storageState
│   ├── eae_kr/
│   │   ├── blog_info.md
│   │   └── blog_whitepaper_v3.md
│   ├── dtslib/
│   │   └── blog_info.md
│   └── parksy_kr/
│       └── blog_info.md
└── posts/
    ├── sample.json
    └── post_001.json

~/dtslib-papyrus/docs/session-logs/
└── 20260619_naver_pipeline.md     — 세션 리마인더 (DeepSeek용)
```

---

## 9. 즉시 실행 TODO

```
[ ] 폰 RustDesk APK 설치
    → 위젯 5번 활성화
    → PC Chrome 화면 폰에서 직접 조작 가능

[ ] 쿠키 갱신 (캡차 우회 후)
    node ~/dtslib-papyrus/tools/naver/login.cjs eae_kr

[ ] 풀 파이프라인 첫 테스트
    python3 ~/dtslib-papyrus/tools/naver/session_post.py eae_kr "테스트"

[ ] 텔레그램 이미지 포함 테스트
    python3 ~/dtslib-papyrus/tools/naver/session_post.py eae_kr "오늘 작업" --tg

[ ] RSS 자동 감지 루틴 표준화
    세션 시작 시 rss.blog.naver.com/eae_kr.xml 파싱 → 최신 포스트 확인
```

---

## 10. 한 줄 결론

> 폰 RustDesk APK 설치 하나가 전체 파이프라인의 마지막 열쇠다.
> 그게 되면: 캡차 → 쿠키 → session_post.py → 네이버 발행 → RSS 피드백 루프 전부 자동.

---
작성: Claude Code | 2026-06-19 KST
파싱 대상: post.cjs / whitepaper_v1.1.md / session_post.py 설계 / RSS 구조 / 에이전트 협업 패턴
