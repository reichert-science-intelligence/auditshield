"""Pytest tests for StarGuard About & Services integration."""
import pytest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
WWW_DIR = APP_DIR / "www"

REQUIRED_FILES = [
    "starguard_about.html",
    "starguard_services.html",
    "auditshield_services.html",
]

MIN_ABOUT_SIZE = 100_000  # 100KB minimum (embedded avatar)


def test_www_directory_exists():
    """www/ directory must exist."""
    assert WWW_DIR.is_dir(), f"www/ directory not found at {WWW_DIR}"


def test_all_html_files_present():
    """All 3 HTML files must be present in www/."""
    for name in REQUIRED_FILES:
        assert (WWW_DIR / name).exists(), f"Missing file: {name}"


def test_starguard_about_has_avatar():
    """starguard_about.html should be large enough to contain embedded avatar."""
    p = WWW_DIR / "starguard_about.html"
    assert p.exists(), "starguard_about.html not found"
    size = p.stat().st_size
    assert size >= MIN_ABOUT_SIZE, f"starguard_about.html is {size:,} bytes (expected >{MIN_ABOUT_SIZE:,})"


def test_files_have_valid_html_structure():
    """Each HTML file must contain doctype or html tag."""
    for name in REQUIRED_FILES:
        p = WWW_DIR / name
        if not p.exists():
            pytest.skip(f"{name} not found")
        text = p.read_text(encoding="utf-8", errors="replace")
        assert "<!DOCTYPE html>" in text or "<html" in text.lower(), \
            f"{name}: Invalid HTML structure"


def test_files_contain_data_disclaimers():
    """Each file should contain the word 'synthetic' (data disclaimer)."""
    for name in REQUIRED_FILES:
        p = WWW_DIR / name
        if not p.exists():
            pytest.skip(f"{name} not found")
        text = p.read_text(encoding="utf-8", errors="replace")
        assert "synthetic" in text.lower(), f"{name}: Missing data disclaimer"


def test_no_corrupted_base64():
    """Check that base64 data (if present) is not obviously corrupted."""
    p = WWW_DIR / "starguard_about.html"
    if not p.exists():
        pytest.skip("starguard_about.html not found")
    text = p.read_text(encoding="utf-8", errors="replace")
    if "data:image" in text and "base64," in text:
        idx = text.find("base64,")
        assert idx >= 0, "base64 marker found but index failed"
        remainder = text[idx + 7 : idx + 50].strip()
        # Base64 should have alphanumeric or +/= chars
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
        sample = remainder[:20] if len(remainder) >= 20 else remainder
        assert all(c in valid_chars or c.isspace() for c in sample) or len(remainder) == 0, \
            "Possible corrupted base64 encoding"
