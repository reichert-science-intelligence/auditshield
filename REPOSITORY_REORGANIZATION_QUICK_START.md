# Quick Start Guide - Repository Reorganization

**Goal:** Move 18 files to `Artifacts/` folder, keep only README.md in root

---

## 🎯 Which Method Should You Use?

### **You're on Windows** → Use PowerShell Script

**File:** `reorganize_github_robust.ps1`

**Steps:**
1. Open PowerShell (Right-click Start → Windows PowerShell)
2. Navigate to where you downloaded the script:
   ```powershell
   cd C:\Users\YourName\Downloads
   ```
3. Allow script execution (first time only):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
4. Run the script:
   ```powershell
   .\reorganize_github_robust.ps1
   ```

---

### **You're on Mac/Linux** → Use Bash Script

**File:** `reorganize_github_robust.sh`

**Steps:**
1. Open Terminal
2. Navigate to where you downloaded the script:
   ```bash
   cd ~/Downloads
   ```
3. Make it executable:
   ```bash
   chmod +x reorganize_github_robust.sh
   ```
4. Run it:
   ```bash
   ./reorganize_github_robust.sh
   ```

---

### **You Have Git Bash on Windows** → Use Bash Script

**File:** `reorganize_github_robust.sh`

**Steps:**
1. Open Git Bash
2. Navigate to script location:
   ```bash
   cd /c/Users/YourName/Downloads
   ```
3. Make executable and run:
   ```bash
   chmod +x reorganize_github_robust.sh
   ./reorganize_github_robust.sh
   ```

---

## ⚡ What the Script Does

**The script will:**
1. ✅ Check if you're already in the repository (smart detection)
2. ✅ Clone fresh if needed OR use existing workspace
3. ✅ Create `Artifacts/` folder
4. ✅ Check each file exists before moving (no crashes)
5. ✅ Move 18 files to `Artifacts/`
6. ✅ Skip files already in `Artifacts/` (safe to re-run)
7. ✅ Commit changes with professional message
8. ✅ Guide you through GitHub authentication
9. ✅ Push to GitHub automatically

**Error handling:**
- Won't crash if files are missing
- Won't crash if Artifacts/ already exists
- Won't crash if files already moved
- Clear error messages if push fails
- Safe to run multiple times

---

## 🔐 GitHub Authentication

The script will pause before pushing and ask you to authenticate.

**You have 3 options:**

### Option 1: Personal Access Token (Recommended)
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "AuditShield CLI Access"
4. Check: ☑️ `repo` (Full control of private repositories)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)
7. When git asks for password, paste the token

### Option 2: GitHub CLI (Easiest if you have it)
```bash
gh auth login
```
Follow the prompts to authenticate.

### Option 3: SSH Key (If already set up)
If you've set up SSH keys, the script will work automatically.

---

## 📊 Expected Output

```
╔════════════════════════════════════════════════════════════╗
║  AuditShield Live - Repository Reorganization Script      ║
║  Moving 18 files to Artifacts/ folder                     ║
╚════════════════════════════════════════════════════════════╝

ℹ️  Cloning repository...
✅ Repository cloned successfully
ℹ️  Pulling latest changes from GitHub...
ℹ️  Creating Artifacts/ folder...
✅ Artifacts/ folder created
ℹ️  Moving files to Artifacts/...
  ✓ Moved: LICENSE
  ✓ Moved: .gitignore
  ✓ Moved: requirements.txt
  ... (15 more files)

ℹ️  Summary:
  • Files moved: 18
  • Files skipped: 0
  • Files failed: 0

ℹ️  Committing changes...
✅ Changes committed successfully
ℹ️  Pushing to GitHub...
✅ Successfully pushed to GitHub!

═══════════════════════════════════════════════════════════
✅ Repository reorganization complete!
═══════════════════════════════════════════════════════════

ℹ️  View your repository at:
  🌐 https://github.com/reichert-science-intelligence/auditshield-live

ℹ️  New structure:
  📂 Root:
    └── README.md
  📂 Artifacts/:
    └── [18 files]
```

---

## 🐛 Troubleshooting

### "Execution Policy" error (Windows PowerShell)
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Permission denied" error (Mac/Linux)
**Solution:**
```bash
chmod +x reorganize_github_robust.sh
```

### "Authentication failed" when pushing
**Solutions:**
1. Generate Personal Access Token (see above)
2. Or run: `gh auth login`
3. Or set up SSH key

### "File not found" warnings
**This is OK!** The script will skip missing files and continue.

### Script exits early
**Check the error message.** Common issues:
- Not in a git repository (script will clone fresh)
- No internet connection (can't clone or push)
- Git not installed (install Git first)

---

## ✅ Verification

After script completes, verify it worked:

1. Go to: https://github.com/reichert-science-intelligence/auditshield-live
2. You should see:
   - ✅ README.md in root (only file visible)
   - ✅ Artifacts/ folder
3. Click Artifacts/ to see all 18 files inside

---

## 🔄 Safe to Re-Run

**The script is idempotent** - safe to run multiple times:
- If files already in Artifacts/, it skips them
- If Artifacts/ exists, it uses the existing folder
- If nothing to move, it exits gracefully

---

## 💡 Quick Decision Tree

```
Do you have Git installed?
├─ Yes → Continue below
└─ No → Install Git first: https://git-scm.com/downloads

What operating system?
├─ Windows → Use reorganize_github_robust.ps1 (PowerShell)
├─ Mac → Use reorganize_github_robust.sh (Bash)
└─ Linux → Use reorganize_github_robust.sh (Bash)

Do you have the repository locally?
├─ Yes → Script will detect and use it
└─ No → Script will clone fresh copy

Are you authenticated with GitHub?
├─ Yes → Script will push automatically
└─ No → Script will guide you through authentication
```

---

## 🚀 Just Run It!

**Windows:**
```powershell
.\reorganize_github_robust.ps1
```

**Mac/Linux:**
```bash
./reorganize_github_robust.sh
```

**That's it!** The script handles everything else.

---

## 📞 Still Need Help?

**Common commands to check your setup:**

```bash
# Check if Git is installed
git --version

# Check if you're in a Git repository
git status

# Check your GitHub authentication
git config user.name
git config user.email

# Check remote URL
git remote -v
```

---

**Ready? Pick your script above and run it!** 🎯
