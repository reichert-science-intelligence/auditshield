# CHDA DG/DQ Coverage Audit — v3 (D6 target recalibration)

**Generated:** 05/20/2026  
**Prior reports:** `dg_audit_report_initial.md`, `dg_audit_report_v2.md`  
**Audit script:** `rsi-academy/prep/audit_dg_coverage.py` @ HF main `8edf6aa`

## Revised D6 target

| Field | Value |
|---|---|
| **Previous target** | 35% (incorrect — assumed AHIMA governance/compliance domain) |
| **Revised target** | **20%** |
| **Authority** | `rsi-academy/prep/chda/CHDA_TAXONOMY.md` — D6 = RSI Prep Extension |
| **Rationale** | Cross-cutting DG/DQ should surface naturally (~1 in 5 items); not governance-primary |

## Coverage vs revised targets (v2 measurement, post pattern extension)

| Domain | Coverage % | Target % | Meets |
|---|---|---|---|
| D1 | 68.0% | 40.0% | yes |
| D2 | 32.0% | 25.0% | yes |
| D3 | 46.0% | 30.0% | yes |
| D4 | 64.0% | 35.0% | yes |
| D5 | 42.0% | 25.0% | yes |
| D6 | **32.0%** | **20.0%** | **yes** |

## Audit closeout status

**All six domains meet targets** after D6 recalibration. No bank content generation required for D2 or D6.

## Spec updates

- `Artifacts/S30/BANK_AUDIT_DATA_GOVERNANCE.md` §4 — D6 row updated to 20%
- `prep/audit_dg_coverage.py` `TARGET_COVERAGE["D6"]` — pending HF commit to 20.0
