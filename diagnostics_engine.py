"""
diagnostics_engine.py — The Fluttering Sail
============================================
Diagnostic Ontology Engine: geometric threshold evaluation of 8-dimensional
ethical vectors against five named philosophical conditions.

Conditions implemented
----------------------
1. Baconian Collapse    — hyper-optimisation / utility extraction
2. Mimetic Shear        — power dominance / ontological erasure
3. Ascetic Drift        — hyper-transcendence / civic deficit
4. Purushartha Equilibrium — holistic synthesis / gold standard
5. Nyaya Meta-Condition — epistemological stability / even distribution

All thresholds are externalised in diagnostics.json (Table 1 in the paper).
Edit that file to run sensitivity analysis without touching Python.

Usage
-----
    from diagnostics_engine import run_diagnostics, render_diagnostics
    alerts = run_diagnostics(avg_dict)
    render_diagnostics(alerts)   # Streamlit banners

Author  : see repository
Licence : see LICENSE
"""

import json
import logging
import os

import numpy as np
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. THRESHOLD LOADING
# ---------------------------------------------------------------------------
_DIAGNOSTICS_FILE = "diagnostics.json"

def load_thresholds() -> dict:
    """
    Load threshold constants from diagnostics.json, filtering _note_ keys.
    Returns empty dict (all diagnostics silently skip) if file is missing.
    """
    if not os.path.exists(_DIAGNOSTICS_FILE):
        logger.error(
            "❌ %s not found — diagnostic engine disabled. "
            "Create the file or restore it from the repository.",
            _DIAGNOSTICS_FILE
        )
        return {}

    try:
        with open(_DIAGNOSTICS_FILE) as f:
            raw = json.load(f).get("DIAG_THRESHOLDS", {})
        thresholds = {k: v for k, v in raw.items() if not k.startswith("_note_")}
        logger.info(
            "✅ Diagnostic thresholds loaded from %s (%d active)",
            _DIAGNOSTICS_FILE, len(thresholds)
        )
        return thresholds
    except Exception as exc:
        logger.error("❌ Failed to parse %s: %s", _DIAGNOSTICS_FILE, exc)
        return {}


# Module-level singleton — loaded once at import time.
# Call reload_thresholds() from the Admin UI if the file is edited at runtime.
DIAG_THRESHOLDS: dict = load_thresholds()


def reload_thresholds() -> int:
    """Re-read diagnostics.json at runtime (e.g. after Admin edits). Returns threshold count."""
    global DIAG_THRESHOLDS
    DIAG_THRESHOLDS = load_thresholds()
    return len(DIAG_THRESHOLDS)


# ---------------------------------------------------------------------------
# 2. CONDITION EVALUATORS
# ---------------------------------------------------------------------------

def _baconian_collapse(v: dict, th: dict) -> dict | None:
    """
    Baconian Collapse — Hyper-Optimisation / Utility Extraction.
    Geometric signature: dominant Utility, near-zero Telos and Structure.
    Represents text that treats human agency as a production input.
    """
    u = v.get('u', 0); t = v.get('t', 0); s = v.get('s', 0)
    if u >= th["baconian_u_min"] and abs(t) <= th["baconian_t_max"] and abs(s) <= th["baconian_s_max"]:
        logger.info(
            "🚨 BACONIAN COLLAPSE triggered — U=%.3f (≥%.2f), |T|=%.3f (≤%.2f), |S|=%.3f (≤%.2f)",
            u, th["baconian_u_min"], abs(t), th["baconian_t_max"], abs(s), th["baconian_s_max"]
        )
        return {
            "name":     "Baconian Collapse",
            "level":    "error",
            "icon":     "⚙️",
            "headline": "Baconian Collapse — Hyper-Optimisation / Utility Extraction",
            "detail": (
                f"Utility is dominant (U={u:+.2f}) while Telos (T={t:+.2f}) and "
                f"Structure (S={s:+.2f}) are near-zero. This text treats human agency "
                "and natural systems as raw inputs for a production pipeline. "
                "Language is entirely extraction-oriented."
            ),
        }
    return None


