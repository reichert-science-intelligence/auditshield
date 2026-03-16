# AuditShield-Live — Architecture

## Purpose

AuditShield-Live is an AI-powered Medicare Advantage RADV Audit Defense Platform. It provides integrated modules for provider scorecards, mock audits, financial impact analysis, RADV command center, chart selection AI, education automation, real-time validation, HCC reconciliation, compliance forecasting, regulatory intelligence, EMR rules, and executive dashboards. Phase 2 adds active suppression (audit-level), HITL Admin View, and hardening artifacts.

---

## Design Decisions

**starguard-core** — Shared library introduced to consolidate audit trail logic (AuditShield), HEDIS gap logic (Desktop/Mobile), and HCC suppression across all three apps. Single source of truth for `write_audit_trail`, `get_suppressed_hccs`, and gap CRUD reduces duplication and enables consistent behavior.

---

## Component Map (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AuditShield-Live (Shiny App)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  app.py (main)                                                               │
│    ├── app_complete.py (HuggingFace entry, uvicorn)                          │
│    ├── starguard_core.audit.trail ──► Google Sheets + Supabase               │
│    │   logic/ audit_trail.py deleted                                         │
│    │   └── .audit_suppressions.json (Phase 2)                                │
│    ├── audit_trail_ui.py                                                     │
│    ├── cloud_status_badge.py                                                 │
│    ├── suppression_banner.py (Phase 2)                                       │
│    ├── hitl_admin_view.py (Phase 2)                                          │
│    ├── meat_validator.py, radv_command_center.py                             │
│    ├── chart_selection_ai.py, education_automation.py                        │
│    ├── realtime_validation.py, hcc_reconciliation.py                         │
│    ├── compliance_forecasting.py, regulatory_intelligence.py                  │
│    ├── emr_rule_builder.py, dashboard_manager.py                             │
│    └── database.py, financial_calculator.py, mock_audit_simulator.py          │
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
         ├──► starguard_core.audit.trail.write_audit_trail() → Google Sheets + Supabase
         ├──► starguard_core.audit.trail.fetch_recent_audits() → DataFrame
         ├──► starguard_core.audit.trail.get_suppressed_hccs() → .audit_suppressions.json
         ├──► add/remove_audit_suppression() → JSON CRUD
         └──► database, MEATValidator, etc. → SQLite / Supabase
```

---

## Supabase Schema

| Table | Purpose |
|------|---------|
| `audit_trail` | Parallel write from audit_trail.py; mirrors Google Sheets RADV audit records |

Primary persistence: Google Sheets. Supabase used for parallel write when `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set.

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

## 4. starguard-core Import Chain

| starguard_core module | Replaces |
|----------------------|----------|
| `starguard_core.audit.trail` | `audit_trail.py` |

**Install:** `pip install starguard-core` (or `pip install -e path/to/starguard-core` for local dev)

**Usage:**
```python
from starguard_core.audit.trail import write_audit_trail, get_suppressed_hccs, fetch_recent_audits
```

---

## Supabase Schema

| Table | Purpose |
|-------|---------|
| `audit_trail` | Parallel write from starguard_core.audit.trail; mirrors Google Sheets RADV audit records |

Google Sheets is source of truth; Supabase receives fire-and-forget parallel writes when `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set.

---

## Mobile Architecture (Sprint 1–4)

### Breakpoint Token Table

| Token | Width | Layout |
|-------|-------|--------|
| Phone | &lt; 768px | Hamburger nav, FAB, sidebar drawer, KPI strip, collapsible cards |
| Tablet | 768–1024px | Hybrid tabs + sidebars |
| Desktop | ≥ 1024px | Full layout, zero-touch |

### File Structure

| Path | Purpose |
|------|---------|
| `Artifacts/www/mobile.css` | Consolidated 16-section CSS, `--brand-*` vars, dark mode |
| `ui/nav_mobile.py` | Hamburger, overlay, FAB shell (FAB click → fab_wiring) |
| `ui/fab_wiring.py` | FAB: Shiny tab switch, sidebar close, scroll-top, gold pulse |
| `ui/mobile/` | Sprint 2 components (KPI strip, cards, stepper, HEDIS table, RAG) |

### Component Responsibility Matrix

| Component | Hamburger | Overlay | FAB | Tab Switch | Sidebar Close |
|-----------|-----------|---------|-----|------------|---------------|
| nav_mobile | ✓ | ✓ | ✓ (shell) | — | ✓ (overlay click) |
| fab_wiring | — | — | ✓ (click handler) | ✓ | ✓ |

### iOS Quirks

- Inputs forced to `font-size: 16px` to block Safari zoom on focus.
- RAG prompt panel and all form inputs inherit this.

### FAB Dual-Mechanism

FAB uses **Shiny.setInputValue()** (server) plus **bootstrap.Tab.show()** (DOM) so both reactive state and Bootstrap tab visibility stay in sync. Gold pulse on Run Audit button draws attention after tab switch.

### CSS Architecture

- `--brand-*` variables for colors; dark mode overrides in one block at bottom.
- Stepper dots: 44px touch via `padding: 17px` + `background-clip: content-box` (10px visual).
- `clamp()` for fluid typography.

### Sprint History

| Sprint | Deliverables |
|--------|--------------|
| 1 | mobile.css (11 sections), nav_mobile (hamburger, overlay, FAB) |
| 2 | ui/mobile: KPI strip, collapsible cards, stepper, HEDIS table, RAG panels |
| 3 | Consolidated mobile.css (16 sections, brand vars, dark mode), fab_wiring, Sprint 2 cleanup |
| 4 | tests/test_mobile.py (Playwright), CI mobile-tests job, README badge, ARCHITECTURE mobile |

---

## Mobile Experience (Sprint 1–4)

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Phone | < 768px | Hamburger nav, FAB, sidebar drawer, KPI strip, collapsible cards |
| Tablet | 768–1024px | Hybrid; sidebar drawer on narrow tablet |
| Desktop | ≥ 1024px | Full layout, zero-touch |

**File structure:**
- `Artifacts/www/mobile.css` — consolidated 16-section CSS, `--brand-*` vars, dark mode
- `ui/nav_mobile.py` — hamburger, overlay, FAB shell (FAB click wired by fab_wiring)
- `ui/fab_wiring.py` — Shiny tab switch, sidebar close, scroll-to-top, gold pulse on Run Audit
- `ui/mobile/` — Sprint 2 layout components (KPI strip, collapsible cards, stepper, HEDIS table, RAG)

**Component responsibility:** nav_mobile renders FAB; fab_wiring attaches click handler (Shiny.setInputValue + bootstrap.Tab.show). Dual mechanism keeps server and DOM in sync.

**iOS quirks:** Inputs forced to 16px to block Safari zoom. Stepper dots use `padding: 17px` + `background-clip: content-box` for 44px tap area with 10px visual.

**Tests:** `tests/test_mobile.py` — Playwright, 11 classes, 40+ tests across 375×812, 768×1024, 1280×900. Skip-aware. CI: `TEST_BASE_URL` secret for live HF Space; otherwise app starts locally.

| Sprint | Deliverable |
|--------|-------------|
| 1 | mobile.css, nav_mobile, sidebar drawer, FAB scaffold |
| 2 | ui/mobile/ (KPI strip, cards, stepper, table, RAG) |
| 3 | Consolidated CSS, fab_wiring, clamp typography, stepper touch |
| 4 | Playwright suite, CI badge, ARCHITECTURE docs |

---

## Mobile Experience (Sprint 1–4)

### Breakpoint Token Table

| Token | Width | Layout |
|-------|-------|--------|
| Phone | &lt; 768px | Hamburger nav, FAB, sidebar drawer, horizontal KPI strip, collapsible cards |
| Tablet | 768–1024px | Hybrid; sidebar drawer on narrow tablet |
| Desktop | ≥ 1024px | Full sidebar, zero-touch layout |

### File Structure

| Path | Responsibility |
|------|----------------|
| `Artifacts/www/mobile.css` | Consolidated 16-section CSS; --brand-* vars; dark mode |
| `ui/nav_mobile.py` | Hamburger, overlay, FAB (delegates to fab_wiring) |
| `ui/fab_wiring.py` | FAB tab switch: Shiny.setInputValue + bootstrap.Tab.show + gold pulse |
| `ui/mobile/` | KPI strip, collapsible cards, stepper, HEDIS table, RAG panels |

### Component Responsibility Matrix

| Component | Sprint | Role |
|-----------|--------|------|
| mobile.css | 1–3 | Breakpoints, sidebar drawer, touch targets, iOS zoom block |
| nav_mobile | 1 | Hamburger (X animation), overlay, FAB shell |
| fab_wiring | 3 | FAB click: tab switch, sidebar close, scroll, gold pulse on Run Audit |
| mobile_kpi_strip | 2 | Horizontal scroll KPI strip |
| mobile_dashboard_card | 2 | Collapsible chart cards |
| mobile_audit_stepper | 2 | One-step-at-a-time with Prev/Next, dots (44px touch via padding+content-box) |
| mobile_hedis_table | 2 | Horizontal scroll, sticky cols, filter toggle |
| rag_*_mobile | 2 | Source accordion, 16px prompt, response panel |

### iOS Quirks

- **Zoom on focus**: Inputs use `font-size: 16px` to block iOS Safari auto-zoom.
- **Touch targets**: 44px minimum via `--touch-min`; stepper dots use `padding: 17px` + `background-clip: content-box`.

### Dual-Mechanism FAB Tab Switch

FAB uses both **Shiny.setInputValue()** (server state) and **bootstrap.Tab.show()** (DOM) for reliable tab switch across server round-trips. Sidebar closes, scroll-to-top, then gold pulse on Run Audit button.

### CSS Architecture

- `--brand-*` variables throughout for consistency and dark mode override.
- Dark mode: single `@media (prefers-color-scheme: dark)` block at bottom overrides `--surface`, `--text`, etc.

### Sprint History

| Sprint | Deliverables |
|--------|--------------|
| 1 | mobile.css, nav_mobile.py, hamburger/FAB scaffold |
| 2 | ui/mobile/ (KPI strip, cards, stepper, table, RAG), SPRINT2_INTEGRATION |
| 3 | Consolidated mobile.css (16 sections), fab_wiring.py, stepper dot touch |
| 4 | tests/test_mobile.py (Playwright), CI mobile-tests job, README badge, ARCHITECTURE |

---

## Phase 2 Hardening Checklist

- [x] pyproject.toml (build, ruff, mypy, pytest)
- [x] Type hints (audit_trail, cloud_status_badge, suppression_banner, hitl_admin_view)
- [x] Unit tests (tests/test_auditshield.py) — 17 tests — 17 tests
- [x] CI workflow (.github/workflows/ci.yml) — strict mode
- [x] ARCHITECTURE.md
- [x] starguard-core import chain

---

## Phase 3 Complete

**starguard-core** — Shared library integrated. AuditShield consumes `starguard_core.audit.trail` for write_audit_trail, get_suppressed_hccs, fetch_recent_audits. `audit_trail.py` deleted.

---

## Mobile Experience (Sprints 1–4)

### Breakpoint Token Table

| Token | Width | Layout |
|-------|-------|--------|
| Phone | < 768px | Hamburger nav, FAB, sidebar drawer, horizontal KPI strip, collapsible cards |
| Tablet | 768–1024px | Hybrid; sidebar drawer on narrow tablet |
| Desktop | ≥ 1024px | Full sidebar, zero-touch layout |

### File Structure

| Path | Responsibility |
|------|----------------|
| `Artifacts/www/mobile.css` | Consolidated 16-section mobile CSS, `--brand-*` vars, dark mode |
| `ui/nav_mobile.py` | Hamburger, overlay, FAB container (FAB logic in fab_wiring) |
| `ui/fab_wiring.py` | FAB → Shiny tab switch, sidebar close, scroll, gold pulse |
| `ui/mobile/dashboard_mobile.py` | KPI strip, collapsible dashboard cards |
| `ui/mobile/rag_mobile.py` | Source accordion, prompt panel (16px input), response panel |
| `ui/mobile/audit_stepper_mobile.py` | One-step-at-a-time stepper, progress bar, dots |
| `ui/mobile/hedis_table_mobile.py` | Table scroll, sticky cols, filter toggle |
| `tests/test_mobile.py` | Playwright suite (11 classes, 40+ tests, 3 viewports) |

### Component Responsibility Matrix

| Component | Hamburger | Overlay | FAB | Tab Switch | Stepper Dots |
|-----------|-----------|---------|-----|------------|--------------|
| nav_mobile | ✓ | ✓ | renders | — | — |
| fab_wiring | — | — | wires | ✓ | — |
| mobile.css | styles | styles | styles | — | 44px touch |

### iOS Quirks

- **Zoom on focus**: Inputs use `font-size: 16px` to block iOS Safari auto-zoom.
- **Touch targets**: Minimum 44px; stepper dots use `padding: 17px` + `background-clip: content-box` for 10px visual, 44px tap area.

### FAB Tab Switch (Dual Mechanism)

1. **Server**: `Shiny.setInputValue("main_nav", "Mock Audit", { priority: "event" })` — syncs Shiny reactive state.
2. **DOM**: `bootstrap.Tab.show(tabEl)` — ensures Bootstrap tab panel is visible.
3. **Post-action**: Sidebar close, scroll-to-top, gold pulse on Run Audit button.

### CSS Architecture

- **Variables**: `--brand-primary`, `--brand-accent`, `--brand-gold`, `--touch-min`, etc.
- **Dark mode**: Single block at bottom, overrides `--surface`, `--text`, etc. when `prefers-color-scheme: dark`.
- **Desktop zero-touch**: All mobile-specific rules scoped to `@media (max-width: 767px)`.

### Sprint History

| Sprint | Deliverables |
|--------|--------------|
| 1 | mobile.css (11 sections), nav_mobile.py, hamburger + overlay + FAB scaffold |
| 2 | ui/mobile/ (KPI strip, dashboard cards, RAG panels, audit stepper, HEDIS table) |
| 3 | Consolidated mobile.css (16 sections, brand vars, dark mode), fab_wiring.py, stepper dot touch target |
| 4 | tests/test_mobile.py, CI mobile-tests job, README badge, ARCHITECTURE section |

---

## Rollback Procedure

**Revert → push → auto-redeploy.** No manual HuggingFace intervention needed in the normal case.

1. `git revert <commit>` (or `git revert HEAD` for last commit)
2. `git push origin main`
3. CI runs tests; deploy job syncs to HuggingFace Space
4. Space rebuilds from updated repo

If deploy fails, add `HF_TOKEN` secret (Settings → Secrets) with write access to the Space. One token covers all three repos.

---

## Rollback Procedure

If a bad deploy reaches production:

1. **Revert** the commit: `git revert HEAD --no-edit`
2. **Push** to main: `git push origin main`
3. **Auto-redeploy** — GitHub Actions deploy job runs on push; HuggingFace Space rebuilds from the reverted commit.

No manual HuggingFace intervention needed in the normal case. If the Space is connected via GitHub integration, the push alone triggers rebuild.

---

*Phase 3 Complete*

---

## Rollback Procedure

If a deploy introduces issues:

1. **Revert** the offending commit: `git revert <commit-hash>`
2. **Push** to main: `git push origin main`
3. **Auto-redeploy** — the deploy workflow runs on push; HuggingFace Space rebuilds from the reverted code.

No manual HuggingFace intervention needed in the normal case. If the Space is connected via GitHub integration, the push itself triggers rebuild.
