#!/bin/bash
# 📸 auto_image_pipe.sh — 사진 자동 영상화 + TG 전송
# 사용법: bash auto_image_pipe.sh
#         bash auto_image_pipe.sh /path/to/images/
#         bash auto_image_pipe.sh --watch  (디렉토리 감시 모드)

# ── 설정 ──────────────────────────────────────────
INBOX="${1:-/data/data/com.termux/files/home/inbox}"
OUTDIR="/root/work/out/auto"
DONE_DIR="/data/data/com.termux/files/home/processed"

# TG 토큰 (직접 하드코딩 — source 문제 방지)
TG_TOKEN="8988031320:AAHYpxv3XuS6jaCh8switB9n7Z_ZP75V8nQ"
TG_CHAT="8579179811"
WATCH_MODE=false

[[ "$1" == "--watch" ]] && WATCH_MODE=true && INBOX="${2:-$INBOX}"

mkdir -p "$OUTDIR" "$DONE_DIR"

# ── TG 전송 함수 ──────────────────────────────────
send_tg() {
    local video="$1" caption="$2"
    if [[ -z "$TG_TOKEN" || -z "$TG_CHAT" ]]; then
        echo "⚠️ TG_TOKEN/TG_CHAT 미설정 — TG 전송 스킵"
        return 1
    fi
    local result=$(curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendVideo" \
        -F chat_id="${TG_CHAT}" \
        -F video="@${video}" \
        -F caption="${caption}")
    if echo "$result" | grep -q '"ok":true'; then
        echo "✅ TG 전송 완료"
    else
        echo "❌ TG 전송 실패: $result"
    fi
}

# ── 영상 생성 함수 ────────────────────────────────
make_video() {
    local files=("$@")
    local count="${#files[@]}"
    local ts=$(date +%Y%m%d_%H%M%S)
    local output="$OUTDIR/auto_${ts}.mp4"

    if [[ $count -eq 0 ]]; then
        echo "처리할 파일 없음"
        return 1
    fi

    echo "🎬 $count 장 처리 중..." >&2

    if [[ $count -eq 1 ]]; then
        ffmpeg -y -loop 1 -t 5 -i "${files[0]}" \
            -vf "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
            -c:v libx264 -preset fast -crf 28 "$output" 2>/tmp/ffmpeg_err.log
    else
        local -a ffargs=()
        local filter=""
        for i in "${!files[@]}"; do
            ffargs+=(-loop 1 -t 3 -i "${files[$i]}")
            filter+="[${i}:v]scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1[v${i}];"
        done
        local concat=""
        for i in "${!files[@]}"; do
            concat+="[v${i}]"
        done
        concat+="concat=n=${count}:v=1:a=0,format=yuv420p[v]"

        ffmpeg -y "${ffargs[@]}" -filter_complex "${filter}${concat}" \
            -map "[v]" -c:v libx264 -preset fast -crf 28 "$output" 2>/tmp/ffmpeg_err.log
    fi

    if [[ -f "$output" ]]; then
        echo "✅ 영상 생성: $output ($(du -h "$output" | cut -f1))" >&2
        echo "$output"
    else
        echo "❌ 영상 생성 실패" >&2
        return 1
    fi
}

# ── 메인 처리 ─────────────────────────────────────
process_inbox() {
    local files=()
    while IFS= read -r -d '' f; do
        files+=("$f")
    done < <(find "$INBOX" -maxdepth 1 \( -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" \) -type f -print0 2>/tmp/ffmpeg_err.log | head -10)

    if [[ ${#files[@]} -eq 0 ]]; then
        return 0
    fi

    echo "📥 ${#files[@]}개 새 이미지 발견"
    local video=$(make_video "${files[@]}")

    if [[ -n "$video" && -f "$video" ]]; then
        send_tg "$video" "🎬 자동 생성: ${#files[@]}장 → $(basename "$video")"

        # 처리 완료된 파일 이동
        for f in "${files[@]}"; do
            mv "$f" "$DONE_DIR/" 2>/tmp/ffmpeg_err.log || true
        done
        echo "📦 처리 완료 → $DONE_DIR"
    fi
}

# ── 감시 모드 ─────────────────────────────────────
if $WATCH_MODE; then
    echo "👀 감시 시작: $INBOX"
    mkdir -p "$INBOX"

    # 최초 1회 처리
    process_inbox

    # inotifywait으로 새 파일 감지
    while inotifywait -q -e create -e moved_to "$INBOX" 2>/tmp/ffmpeg_err.log; do
        sleep 1  # 파일 쓰기 완료 대기
        process_inbox
    done
else
    # 1회 실행
    process_inbox
fi
