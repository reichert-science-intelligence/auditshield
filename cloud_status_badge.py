# cloud_status_badge.py
# ─────────────────────────────────────────────────────────────
# Drop-in Cloud Status Badge — 4-badge layout (Phase 1)
# AuditShield-Live & StarGuard | reichert-science-intelligence
# Brand: Purple #4A3E8F | Gold #D4AF37 | Green #10b981
# Layout: layout="strip" = compact horizontal bar | default = stacked sidebar
# ─────────────────────────────────────────────────────────────

from shiny import ui
from datetime import datetime, timezone, timedelta
import os

# ── Config: set per-app in app.py via environment or direct ──
APP_NAME = os.environ.get("APP_NAME", "AuditShield-Live")   # or "StarGuard"
HUGGINGFACE_URL = os.environ.get("HF_SPACE_URL", "https://tinyurl.com/2vj79bem")
LINKEDIN_URL = "https://tinyurl.com/24523hmy"
GITHUB_URL = "https://github.com/reichert-science-intelligence"


def cloud_status_css() -> ui.tags.style:
    """Inject badge CSS — call once inside app_ui head."""
    return ui.tags.style("""
        /* ── Cloud Status Badge (sidebar layout) ── */
        .cloud-badge-panel {
            background: linear-gradient(135deg, #1a1240 0%, #2d1f6e 100%);
            border: 1px solid #4A3E8F;
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 16px;
            font-family: 'Segoe UI', sans-serif;
        }
        .cloud-badge-title {
            color: #D4AF37;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .cloud-badge-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 4px 0;
            font-size: 12px;
            color: #e2e8f0;
        }
        .dot-green  { width:8px; height:8px; border-radius:50%;
                      background:#10b981; box-shadow:0 0 6px #10b981; 
                      flex-shrink:0; animation: pulse-green 2s infinite; }
        .dot-gold   { width:8px; height:8px; border-radius:50%;
                      background:#D4AF37; box-shadow:0 0 6px #D4AF37;
                      flex-shrink:0; }
        .dot-purple { width:8px; height:8px; border-radius:50%;
                      background:#a78bfa; box-shadow:0 0 6px #a78bfa;
                      flex-shrink:0; }
        @keyframes pulse-green {
            0%, 100% { opacity:1; } 50% { opacity:0.4; }
        }
        .cloud-badge-footer {
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid #4A3E8F44;
            font-size: 10px;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .cloud-badge-footer a {
            color: #D4AF37;
            text-decoration: none;
            font-weight: 600;
        }
        .cloud-badge-footer a:hover { text-decoration: underline; }
        .sync-time { color: #10b981; font-weight: 600; }

        /* ── Strip layout: compact horizontal status bar ── */
        .cloud-badge-panel.cloud-badge-strip {
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: space-between;
            padding: 8px 16px;
            margin-bottom: 12px;
            min-height: 40px;
        }
        .cloud-badge-strip .cloud-badge-strip-left {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            font-size: 11px;
            color: #e2e8f0;
        }
        .cloud-badge-strip .cloud-badge-strip-title {
            color: #D4AF37;
            font-weight: 700;
            letter-spacing: 1px;
            margin-right: 4px;
        }
        .cloud-badge-strip .cloud-badge-strip-item {
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .cloud-badge-strip .cloud-badge-strip-sep {
            color: #4A3E8F;
            margin: 0 2px;
        }
        .cloud-badge-strip .cloud-badge-strip-right {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 10px;
            color: #94a3b8;
        }
        .cloud-badge-strip .cloud-badge-strip-right a {
            color: #D4AF37;
            text-decoration: none;
            font-weight: 600;
        }
        .cloud-badge-strip .cloud-badge-strip-right a:hover { text-decoration: underline; }
    """)


