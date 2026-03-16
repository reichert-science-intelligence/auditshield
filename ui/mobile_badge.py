"""
Mobile badge with QR popover — client-side render via qrcode.js (cdnjs).
No external image API, no rate limits. Badge pill wrapped in <a>; hover 250ms opens
popover with QR (accent color), URL, "Point your phone camera" tip.
✕ and Escape close; mouse into popover keeps it open.
"""
from shiny import ui

QRCODE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"


def mobile_badge(
    *,
    url: str = "https://tinyurl.com/bdevpdz5",
    accent_color: str = "#D4AF37",
    id: str = "mobile_badge",
    label: str = "📱 Mobile",
) -> ui.Tag:
    """
    Badge + QR popover. Same import, same call site — add url, accent_color, id as needed.
    url: URL encoded in QR (resume/demo link).
    accent_color: QR foreground — gold #D4AF37 (AuditShield), green #10b981 (SovereignShield).
    """
    popover_id = f"{id}_popover"
    return ui.div(
        ui.tags.style("""
            .mobile-badge-url { font-size: 11px; color: #666; word-break: break-all; margin: 8px 0 4px; }
            .mobile-badge-tip { font-size: 10px; color: #999; margin: 0; }
        """),
        ui.tags.script(src=QRCODE_CDN),
        ui.tags.a(
            label,
            href="#",
            class_="mobile-badge-pill",
            id=id,
            style=f"background: linear-gradient(135deg, {accent_color} 0%, {accent_color}cc 100%); color: #fff; padding: 6px 14px; border-radius: 50px; font-size: 12px; font-weight: 600; text-decoration: none; display: inline-block; box-shadow: 0 2px 8px rgba(0,0,0,0.15); transition: transform 0.2s;",
        ),
        ui.tags.script(_popover_script(id, popover_id, url, accent_color)),
        class_="mobile-badge-wrapper",
    )


def _popover_script(badge_id: str, popover_id: str, url: str, accent_color: str) -> str:
    # Escape for JS string
    url_js = url.replace("\\", "\\\\").replace("'", "\\'")
    accent_js = accent_color.replace("'", "\\'")
    return f"""
(function(){{
'use strict';
var badgeId = '{badge_id}';
var popoverId = '{popover_id}';
var url = '{url_js}';
var accent = '{accent_js}';
var hoverTimer = null;
var leaveTimer = null;
var opened = false;

function ensurePopover() {{
  var badge = document.getElementById(badgeId);
  if (!badge || document.getElementById(popoverId)) return;
  var wrap = document.createElement('span');
  wrap.className = 'mobile-badge-popover-wrap';
  wrap.style.cssText = 'position:relative; display:inline-block;';
  badge.parentNode.insertBefore(wrap, badge);
  wrap.appendChild(badge);
  var pop = document.createElement('div');
  pop.id = popoverId;
  pop.className = 'mobile-badge-popover';
  pop.innerHTML = '<button type="button" class="mobile-badge-close" aria-label="Close">✕</button><div id="' + popoverId + '_qr"></div><p class="mobile-badge-url">' + url + '</p><p class="mobile-badge-tip">Point your phone camera at the QR code</p>';
  pop.style.cssText = 'position:absolute; left:0; top:100%; margin-top:8px; z-index:9999; background:#fff; border-radius:12px; padding:16px; box-shadow:0 8px 24px rgba(0,0,0,0.2); display:none; min-width:220px;';
  wrap.appendChild(pop);
  var closeBtn = pop.querySelector('.mobile-badge-close');
  closeBtn.style.cssText = 'position:absolute; top:8px; right:8px; border:none; background:transparent; font-size:18px; cursor:pointer; color:#666; padding:0; line-height:1;';
  closeBtn.addEventListener('click', hide);
  badge.addEventListener('mouseenter', function() {{ clearTimeout(leaveTimer); leaveTimer = null; hoverTimer = setTimeout(show, 250); }});
  badge.addEventListener('mouseleave', function() {{ clearTimeout(hoverTimer); leaveTimer = setTimeout(function() {{ var p = document.getElementById(popoverId); if (p && !p.matches(':hover')) hide(); }}, 80); }});
  pop.addEventListener('mouseenter', function() {{ clearTimeout(hoverTimer); clearTimeout(leaveTimer); leaveTimer = null; opened = true; }});
  pop.addEventListener('mouseleave', function() {{ opened = false; hide(); }});
  document.addEventListener('keydown', function(e) {{ if (e.key === 'Escape') hide(); }});
}}

function show() {{
  var pop = document.getElementById(popoverId);
  if (!pop) return;
  pop.style.display = 'block';
  opened = true;
  var qrEl = document.getElementById(popoverId + '_qr');
  if (qrEl && !qrEl.querySelector('canvas') && typeof QRCode !== 'undefined') {{
    qrEl.innerHTML = '';
    new QRCode(qrEl, {{ text: url, width: 160, height: 160, colorDark: accent, colorLight: '#ffffff' }});
  }}
}}

function hide() {{
  var pop = document.getElementById(popoverId);
  if (pop) pop.style.display = 'none';
  opened = false;
}}

function setup() {{
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', ensurePopover);
  }} else {{
    ensurePopover();
  }}
}}
setup();
setTimeout(ensurePopover, 500);
}})();
"""
