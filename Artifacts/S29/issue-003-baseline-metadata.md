# ISSUE-003 Pre-Fix Baseline — Capture Metadata

- **Captured:** 2026-05-20 [HH:MM ET]
- **Device:** Android [manufacturer + model]
- **Android version:** [Settings → About phone → Android version]
- **Browser:** Chrome [version — Settings → About Chrome]
- **Network:** [Wi‑Fi SSID OR cellular carrier + signal]
- **URL:** https://rreichert-rsi-academy.hf.space/ → **Prep Store** → **CHDA Prep** tab (not `/prep/chda` marketing page)
- **HF Space SHA at capture:** 960428d
- **Session state:** Cold — Chrome data cleared (All time, all 3 categories) + force-quit immediately prior to capture
- **Trigger tap identified in dry-run (B.3):** **Start practice draw** button (CHDA Prep tab, Prep Store)
- **Behavior observed:**
  - First tap on **Start practice draw**: UI froze at top of start draw for ~[N] seconds; no draw/question content rendered
  - Second tap on same button: UI unfroze; draw / first question rendered normally
- **Reproducibility:** confirmed in dry-run (B.3) + capture (B.4)
- **Video file:** `Artifacts/S29/issue-003-prefix-baseline.mp4`
- **Diagnostic note:** Freeze surface is **`_chda_practice_start`** (`prep_chda_practice_start` input), not `_make_chda_pick`. See `Artifacts/S29/ISSUE-003_FIX_DESIGN.md`.
