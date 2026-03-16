"""
Sprint 2: Mobile HEDIS table.
- Horizontal scroll wrapper
- Columns 1–2 sticky (Measure + Gaps)
- P2 columns hide below 600px, P3 always hidden on mobile
- Filter bar collapses behind "⚙ Filters" toggle
- ← scroll → hint fades after first scroll
"""
from shiny import ui


def hedis_table_mobile_ui(
    table_ui: ui.TagChild,
    filter_ui: ui.TagChild | None = None,
    id: str = "hedis_table_mobile",
) -> ui.Tag:
    """
    Wraps your table and optional filter bar.
    table_ui: your output_data_frame or table output.
    filter_ui: filter controls — collapse behind "⚙ Filters" on mobile.
    """
    filter_toggle = ui.div(
        ui.tags.button(
            "⚙ Filters",
            type="button",
            class_="btn btn-outline-secondary btn-sm mobile-filter-toggle",
            id=f"{id}_filter_btn",
            data_bs_toggle="collapse",
            data_bs_target=f"#{id}_filter_collapse",
        ),
        class_="mobile-filter-toggle-wrap",
    )
    filter_collapse = (
        ui.div(
            ui.div(filter_ui, class_="mobile-filter-inner"),
            id=f"{id}_filter_collapse",
            class_="collapse",
        )
        if filter_ui
        else None
    )
    scroll_hint = ui.div(
        "← scroll →",
        class_="mobile-scroll-hint",
        id=f"{id}_hint",
    )
    return ui.div(
        filter_toggle if filter_ui else None,
        filter_collapse,
        scroll_hint,
        ui.div(
            table_ui,
            class_="mobile-table-scroll-wrap",
            id=f"{id}_wrap",
        ),
        ui.tags.script(_scroll_hint_script(id)),
        id=id,
        class_="hedis-table-mobile",
    )


def _scroll_hint_script(component_id: str) -> str:
    return f"""
(function(){{
  var wrap = document.getElementById('{component_id}_wrap');
  var hint = document.getElementById('{component_id}_hint');
  if (!wrap || !hint) return;
  var faded = false;
  wrap.addEventListener('scroll', function() {{
    if (!faded) {{
      faded = true;
      hint.classList.add('faded');
    }}
  }}, {{ passive: true }});
}})();
"""
