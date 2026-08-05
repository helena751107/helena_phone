#!/usr/bin/env python3
"""Helena TTS Maker — 성우 플러그인 기반 (director/voice_engine)
Usage: python3 _make_tts.py <outdir>
Env: TTS_ENGINE=grok|openai|edge  (기본: grok)
"""
import subprocess, os, sys
from pathlib import Path

# Add parent to path so we can import director
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

outdir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('OUTDIR', '/root/work/out/intro')

# Try unified voice engine first, fall back to edge-tts directly
try:
    from director.voice_engine import synthesize
    USE_VOICE_ENGINE = True
except ImportError:
    USE_VOICE_ENGINE = False
    print("  ⚠ director/voice_engine.py 없음 — edge-tts 직접 사용")

voice = os.environ.get('VOICE', 'ko-KR-SunHiNeural')
engine = os.environ.get('TTS_ENGINE', 'auto')

slides = [
    ('S21 Phone. 갤럭시 한 대로 돌봄과 소망을 돌리는 AI 워크스테이션입니다. 대필작가이자 간병인인 헬레나가 스마트폰 하나로 풀스택 개발 환경을 구축했습니다. 터먹스와 프로트 우분투 위에서 모든 것이 돌아갑니다. PC 없이도 가능한 풀스택 개발. 이게 S21 Phone 프로젝트입니다.', '01_hero'),
    ('세 명의 AI 에이전트가 각자 역할을 맡아 일합니다. 클로드 코드는 감사와 기획을, 딥시크 에이더는 작업반장으로 코드를, 그리고 그록은 이미지와 영상 디자인을 담당합니다. 만능 하나보다 분업. 세 에이전트가 협력하여 콘텐츠를 생산합니다.', '02_agents'),
    ('시스템 맵을 보면 데이터가 폰에서 세상으로 흐르는 전체 아키텍처가 한눈에 들어옵니다. 깃허브 페이지스, 유튜브, 텔레그램, 디스코드, 티스토리, 네이버까지. 모든 채널이 폰에서 시작되고 폰에서 관리됩니다. 한 대의 갤럭시가 미디어 스튜디오가 되는 순간입니다.', '03_system'),
    ('일곱 개의 워크센터. 공장, 출판사, 방송탑, 탐사대, 연구소, 로비, 인터컴. 모든 작업을 자동화와 수동으로 나누어 운영합니다. 각 워크센터는 깃허브 액션즈로 자동화되어 있고 폰에서 모든 것을 통제합니다. PC 없는 스튜디오. 오직 갤럭시 한 대로.', '04_centers'),
    ('콘텐츠는 네이버 웹진에서 시작해 유튜브 강의로 완성됩니다. 그록이 80퍼센트 드래프트를 만들고 클로드 코드가 다듬어서 출판합니다. 월 비용은 거의 제로. 깃허브 페이지스와 액션즈, 텔레그램, 디스코드까지 전부 공짜입니다. 구독과 좋아요로 이 채널을 응원해 주세요.', '05_funnel'),
    ('이 모든 것은 한 가지 원칙 위에 서 있습니다. 핸드오프가 곧 성공이다. 모든 계정은 누나 명의. 돌봄은 깨지지 않게. 소망은 세상에 닿게. S21 Phone. 갤럭시 한 대로 시작하는 당신의 AI 워크스테이션. 지금 구독하세요.', '06_constitution'),
]

for i, (text, name) in enumerate(slides):
    txt_file = os.path.join(outdir, name + '.txt')
    mp3_file = os.path.join(outdir, name + '.mp3')
    Path(txt_file).write_text(text, encoding='utf-8')

    if USE_VOICE_ENGINE:
        try:
            dur, provider = synthesize(text, Path(mp3_file), engine=engine)
            print(f'  [{i+1}/{len(slides)}] {name}: {dur:.1f}s  ({provider})')
        except Exception as e:
            print(f'  ❌ {name}: voice engine failed — {e}')
            sys.exit(1)
    else:
        # Fallback: edge-tts directly
        r = subprocess.run(
            ['edge-tts', '-f', txt_file, '--voice', voice, '--write-media', mp3_file],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            print(f'  ❌ {name}: TTS failed'); sys.exit(1)
        dur = float(subprocess.check_output(
            ['ffprobe','-v','error','-show_entries','format=duration',
             '-of','default=noprint_wrappers=1:nokey=1',mp3_file]
        ).decode().strip())
        print(f'  [{i+1}/{len(slides)}] {name}: {dur:.1f}s  (edge/{voice})')

    sys.stdout.flush()

print('TTS 완료')
