"""
radar.py — The Fluttering Sail
================================
Pure Plotly computation for radar (Scatterpolar) figures.
Zero Streamlit dependencies — fully testable in isolation.

The dual-trace design
---------------------
Each radar renders two overlaid polygons:
  Aligned     (solid, blue or red)   — dimensions with positive values
  Antagonistic (dotted, orange)      — dimensions with negative values (shown as abs)

This preserves the philosophical distinction between neutrality (zero) and
active opposition (negative), which a single-trace radar would collapse.

Public API
----------
    make_radar_figure(keys_list, data_dict, ...) -> go.Figure
    make_overlay_figure(mat_dict, dharmic_dict, ...) -> go.Figure

Both functions need SCHEMA (the loaded epistemic_schema.json) passed in
rather than accessing a module-level global, making them truly stateless.

Author  : see repository
Licence : see LICENSE
"""

import logging

import plotly.graph_objects as go

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _radar_range(keys_list: list, *data_dicts) -> float:
    """
    Compute radial axis ceiling: max abs value across all traces + 15% padding.
    Clamped to [0.5, 1.0] so the canvas is never trivially empty or clipped.
    """
    vals = []
    for d in data_dicts:
        vals.extend(abs(d.get(k, 0)) for k in keys_list)
    peak    = max(vals) if vals else 0.6
    ceiling = min(max(round(peak * 1.15, 2), 0.5), 1.0)
    return ceiling


def _extract_traces(keys: list, data: dict, lineage_map: dict) -> tuple:
    """
    Decompose a vector dict into parallel lists for Scatterpolar.

    Returns (labels, aligned_vals, antag_vals) where:
      labels       — angular axis labels (friendly name, antagonistic marker if negative)
      aligned_vals — max(v, 0) per dimension
      antag_vals   — abs(min(v, 0)) per dimension
    """
    labels, aligned, antag = [], [], []
    for k in keys:
        raw     = data.get(k, 0)
        mapping = lineage_map.get(k.lower(), {})
        friendly = mapping.get("friendly_display", k)
        if raw < 0:
            labels.append(f"↙ {friendly}<br><i>(Antagonistic)</i>")
            aligned.append(0)
            antag.append(abs(raw))
        else:
            labels.append(friendly.replace(" (", "<br>("))
            aligned.append(raw)
            antag.append(0)
        logger.debug("📍 Radar '%s' raw=%.3f antagonistic=%s", k, raw, raw < 0)
    return labels, aligned, antag


# ---------------------------------------------------------------------------
# PUBLIC FIGURES
# ---------------------------------------------------------------------------

