"""
Sprint 2: Mobile dashboard components.
mobile_kpi_strip() — horizontal scroll KPI strip; mobile_dashboard_card() — collapsible chart cards.
"""
from shiny import ui


def mobile_kpi_strip(
    kpis: list[tuple[str, str]],
    *,
    id_prefix: str = "kpi",
) -> ui.Tag:
    """
    Renders KPIs as a horizontal scroll strip on mobile.
    kpis: List of (label, value) tuples, e.g. [("Star Rating", "4.2"), ("HEDIS Gaps", "3"), ...]
    """
    items = []
    for i, (label, value) in enumerate(kpis):
        items.append(
            ui.div(
                ui.span(value, class_="mobile-kpi-value"),
                ui.span(label, class_="mobile-kpi-label"),
                class_="mobile-kpi-item",
                id=f"{id_prefix}_{i}",
            )
        )
    return ui.div(
        ui.div(*items, class_="mobile-kpi-strip"),
        class_="mobile-kpi-strip-wrap",
    )


def mobile_dashboard_card(
    title: str,
    content: ui.TagChild,
    *,
    id: str | None = None,
    collapsed_default: bool = False,
) -> ui.Tag:
    """
    Collapsible chart card — tap the header to collapse when screen space is tight.
    content: Your existing chart/output UI.
    """
    uid = id or f"card_{hash(title) % 10**8}"
    collapse_id = f"{uid}_collapse"
    return ui.div(
        ui.div(
            title,
            class_="mobile-card-header",
            id=f"{uid}_header",
            data_bs_toggle="collapse",
            data_bs_target=f"#{collapse_id}",
            aria_expanded="false" if collapsed_default else "true",
            aria_controls=collapse_id,
        ),
        ui.div(
            content,
            id=collapse_id,
            class_="collapse" + (" show" if not collapsed_default else ""),
        ),
        class_="mobile-dashboard-card",
        id=uid,
    )
