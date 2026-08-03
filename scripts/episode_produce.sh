#!/bin/bash
# 🎬 episode_produce.sh — 시리즈 에피소드 제작 표준 파이프
# 사용법: bash episode_produce.sh <에피소드번호> <페이지URL> <제목>
# 예: bash episode_produce.sh e01 https://helena751107.github.io/helena_phone/notebook/series/e01-proot-linux.html "스마트폰에 리눅스를?"

# ── 표준 설정 (변경 금지) ─────────────────────
EP="${1:?에피소드 번호 필요 (e01~e24)}"
URL="${2:?페이지 URL 필요}"
TITLE="${3:?제목 필요}"
OUTDIR="/root/work/out/${EP}"
WORKDIR="/root/work/helena-programming/director/out"
TG_TOKEN="8988031320:AAHYpxv3XuS6jaCh8switB9n7Z_ZP75V8nQ"
TG_CHAT="8579179811"
VOICE="ko-KR-SunHiNeural"
RESOLUTION="720:1280"
PRESET="ultrafast"
CRF="28"

mkdir -p "$OUTDIR"

echo "=== 🎬 ${EP}: ${TITLE} ==="
echo "URL: $URL"
echo ""

# ── Step 1: 페이지 스크린샷 (4구간) ──────────
echo "[1/4] 스크린샷 촬영..."
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={'width': 412, 'height': 915})
    page.goto('$URL', wait_until='networkidle')

    # Hero
    page.screenshot(path='${OUTDIR}/s01_hero.png', full_page=False)

    # Section 1
    page.evaluate('window.scrollBy(0, window.innerHeight)')
    page.wait_for_timeout(500)
    page.screenshot(path='${OUTDIR}/s02_content.png', full_page=False)

    # Section 2
    page.evaluate('window.scrollBy(0, window.innerHeight)')
    page.wait_for_timeout(500)
    page.screenshot(path='${OUTDIR}/s03_detail.png', full_page=False)

    # Section 3
    page.evaluate('window.scrollBy(0, window.innerHeight)')
    page.wait_for_timeout(500)
    page.screenshot(path='${OUTDIR}/s04_footer.png', full_page=False)

    b.close()
    print('스크린샷 4장 완료')
"

# ── Step 2: 페이지 콘텐츠 추출 → TTS 대본 ─────
echo "[2/4] 대본 추출 + TTS 생성..."
python3 -c "
from playwright.sync_api import sync_playwright
import subprocess, re

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto('$URL', wait_until='networkidle')

    # h1, h2, p 텍스트 추출
    texts = page.evaluate('''() => {
        const els = document.querySelectorAll('h1, h2, .flow-title, .hero p');
        return Array.from(els).map(e => e.textContent.trim()).filter(t => t.length > 3);
    }''')
    b.close()

# 4개 이하로 압축
texts = texts[:4]
while len(texts) < 4:
    texts.append('S21 Phone 시리즈.')

for i, t in enumerate(texts):
    t = re.sub(r'<[^>]+>', '', t)  # HTML 태그 제거
    t = t.replace('\"', '').replace('\\'', '')
    if len(t) > 200: t = t[:200]
    fname = f'${OUTDIR}/s0{i+1}.txt'
    with open(fname, 'w') as f:
        f.write(t)
    subprocess.run(['edge-tts', '-f', fname, '--voice', '${VOICE}', '--write-media', f'${OUTDIR}/s0{i+1}.mp3'], capture_output=True)
    print(f'  s0{i+1}: {t[:60]}...')

print('TTS 완료')
"

# ── Step 3: ffmpeg 클립 인코딩 + concat ───────
echo "[3/4] 영상 인코딩..."
for i in 1 2 3 4; do
    ffmpeg -y -loop 1 -i "${OUTDIR}/s0${i}_hero.png" -i "${OUTDIR}/s0${i}.mp3" \
        -c:v libx264 -preset ${PRESET} -crf ${CRF} -tune stillimage \
        -c:a aac -b:a 128k -shortest \
        -vf "scale=${RESOLUTION}:force_original_aspect_ratio=decrease,pad=${RESOLUTION}:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
        "${OUTDIR}/clip0${i}.mp4" 2>/dev/null && echo "  clip0${i} OK"
done

# concat
for i in 1 2 3 4; do
    echo "file 'clip0${i}.mp4'" >> "${OUTDIR}/concat.txt"
done
ffmpeg -y -f concat -safe 0 -i "${OUTDIR}/concat.txt" -c copy "${OUTDIR}/${EP}_final.mp4" 2>/dev/null
echo "  → ${EP}_final.mp4 ($(du -h ${OUTDIR}/${EP}_final.mp4 | cut -f1))"

# ── Step 4: TG 전송 ───────────────────────────
echo "[4/4] TG 전송..."
RESULT=$(curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendVideo" \
    -F chat_id="${TG_CHAT}" \
    -F video="@${OUTDIR}/${EP}_final.mp4" \
    -F caption="🎬 ${EP^^}: ${TITLE}

S21 Phone Series · Ch${EP:1:1}
4슬라이드 · TTS(SunHi) · 720p")

if echo "$RESULT" | grep -q '"ok":true'; then
    echo "✅ ${EP} TG 전송 완료"
else
    echo "❌ TG 전송 실패: $(echo $RESULT | head -c 100)"
fi

echo ""
echo "=== ${EP} 제작 완료 ==="
echo "파일: ${OUTDIR}/${EP}_final.mp4"
echo "페이지: $URL"
