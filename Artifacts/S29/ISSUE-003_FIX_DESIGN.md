# ISSUE-003 — Mobile WebSocket First-Tap Race (Sev-1)

**Sprint:** S29 closeout / S30 gate  
**Status:** Design updated 05/20/2026 after operator dry-run  
**HF Space:** `rreichert-rsi-academy.hf.space` @ `960428d`  
**Baseline:** Pending `Artifacts/S29/issue-003-prefix-baseline.mp4`

## Symptom

On mobile Safari/Chrome (cold session), first tap on **Start practice draw** (CHDA Prep tab) freezes the UI at the top of the draw-initiation step. Second tap on the same button unfreezes and the draw / first question renders.

## Diagnostic correction (05/20/2026)

| Prior hypothesis | Operator dry-run result |
|---|---|
| Freeze on first **answer pick** (A/B/C/D) via `_make_chda_pick` | **Rejected** |
| Freeze on **Start practice draw** button | **Confirmed** |

Reproduction path:

```
https://rreichert-rsi-academy.hf.space/
  → Prep Store → CHDA Prep tab
  → Start practice draw (first tap freezes, second tap unfreezes)
```

`/prep/chda` is marketing-only — not the reproduction surface.

## Root cause (design)

Shiny mobile WebSocket: synchronous `reactive.Value.set()` inside an `@reactive.effect` on the **first** user input after cold load can race the session flush. The UI re-render triggers before the client ack settles, leaving the practice panel stuck until a second input forces another flush.

## Code surface (grep-verified)

| Pack | UI control | Input id | Handler | Lines (prep_exam.py) |
|---|---|---|---|---|
| CHDA | Start practice draw | `prep_chda_practice_start` | `_chda_practice_start` | 1487–1524 |
| CRC | Start practice draw | `prep_crc_practice_start` | `_crc_practice_start` | 1421–1451 |
| CPHQ | Start practice draw | `prep_cphq_practice_start` | `_cphq_practice_start` | 1454–1484 |
| CHDA | Answer pick A–D | `prep_chda_practice_pick_{a,b,c,d}` | `_make_chda_pick` | 1556–1569 |
| CRC | Answer pick | `prep_crc_practice_pick_*` | `_make_crc_pick` | 1526–1539 |
| CPHQ | Answer pick | `prep_cphq_practice_pick_*` | `_make_cphq_pick` | 1541–1554 |

**Fix scope finding: (c) Both handler families may race on mobile.**

- **Primary (confirmed):** practice-start handlers — defer `{pack}_practice_state.set(...)` after draw computation.
- **Secondary (preventive):** pick handlers — defer `{pack}_practice_state.set(...)` on answer selection (original design; still apply for parity across CRC/CPHQ/CHDA).

`_make_chda_pick` is **not** invoked by Start practice draw; it is a separate reactive chain.

## Fix pattern

New module: `rsi-academy/prep/_reactive_flush_helpers.py` (name may alias `_pick_helpers.py` if extended).

```python
def defer_state_update(session, setter: Callable[[], None]) -> None:
    """Run setter after WebSocket session flush (once=True)."""
    session.on_flushed(setter, once=True)
```

### Practice-start refactor

Replace inline `{pack}_practice_state.set(...)` at end of `_chda_practice_start` (and CRC/CPHQ siblings) with:

```python
payload = {"error": None, "items": drawn, "idx": 0, "answers": {}, "done": False}

def _apply():
    chda_practice_state.set(payload)

defer_state_update(session, _apply)
```

Draw computation (`_draw_practice_items`, bank load, tier gate) stays **synchronous** in the effect; only the state write that triggers UI re-render is deferred.

### Pick refactor

Same defer wrapper around `{pack}_practice_state.set({**st, "answers": ...})` inside `_make_*_pick` effects.

## Commit sequence (after baseline mp4 lands)

1. `docs(s29): update ISSUE-003 fix design for Start practice draw trigger` — this file + metadata
2. `feat(prep): add _reactive_flush_helpers scaffold` — no call-site changes
3. `test(prep): add flush helper unit tests`
4. `fix(prep): defer practice-start + pick state updates (ISSUE-003)`
5. Post-fix Android capture → `issue-003-postfix-verified.mp4`
6. `docs(s29): close ISSUE-003 sev-1 with mobile parity evidence`

## Validation gates

- [ ] Pre-fix baseline mp4 at `Artifacts/S29/issue-003-prefix-baseline.mp4`
- [ ] Post-fix mp4 same device/network pattern
- [ ] CHDA + CRC + CPHQ: Start practice draw first tap <200ms to visible draw
- [ ] First answer pick still works after draw loads
- [ ] Desktop regression: no added latency on cold start

## Open items

- MA Bundle prep start handler — grep at scaffold time; extend defer if present.
- Consider renaming `_pick_helpers` → `_reactive_flush_helpers` to reflect expanded scope.
