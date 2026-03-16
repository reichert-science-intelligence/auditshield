"""
Sprint 1: Mobile hamburger nav component for AuditShield.
Self-contained Shiny component: hamburger button, dimmed overlay, Run Audit FAB, toggle JS inline.
Targets bslib sidebar layout (.bslib-sidebar-layout, .sidebar, .main, .sidebar-toggle).
"""
from shiny import ui


def nav_mobile_ui(id: str = "nav_mobile") -> ui.Tag:
    """Mobile nav: hamburger (X animation), overlay, Run Audit FAB. Use below 768px."""
    return ui.div(
        ui.div(
            ui.tags.button(
                ui.span(class_="hamburger-line"),
                ui.span(class_="hamburger-line"),
                ui.span(class_="hamburger-line"),
                type="button",
                class_="mobile-hamburger",
                id=f"{id}_hamburger",
                aria_label="Toggle sidebar",
            ),
            class_="mobile-hamburger-wrap",
        ),
        ui.div(
            class_="mobile-overlay",
            id=f"{id}_overlay",
        ),
        ui.div(
            ui.tags.a(
                "Run Audit",
                href="#",
                class_="mobile-fab",
                id=f"{id}_fab",
            ),
            class_="mobile-fab-wrap",
        ),
        ui.tags.script(_toggle_script(id)),
        id=id,
        class_="nav-mobile-component",
    )


def _toggle_script(component_id: str) -> str:
    return f"""
(function(){{
'use strict';
var hid = '{component_id}_hamburger';
var oid = '{component_id}_overlay';
var fid = '{component_id}_fab';

function toggleSidebar() {{
  var btn = document.getElementById(hid);
  var ov = document.getElementById(oid);
  var tog = document.querySelector('.sidebar-toggle, [data-bs-toggle="offcanvas"], .bslib-sidebar-toggle');
  if (tog) {{
    tog.click();
  }} else {{
    var off = document.querySelector('.offcanvas');
    if (off && typeof bootstrap !== 'undefined') {{
      var inst = bootstrap.Offcanvas.getInstance(off);
      if (inst) inst.toggle(); else new bootstrap.Offcanvas(off).show();
    }}
  }}
  btn && btn.classList.toggle('open');
  ov && ov.classList.toggle('visible');
}}

function closeSidebar() {{
  var btn = document.getElementById(hid);
  var ov = document.getElementById(oid);
  var open = document.querySelectorAll('.offcanvas.show');
  open.forEach(function(el){{
    if (typeof bootstrap !== 'undefined') {{
      var inst = bootstrap.Offcanvas.getInstance(el);
      if (inst) inst.hide();
    }}
  }});
  btn && btn.classList.remove('open');
  ov && ov.classList.remove('visible');
}}

function setup() {{
  var hamburger = document.getElementById(hid);
  var overlay = document.getElementById(oid);

  if (hamburger && !hamburger.dataset.bound) {{
    hamburger.dataset.bound = '1';
    hamburger.addEventListener('click', function() {{ toggleSidebar(); }});
  }}

  if (overlay && !overlay.dataset.bound) {{
    overlay.dataset.bound = '1';
    overlay.addEventListener('click', function() {{ closeSidebar(); }});
  }}

  /* FAB click handled by fab_wiring.py (Shiny tab switch, scroll, gold pulse) */

  document.addEventListener('bs.offcanvas.hidden', function() {{
    var btn = document.getElementById(hid);
    var ov = document.getElementById(oid);
    if (btn) btn.classList.remove('open');
    if (ov) ov.classList.remove('visible');
  }});
}}

if (document.readyState === 'loading') {{
  document.addEventListener('DOMContentLoaded', setup);
}} else {{ setup(); }}
setTimeout(setup, 500);
setTimeout(setup, 2000);
}})();
"""
