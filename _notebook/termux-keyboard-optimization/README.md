# Termux 기능키 최적화 — 오픈 이슈

> 상태: **오픈** | 생성: 2026-07-27 | 담당: Boss

## 문제
- 음성 입력으로 터미널(Termux) 작업 시 필수 자판/기능키가 뭔지 정리 안 됨
- 삼성 키보드 + Keys Cafe 조합으로 최적화된 터미널 자판 레이아웃 필요
- 비밀번호/패스워드 등 반복 타이핑을 Keys Cafe에 등록해 빠르게 입력하는 솔루션

## 목표
1. Termux 음성 입력 시뮬레이션 → **꼭 필요한 키** 식별
2. Termux extra-keys (`termux.properties`) 최적 세팅
3. 삼성 키보드 Keys Cafe 편집 → 터미널 전용 자판 설계
4. 자주 쓰는 문자열(비밀번호, 패스워드 등) Keys Cafe 매크로 등록

## 관련 파일
- Termux 설정: `/data/data/com.termux/files/home/.termux/termux.properties`
- 삼성 Good Lock → Keys Cafe 모듈

## 연관 메모
- [[termux-keyboard-layout]] — 추후 작성 예정
- [[samsung-keys-cafe-config]] — 추후 작성 예정

## 참고
- `enforce-char-based-input = true` — 삼성 키보드 입력 지연 버그 픽스
- `extra-keys-style = arrows-all` — 방향키 위주 간소화
