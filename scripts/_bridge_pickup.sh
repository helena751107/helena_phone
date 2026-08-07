#!/bin/bash
# 🔗 _bridge_pickup.sh — Android 갤러리/다운로드 → PD bridge 자동 감지
# Usage: bash scripts/_bridge_pickup.sh <ep>
# Android에서 만든 영상을 out/<ep>/bridge/ 로 자동 복사
#
# Boss 워크플로:
#   1. Gemini/공짜LLM으로 영상 만들기
#   2. 갤러리나 Download 폴더에 저장
#   3. produce_pd.sh 실행 → 이 스크립트가 자동 감지

set -euo pipefail

EP="${1:-pd_intro}"
ROOT="${ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BRIDGE_DIR="$ROOT/out/$EP/bridge"

# Android storage paths (proot에서 접근 가능)
ANDROID_BASE="/storage/emulated/0"
DOWNLOAD="$ANDROID_BASE/Download"
MOVIES="$ANDROID_BASE/Movies"
DCIM="$ANDROID_BASE/DCIM/Camera"
PICTURES="$ANDROID_BASE/Pictures"

mkdir -p "$BRIDGE_DIR"

# ── 검색 소스 (우선순위) ──
# 1) 정확한 파일명 (b_open.mp4 / b_close.mp4)
# 2) 에피소드 prefix (pd_intro_open*.mp4 / pd_intro_close*.mp4)
# 3) 패턴 매칭 (*open* / *close* / *intro* / *outro*)
# 4) 최신 영상 (가장 최근 수정된 mp4 2개 → open/close)

found_open=""
found_close=""

echo "  🔗 scanning Android storage for bridge videos..."

# helper: check if dir exists before listing
scan_dir() {
    local dir="$1"
    [[ -d "$dir" ]] || return 1
    return 0
}

# ── Strategy 1: exact filenames ──
for name in b_open.mp4 b_close.mp4; do
    for dir in "$DOWNLOAD" "$MOVIES" "$DCIM" "$PICTURES"; do
        scan_dir "$dir" || continue
        candidate="$dir/$name"
        if [[ -f "$candidate" ]]; then
            dest="$BRIDGE_DIR/$name"
            cp "$candidate" "$dest"
            echo "  ✅ exact match: $candidate → bridge/$name ($(du -h "$dest" | cut -f1))"
            [[ "$name" == "b_open.mp4" ]] && found_open="$dest"
            [[ "$name" == "b_close.mp4" ]] && found_close="$dest"
            break
        fi
    done
done

# ── Strategy 2: episode-prefix match ──
if [[ -z "$found_open" ]]; then
    for dir in "$DOWNLOAD" "$MOVIES" "$DCIM" "$PICTURES"; do
        scan_dir "$dir" || continue
        for pattern in "${EP}_open" "${EP}_intro" "open_${EP}" "intro_${EP}" "b_open"; do
            candidate=$(ls -t "$dir/${pattern}"*.mp4 2>/dev/null | head -1) || true
            if [[ -n "$candidate" && -f "$candidate" ]]; then
                found_open="$BRIDGE_DIR/b_open.mp4"
                cp "$candidate" "$found_open"
                echo "  ✅ prefix match: $(basename "$candidate") → bridge/b_open.mp4 ($(du -h "$found_open" | cut -f1))"
                break 2
            fi
        done
    done
fi

if [[ -z "$found_close" ]]; then
    for dir in "$DOWNLOAD" "$MOVIES" "$DCIM" "$PICTURES"; do
        scan_dir "$dir" || continue
        for pattern in "${EP}_close" "${EP}_outro" "close_${EP}" "outro_${EP}" "b_close"; do
            candidate=$(ls -t "$dir/${pattern}"*.mp4 2>/dev/null | head -1) || true
            if [[ -n "$candidate" && -f "$candidate" ]]; then
                found_close="$BRIDGE_DIR/b_close.mp4"
                cp "$candidate" "$found_close"
                echo "  ✅ prefix match: $(basename "$candidate") → bridge/b_close.mp4 ($(du -h "$found_close" | cut -f1))"
                break 2
            fi
        done
    done
fi

# ── Strategy 3: chronological pairing ──
# Boss가 Gemini로 open 먼저 만들고 close 나중에 만든다 → 시간순 = open<close
# 최신 2개를 골라 먼저 만든 것(오래된 것)을 b_open, 나중에 만든 것을 b_close 로 배정
if [[ -z "$found_open" || -z "$found_close" ]]; then
    all_media=$(find "$DOWNLOAD" "$MOVIES" "$DCIM" "$PICTURES" \
        -maxdepth 1 -name "*.mp4" -type f -printf "%T@ %p\n" 2>/dev/null | \
        sort -rn | head -4) || true

    # 최신 2개 중 오래된 것 → b_open, 더 새로운 것 → b_close
    newest=$(echo "$all_media" | head -1 | cut -d' ' -f2-)
    second=$(echo "$all_media" | head -2 | tail -1 | cut -d' ' -f2-)

    if [[ -z "$found_open" ]]; then
        # 먼저 만들어진 것(second=더 오래됨)이 opening
        candidate="$second"
        if [[ -n "$candidate" && -f "$candidate" ]]; then
            found_open="$BRIDGE_DIR/b_open.mp4"
            cp "$candidate" "$found_open"
            echo "  📱 chrono-pair: $(basename "$candidate") → b_open (먼저 생성)"
        fi
    fi

    if [[ -z "$found_close" ]]; then
        # 나중에 만들어진 것(newest=더 최신)이 closing
        candidate="$newest"
        if [[ -n "$candidate" && -f "$candidate" ]]; then
            found_close="$BRIDGE_DIR/b_close.mp4"
            cp "$candidate" "$found_close"
            echo "  📱 chrono-pair: $(basename "$candidate") → b_close (나중 생성)"
        fi
    fi
fi

# ── Summary ──
echo "  ─────────────────────"
if [[ -n "$found_open" ]]; then
    echo "  🟢 bridge/b_open.mp4  ready"
else
    echo "  ⚪ bridge/b_open.mp4  (없음 — SKIP)"
fi
if [[ -n "$found_close" ]]; then
    echo "  🟢 bridge/b_close.mp4 ready"
else
    echo "  ⚪ bridge/b_close.mp4 (없음 — SKIP)"
fi
echo "  📁 Android 소스: Download · Movies · DCIM/Camera · Pictures"
