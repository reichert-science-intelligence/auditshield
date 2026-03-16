# Cursor Rules Install — Master Reference

**Location:** Artifacts/project/auditshield/ (canonical governance folder)  
**Purpose:** Install `.cursorrules` into each portfolio app repo via Cursor.

---

## 3-Step Install Workflow (per app)

| Step | Action |
|------|--------|
| 1 | Drop the app's `.md` source file into that app's repo root in Cursor |
| 2 | Open the file in the Cursor editor so it's in context |
| 3 | Paste the **Install Prompt** below into Cursor chat |

---

## Install Prompt (same for all five apps)

```
Read this file and create a `.cursorrules` file in the root of this project using exactly the content under the ## Rules section below. Do not modify any content. Confirm when complete.
```

---

## Verification Checklist

After each install:

1. Open a **new** Cursor chat in that project
2. Type: **"What are your active rules?"**
3. Cursor should respond with:
   - The **Effort Evaluation rule** (HIGH/MED/LOW signal table)
   - **App-specific context** (repo layout, Shiny modules, URLs)

If Cursor returns the Effort Evaluation table and app context, the rules are loaded correctly.

---

## File Map

| Source file | Target repo | Demo URL | GitHub |
|------------|-------------|----------|--------|
| `CURSORRULES-AUDITSHIELD-LIVE.md` | auditshield | rreichert-auditshield-live.hf.space | reichert-science-intelligence/auditshield |
| `CURSORRULES-STARGUARD-DESKTOP.md` | starguard-desktop | rreichert-starguard-desktop.hf.space | reichert-science-intelligence/starguard-desktop |
| `CURSORRULES-STARGUARD-MOBILE.md` | starguard-mobile | rreichert-starguardai.hf.space | reichert-science-intelligence/starguard-mobile |
| `CURSORRULES-SOVEREIGNSHIELD-DESKTOP.md` | sovereignshield | — | reichert-science-intelligence/sovereignshield |
| `CURSORRULES-SOVEREIGNSHIELD-MOBILE.md` | sovereignshield-mobile | — | reichert-science-intelligence/sovereignshield-mobile |

Each source file maps to `.cursorrules` at the **root** of its target repo.

---

## Five Apps

| App | Source file | .cursorrules target |
|-----|-------------|---------------------|
| AuditShield Live | CURSORRULES-AUDITSHIELD-LIVE.md | auditshield repo root |
| StarGuard Desktop | CURSORRULES-STARGUARD-DESKTOP.md | starguard-desktop repo root |
| StarGuard Mobile | CURSORRULES-STARGUARD-MOBILE.md | starguard-mobile repo root |
| SovereignShield Desktop | CURSORRULES-SOVEREIGNSHIELD-DESKTOP.md | sovereignshield repo root |
| SovereignShield Mobile | CURSORRULES-SOVEREIGNSHIELD-MOBILE.md | sovereignshield-mobile repo root |