def _mimetic_shear(v: dict, th: dict) -> dict | None:
    """
    Mimetic Shear — Power Dominance / Ontological Erasure.
    Geometric signature: high Power and Mimetic conflict, collapsed Dharma and Consciousness.
    Signature of hyper-partisan language, wartime mobilisation, algorithmic outrage loops.
    """
    p = v.get('p', 0); m = v.get('m', 0); d = v.get('d', 0); c = v.get('c', 0)
    if (p >= th["mimetic_p_min"] and abs(m) >= th["mimetic_m_min"]
            and abs(d) <= th["mimetic_d_max"] and abs(c) <= th["mimetic_c_max"]):
        logger.info(
            "🚨 MIMETIC SHEAR triggered — P=%.3f, |M|=%.3f, |D|=%.3f, |C|=%.3f",
            p, abs(m), abs(d), abs(c)
        )
        return {
            "name":     "Mimetic Shear",
            "level":    "error",
            "icon":     "⚔️",
            "headline": "Mimetic Shear — Power Dominance / Ontological Erasure",
            "detail": (
                f"Power (P={p:+.2f}) and Mimetic conflict (M={m:+.2f}) dominate "
                f"while Dharma (D={d:+.2f}) and Consciousness (C={c:+.2f}) collapse. "
                "This is the signature of hyper-partisan propaganda, outrage loops, "
                "or wartime mobilisation language. The text severs connection to "
                "holistic cosmic balance (Ṛta)."
            ),
        }
    return None


def _ascetic_drift(v: dict, th: dict) -> dict | None:
    """
    Ascetic Drift — Hyper-Transcendence / Civic Deficit.
    Geometric signature: extreme Consciousness and Telos, collapsed Utility and Fairness.
    Ethically pure at the individual level; fails collective governance.
    """
    c = v.get('c', 0); t = v.get('t', 0); u = v.get('u', 0); f = v.get('f', 0)
    if (abs(c) >= th["ascetic_c_min"] and abs(t) >= th["ascetic_t_min"]
            and abs(u) <= th["ascetic_u_max"] and abs(f) <= th["ascetic_f_max"]):
        logger.info(
            "⚠️  ASCETIC DRIFT triggered — |C|=%.3f, |T|=%.3f, |U|=%.3f, |F|=%.3f",
            abs(c), abs(t), abs(u), abs(f)
        )
        return {
            "name":     "Ascetic Drift",
            "level":    "warning",
            "icon":     "🌫️",
            "headline": "Ascetic Drift — Hyper-Transcendence / Civic Deficit",
            "detail": (
                f"Consciousness (C={c:+.2f}) and Telos (T={t:+.2f}) are extreme "
                f"while Utility (U={u:+.2f}) and Fairness (F={f:+.2f}) collapse. "
                "This text is ethically pure but lacks actionable framework for "
                "institutional execution, distributive justice, or collective governance."
            ),
        }
    return None


def _purushartha_equilibrium(v: dict, th: dict) -> dict | None:
    """
    Purushartha Equilibrium — Holistic Synthesis / Gold Standard.
    Geometric signature: balanced high-magnitude convergence across both manifolds.
    The directional angle between Materialist and Dharmic vectors approaches harmonic symmetry.
    """
    f = v.get('f', 0); u = v.get('u', 0); d = v.get('d', 0); s = v.get('s', 0)
    if (f >= th["equilibrium_f_min"] and u >= th["equilibrium_u_min"]
            and abs(d) >= th["equilibrium_d_min"] and abs(s) >= th["equilibrium_s_min"]):
        logger.info(
            "🪷  PURUSHARTHA EQUILIBRIUM triggered — F=%.3f, U=%.3f, |D|=%.3f, |S|=%.3f",
            f, u, abs(d), abs(s)
        )
        return {
            "name":     "Purushartha Equilibrium",
            "level":    "success",
            "icon":     "🪷",
            "headline": "Purushartha Blueprint — Holistic Synthesis / Equilibrium Zone",
            "detail": (
                f"Balanced high-magnitude convergence: F={f:+.2f}, U={u:+.2f}, "
                f"D={d:+.2f}, S={s:+.2f}. This text achieves integration of worldly "
                "efficiency and transcendent purpose — the gold standard of the framework."
            ),
        }
    return None


def _nyaya_meta_condition(v: dict, th: dict) -> dict | None:
    """
    Nyaya Meta-Condition — Epistemological Stability.
    Geometric signature: low standard deviation AND high mean magnitude across all 8 dimensions.
    Flags harmonised, philosophically integrated worldviews — neither extremist nor vacuous.
    """
    vals  = np.array([v.get(d, 0) for d in ['u','f','p','m','t','s','d','c']])
    sigma = float(np.std(np.abs(vals)))
    mu    = float(np.mean(np.abs(vals)))
    if sigma <= th["nyaya_sigma_max"] and mu >= th["nyaya_mu_min"]:
        logger.info(
            "🔷 NYAYA META-CONDITION triggered — σ=%.3f (≤%.2f), μ=%.3f (≥%.2f)",
            sigma, th["nyaya_sigma_max"], mu, th["nyaya_mu_min"]
        )
        return {
            "name":     "Nyaya Meta-Condition",
            "level":    "info",
            "icon":     "🔷",
            "headline": "Nyaya Meta-Condition — Epistemological Stability",
            "detail": (
                f"σ={sigma:.3f} (≤{th['nyaya_sigma_max']}) and μ={mu:.3f} "
                f"(≥{th['nyaya_mu_min']}) across all 8 dimensions. "
                "This corpus reflects a harmonised, epistemologically stable worldview "
                "consistent with classical Nyaya analytical equilibrium."
            ),
        }
    return None


