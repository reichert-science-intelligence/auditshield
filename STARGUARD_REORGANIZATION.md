# 🚀 StarGuard Repository Reorganization Guide

**Status:** ✅ Scripts ready to execute  
**Date:** March 2026  
**Location:** `c:\Users\reich\Projects\HEDIS-MA-Top-12-w-HEI-Prep\Artifacts\project\auditshield`

---

## ✅ What's Ready

Same cleanup process you used for **AuditShield Live** — applied to StarGuard Desktop and Mobile.

| Script | Repository | Files to Move |
|--------|------------|---------------|
| `reorganize_starguard_desktop.ps1` | starguard-desktop | 200+ (all except README.md) |
| `reorganize_starguard_mobile.ps1` | starguard-mobile | ~15 (all except README.md) |

**Reusable v2 script:** `reorganize_github_robust_v2.ps1` — parameterized for any repo.

---

## 🎯 Execute — Three Commands Per Repo

### StarGuard Desktop (200+ files)

```powershell
cd "c:\Users\reich\Projects\HEDIS-MA-Top-12-w-HEI-Prep\Artifacts\project\auditshield"
.\reorganize_starguard_desktop.ps1
```

### StarGuard Mobile (~15 files)

```powershell
cd "c:\Users\reich\Projects\HEDIS-MA-Top-12-w-HEI-Prep\Artifacts\project\auditshield"
.\reorganize_starguard_mobile.ps1
```

---

## 📊 Execution Flow (Same as AuditShield)

1. **Script checks/clones** starguard-desktop or starguard-mobile from GitHub
2. **Git credentials** — prompts if not set
3. **Creates Artifacts/** folder
4. **Moves all files** except README.md into Artifacts/
5. **Commits** with message: "Organize repository: Move N files to Artifacts folder"
6. **Pauses** — "Press Enter to continue with push..."
7. **Push** — you authenticate with Personal Access Token

---

## 🔐 GitHub Token (Same as AuditShield)

1. **Go to:** https://github.com/settings/tokens  
2. **Generate new token (classic)**  
   - Scopes: ☑️ `repo`  
3. **When prompted:**
   - Username: `reichert-science-intelligence`  
   - Password: **Paste your token**  

---

## ✅ Verification Checklist

**After each script completes:**

- [ ] Root shows only **README.md**
- [ ] **Artifacts/** folder contains all other files
- [ ] README renders with demo/portfolio links
- [ ] Repository description and topics updated on GitHub
- [ ] Pin repository on profile (if top 6)

---

## 📁 Where Scripts Live

```
Artifacts/project/auditshield/
├── reorganize_github_robust.ps1      # Original (AuditShield)
├── reorganize_github_robust_v2.ps1  # Parameterized for any repo
├── reorganize_starguard_desktop.ps1 # StarGuard Desktop
├── reorganize_starguard_mobile.ps1  # StarGuard Mobile
├── STARGUARD_REORGANIZATION.md      # This guide
└── READY_TO_EXECUTE.md              # AuditShield guide
```

---

## 🔄 Using v2 for Other Repos

```powershell
& ".\reorganize_github_robust_v2.ps1" `
  -RepoUrl "https://github.com/reichert-science-intelligence/YOUR-REPO.git" `
  -RepoName "YOUR-REPO" `
  -MoveAllExceptReadme:$true
```

Or edit the param defaults in `reorganize_github_robust_v2.ps1` and run it directly.

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| **Clone fails** | Verify repo exists: https://github.com/reichert-science-intelligence/starguard-desktop |
| **Push: Invalid credentials** | Use Personal Access Token, not GitHub password |
| **Script won't run** | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| **"No files to move"** | Repo may already be reorganized — verify on GitHub |

---

## 📅 Suggested Schedule (Before LinkedIn Launch)

| Day | Task |
|-----|------|
| **Monday** | Run `reorganize_starguard_desktop.ps1` (~15 min) |
| **Tuesday** | Run `reorganize_starguard_mobile.ps1` (~10 min) |
| **Wednesday** | Verify all 3 repos (AuditShield ✅, Desktop, Mobile) |
| **Thursday** | Update GitHub profile, pin top 6 repositories |
| **Friday** | LinkedIn launch with all 3 projects featured |

---

## 🎯 Final Result

**Your pinned repositories:**

- ⭐ AuditShield Live ✅
- ⭐ StarGuard Desktop ⏳
- ⭐ StarGuard Mobile ⏳

All with: **clean root (README only)**, professional organization, live demo links.

**GO EXECUTE!** 🚀
