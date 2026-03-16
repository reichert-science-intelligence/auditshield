"""
Sprint 2: RAG mobile components.
Source accordion (NCQA / CMS / Proprietary), full-width prompt panel (16px input), response panel.
"""
from shiny import ui


def rag_source_accordion_mobile(
    sources: list[tuple[str, ui.TagChild]],
    *,
    id_prefix: str = "rag_src",
) -> ui.Tag:
    """
    Sources as accordion — collapse to tap-targets on mobile.
    sources: List of (title, content) tuples, e.g. [("NCQA", ...), ("CMS", ...), ("Proprietary", ...)]
    """
    items = []
    for i, (title, content) in enumerate(sources):
        cid = f"{id_prefix}_{i}"
        items.append(
            ui.div(
                ui.div(
                    ui.tags.button(
                        title,
                        type="button",
                        class_="accordion-button collapsed",
                        data_bs_toggle="collapse",
                        data_bs_target=f"#{cid}",
                        aria_expanded="false",
                        aria_controls=cid,
                    ),
                    class_="accordion-header",
                ),
                ui.div(
                    ui.div(content, class_="accordion-body"),
                    id=cid,
                    class_="accordion-collapse collapse",
                ),
                class_="accordion-item",
            )
        )
    return ui.div(*items, class_="accordion", id=f"{id_prefix}_accordion")


def rag_prompt_panel_mobile(
    input_id: str,
    *,
    placeholder: str = "Ask a question...",
    button_id: str | None = None,
) -> ui.Tag:
    """
    Full-width prompt panel with 16px input to block iOS zoom.
    """
    btn_id = button_id or f"{input_id}_btn"
    return ui.div(
        ui.div(
            ui.input_text_area(
                input_id,
                None,
                placeholder=placeholder,
                rows=3,
                class_="rag-prompt-input",
            ),
            ui.input_action_button(btn_id, "Submit", class_="btn-primary mt-2"),
            class_="rag-prompt-inner",
        ),
        class_="rag-prompt-panel-mobile",
    )


def rag_response_panel_mobile(
    output_id: str,
    *,
    min_height: str = "200px",
) -> ui.Tag:
    """
    Response panel with no fixed-height clipping — long RAG answers scroll naturally.
    """
    return ui.div(
        ui.output_ui(output_id),
        class_="rag-response-panel-mobile",
    )