# ---------------------------------------------------------------------------
# 4. PROXIMITY METERS
# ---------------------------------------------------------------------------

def compute_proximity(avg: dict) -> list:
    """
    For each diagnostic condition, compute how close the text is as a percentage.
    Returns list of {name, pct, icon, colour, detail} dicts sorted by pct descending.

    Proximity is computed per condition as:
        pct = (weighted sum of how far each component is toward its threshold) * 100
    Values are clamped [0, 100]. 100% = threshold exactly met; >100% = exceeded.
    """
    if not DIAG_THRESHOLDS:
        return []

    th = DIAG_THRESHOLDS
    u = avg.get('u', 0); f = avg.get('f', 0)
    p = avg.get('p', 0); m = avg.get('m', 0)
    t = avg.get('t', 0); s = avg.get('s', 0)
    d = avg.get('d', 0); c = avg.get('c', 0)
    vals = [u, f, p, m, t, s, d, c]
    sigma = float(np.std(np.abs(np.array(vals))))
    mu    = float(np.mean(np.abs(np.array(vals))))

    def pct(*components):
        """Average of component ratios, clamped 0-110."""
        return min(110, max(0, round(100 * sum(components) / len(components))))

    meters = [
        {
            "name":   "Baconian Collapse",
            "icon":   "⚙️",
            "colour": "#e74c3c",
            "pct":    pct(
                u / th["baconian_u_min"],
                (th["baconian_t_max"] - abs(t)) / th["baconian_t_max"] if abs(t) < th["baconian_t_max"] else 0,
                (th["baconian_s_max"] - abs(s)) / th["baconian_s_max"] if abs(s) < th["baconian_s_max"] else 0,
            ),
            "detail": f"U={u:+.2f} (need {th['baconian_u_min']}), |T|={abs(t):.2f} (need <{th['baconian_t_max']}), |S|={abs(s):.2f} (need <{th['baconian_s_max']})",
        },
        {
            "name":   "Mimetic Shear",
            "icon":   "⚔️",
            "colour": "#c0392b",
            "pct":    pct(
                p / th["mimetic_p_min"],
                abs(m) / th["mimetic_m_min"],
                (th["mimetic_d_max"] - abs(d)) / th["mimetic_d_max"] if abs(d) < th["mimetic_d_max"] else 0,
                (th["mimetic_c_max"] - abs(c)) / th["mimetic_c_max"] if abs(c) < th["mimetic_c_max"] else 0,
            ),
            "detail": f"P={p:+.2f} (need {th['mimetic_p_min']}), |M|={abs(m):.2f} (need {th['mimetic_m_min']})",
        },
        {
            "name":   "Ascetic Drift",
            "icon":   "🌫️",
            "colour": "#e67e22",
            "pct":    pct(
                abs(c) / th["ascetic_c_min"],
                abs(t) / th["ascetic_t_min"],
                (th["ascetic_u_max"] - abs(u)) / th["ascetic_u_max"] if abs(u) < th["ascetic_u_max"] else 0,
                (th["ascetic_f_max"] - abs(f)) / th["ascetic_f_max"] if abs(f) < th["ascetic_f_max"] else 0,
            ),
            "detail": f"|C|={abs(c):.2f} (need {th['ascetic_c_min']}), |T|={abs(t):.2f} (need {th['ascetic_t_min']})",
        },
        {
            "name":   "Purushartha Equilibrium",
            "icon":   "🪷",
            "colour": "#27ae60",
            "pct":    pct(
                f / th["equilibrium_f_min"],
                u / th["equilibrium_u_min"],
                abs(d) / th["equilibrium_d_min"],
                abs(s) / th["equilibrium_s_min"],
            ),
            "detail": f"F={f:+.2f} (need {th['equilibrium_f_min']}), U={u:+.2f}, |D|={abs(d):.2f}, |S|={abs(s):.2f}",
        },
        {
            "name":   "Nyaya Meta-Condition",
            "icon":   "🔷",
            "colour": "#2980b9",
            "pct":    pct(
                (th["nyaya_sigma_max"] - sigma) / th["nyaya_sigma_max"] if sigma < th["nyaya_sigma_max"] else 0,
                mu / th["nyaya_mu_min"],
            ),
            "detail": f"σ={sigma:.3f} (need <{th['nyaya_sigma_max']}), μ={mu:.3f} (need {th['nyaya_mu_min']})",
        },
    ]

    return sorted(meters, key=lambda x: x["pct"], reverse=True)


