#!/usr/bin/env python3
"""Quick validation script for StarGuard About & Services integration."""
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
WWW_DIR = APP_DIR / "Artifacts" / "www"

REQUIRED_FILES = [
    "starguard_about.html",
    "starguard_services.html",
    "auditshield_services.html",
]

# Note: Guide expects starguard_about.html >100KB with embedded avatar.
# Your source file may be smaller (~44KB); adjust MIN_ABOUT_SIZE if needed.
MIN_ABOUT_SIZE = 100_000  # 100KB minimum (embedded avatar)


def main():
    print("=" * 50)
    print("StarGuard Integration Quick Check")
    print("=" * 50)

    errors = []

    # 1. www/ exists
    if not WWW_DIR.is_dir():
        errors.append(f"www/ directory not found at {WWW_DIR}")
    else:
        print("OK: Artifacts/www/ directory exists")

    # 2. All 3 HTML files present
    for name in REQUIRED_FILES:
        p = WWW_DIR / name
        if not p.exists():
            errors.append(f"Missing: {name}")
        else:
            size = p.stat().st_size
            print(f"OK: {name} ({size:,} bytes)")

    # 3. starguard_about.html size
    about_path = WWW_DIR / "starguard_about.html"
    if about_path.exists():
        size = about_path.stat().st_size
        if size < MIN_ABOUT_SIZE:
            errors.append(f"starguard_about.html is {size:,} bytes (expected >{MIN_ABOUT_SIZE:,})")
        else:
            print("OK: starguard_about.html size check passed")

    # 4. HTML structure
    for name in REQUIRED_FILES:
        p = WWW_DIR / name
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            if "<!DOCTYPE html>" not in text and "<html" not in text.lower():
                errors.append(f"{name}: Invalid HTML (missing doctype/html tag)")
            else:
                print(f"OK: {name} has valid HTML structure")

    # 5. Data disclaimer
    for name in REQUIRED_FILES:
        p = WWW_DIR / name
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            if "synthetic" not in text.lower():
                errors.append(f"{name}: Missing 'synthetic' disclaimer")
            else:
                print(f"OK: {name} contains data disclaimer")

    print("=" * 50)
    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    exit(main())
