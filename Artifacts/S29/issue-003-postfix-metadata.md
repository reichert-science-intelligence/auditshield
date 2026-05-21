# ISSUE-003 Post-Fix Verification — Capture Metadata

- **Captured:** 2026-05-20 (F12 functional verify; closeout evidence)
- **Device:** Chrome DevTools device emulation **375×812** (platform-agnostic gate logic; defect not mobile-specific)
- **Browser:** Chrome (desktop host, emulated mobile viewport)
- **URL:** https://rreichert-rsi-academy.hf.space/ → **Prep Store** → **CHDA Prep**
- **HF Space SHA at verify:** 52d0b3f
- **Session state:** Live Space; `DEMO_MODE=true` for happy-path draw only (revert to `false` after verify)
- **Video file:** Not captured — functional verify via F12 + automation screenshot (Question 1 of 10). Optional mp4: `Artifacts/S29/issue-003-postfix-verified.mp4` if operator records later.

## Scenes verified

1. **Gate-fail path (fix):** Empty email → tap **Start practice draw** once → warning toast (*Enter the email you used at CHDA checkout…*) — no apparent freeze.
2. **Happy path:** Enter `test@test.com` (with `DEMO_MODE=true`) → tap **Start practice draw** → **Question 1 of 10** renders (D5 RAPS/EDPS stem, A–D options, Exit session).

## Behavior observed

- **Gate-fail:** Toast shown; no freeze.
- **Happy path:** Draw rendered; Question 1 of 10 with four answer options (first-tap after email synced to server).

## Issue classification

- **Was:** Mobile WebSocket first-tap race (sev-1)
- **Actual:** UX gating defect — ungated **Start practice draw** button with silent gate-fail (empty email / no tier)
- **Fix:** `ui.notification_show(type="warning")` on gate-fail — CHDA/CRC/CPHQ (`52d0b3f`)
- **Status:** **S29 sev-1 CLOSED** (2026-05-20)
