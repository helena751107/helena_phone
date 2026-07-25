# YouTube 채널 아키텍처

> 방송탑 워크센터 — 강의·수익화 송신 인프라

## 개요
S21 Phone의 **방송탑**은 YouTube Data API + OAuth로 운영한다. 채널 계정은 큰누나 명의.

## 관련 문서
- [notebook YouTube](../_notebook/06-youtube.md)
- [yt_upload.py](../scripts/yt_upload.py)
- [워크센터 최종](../_notebook/20-workcenters-final.md)

## 상태
설계 완료 · OAuth 연결 대기. 상세 운영 노트는 `_notebook/06-youtube.md`를 본다.

## 스택
```
Claude Code / 스크립트 → YouTube Data API (OAuth)
                      → @helena_phone 채널 업로드
```