def render_proximity_meters(avg: dict) -> None:
    """
    Render VU-style proximity bars for all five diagnostic conditions.
    Shows how close the text is to each condition as a percentage.
    Fully triggered conditions (pct >= 100) render as alert banners.
    """
    meters = compute_proximity(avg)
    if not meters:
        return

    st.markdown("---")
    st.markdown("### 🔬 Diagnostic Proximity")
    st.caption(
        "How close is this text to each ethical condition? "
        "100% = threshold met. Bars show directional proximity — "
        "canonical texts rarely reach 100% on a single condition; "
        "the framework is most informative when read comparatively."
    )

    # Check for full triggers to show as banners
    full_alerts = run_diagnostics(avg)
    triggered_names = {a["name"] for a in full_alerts}

    for m in meters:
        pct   = m["pct"]
        col   = m["colour"]
        fired = m["name"] in triggered_names

        if fired:
            # Full trigger — banner + meter
            fn = {"Baconian Collapse": st.error, "Mimetic Shear": st.error,
                  "Ascetic Drift": st.warning}.get(m["name"],
                  st.success if m["name"] == "Purushartha Equilibrium" else st.info)
            fn(f"{m['icon']} **{m['name']} — TRIGGERED**")

        # VU-style bar
        bar_pct = min(pct, 100)
        label_colour = col if pct >= 70 else "#888"
        st.markdown(
            f"""<div style="margin:6px 0 10px 0">
              <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px">
                <span style="font-size:13px;color:#ccc">{m['icon']} {m['name']}</span>
                <span style="font-size:15px;font-weight:700;color:{label_colour}">{pct}%</span>
              </div>
              <div style="background:#2a2a3e;border-radius:4px;height:10px;width:100%;position:relative">
                <div style="background:{col};border-radius:4px;height:10px;width:{bar_pct}%;
                     {'box-shadow:0 0 8px ' + col if pct >= 90 else ''}"></div>
              </div>
              <div style="font-size:11px;color:#666;margin-top:2px">{m['detail']}</div>
            </div>""",
            unsafe_allow_html=True
        )
    logger.info("📊 Proximity meters rendered — top: %s at %d%%",
                meters[0]["name"], meters[0]["pct"])

# Ordered list of evaluator functions — add new conditions here
_EVALUATORS = [
    _baconian_collapse,
    _mimetic_shear,
    _ascetic_drift,
    _purushartha_equilibrium,
    _nyaya_meta_condition,
]


def run_diagnostics(avg: dict) -> list:
    """
    Evaluate avg_dict against all geometric diagnostic zones.
    Returns list of triggered alert dicts: [{name, level, icon, headline, detail}, ...].
    Skips all evaluations silently if thresholds failed to load.

    Parameters
    ----------
    avg : dict  keys u,f,p,m,t,s,d,c → float values in [-1, 1]

    Returns
    -------
    list of alert dicts (may be empty)
    """
    if not DIAG_THRESHOLDS:
        logger.warning("run_diagnostics: DIAG_THRESHOLDS empty — skipping all conditions")
        return []

    alerts = []
    for evaluator in _EVALUATORS:
        try:
            result = evaluator(avg, DIAG_THRESHOLDS)
            if result:
                alerts.append(result)
        except Exception as exc:
            logger.error("Diagnostic evaluator %s failed: %s", evaluator.__name__, exc)

    if not alerts:
        logger.info("📊 Diagnostics: no thresholds breached (checked %d conditions)", len(_EVALUATORS))

    return alerts


def render_diagnostics(alerts: list) -> None:
    """
    Render Streamlit alert banners for each triggered diagnostic condition.
    Noop if alerts list is empty — no divider is rendered.

    Parameters
    ----------
    alerts : list  output of run_diagnostics()
    """
    if not alerts:
        return

    st.markdown("---")
    st.markdown("### 🔬 Diagnostic Alerts")
    _level_map = {
        "error":   st.error,
        "warning": st.warning,
        "success": st.success,
        "info":    st.info,
    }
    for alert in alerts:
        render_fn = _level_map.get(alert["level"], st.info)
        render_fn(f"{alert['icon']} **{alert['headline']}**\n\n{alert['detail']}")
        logger.info("🖥️  Rendered diagnostic banner: %s", alert["name"])