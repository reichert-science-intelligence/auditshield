# CHDA Bank Audit — Data Governance / Data Quality Cross-Cutting Coverage

**Sprint:** S30
**Owner:** Robert Reichert (RSI Academy)
**Triggered by:** 4th calibration respondent — "noticeable data governance/data quality emphasis across [all domains]"
**Status:** Audit framework ready; execution pending

## 1. Objective

Verify that the 6-domain CHDA bank (300 items) reflects the cross-cutting DG/DQ emphasis exam holders report, not just the items in domains where DG/DQ is the primary topic. Identify under-represented tags and produce a remediation list before S30 spec doc lock.

## 2. Definitions (audit-internal)

- **DG (Data Governance):** items testing policy, stewardship, ownership, lifecycle, access control, regulatory alignment (HIPAA, 21st Century Cures, ONC), master data management, data dictionary, lineage.
- **DQ (Data Quality):** items testing completeness, accuracy, consistency, timeliness, validity, uniqueness, integrity checks, profiling, cleansing, validation rules.
- **Cross-cutting:** items where DG or DQ is the underlying concept being tested, even if the surface scenario is analytics, terminology, or reporting.

## 3. Audit method (per-domain pass)

For each of D1–D6:

1. Load `rsi-academy/prep/banks/chda/d{N}.json`
2. For each item, tag with `dg_dq_relevance`:
   - `primary` — DG/DQ is the core concept tested
   - `secondary` — DG/DQ surfaces in rationale or distractor logic
   - `none` — no DG/DQ surface
3. Compute per-domain distribution: % primary / % secondary / % none
4. Compare against target distribution (below)

## 4. Target distribution (proposed)

Based on the 4th respondent's "across all domains" signal:

| Domain | Min `primary+secondary` % | Rationale |
|---|---|---|
| D1 | 40% | Likely the dedicated DG domain — should be majority |
| D2 | 25% | DG/DQ surfaces in analytics methodology decisions |
| D3 | 30% | Reporting requires DQ posture (completeness, timeliness) |
| D4 | 35% | Clinical data management is DQ-adjacent by nature |
| D5 (MA) | 25% | Submissions (MMR/MOR/RAPS/EDPS/PDE) are DQ-heavy |
| D6 | 35% | Governance/compliance domain — should be majority |

Tunable after first audit pass.

## 5. Execution script (proposed)

```python
# rsi-academy/prep/audit_dg_coverage.py
"""
Cross-cutting DG/DQ coverage audit for CHDA bank.

Usage:
    python rsi-academy/prep/audit_dg_coverage.py
    python rsi-academy/prep/audit_dg_coverage.py --domain D3 --verbose
    python rsi-academy/prep/audit_dg_coverage.py --report-md > Artifacts/S30/dg_audit_report.md
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

BANK_ROOT = Path("rsi-academy/prep/banks/chda")

DG_PATTERNS = [
    r"\bgovernance\b", r"\bsteward(ship)?\b", r"\bpolicy\b",
    r"\bownership\b", r"\bHIPAA\b", r"\bONC\b", r"\b21st\s+Century\s+Cures\b",
    r"\bmaster\s+data\b", r"\bdata\s+dictionary\b", r"\blineage\b",
    r"\baccess\s+control\b", r"\bdata\s+lifecycle\b",
]

DQ_PATTERNS = [
    r"\bcomplete(ness)?\b", r"\baccura(cy|te)\b", r"\bconsisten(cy|t)\b",
    r"\btimeliness\b", r"\bvalid(ity|ation)\b", r"\buniqueness\b",
    r"\bintegrity\b", r"\bprofil(e|ing)\b", r"\bcleans(e|ing)\b",
    r"\bvalidation\s+rule\b", r"\bdata\s+quality\b",
]

def classify(item: dict) -> str:
    text = " ".join([
        item.get("question", ""),
        item.get("rationale", ""),
        " ".join(item.get("distractors", [])),
    ]).lower()

    dg_hits = sum(1 for p in DG_PATTERNS if re.search(p, text, re.I))
    dq_hits = sum(1 for p in DQ_PATTERNS if re.search(p, text, re.I))

    total = dg_hits + dq_hits
    if total >= 3:
        return "primary"
    if total >= 1:
        return "secondary"
    return "none"

def audit_domain(domain: str) -> dict:
    # Domain files exist in two schema lineages — handle both
    path = BANK_ROOT / f"{domain.lower()}.json"
    raw = json.loads(path.read_text())
    items = raw if isinstance(raw, list) else raw.get("items", [])

    counts = {"primary": 0, "secondary": 0, "none": 0}
    for item in items:
        counts[classify(item)] += 1

    total = len(items) or 1
    return {
        "domain": domain,
        "total_items": len(items),
        "primary_pct": round(100 * counts["primary"] / total, 1),
        "secondary_pct": round(100 * counts["secondary"] / total, 1),
        "none_pct": round(100 * counts["none"] / total, 1),
        "coverage_pct": round(100 * (counts["primary"] + counts["secondary"]) / total, 1),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", help="Single domain (D1-D6)")
    parser.add_argument("--report-md", action="store_true")
    args = parser.parse_args()

    domains = [args.domain] if args.domain else [f"D{i}" for i in range(1, 7)]
    results = [audit_domain(d) for d in domains]

    if args.report_md:
        print("| Domain | Items | Primary % | Secondary % | None % | Coverage % |")
        print("|---|---|---|---|---|---|")
        for r in results:
            print(f"| {r['domain']} | {r['total_items']} | {r['primary_pct']}% | "
                  f"{r['secondary_pct']}% | {r['none_pct']}% | {r['coverage_pct']}% |")
    else:
        for r in results:
            print(r)

if __name__ == "__main__":
    main()
```

## 6. Remediation playbook

If a domain falls below target coverage:

1. Identify N items needed to reach target (math: `(target_pct - current_pct) * total_items / 100`)
2. Generate candidate items per `rsi-academy/prep/generate_questions.py` workflow with DG/DQ scenario seeds
3. Validate via `validate_question_bank.py --strict --max-bloom-drift-items 8 --max-answer-skew-pct 10`
4. Re-run audit to confirm uplift
5. Commit per-domain: `feat(banks/chda): add DG/DQ coverage to D{N} (audit closeout)`

## 7. Validation gates

- [ ] Audit script committed and runs clean on all 6 domains
- [ ] Initial coverage report saved to `Artifacts/S30/dg_audit_report_initial.md`
- [ ] All 6 domains meet target coverage post-remediation
- [ ] Re-run strict validator: 0 new bloom drift, 0 new answer skew
- [ ] Final report saved to `Artifacts/S30/dg_audit_report_final.md`

## 8. Open questions

1. Should the regex patterns be tuned for AHIMA terminology specifically? (Recommend yes — pull authoritative term list from AHIMA CHDA Exam Content Outline slug `lflpvl4k`.)
2. Does a "DG/DQ in rationale only" item count toward exam-day applicability? (Recommend yes — distractor and rationale reasoning is part of test-taking skill.)
3. Should D5 (MA-specific) carry a lower bar given MMR/MOR/RAPS/EDPS/PDE are inherently DQ-heavy by submission semantics? (Recommend no — verify floor.)
