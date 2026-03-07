# AuditShield-Live — Architecture

## Purpose

AuditShield-Live is an AI-powered Medicare Advantage RADV Audit Defense Platform. It provides integrated modules for provider scorecards, mock audits, financial impact analysis, RADV command center, chart selection AI, education automation, real-time validation, HCC reconciliation, compliance forecasting, regulatory intelligence, EMR rules, and executive dashboards. Phase 2 adds active suppression (audit-level), HITL Admin View, and hardening artifacts.

---

## Component Map (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AuditShield-Live (Shiny App)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  app.py (main)                                                               │
│    ├── app_complete.py (HuggingFace entry, uvicorn)                          │
│    ├── audit_trail.py ────────► Google Sheets + Supabase                     │
│    │   └── .audit_suppressions.json (Phase 2)                                │
│    ├── audit_trail_ui.py                                                     │
│    ├── cloud_status_badge.py                                                 │
│    ├── suppression_banner.py (Phase 2)                                       │
│    ├── hitl_admin_view.py (Phase 2)                                           │
│    ├── meat_validator.py, radv_command_center.py                             │
│    ├── chart_selection_ai.py, education_automation.py                        │
│    ├── realtime_validation.py, hcc_reconciliation.py                        │
│    ├── compliance_forecasting.py, regulatory_intelligence.py                │
│    ├── emr_rule_builder.py, dashboard_manager.py                            │
│    └── database.py, financial_calculator.py, mock_audit_simulator.py        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Reference

| Module | Role |
|--------|------|
| `app.py` | Main Shiny UI + server |
| `app_complete.py` | HuggingFace entry, init check, uvicorn |
| `audit_trail.py` | RADV audit CRUD, Google Sheets, Supabase, Phase 2 suppression |
| `audit_trail_ui.py` | Audit Trail panel UI |
| `cloud_status_badge.py` | Cloud services badge (sidebar/strip) |
| `suppression_banner.py` | Phase 2 suppression status banner |
| `hitl_admin_view.py` | Phase 2 HITL Admin View (audit suppressions) |
| `meat_validator.py` | M.E.A.T. validation |
| `radv_command_center.py` | RADV command center |
| `chart_selection_ai.py` | Chart selection AI |
| `education_automation.py` | Education automation |
| `realtime_validation.py` | Real-time validation engine |
| `hcc_reconciliation.py` | HCC reconciliation |
| `compliance_forecasting.py` | Compliance forecasting |
| `regulatory_intelligence.py` | Regulatory intelligence |
| `emr_rule_builder.py` | EMR rule builder |
| `dashboard_manager.py` | Dashboard manager |
| `database.py` | SQLite/Supabase database |
| `financial_calculator.py` | Financial impact calculator |
| `mock_audit_simulator.py` | Mock audit simulator |

---

## Data Flow

```
User → Shiny UI → Server Handlers
         │
         ├──► audit_trail.push_audit_record() → Google Sheets + Supabase
         ├──► audit_trail.fetch_recent_audits() → DataFrame
         ├──► get_audit_suppressions() → .audit_suppressions.json
         ├──► add/remove_audit_suppression() → JSON CRUD
         └──► database, MEATValidator, etc. → SQLite / Supabase
```

---

## Deployment Topology

| Environment | Host | Port | Entry |
|-------------|------|------|-------|
| Local | localhost | 7860 | `python app_complete.py` |
| HuggingFace Spaces | rreichert/auditshield-live | 7860 | uvicorn via app_complete |
| Docker | python:3.11-slim | 7860 | `python app_complete.py` |

---

## Dependency Graph

```
app.py
  ├── shiny, pandas, plotly
  ├── audit_trail, audit_trail_ui, cloud_status_badge
  ├── suppression_banner, hitl_admin_view
  ├── meat_validator, radv_command_center, chart_selection_ai
  ├── education_automation, realtime_validation, hcc_reconciliation
  ├── compliance_forecasting, regulatory_intelligence, emr_rule_builder
  ├── dashboard_manager, database, financial_calculator, mock_audit_simulator
  └── gspread, supabase, google-auth, anthropic
```

---

## Configuration

| Variable | Purpose |
|----------|---------|
| `GSHEETS_CREDS_JSON` | Google Sheets credentials (HF Secret) |
| `AUDIT_SHEET` | Sheet name (default: AuditShield_RADV_Audit_Trail) |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | Supabase parallel write |
| `AUDIT_SUPPRESSION_FILE` | Phase 2 suppression JSON path |
| `ANTHROPIC_API_KEY` | Claude API |
| `SQLITE_PATH` | SQLite path (default: /tmp/auditshield.db) |

---

## Phase 2 Hardening Checklist

- [x] pyproject.toml (build, ruff, mypy, pytest)
- [x] Type hints (audit_trail, audit_trail_ui, cloud_status_badge, suppression_banner, hitl_admin_view)
- [x] Unit tests (tests/test_auditshield.py)
- [x] CI workflow (.github/workflows/ci.yml)
- [x] ARCHITECTURE.md

---

## Phase 3 Forward Reference

**starguard-core** — Shared library for StarGuard Desktop and Mobile (HEDIS measures, ROI calculators, compound framework). Deferred until Phase 2 gate closes. Dependency: Phase 2 hardening complete across all three apps.
