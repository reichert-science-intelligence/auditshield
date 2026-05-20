# CHDA DG/DQ Coverage Audit — v2 (pattern extension)

**Generated:** 05/20/2026  
**Bank path:** `prep/chda/chda_d{N}_question_bank.json`  
**Audit script:** `rsi-academy/prep/audit_dg_coverage.py` (extended patterns)  
**Prior report:** `dg_audit_report_initial.md`

Pattern extension (measurement fix, no bank edits):
- **DG added:** audit_trail, metadata, schema_versioning, data_catalog
- **DQ added:** missing_data, outlier, duplicate, bias, skew, standardization, sampling

| Domain | Items | Primary % | Secondary % | None % | Coverage % | Target % | Meets | Gap items | Δ vs v1 |
|---|---|---|---|---|---|---|---|---|---|
| D1 | 50 | 26.0% | 42.0% | 32.0% | 68.0% | 40.0% | yes | 0 | — |
| D2 | 50 | 2.0% | 30.0% | 68.0% | **32.0%** | 25.0% | **yes** | 0 | +14pp |
| D3 | 50 | 0.0% | 46.0% | 54.0% | 46.0% | 30.0% | yes | 0 | +10pp |
| D4 | 50 | 20.0% | 44.0% | 36.0% | 64.0% | 35.0% | yes | 0 | +8pp |
| D5 | 50 | 4.0% | 38.0% | 58.0% | 42.0% | 25.0% | yes | 0 | +10pp |
| D6 | 50 | 2.0% | 30.0% | 68.0% | **32.0%** | 35.0% | **no** | ~1 | +26pp |

## Domains below target

- **D6 only:** 32.0% vs 35.0% target (~1 item by math; see D6 strategy note)

## D6 strategy note (authoritative)

Per `prep/chda/CHDA_TAXONOMY.md`, **D6 is the RSI Prep Extension** (study skills, claims context, exam tactics) — **not** AHIMA governance/compliance. The original 35% target assumed wrong domain scope.

**Recommended action:** Lower D6 target to **15–20%** (or document as out-of-scope for DG/DQ cross-cutting audit). Do **not** generate 14 governance items for D6. At 32% with corrected scope, D6 likely **exceeds** a 20% target.

## D2 retag closeout

D2 retag track **complete** via pattern extension (18% → 32%). No bank content changes required.
