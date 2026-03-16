"""
Sprint 3: FAB wiring — real Shiny tab switch, sidebar close, scroll-to-top, gold pulse on Run Audit.
Uses Shiny.setInputValue() for server, bootstrap.Tab.show() for DOM.
Default IDs: main_tabs, audit, run_audit. Confirm via browser console if your app uses different values.
"""
from shiny import ui


def fab_wiring_script(
    *,
    main_tabs_id: str = "main_nav",
    audit_tab_id: str = "Mock Audit",
    run_audit_btn_id: str = "run_mock_audit",
    fab_id: str = "nav_mobile_fab",
) -> ui.Tag:
    """
    One-time setup: wires the FAB to switch to audit tab, close sidebar, scroll top, pulse Run Audit.
    Include once in app head or with nav_mobile component.
    """
    return ui.tags.script(
        f"""
(function(){{
'use strict';
var MT = '{main_tabs_id}';
var AT = '{audit_tab_id}';
var RB = '{run_audit_btn_id}';
var FID = '{fab_id}';

function doFabAction() {{
  var fab = document.getElementById(FID);
  if (!fab) return;

  // 1. Close sidebar
  var open = document.querySelectorAll('.offcanvas.show');
  open.forEach(function(el){{
    if (typeof bootstrap !== 'undefined') {{
      var inst = bootstrap.Offcanvas.getInstance(el);
      if (inst) inst.hide();
    }}
  }});

  // 2. Shiny tab switch (server)
  if (typeof Shiny !== 'undefined' && Shiny.setInputValue) {{
    Shiny.setInputValue(MT, AT, {{ priority: 'event' }});
  }}

  // 3. Bootstrap tab show (DOM)
  var tabEl = document.querySelector('[data-bs-target="#' + AT + '"], [data-value="' + AT + '"], [href="#' + AT + '"]');
  if (tabEl) {{
    if (typeof bootstrap !== 'undefined') {{
      var tab = new bootstrap.Tab(tabEl);
      tab.show();
    }} else {{
      tabEl.click();
    }}
  }}

  // 4. Scroll to top
  window.scrollTo({{ top: 0, behavior: 'smooth' }});

  // 5. Gold pulse on Run Audit button (after tab visible)
  setTimeout(function(){{
    var runBtn = document.getElementById(RB) || document.querySelector('[id$="' + RB + '"]');
    if (runBtn) {{
      runBtn.classList.add('fab-pulse-gold');
      setTimeout(function(){{
        runBtn.classList.remove('fab-pulse-gold');
      }}, 2000);
    }}
  }}, 400);
}}

function setup() {{
  var fab = document.getElementById(FID);
  if (fab && !fab.dataset.fabWired) {{
    fab.dataset.fabWired = '1';
    fab.addEventListener('click', function(e){{
      e.preventDefault();
      doFabAction();
    }});
  }}
}}

if (document.readyState === 'loading') {{
  document.addEventListener('DOMContentLoaded', setup);
}} else {{ setup(); }}
setTimeout(setup, 500);
setTimeout(setup, 2000);
}})();
"""
    )
