# suppression_banner.py
# ─────────────────────────────────────────────────────────────
# Phase 2: Suppression Status Banner — AuditShield
# Shows active suppression count; wraps content with banner when rules exist
# Brand: Purple #4A3E8F | Gold #D4AF37
# ─────────────────────────────────────────────────────────────

from htmltools import Tag
from shiny import ui

from audit_trail import get_audit_suppressions


def suppression_banner_base_css() -> Tag:
    return ui.tags.style("""
        .suppression-banner {
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            position: sticky;
            top: 0;
            z-index: 100;
            flex-shrink: 0;
        }
        .suppression-banner-icon { font-size: 18px; }
        .suppression-banner-text { font-weight: 600; font-size: 13px; }
    """)


def suppression_banner(app_type: str = "audit") -> Tag:
    """
    Banner showing suppression status. Color reacts to state:
    - Amber when suppressions exist
    - Green when no suppressions
    app_type: "audit" (AuditShield) | "gap" (StarGuard)
    """
    if app_type == "audit":
        active = get_audit_suppressions()
    else:
        try:
            from hedis_gap_trail import get_gap_suppressions
            active = get_gap_suppressions()
        except ImportError:
            active = []

    label = "Audit" if app_type == "audit" else "Gap"
    if active:
        bg, border, text_color, msg = "#fffbeb", "#fcd34d", "#92400e", f"[!] {len(active)} {label} suppression(s) active"
    else:
        bg, border, text_color, msg = "#f0fdf4", "#bbf7d0", "#166534", "[OK] No suppressions active"

    return ui.div(
        suppression_banner_base_css(),
        ui.div(
            ui.span(msg.split()[0], class_="suppression-banner-icon"),
            ui.span(msg, class_="suppression-banner-text"),
            style=f"display: flex; align-items: center; gap: 8px; color: {text_color};"
        ),
        ui.a(
            "Manage in Admin View ->",
            href="#",
            style=f"color: {text_color}; font-size: 12px; text-decoration: none;",
            id="suppression_manage_link"
        ),
        class_="suppression-banner",
        style=f"background: {bg}; border: 1px solid {border};"
    )
