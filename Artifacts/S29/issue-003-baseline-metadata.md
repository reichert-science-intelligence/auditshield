# ISSUE-003 Pre-Fix Baseline — Capture Metadata

- **Captured:** [YYYY-MM-DD HH:MM ET]
- **Device:** Android [manufacturer + model, e.g. Samsung Galaxy S24]
- **Android version:** [e.g. 14 / API 34]
- **Browser:** Chrome [version — Settings → About Chrome]
- **Network:** [Wi‑Fi SSID name OR cellular carrier + signal strength]
- **URL:** https://rreichert-rsi-academy.hf.space/ → **Prep Store** → **CHDA Prep** tab (interactive practice; `/prep/chda` is marketing landing only)
- **HF Space SHA at capture:** 960428d (or latest on HF main after D6 target commit)
- **Session state:** Cold (Chrome site data cleared immediately prior; see Phase 2 Android steps)
- **Behavior observed:**
  - Enter Stripe-unlock email if required, tap **Start practice draw**, then first **Next question** / answer pick: pane froze ~[N] sec, no question
  - Second tap on same control: unfreeze, question rendered normally
- **Reproducibility:** [confirmed N times / first try / intermittent]
- **Video file:** `Artifacts/S29/issue-003-prefix-baseline.mp4` (or `.webm` if native recorder)
