"""
Sprint 2: Mobile audit stepper.
One step at a time with Prev/Next, progress bar, dot indicators.
Wraps existing step UI content — no rewrites.
"""
from shiny import ui


def mobile_audit_stepper(
    steps: list[tuple[str, ui.TagChild]],
    *,
    id: str = "audit_stepper",
) -> ui.Tag:
    """
    On desktop: all steps render stacked. On mobile: one step at a time, Prev/Next, progress bar.

    steps: List of (title, ui_content) tuples. Your existing step UI content passes through unchanged.
    Example:
        steps = [
            ("Overview", ui.div(...)),
            ("Documentation", ui.div(...)),
            ("Review", ui.div(...)),
            ("Submit", ui.div(...)),
            ("Complete", ui.div(...)),
        ]
    """
    n = len(steps)
    if n == 0:
        return ui.div("No steps defined.", class_="text-muted")

    # Dot indicators
    dots = []
    for i in range(n):
        dots.append(
            ui.span(
                "",
                class_="stepper-dot",
                id=f"{id}_dot_{i}",
                aria_label=f"Step {i + 1}",
            )
        )

    # Step panels (one visible per index on mobile)
    panels = []
    for i, (title, content) in enumerate(steps):
        panels.append(
            ui.div(
                ui.h5(title, class_="stepper-step-title"),
                content,
                class_="stepper-step-panel",
                id=f"{id}_panel_{i}",
            )
        )

    return ui.div(
        ui.div(
            ui.div(class_="stepper-progress-bar", id=f"{id}_progress"),
            ui.div(*dots, class_="stepper-dots", id=f"{id}_dots"),
            class_="stepper-header",
        ),
        ui.div(*panels, class_="stepper-panels", id=f"{id}_panels"),
        ui.div(
            ui.input_action_button(f"{id}_prev", "← Prev", class_="btn-outline-secondary"),
            ui.span(f"Step 1 of {n}", id=f"{id}_step_label"),
            ui.input_action_button(f"{id}_next", "Next →", class_="btn-primary"),
            class_="stepper-nav",
        ),
        ui.tags.script(_stepper_script(id, n)),
        id=id,
        class_="mobile-audit-stepper",
    )


def _stepper_script(sid: str, total: int) -> str:
    return f"""
(function(){{
  var id = '{sid}';
  var n = {total};
  var idx = 0;

  function go(step) {{
    idx = Math.max(0, Math.min(n - 1, step));
    document.querySelectorAll('[id^="' + id + '_panel_"]').forEach(function(p, i) {{
      p.style.display = i === idx ? 'block' : 'none';
    }});
    document.querySelectorAll('[id^="' + id + '_dot_"]').forEach(function(d, i) {{
      d.classList.toggle('active', i === idx);
    }});
    var lab = document.getElementById(id + '_step_label');
    if (lab) lab.textContent = 'Step ' + (idx + 1) + ' of ' + n;
    var prog = document.getElementById(id + '_progress');
    if (prog) prog.style.width = ((idx + 1) / n * 100) + '%';
  }}

  function setup() {{
    var prev = document.getElementById(id + '_prev');
    var next = document.getElementById(id + '_next');
    if (prev && !prev.dataset.bound) {{
      prev.dataset.bound = '1';
      prev.addEventListener('click', function() {{ go(idx - 1); }});
    }}
    if (next && !next.dataset.bound) {{
      next.dataset.bound = '1';
      next.addEventListener('click', function() {{ go(idx + 1); }});
    }}
    go(0);
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', setup);
  }} else {{ setup(); }}
  setTimeout(setup, 500);
}})();
"""