def make_radar_figure(
    keys_list: list,
    data_dict: dict,
    schema: dict,
    title: str | None = None,
    fillcolor: str | None = None,
    line_color: str | None = None,
    height: int = 420,
) -> go.Figure:
    """
    Single-lens dual-trace radar figure.

    Parameters
    ----------
    keys_list   : list of dimension codes, e.g. ['u','f','p','m']
    data_dict   : dict mapping dimension codes to float values in [-1, 1]
    schema      : loaded epistemic_schema.json dict (for friendly labels)
    title       : optional figure title (currently unused in layout)
    fillcolor   : RGBA fill for aligned trace (default: blue)
    line_color  : RGBA line for aligned trace (default: blue)
    height      : figure height in pixels

    Returns
    -------
    plotly.graph_objects.Figure
    """
    lineage_map = schema.get("LINEAGE_MAP", {})
    labels, aligned_vals, antag_vals = _extract_traces(keys_list, data_dict, lineage_map)

    # Close polygon
    labels_c       = labels       + [labels[0]]
    aligned_vals_c = aligned_vals + [aligned_vals[0]]
    antag_vals_c   = antag_vals   + [antag_vals[0]]

    r_max      = _radar_range(keys_list, data_dict)
    tick_step  = 0.25
    ticks      = [round(i * tick_step, 2) for i in range(int(r_max / tick_step) + 1)]

    aligned_color = fillcolor  or 'rgba(100,160,255,0.25)'
    aligned_line  = line_color or 'rgba(100,160,255,0.9)'

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=aligned_vals_c, theta=labels_c,
        fill='toself', fillcolor=aligned_color,
        line=dict(color=aligned_line, width=2),
        name='Aligned',
    ))
    fig.add_trace(go.Scatterpolar(
        r=antag_vals_c, theta=labels_c,
        fill='toself', fillcolor='rgba(255,140,0,0.20)',
        line=dict(color='rgba(255,140,0,0.9)', width=2, dash='dot'),
        name='Antagonistic',
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, r_max],
                tickfont=dict(size=9),
                tickvals=ticks,
            ),
            angularaxis=dict(tickfont=dict(size=11)),
            hole=0.0,
            domain=dict(x=[0.0, 1.0], y=[0.0, 1.0]),
        ),
        height=height,
        margin=dict(l=70, r=70, t=50, b=70),
        showlegend=True,
        legend=dict(orientation='h', y=-0.08, font=dict(size=11)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig


def make_overlay_figure(
    mat_dict: dict,
    dharmic_dict: dict,
    schema: dict,
    mat_dims: list,
    dharmic_dims: list,
    height: int = 520,
) -> go.Figure:
    """
    Synthesis view: both lenses on a single 8-axis radar with four traces.
    Materialist (red) and Dharmic (blue), each with aligned and antagonistic traces.

    Parameters
    ----------
    mat_dict     : dict of Materialist dimension values
    dharmic_dict : dict of Dharmic dimension values
    schema       : loaded epistemic_schema.json dict
    mat_dims     : list of Materialist dimension codes, e.g. ['u','f','p','m']
    dharmic_dims : list of Dharmic dimension codes, e.g. ['t','s','d','c']
    height       : figure height in pixels
    """
    lineage_map = schema.get("LINEAGE_MAP", {})

    ml, ma, mx = _extract_traces(mat_dims,     mat_dict,     lineage_map)
    el, ea, ex = _extract_traces(dharmic_dims,  dharmic_dict, lineage_map)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=ma + [ma[0]], theta=ml + [ml[0]],
        fill='toself', fillcolor='rgba(255,80,80,0.2)',
        line=dict(color='rgba(255,80,80,0.9)', width=2),
        name='Materialist — Aligned'
    ))
    fig.add_trace(go.Scatterpolar(
        r=mx + [mx[0]], theta=ml + [ml[0]],
        fill='toself', fillcolor='rgba(255,140,0,0.15)',
        line=dict(color='rgba(255,140,0,0.9)', width=2, dash='dot'),
        name='Materialist — Antagonistic'
    ))
    fig.add_trace(go.Scatterpolar(
        r=ea + [ea[0]], theta=el + [el[0]],
        fill='toself', fillcolor='rgba(80,130,255,0.2)',
        line=dict(color='rgba(80,130,255,0.9)', width=2),
        name='Dharmic — Aligned'
    ))
    fig.add_trace(go.Scatterpolar(
        r=ex + [ex[0]], theta=el + [el[0]],
        fill='toself', fillcolor='rgba(160,80,255,0.15)',
        line=dict(color='rgba(160,80,255,0.9)', width=2, dash='dot'),
        name='Dharmic — Antagonistic'
    ))

    all_keys = mat_dims + dharmic_dims
    r_max     = _radar_range(all_keys, mat_dict, dharmic_dict)
    tick_step = 0.25
    ticks     = [round(i * tick_step, 2) for i in range(int(r_max / tick_step) + 1)]

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, r_max],
                tickfont=dict(size=9), tickvals=ticks
            ),
            angularaxis=dict(tickfont=dict(size=11)),
            domain=dict(x=[0.0, 1.0], y=[0.0, 1.0]),
        ),
        height=height,
        margin=dict(l=70, r=70, t=50, b=70),
        legend=dict(orientation='h', y=-0.18, font=dict(size=10)),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig