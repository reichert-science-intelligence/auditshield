# Effort Recommendation Engine — Deploy Status

Permanent reference for the prompt-level recommendation engine deployment across all portfolio apps.

---

## Summary

The system reads every prompt and actively recommends level alignment: *"You should be at MED, not LOW"* or *"This is HIGH territory, escalate."* Logic is baked into `.cursorrules` and `claude-custom-instructions.md`, with an interactive widget for live testing.

---

## Four Behaviors

| Scenario | Claude output |
|----------|----------------|
| User prefix **[LOW]**, prompt is UI-only | Silent — levels match, proceed |
| User prefix **[LOW]**, prompt has MED signals | Header: *"You should be at MED, not LOW."* → proceed or offer escalate |
| User prefix **[LOW]**, prompt has HIGH signals | Header: *"You sent LOW, this reads as HIGH — consider escalating for safety."* → proceed or offer y/escalate |
| User prefix **[HIGH]**, prompt is trivial (e.g. color change) | Header: *"Downgrade to LOW recommended — saves tokens"* → then proceed |
| **No prefix** | State detected level and proceed — no waiting |

The recommendation fires on the first read of every prompt, before any code is written.

---

## Signal Table (Domain-Specific)

| Level | Signals (keywords/phrases) |
|-------|----------------------------|
| **HIGH** | SQL, schema, migrate, RLS, auth, OPA, Rego, Terraform, Supabase, batch remediation, HuggingFace, reactive chain, @reactive, credentials, API key, token, policy engine, compliance rule, audit trail, gap trail |
| **MED** | refactor, new module, pyproject, dependency, test suite, CI/CD, workflow |
| **LOW** | CSS, color, font, padding, margin, layout, style, button, modal, UI-only, copy change, typos |

---

## Files

| File | Purpose |
|------|---------|
| `Artifacts/project/auditshield/.cursorrules` | Source rules (includes engine at top); synced to all apps |
| `Artifacts/project/auditshield/claude-custom-instructions.md` | Copy into Claude.ai → Settings → Profile → Personal Preferences |
| `Artifacts/project/auditshield/prompt-level-widget.html` | Interactive widget — paste prompt, set prefix, run to see recommendation |
| `Artifacts/project/auditshield/sync-cursorrules.ps1` | Syncs `.cursorrules` + `Phase2-to-Hardening-Sprint-Checklist.md` to all apps |

---

## Deploy Sequence (Completed)

1. ✅ Engine baked into `auditshield/.cursorrules` (runs first on every prompt)
2. ✅ `claude-custom-instructions.md` created — copy to Claude.ai for every-chat coverage
3. ✅ Interactive widget built — `prompt-level-widget.html` with live recommendation logic
4. ✅ `sync-cursorrules.ps1` run — starguard-desktop, starguard-mobile, sovereignshield updated

---

## Open Gate (Final Step Before Phase 3 / starguard-core)

| Step | Status |
|------|--------|
| Upload `.cursorrules` + `Phase2-to-Hardening-Sprint-Checklist.md` + 3× `ARCHITECTURE.md` to the **reichert-science-intelligence** Claude Project knowledge base | ⏳ Pending |

This closes the loop. Everything else in the checklist is deployable today. That one step unlocks Phase 3 / starguard-core.

**3× ARCHITECTURE.md:** auditshield, starguard-desktop, starguard-mobile.

---

## Suggested Git Commit

```bash
git add .cursorrules */.cursorrules EFFORT-ENGINE-STATUS.md claude-custom-instructions.md prompt-level-widget.html sync-cursorrules.ps1
git commit -m "chore: deploy effort recommendation engine across all five apps"
```

Run from `Artifacts/project/auditshield/` or adjust paths for repo root.
