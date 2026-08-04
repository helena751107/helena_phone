#!/bin/bash
# 📰 tistory_rss_watch.sh — 티스토리 RSS 감시 + 새 글 TG 보고
# 사용법: bash tistory_rss_watch.sh
#         bash tistory_rss_watch.sh --watch  (30분 간격 감시)

TG_TOKEN="8988031320:AAHYpxv3XuS6jaCh8switB9n7Z_ZP75V8nQ"
TG_CHAT="8579179811"
CACHE_DIR="/root/work/out/tistory_cache"
mkdir -p "$CACHE_DIR"

# Boss의 5개 티스토리 RSS 주소 (실제 URL로 교체 필요)
BLOGS=(
  "helena-work"       # 업무일지
  "helena-tech"       # 기술·AI
  "helena-video"      # 영상 제작
  "helena-content"    # 콘텐츠 자동화
  "helena-life"       # 생각·아이디어
)

fetch_rss() {
  local blog="$1"
  # 티스토리 RSS: https://[blogname].tistory.com/rss
  local rss_url="https://${blog}.tistory.com/rss"
  curl -s "$rss_url" 2>/dev/null | python3 -c "
import sys, xml.etree.ElementTree as ET
try:
    root = ET.fromstring(sys.stdin.read())
    ns = {'dc':'http://purl.org/dc/elements/1.1/'}
    for item in root.findall('.//item')[:5]:
        title = item.find('title').text if item.find('title') is not None else '(제목없음)'
        link = item.find('link').text if item.find('link') is not None else ''
        desc = item.find('description').text if item.find('description') is not None else ''
        desc = desc[:100].replace('\n',' ')
        pubdate = item.find('pubDate').text if item.find('pubDate') is not None else ''
        print(f'{title}|{link}|{desc}|{pubdate}')
except Exception as e:
    print(f'ERROR:{e}')
"
}

check_new() {
  local blog="$1" title="$2" link="$3"
  local hash=$(echo "$link" | md5sum | cut -c1-8)
  local cache_file="$CACHE_DIR/${blog}_${hash}"

  if [ -f "$cache_file" ]; then
    return 1  # 이미 본 글
  fi
  touch "$cache_file"
  return 0  # 새 글
}

report() {
  local blog="$1" title="$2" link="$3" desc="$4" date="$5"

  # TG 보고
  curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
    -d chat_id="${TG_CHAT}" \
    --data-urlencode "text=📰 새 기고: ${blog}

${title}
${desc}...

🔗 ${link}
📅 ${date}" > /dev/null

  # 로컬 로그
  echo "[$(date +%H:%M)] ${blog}: ${title}" >> "$CACHE_DIR/history.log"
}

# ── 메인 ──
scan_all() {
  local new_count=0
  for blog in "${BLOGS[@]}"; do
    while IFS='|' read -r title link desc pubdate; do
      [[ "$title" == "ERROR:"* ]] && continue
      [[ -z "$link" ]] && continue
      if check_new "$blog" "$title" "$link"; then
        report "$blog" "$title" "$link" "$desc" "$pubdate"
        ((new_count++))
      fi
    done < <(fetch_rss "$blog")
  done

  if [ "$new_count" -gt 0 ]; then
    echo "📰 ${new_count}개 새 기고 발견"
  fi
}

# 감시 모드
if [ "$1" == "--watch" ]; then
  echo "👀 티스토리 RSS 감시 시작 (30분 간격)"
  scan_all
  while true; do
    sleep 1800  # 30분
    scan_all
  done
else
  scan_all
fi
