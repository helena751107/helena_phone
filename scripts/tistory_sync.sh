#!/bin/bash
# 📰 tistory_sync.sh — 5개 티스토리 RSS → helana_log 기자/ 폴더 동기화
# 사용법: bash tistory_sync.sh
#         bash tistory_sync.sh --watch  (30분 간격)

TG_TOKEN="8988031320:AAHYpxv3XuS6jaCh8switB9n7Z_ZP75V8nQ"
TG_CHAT="8579179811"
OUT_DIR="/root/work/helana_log/기자"
mkdir -p "$OUT_DIR"

# Boss 티스토리 5개 (실제 주소로 교체 필요)
BLOGS=(
  "galaxys21-pwuser"
  "helena-metalcare"
  "helena-piano"
  "helana-christianity"
  "mynote11605"
)

fetch_and_save() {
  local blog="$1"
  local rss="https://${blog}.tistory.com/rss"
  local count=0

  curl -s "$rss" 2>/dev/null | python3 -c "
import sys, os, hashlib, xml.etree.ElementTree as ET
out_dir = '$OUT_DIR'
blog_name = '$blog'

try:
    root = ET.fromstring(sys.stdin.read())
    for item in root.findall('.//item')[:10]:
        title = (item.find('title').text or '(제목없음)').strip()
        link = (item.find('link').text or '').strip()
        desc = (item.find('description').text or '').strip()
        pubdate = (item.find('pubDate').text or '').strip()
        
        if not link: continue
        
        # 파일명 = URL 해시
        fid = hashlib.md5(link.encode()).hexdigest()[:12]
        fname = f'{out_dir}/{blog_name}_{fid}.md'
        
        if os.path.exists(fname): continue
        
        content = f'''---
source: {link}
date: {pubdate}
blog: {blog_name}
---

# {title}

{desc}

---
원문: {link}
'''
        with open(fname, 'w') as f:
            f.write(content)
        print(f'NEW:{title}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>/dev/null

  while IFS= read -r line; do
    if [[ "$line" == NEW:* ]]; then
      ((count++))
      echo "  ✅ ${line#NEW:}"
    fi
  done < <(echo "$count")
}

sync_all() {
  local total=0
  echo "[$(date +%H:%M)] RSS 동기화 시작..."
  
  for blog in "${BLOGS[@]}"; do
    fetch_and_save "$blog"
  done

  # 변경 있으면 git push
  cd "$OUT_DIR/.."
  if ! git diff --quiet 기자/ 2>/dev/null; then
    git add 기자/
    git commit -m "📰 RSS sync: $(date +%Y-%m-%d %H:%M)" 2>/dev/null
    git push 2>/dev/null && echo "✅ GitHub Pages 갱신됨"
  fi
}

if [ "$1" == "--watch" ]; then
  echo "👀 RSS 감시 시작 (30분 간격)"
  while true; do
    sync_all
    sleep 1800
  done
else
  sync_all
fi
