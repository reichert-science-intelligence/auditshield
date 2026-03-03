#!/usr/bin/env python3
"""Patch starguard_about.html with full base64 avatar from avatar_base64.txt"""
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
AVATAR_TXT = APP_DIR / "avatar_base64.txt"
HTML_FILE = APP_DIR / "www" / "starguard_about.html"


def main():
    if not AVATAR_TXT.exists():
        print("ERROR: avatar_base64.txt not found")
        return 1
    if not HTML_FILE.exists():
        print("ERROR: www/starguard_about.html not found")
        return 1

    avatar_b64 = AVATAR_TXT.read_text(encoding="utf-8").strip()
    html = HTML_FILE.read_text(encoding="utf-8")

    # Match img src with data URI (base64)
    pattern = r'src="data:image/[^"]+base64,[^"]+"'
    replacement = f'src="data:image/jpeg;base64,{avatar_b64}"'

    if not re.search(pattern, html):
        print("ERROR: No base64 img src found in HTML")
        return 1

    html_new = re.sub(pattern, replacement, html, count=1)
    HTML_FILE.write_text(html_new, encoding="utf-8")

    size = HTML_FILE.stat().st_size
    print(f"Patched starguard_about.html ({size:,} bytes, ~{size/1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    exit(main())