def cloud_status_badge(app_variant: str = "auditshield", layout: str = "sidebar") -> ui.div:
    """
    Returns the full badge div for sidebar or strip injection.
    app_variant: 'auditshield' | 'starguard'
    layout: 'sidebar' (default, stacked rows) | 'strip' (compact horizontal bar)
    """
    EST = timezone(timedelta(hours=-5))
    now = datetime.now(EST).strftime("%I:%M:%S %p EST")

    if app_variant == "auditshield":
        services = [
            ("dot-green",  "Anthropic Claude API — Active"),
            ("dot-green",  "Agentic RAG Pipeline — Live"),
            ("dot-gold",   "M.E.A.T. Validator — Ready"),
            ("dot-purple", "HuggingFace Spaces — Deployed"),
        ]
        strip_items = [
            ("dot-green",  "Claude API"),
            ("dot-green",  "Agentic RAG"),
            ("dot-gold",   "M.E.A.T."),
            ("dot-purple", "HuggingFace"),
        ]
        hf_url = "https://tinyurl.com/2vj79bem"

    else:  # starguard
        services = [
            ("dot-green",  "Anthropic Claude API — Active"),
            ("dot-green",  "HEDIS Analytics Engine — Live"),
            ("dot-gold",   "HCC Risk Model — Ready"),
            ("dot-purple", "HuggingFace Spaces — Deployed"),
        ]
        strip_items = [
            ("dot-green",  "Claude API"),
            ("dot-green",  "HEDIS Analytics"),
            ("dot-gold",   "HCC Risk"),
            ("dot-purple", "HuggingFace"),
        ]
        hf_url = "https://rreichert-starguard-desktop.hf.space"

    if layout == "strip":
        # Compact horizontal status bar
        parts = [ui.span("☁ Cloud Services", class_="cloud-badge-strip-title")]
        for i, (dot_class, label) in enumerate(strip_items):
            if i > 0:
                parts.append(ui.span("·", class_="cloud-badge-strip-sep"))
            parts.append(ui.span(
                ui.span(class_=dot_class),
                ui.span(label),
                class_="cloud-badge-strip-item"
            ))
        return ui.div(
            ui.div(*parts, class_="cloud-badge-strip-left"),
            ui.div(
                ui.span("Last sync: ", ui.span(now, class_="sync-time")),
                ui.tags.a("🔗 Live Demo", href=hf_url, target="_blank"),
                class_="cloud-badge-strip-right"
            ),
            class_="cloud-badge-panel cloud-badge-strip"
        )

    # Default: stacked sidebar layout
    rows = [
        ui.div(
            ui.span(class_=dot_class),
            ui.span(label),
            class_="cloud-badge-row"
        )
        for dot_class, label in services
    ]
    return ui.div(
        ui.div("☁ Cloud Services", class_="cloud-badge-title"),
        *rows,
        ui.div(
            ui.span("Last sync: ", ui.span(now, class_="sync-time")),
            ui.tags.a("🔗 Live Demo", href=hf_url, target="_blank"),
            class_="cloud-badge-footer"
        ),
        class_="cloud-badge-panel"
    )


def provenance_footer(app_variant: str = "auditshield") -> ui.div:
    """
    Sticky bottom footer — shows on every page.
    Signals production deployment to recruiters.
    """
    if app_variant == "auditshield":
        app_label = "AuditShield-Live"
        hf_url = "https://tinyurl.com/2vj79bem"
    else:
        app_label = "StarGuard AI"
        hf_url = "https://rreichert-starguard-desktop.hf.space"

    return ui.div(
        ui.tags.style("""
            .provenance-footer {
                position: fixed; bottom: 0; left: 0; right: 0;
                background: #1a1240ee;
                border-top: 1px solid #4A3E8F;
                padding: 6px 20px;
                font-size: 11px;
                color: #94a3b8;
                display: flex;
                justify-content: space-between;
                z-index: 9999;
                backdrop-filter: blur(4px);
            }
            .provenance-footer a { color: #D4AF37; text-decoration: none; }
            .provenance-footer a:hover { text-decoration: underline; }
        """),
        ui.div(
            f"⚡ {app_label}  |  Powered by ",
            ui.tags.a("Anthropic Claude API", href="https://anthropic.com", target="_blank"),
            "  |  Deployed on ",
            ui.tags.a("HuggingFace Spaces", href=hf_url, target="_blank"),
        ),
        ui.div(
            "Robert Reichert · Healthcare AI Architect · ",
            ui.tags.a("LinkedIn", href=LINKEDIN_URL, target="_blank"),
            " · ",
            ui.tags.a("GitHub", href=GITHUB_URL, target="_blank"),
        ),
        class_="provenance-footer"
    )
