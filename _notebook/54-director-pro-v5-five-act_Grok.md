# Director PRO v5 — 연출 5막 shoot 연주 (_Grok)

> 2026-08-02 · URL: https://helena751107.github.io/helena_phone/  
> 산출: `helena-programming/director/out/helena_phone_pro_v5.mp4`  
> 전제: pro_v4 (VQA 100) + `product_tour_v1` 설정만 있고 shoot 미연주 → **이번이 연주 구현**

---

## 1. 이력 파싱 (TG 전송 체인)

| 버전 | 파일 | TG | 비고 |
|------|------|-----|------|
| intro | `helena_phone_intro.mp4` | ✅ | Director 1편 샘플 |
| scout+intro | `helena_phone_scout_intro.mp4` | ✅ | scout→tts→click |
| pro | `helena_phone_pro.mp4` | ✅ | quality_gate 첫 PASS |
| tutorial_v1 | `helena_phone_tutorial.mp4` | ✅ | policy force |
| pro_v2 | `helena_phone_pro_v2.mp4` | ✅ | 가짜 SHIP (클릭 메트릭만) |
| pro_v3 | `helena_phone_pro_v3.mp4` | ✅ | visual proof 강제 |
| pro_v4 | `helena_phone_pro_v4.mp4` | ✅ | Vision QA 100/100 |
| **pro_v5** | `helena_phone_pro_v5.mp4` | ✅ | **5막 연출 시계** |

로컬 잔존 TG 응답: `/tmp/tg_video_resp.json` … `/tmp/tg_v2.json` · `/tmp/tg_v5.json`

---

## 2. v5에서 한 일

1. `shoot()` 가 `directing/product_tour_v1` **5막**을 비트마다 연주  
   `establish → focus → act → hold → release`
2. `phases_played[]` actions_log + enforce (`require_phases_played`)
3. 비트 wall-clock = VO 길이 (Parksy Air: 영상이 오디오 시계를 따름)
4. 인트로/바디 이음 검정 프레임 스킵 (`-ss 0.07` body)

---

## 3. SHIP 성적

| 항목 | 값 |
|------|-----|
| 파일 | `out/helena_phone_pro_v5.mp4` (~3.7MB) |
| shoot_version | **5** |
| phases_played | **6 beats × 5 phases** |
| 클릭 | **6 OK / 0 FAIL** |
| Proof | **12/12** |
| Auto VQA | **100/100 · S · PASS** |
| quality gate | PASS |
| 연출 | `product_tour_v1` |

---

## 4. 남은 갭

- multi-click 비트(`#archBox g.node`, `#wcList button.wc-item`)가 시간 예산에 밀려 **1차 클릭만** 수행됨 (min_successful=4는 통과)
- lead trim ~8s (페이지 로드 다크 프레임) — 부트 단축 여지
- dtslib Air `action_mapper` / `humanlike_scroll` 이식은 다음 라운드

---

## 5. 파일

| 경로 | 역할 |
|------|------|
| `director/run_director.py` | shoot v5 5막 |
| `director/directing/product_tour_v1.json` | 연출 악보 |
| `director/policy/tutorial_v1.json` | `require_phases_played` |
| `director/enforce.py` | phases_played 검사 |
| `out/helena_phone_pro_v5.*` | mp4 + actions + vqa |

---

## 6. 서명

- 구현·렌더·TG: **_Grok** (2026-08-02)  
- Boss 검수: _대기_
