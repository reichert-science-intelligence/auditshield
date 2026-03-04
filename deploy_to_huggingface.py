#!/usr/bin/env python3
"""Deployment preparation script for HuggingFace Spaces - StarGuard integration."""
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
WWW_DIR = APP_DIR / "Artifacts" / "www"

REQUIRED_FILES = [
    "starguard_about.html",
    "starguard_services.html",
    "auditshield_services.html",
]


def main():
    print("=" * 60)
    print("HuggingFace Deployment Preparation")
    print("=" * 60)

    errors = []
    warnings = []

    # 1. Verify www/
    if not WWW_DIR.is_dir():
        errors.append("www/ directory not found")
    else:
        print("[OK] Artifacts/www/ directory exists")

    # 2. Check file sizes
    for name in REQUIRED_FILES:
        p = WWW_DIR / name
        if not p.exists():
            errors.append(f"Missing: {name}")
        else:
            size = p.stat().st_size
            print(f"[OK] {name}: {size:,} bytes")
            if name == "starguard_about.html" and size < 100_000:
                warnings.append(f"starguard_about.html is {size:,} bytes (guide recommends >100KB for embedded avatar)")

    # 3. Validate HTML structure
    for name in REQUIRED_FILES:
        p = WWW_DIR / name
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            if "<!DOCTYPE html>" not in text and "<html" not in text.lower():
                errors.append(f"{name}: Invalid HTML structure")
            else:
                print(f"[OK] {name}: Valid HTML")

    # 4. Deployment checklist
    print("\n" + "-" * 60)
    print("Deployment Checklist")
    print("-" * 60)
    checklist = [
        ("Artifacts/www/ with 3 HTML files", WWW_DIR.is_dir() and all((WWW_DIR / f).exists() for f in REQUIRED_FILES)),
        ("app.py has static_assets", "static_assets" in (APP_DIR / "app.py").read_text()),
        ("app.py has Resources menu", "Resources" in (APP_DIR / "app.py").read_text()),
        ("app.py has create_footer", "create_footer" in (APP_DIR / "app.py").read_text()),
    ]
    for desc, ok in checklist:
        status = "[OK]" if ok else "[--]"
        print(f"  {status} {desc}")

    # 5. Git commands
    print("\n" + "-" * 60)
    print("Suggested Git Commands")
    print("-" * 60)
    print("""
  git add Artifacts/www/
  git add app.py
  git add test_quick_check.py
  git add tests/test_integration.py
  git add deploy_to_huggingface.py
  git status
  git commit -m "Add StarGuard About & Services static pages integration"
  git push
""")

    # Warnings
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    # Final status
    print("\n" + "=" * 60)
    if errors:
        print("FAILED - fix errors before deploying:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("Ready for deployment (address warnings if applicable).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
