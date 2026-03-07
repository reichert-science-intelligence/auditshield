"""
Phase 2 unit tests — AuditShield
18 tests: suppression CRUD, JSON round-trips, duplicate guard,
cloud badge structure, banner/HITL UI contracts.
No live DB/API calls.
"""
import json
import os
import tempfile

import pytest

# ── Suppression CRUD (audit_trail) ─────────────────────────────────────────

@pytest.fixture
def audit_suppression_temp(monkeypatch):
    """Use temp file for audit suppressions."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    monkeypatch.setenv("AUDIT_SUPPRESSION_FILE", path)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


def test_get_audit_suppressions_empty(audit_suppression_temp):
    """get_audit_suppressions returns [] when file empty/missing."""
    import audit_trail
    audit_trail._SUPPRESSION_FILE = audit_suppression_temp
    audit_trail._AUDIT_SUPPRESSIONS_CACHE = None
    assert audit_trail.get_audit_suppressions() == []


def test_add_audit_suppression_success(audit_suppression_temp):
    """add_audit_suppression adds rule and returns success."""
    import audit_trail
    audit_trail._SUPPRESSION_FILE = audit_suppression_temp
    audit_trail._AUDIT_SUPPRESSIONS_CACHE = None
    r = audit_trail.add_audit_suppression("AUD-20260304-001", "Excluded per CMS")
    assert r["success"] is True
    assert r["audit_id"] == "AUD-20260304-001"
    rules = audit_trail.get_audit_suppressions()
    assert len(rules) == 1
    assert rules[0]["audit_id"] == "AUD-20260304-001"
    assert "reason" in rules[0]
    assert "created" in rules[0]


def test_add_audit_suppression_duplicate_guard(audit_suppression_temp):
    """add_audit_suppression rejects duplicate audit_id."""
    import audit_trail
    audit_trail._SUPPRESSION_FILE = audit_suppression_temp
    audit_trail._AUDIT_SUPPRESSIONS_CACHE = None
    audit_trail.add_audit_suppression("AUD-X", "First")
    r = audit_trail.add_audit_suppression("AUD-X", "Second")
    assert r["success"] is False
    assert "Already suppressed" in r.get("error", "")
    assert len(audit_trail.get_audit_suppressions()) == 1


def test_remove_audit_suppression_success(audit_suppression_temp):
    """remove_audit_suppression removes rule."""
    import audit_trail
    audit_trail._SUPPRESSION_FILE = audit_suppression_temp
    audit_trail._AUDIT_SUPPRESSIONS_CACHE = None
    audit_trail.add_audit_suppression("AUD-Y", "Test")
    assert len(audit_trail.get_audit_suppressions()) == 1
    r = audit_trail.remove_audit_suppression("AUD-Y")
    assert r["success"] is True
    assert audit_trail.get_audit_suppressions() == []


def test_audit_suppression_json_roundtrip(audit_suppression_temp):
    """Suppression rules persist to JSON and reload."""
    import audit_trail
    audit_trail._SUPPRESSION_FILE = audit_suppression_temp
    audit_trail._AUDIT_SUPPRESSIONS_CACHE = None
    audit_trail.add_audit_suppression("AUD-1", "R1")
    audit_trail.add_audit_suppression("AUD-2", "R2")
    with open(audit_suppression_temp, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 2
    ids = {r["audit_id"] for r in data}
    assert ids == {"AUD-1", "AUD-2"}


# ── Cloud badge structure ───────────────────────────────────────────────────

def test_cloud_status_css_returns_tag():
    """cloud_status_css returns a Tag (style element)."""
    from cloud_status_badge import cloud_status_css
    out = cloud_status_css()
    assert out is not None


def test_cloud_status_badge_auditshield_variant():
    """cloud_status_badge with auditshield variant returns Tag."""
    from cloud_status_badge import cloud_status_badge
    out = cloud_status_badge(app_variant="auditshield", layout="sidebar")
    assert out is not None


def test_cloud_status_badge_starguard_variant():
    """cloud_status_badge with starguard variant returns Tag."""
    from cloud_status_badge import cloud_status_badge
    out = cloud_status_badge(app_variant="starguard", layout="strip")
    assert out is not None


def test_auditshield_badge_returns_tag():
    """auditshield_badge returns Tag."""
    from cloud_status_badge import auditshield_badge
    assert auditshield_badge(mode="strip") is not None


def test_provenance_footer_returns_tag():
    """provenance_footer returns Tag."""
    from cloud_status_badge import provenance_footer
    assert provenance_footer(app_variant="auditshield") is not None


# ── Suppression banner UI contract ──────────────────────────────────────────

def test_suppression_banner_base_css_returns_tag():
    """suppression_banner_base_css returns Tag."""
    from suppression_banner import suppression_banner_base_css
    assert suppression_banner_base_css() is not None


def test_suppression_banner_audit_type_returns_tag():
    """suppression_banner(app_type=audit) returns Tag."""
    from suppression_banner import suppression_banner
    out = suppression_banner(app_type="audit")
    assert out is not None


def test_suppression_banner_gap_type_returns_tag():
    """suppression_banner(app_type=gap) returns Tag when hedis_gap_trail available."""
    from suppression_banner import suppression_banner
    out = suppression_banner(app_type="gap")
    assert out is not None


# ── HITL Admin View UI contract ─────────────────────────────────────────────

def test_hitl_admin_css_returns_tag():
    """hitl_admin_css returns Tag."""
    from hitl_admin_view import hitl_admin_css
    assert hitl_admin_css() is not None


def test_hitl_admin_panel_audit_returns_tag():
    """hitl_admin_panel(app_type=audit) returns Tag."""
    from hitl_admin_view import hitl_admin_panel
    assert hitl_admin_panel(app_type="audit") is not None


def test_hitl_admin_panel_gap_returns_tag():
    """hitl_admin_panel(app_type=gap) returns Tag."""
    from hitl_admin_view import hitl_admin_panel
    assert hitl_admin_panel(app_type="gap") is not None


def test_audit_trail_columns_schema():
    """AUDIT_COLUMNS has expected schema."""
    from audit_trail import AUDIT_COLUMNS
    assert "audit_id" in AUDIT_COLUMNS
    assert "audit_status" in AUDIT_COLUMNS
    assert "measure_code" in AUDIT_COLUMNS
    assert len(AUDIT_COLUMNS) >= 10
