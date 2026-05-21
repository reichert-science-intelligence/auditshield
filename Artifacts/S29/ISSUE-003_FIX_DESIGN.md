# ISSUE-003 — Practice Start “Freeze” on Mobile (S29)

**Sprint:** S29 closeout / S30 gate  
**Status:** **CLOSED** (2026-05-20) — gate-fail toast + happy-path draw verified @ `52d0b3f` (F12 375px)  
**HF Space:** `rreichert-rsi-academy.hf.space`  
**Fix SHA:** `52d0b3f` (`rsi-academy` `main`)

## Symptom (reported)

On mobile Chrome (cold session), first tap on **Start practice draw** (CHDA Prep) appeared to freeze the UI. Second tap sometimes “unfroze” and the draw rendered.

Reproduction path:

```
https://rreichert-rsi-academy.hf.space/
  → Prep Store → CHDA Prep tab
  → Start practice draw
```

## Resolution (05/20/2026) — reclassified

| Original classification | Actual root cause |
|---|---|
| Mobile WebSocket first-tap race (sev-1) | **UX gating defect:** ungated Start button + silent gate-fail |

### What actually happened

1. **Start practice draw** is always rendered (`_prep_practice_draw_controls`) — not gated in UI.
2. Handler `_chda_practice_start` calls `_chda_practice_gate_ok()`, which checks **email before `demo_mode`**:

```python
email = (input.prep_chda_email() or "").strip()
if not email or "@" not in email:
    return False  # empty email exits here
if demo_mode:
    return True
return chda_effective_tier(email) is not None
```

3. With **empty email** (common on cold mobile tap), handler fires, gate fails, **silent early-return** — no UI update, no feedback → reads as “freeze.”
4. Step logs @ `11d6ecb` showed: `FIRED → gate not OK — early return` (no `state.set`, no reload).
5. Three WS-timing deploys (`defer_to_flush`, `sleep(0)`, `$sendMsg` buffer) addressed a **misdiagnosis**. Instrumentation (step logs), not another fix, exposed the gate.

### Fix shipped (`52d0b3f`)

- **`_notify_prep_practice_gate_fail()`** — `ui.notification_show(type="warning")` on gate-fail for CHDA, CRC, CPHQ practice-start handlers.
- **Cleanup:** removed `[ISSUE-003]` step logs, reverted `async`/`sleep(0)` experiments, deleted unused `prep/_reactive_helpers.py`.
- **Kept:** `$sendMsg` readyState buffer (defensive; unrelated to this bug).

### Verified

- **Gate-fail @ `52d0b3f`:** empty email → warning toast; no apparent freeze.

### Closeout (2026-05-20)

- [x] Happy-path: `test@test.com` + `DEMO_MODE=true` → draw renders (Question 1 of 10).
- [x] Gate-fail: empty email → warning toast.
- [x] Post-fix metadata: `issue-003-postfix-metadata.md` (F12 375px; mp4 optional).
- [ ] Operator: revert `DEMO_MODE=false` on HF (if still `true`).
- [x] auditshield closeout commit (docs + reclassification).

## Post-mortem notes

- **H3 “handler fires then crash/reload”** was over-read from incomplete logs @ `7213826` (only `FIRED` line); asset 200 burst likely operator page reload, not session crash.
- **`DEMO_MODE=true` gate test** could not bypass empty email because email check runs first.
- **Deferred (S30):** conditional-render Start button only when gate passes (`update_action_button` has no `disabled` in Shiny 0.9.0).

## Artifacts

| File | Purpose |
|---|---|
| `issue-003-prefix-baseline.mp4` | Pre-fix freeze (empty-email silent no-op) |
| `issue-003-baseline-metadata.md` | Baseline capture metadata |
| `issue-003-postfix-verified.mp4` | Post-fix (pending) |
| `issue-003-postfix-metadata.md` | Post-fix capture template |

## Code surface (final)

| Pack | Input id | Handler | Gate-fail notify |
|---|---|---|---|
| CHDA | `prep_chda_practice_start` | `_chda_practice_start` | Yes |
| CRC | `prep_crc_practice_start` | `_crc_practice_start` | Yes |
| CPHQ | `prep_cphq_practice_start` | `_cphq_practice_start` | Yes |
