# CHDA DG/DQ Coverage Audit — Initial Report

**Generated:** 05/20/2026  
**Bank path:** `prep/chda/chda_d{N}_question_bank.json` (rsi-academy `origin/main`)  
**Audit script:** `rsi-academy/prep/audit_dg_coverage.py`  
**Note:** D5 uses `question_text` / `option_a–d` schema (not `stem` / `options`); script updated to include both lineages.

| Domain | Items | Primary % | Secondary % | None % | Coverage % | Target % | Meets | Gap items |
|---|---|---|---|---|---|---|---|---|
| D1 | 50 | 22.0% | 46.0% | 32.0% | 68.0% | 40.0% | yes | 0 |
| D2 | 50 | 0.0% | 18.0% | 82.0% | 18.0% | 25.0% | **no** | 3 |
| D3 | 50 | 0.0% | 36.0% | 64.0% | 36.0% | 30.0% | yes | 0 |
| D4 | 50 | 16.0% | 40.0% | 44.0% | 56.0% | 35.0% | yes | 0 |
| D5 | 50 | 2.0% | 30.0% | 68.0% | 32.0% | 25.0% | yes | 0 |
| D6 | 50 | 0.0% | 6.0% | 94.0% | 6.0% | 35.0% | **no** | 14 |

## Domains below target

- **D2**: 18.0% vs 25.0% target (~3 items needed) — likely regex/content gap, not schema issue
- **D6**: 6.0% vs 35.0% target (~14 items needed) — RSI Prep Extension; many stems are study-skills/epidemiology without explicit DG/DQ vocabulary

## D5 vocabulary spot-check (5 random “none” items)

After schema fix, D5 **meets target** (32% vs 25%). Sample “none” items are legitimately MA-submissions content without DG/DQ keywords (MMR enrollment, MBI linkage, PDE days supply, CAHPS thematic analysis, Star Ratings category). **No regex extension required for D5** before remediation review.

## Remediation magnitude (Phase 3 decision matrix)

| Domain | items_needed | Recommended action |
|---|---|---|
| D2 | 3 | Revisit `classify()` thresholds OR tag 3 existing items — detection/content borderline |
| D5 | 0 | No action |
| D6 | 14 | **Pause** — consider lowering D6 target OR bulk item generation; target may be aggressive for extension domain |
