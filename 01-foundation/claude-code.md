# 1.3 Claude Code + DeepSeek

> AI 코딩 에이전트를 폰에서 돌리기 — 과금 없이

## Claude Code란?

Claude Code는 Anthropic이 만든 **터미널 기반 AI 코딩 에이전트**다.
파일 생성/수정, git 작업, 터미널 명령 등 개발 작업을 자연어로 시킬 수 있다.

## 문제: Anthropic API는 비싸다

Claude Code는 기본적으로 Anthropic API를 호출하는데, 한국에서 쓰면 호출당 수백 원.

## 해결: DeepSeek

[DeepSeek](https://platform.deepseek.ai/)이 Anthropic 호환 API를 제공한다.
Claude Code의 `ANTHROPIC_BASE_URL`만 DeepSeek 엔드포인트로 바꾸면 된다.

```bash
# DeepSeek 환경변수 설정
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_MODEL=deepseek-chat
export ANTHROPIC_AUTH_TOKEN=sk-xxxxx  # DeepSeek API 키
export DEEPSEEK_API_KEY=sk-xxxxx       # 동일
```

이렇게 하면:
- **Claude Code UI/도구는 그대로**
- **LLM 엔진만 DeepSeek V3로 교체**
- **비용 약 10~50배 절감**

## Claude Code 설치

```bash
# proot Ubuntu 안에서
npm install -g @anthropic-ai/claude-code
```

또는 공식 설치 스크립트:
```bash
curl -sS https://docs.anthropic.com/claude-code/install.sh | bash
```

## 실행

```bash
# 환경변수 설정 후 실행
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_MODEL=deepseek-chat
export ANTHROPIC_AUTH_TOKEN=sk-xxxxx
claude
```

또는 `.bashrc`에 등록해서 항상 적용:
```bash
echo 'export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic' >> ~/.bashrc
echo 'export ANTHROPIC_MODEL=deepseek-chat' >> ~/.bashrc
```

## 주의사항

- DeepSeek API 키 발급: https://platform.deepseek.ai/ → API Keys
- 응답 속도는 Anthropic보다 느릴 수 있음 (DeepSeek V3 기준)
- 한/영 모두 가능

## 다음 단계

→ [Git/GitHub 연결하기](./git-github.md)
