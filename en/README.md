# S21 Phone — A Phone That Became an AI Workstation

> Built in 36 hours. 39 commits, 102 files, 15,874 lines. Cost: $0.

## What Is This?

A 5-year-old Galaxy S21 running as a full-stack AI development server. No PC required. No keyboard required — 100% voice input (STT). Built by a caregiver-ghostwriter for one person: their older sister.

## Two Tracks

| Track | Purpose | Access |
|-------|---------|--------|
| **Track 1 — Caregiving** | Safety monitoring. Location, battery, anomaly detection. Emergency escalation. | **Private** (2 people only) |
| **Track 2 — Aspiration** | Ghostwriting. Mirroring the sister's best possible self through content. | **Public** |

## Tech Stack

```
Galaxy S21 (Android + Termux)
  └── proot Ubuntu
       ├── Claude Code (DeepSeek Radar) — AI coding agent
       ├── phone-mcp-server — 18 device control tools (no root)
       ├── phone-health.sh — 27-item hardware diagnostics
       ├── care-daemon.sh — autonomous safety monitoring
       ├── g/install.sh — one-line full install
       └── scripts/yt_upload.py — YouTube automation
```

## 5×5 Ecosystem

| Tistory (KR blog) | YouTube | GitHub | Theme |
|-------------------|---------|--------|-------|
| galaxys21-pwuser | @helena_phone | helena_phone | 📱 Phone Optimization Bible |
| mynote11605 | @HelenaTechLog | helana_log | 🗃️ APK Reverse Engineering |
| helana-christianity | @HelenaFaith | helena-faith | ✝️ Family Faith History |
| helena-piano | @HelenaPiano | helena-piano | 🎹 Piano + AI Music |
| helena-psycare | @HelenaPsycare | helena-psycare | 🧠 Mental Health Analysis |

## Core Principles

1. **Code is a gift.** Copyright is meaningless. The ability to explain code live is the real asset.
2. **Handoff is success.** The ghostwriter's role ends when the sister can operate this system alone using only her voice.
3. **Judgment is the only scarce asset.** Code production speed is the new normal. Verification, prioritization, and knowing what NOT to build — that's real value.
4. **Layer A/B separation.** Every platform splits into Layer A (human creative work) and Layer B (metadata/structure, automatable via STT+agent).
5. **AI output is hypothesis v1.** Nothing AI produces is considered fact until Boss approves it.

## Quick Install

```bash
curl -sL https://raw.github.com/helena751107/helena_phone/main/g/install.sh | bash
```

## Links

- 🇰🇷 [Korean Original](https://helena751107.github.io/helena_phone/)
- 📺 [YouTube @helena_phone](https://www.youtube.com/@helena_phone)
- 💬 [Discord](https://discord.gg/JTYSZv2WQE)
- 📝 [Tistory (Work Log)](https://galaxys21-pwuser.tistory.com)

---

*Built with Claude Code (DeepSeek Radar) on a Galaxy S21. All content is the sister's voice, ghostwritten by Helena.*
