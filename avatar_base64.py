"""
LinkedIn avatar as base64-encoded JPEG for About page.

To use your photo:
1. Save LinkedIn photo as photo.jpg in this folder
2. Run: python -c "import base64; open('avatar_base64.txt','w').write(base64.b64encode(open('photo.jpg','rb').read()).decode())"
3. Add avatar_base64.txt to the repo (or paste base64 below)
"""
import os

AVATAR_BASE64 = ""
_path = os.path.join(os.path.dirname(__file__), "avatar_base64.txt")
if os.path.isfile(_path):
    with open(_path, "r") as f:
        AVATAR_BASE64 = f.read().strip()

# Fallback: paste base64 here if not using avatar_base64.txt
if not AVATAR_BASE64:
    pass  # Will use generic RR placeholder in app.py
