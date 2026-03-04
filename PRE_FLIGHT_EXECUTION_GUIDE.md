# Pre-Flight & Execution Guide - Repository Reorganization

**Goal:** Move 18 files to `Artifacts/` folder, keep only README.md in root

---

## ✅ Pre-Execution Checklist

Before you run the script, verify:

| Check | How to Verify |
|-------|----------------|
| **Git installed** | Run `git --version` in PowerShell |
| **GitHub credentials ready** | Have your Personal Access Token or SSH set up |
| **Internet connection** | Script needs to clone/pull/push |
| **No pending work** | If you have local changes in auditshield-live, commit them first |

---

## 🚀 Execute Now

```powershell
# Navigate to script location
cd "c:\Users\reich\Projects\HEDIS-MA-Top-12-w-HEI-Prep\Artifacts\project\auditshield"

# Set execution policy (FIRST TIME ONLY - skip if already done)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the script
.\reorganize_github_robust.ps1
```

---

## 📊 What You'll See

### Scenario 1: No Local Repository (Fresh Clone)

```
╔════════════════════════════════════════════════════════════╗
║  AuditShield Live - Repository Reorganization Script      ║
║  Moving 18 files to Artifacts/ folder                     ║
╚════════════════════════════════════════════════════════════╝

ℹ️  Cloning repository...
✅ Repository cloned successfully
ℹ️  Pulling latest changes from GitHub...
ℹ️  Checking Git credentials...
✅ Git credentials OK (Robert Reichert <you@example.com>)
ℹ️  Creating Artifacts/ folder...
✅ Artifacts/ folder created
ℹ️  Moving files to Artifacts/...
  ✓ Moved: LICENSE
  ✓ Moved: .gitignore
  ✓ Moved: requirements.txt
  ... (continues for all 18 files)

ℹ️  Summary:
  • Files moved: 18
  • Files skipped: 0
  • Files failed: 0

ℹ️  Committing changes...
✅ Changes committed successfully
ℹ️  Pushing to GitHub...

  ⚠️  This will require GitHub authentication.
  ℹ️  Options:
     1. Personal Access Token (recommended) - use as password when prompted
     2. SSH key - if already configured, push will work automatically
     3. GitHub CLI - run 'gh auth login' first, then re-run this script

  Press Enter to continue with push, or Ctrl+C to cancel
```

**At this point:**
- Press **Enter** to continue
- Git will prompt for credentials
- Use your **Personal Access Token** as the password (not your GitHub password)

```
✅ Successfully pushed to GitHub!

═══════════════════════════════════════════════════════════
✅ Repository reorganization complete!
═══════════════════════════════════════════════════════════

ℹ️  View your repository at:
  🌐 https://github.com/reichert-science-intelligence/auditshield-live

ℹ️  New structure:
  📂 Root: README.md
  📂 Artifacts/: [18 files]

✅ Script completed!
```

### Scenario 2: Existing Local Repository Found

```
ℹ️  Using existing repository at: C:\...\auditshield-live
ℹ️  Pulling latest changes from GitHub...
ℹ️  Checking Git credentials...
✅ Git credentials OK (Robert Reichert <you@example.com>)
ℹ️  Artifacts/ folder already exists
ℹ️  Moving files to Artifacts/...
  ✓ Moved: LICENSE
  ... (continues)
```

---

## 🔐 GitHub Authentication

When the script pauses for authentication:

### Option 1: Personal Access Token (Recommended)

If you don't have one yet:

1. Open: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Settings:
   - **Note:** AuditShield CLI Access
   - **Expiration:** 90 days (or No expiration)
   - **Select scopes:** ☑️ `repo` (Full control of private repositories)
4. Click **"Generate token"**
5. **COPY THE TOKEN** (you won't see it again!)

When script prompts for password:
- **Username:** `reichert-science-intelligence`
- **Password:** Paste your token (not your GitHub password!)

### Option 2: GitHub CLI

```powershell
gh auth login
```

Follow the prompts to authenticate.

### Option 3: SSH (If already set up)

Script will work automatically.

---

## 🐛 Potential Issues & Solutions

### Issue 1: "Execution Policy" Error

```
.\reorganize_github_robust.ps1 : File cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 2: "Git not recognized"

```
git : The term 'git' is not recognized
```

**Solution:**
- Install Git: https://git-scm.com/download/win
- Restart PowerShell after installation

### Issue 3: "Authentication failed"

```
remote: Invalid username or password
```

**Solution:**
- Don't use your GitHub password
- Use a **Personal Access Token** instead
- Or run: `gh auth login`

### Issue 4: Files Already in Artifacts/

```
⏭️  Already in Artifacts: LICENSE
...
ℹ️  No files to move - nothing to commit
```

**This is normal!** It means files were already reorganized.

### Issue 5: Some Files Not Found

```
⏭️  Not found (skipping): some_file.py
```

**This is OK!** Script continues with files that exist.

### Issue 6: Git credentials not set

```
  Git user.name is not set.
  Enter your name (e.g., Robert Reichert):
```

**Solution:** Enter your name and email when prompted. The script will set them globally for future commits.

---

## ✅ Verification Steps (After Success)

1. **Check GitHub repository:**
   - Go to: https://github.com/reichert-science-intelligence/auditshield-live
   - Refresh the page
   - You should see:
     - ✅ README.md (only file in root)
     - ✅ Artifacts/ folder

2. **Click into Artifacts/ folder:**
   - Should see all 18 files

3. **Check README displays properly:**
   - Scroll down on main page
   - README should render nicely with your demo link

---

## 📸 Expected Final View on GitHub

**Root Directory:**
```
auditshield-live/
  📄 README.md
  📁 Artifacts/
```

**Inside Artifacts/ folder:**
```
Artifacts/
  📄 LICENSE
  📄 .gitignore
  📄 requirements.txt
  📄 GITHUB_UPLOAD_GUIDE.md
  📄 PHASE_1_COMPLETE.md
  📄 PHASE_2_COMPLETE.md
  📄 PHASE_3_COMPLETE.md
  📄 PHASE_4_COMPLETE.md
  📄 DEPLOYMENT_GUIDE.md
  🐍 synthetic_chart_generator.py
  🐍 ncqa_specification_builder.py
  🐍 validation_engine.py
  🐍 layer1_document_intelligence.py
  🐍 layer3_self_correction.py
  🐍 compound_pipeline.py
  🐍 agentic_rag_coordinator.py
  ⚛️ AuditShieldMobile.jsx
  🌐 AuditShieldLive_Demo.html
```

---

## 🎯 You're Ready - Execute the Script!

Run these commands in PowerShell:

```powershell
cd "c:\Users\reich\Projects\HEDIS-MA-Top-12-w-HEI-Prep\Artifacts\project\auditshield"
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser  # first time only
.\reorganize_github_robust.ps1
```

Then:
1. Follow the prompts
2. Have your GitHub token ready
3. Watch for the success message
