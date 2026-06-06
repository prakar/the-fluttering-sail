import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import hashlib
import plotly.graph_objects as go
import openai
import httpx
import logging
import io
import sys
from datetime import datetime

# --- 1. CORE CONFIG & LOGGING ---
# In-memory log capture for the Admin log viewer
class MemoryLogHandler(logging.Handler):
    MAX_LINES = 500
    def __init__(self):
        super().__init__()
        self.records = []
    def emit(self, record):
        self.records.append({
            "ts": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
            "level": record.levelname,
            "msg": self.format(record)
        })
        if len(self.records) > self.MAX_LINES:
            self.records = self.records[-self.MAX_LINES:]

memory_handler = MemoryLogHandler()
memory_handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(memory_handler)
# Also capture root so plotly/sqlite noise is visible if needed
logging.getLogger().addHandler(memory_handler)

st.set_page_config(page_title="The Fluttering Sail", page_icon="⛵", layout="wide")

DB_NAME = "epistemic_lexicon.db"
SCHEMA, CORPORA = {}, {}

DIMS = ['u', 'f', 'p', 'm', 't', 's', 'd', 'c']
MAT_DIMS  = ['u', 'f', 'p', 'm']   # Materialist Lens
DHARMIC_DIMS = ['t', 's', 'd', 'c'] # Dharmic-Essentialist Lens

def load_assets():
    global SCHEMA, CORPORA
    if os.path.exists("epistemic_schema.json"):
        with open("epistemic_schema.json", "r") as f:
            SCHEMA = json.load(f)
        logger.info("✅ Schema loaded — %d lineage entries", len(SCHEMA.get("LINEAGE_MAP", {})))
    else:
        logger.warning("⚠️  epistemic_schema.json not found")
    if os.path.exists("corpora.json"):
        with open("corpora.json", "r") as f:
            CORPORA = json.load(f)
        logger.info("✅ Corpora loaded — %d documents", len(CORPORA))
    else:
        logger.warning("⚠️  corpora.json not found")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("CREATE TABLE IF NOT EXISTS synthesis_cache (hash TEXT PRIMARY KEY, response TEXT)")
    conn.commit()
    conn.close()
    logger.info("✅ DB initialised: %s", DB_NAME)

load_assets()
init_db()

# --- 2. DIAGNOSTIC ENGINE ---

import numpy as np

# Threshold constants — documented in the paper as Table 1
DIAG_THRESHOLDS = {
    "baconian_u_min":    0.80,
    "baconian_t_max":    0.15,
    "baconian_s_max":    0.10,
    "mimetic_p_min":     0.75,
    "mimetic_m_min":     0.70,
    "mimetic_d_max":     0.20,
    "mimetic_c_max":     0.15,
    "ascetic_c_min":     0.90,
    "ascetic_t_min":     0.85,
    "ascetic_u_max":     0.20,
    "ascetic_f_max":     0.20,
    "equilibrium_f_min": 0.70,
    "equilibrium_u_min": 0.60,
    "equilibrium_d_min": 0.75,
    "equilibrium_s_min": 0.75,
    "nyaya_sigma_max":   0.15,
    "nyaya_mu_min":      0.40,
}

def run_diagnostics(avg: dict) -> list:
    """
    Evaluate avg_dict against all geometric diagnostic zones.
    Returns list of triggered alerts: [{"name", "level", "icon", "headline", "detail"}, ...]
    level: "warning" | "error" | "success" | "info"
    """
    alerts = []
    u  = avg.get('u', 0);  f = avg.get('f', 0)
    p  = avg.get('p', 0);  m = avg.get('m', 0)
    t  = avg.get('t', 0);  s = avg.get('s', 0)
    d  = avg.get('d', 0);  c = avg.get('c', 0)
    th = DIAG_THRESHOLDS

    # -- Baconian Collapse --
    if u >= th["baconian_u_min"] and abs(t) <= th["baconian_t_max"] and abs(s) <= th["baconian_s_max"]:
        alerts.append({
            "name":     "Baconian Collapse",
            "level":    "error",
            "icon":     "⚙️",
            "headline": "Baconian Collapse — Hyper-Optimisation / Utility Extraction",
            "detail":   (
                f"Utility is dominant (U={u:+.2f}) while Telos (T={t:+.2f}) and "
                f"Structure (S={s:+.2f}) are near-zero. This text treats human agency "
                "and natural systems as raw inputs for a production pipeline. "
                "Language is entirely extraction-oriented."
            ),
        })
        logger.info("🚨 Diagnostic: Baconian Collapse triggered (U=%.2f, T=%.2f, S=%.2f)", u, t, s)

    # -- Mimetic Shear --
    if (p >= th["mimetic_p_min"] and abs(m) >= th["mimetic_m_min"]
            and abs(d) <= th["mimetic_d_max"] and abs(c) <= th["mimetic_c_max"]):
        alerts.append({
            "name":     "Mimetic Shear",
            "level":    "error",
            "icon":     "⚔️",
            "headline": "Mimetic Shear — Power Dominance / Ontological Erasure",
            "detail":   (
                f"Power (P={p:+.2f}) and Mimetic conflict (M={m:+.2f}) dominate "
                f"while Dharma (D={d:+.2f}) and Consciousness (C={c:+.2f}) collapse. "
                "This is the signature of hyper-partisan propaganda, outrage loops, "
                "or wartime mobilisation language. The text severs connection to "
                "holistic cosmic balance (Ṛta)."
            ),
        })
        logger.info("🚨 Diagnostic: Mimetic Shear triggered (P=%.2f, M=%.2f, D=%.2f, C=%.2f)", p, m, d, c)

    # -- Ascetic Drift --
    if (abs(c) >= th["ascetic_c_min"] and abs(t) >= th["ascetic_t_min"]
            and abs(u) <= th["ascetic_u_max"] and abs(f) <= th["ascetic_f_max"]):
        alerts.append({
            "name":     "Ascetic Drift",
            "level":    "warning",
            "icon":     "🌫️",
            "headline": "Ascetic Drift — Hyper-Transcendence / Civic Deficit",
            "detail":   (
                f"Consciousness (C={c:+.2f}) and Telos (T={t:+.2f}) are extreme "
                f"while Utility (U={u:+.2f}) and Fairness (F={f:+.2f}) collapse. "
                "This text is ethically pure but lacks actionable framework for "
                "institutional execution, distributive justice, or collective governance."
            ),
        })
        logger.info("⚠️  Diagnostic: Ascetic Drift triggered (C=%.2f, T=%.2f, U=%.2f, F=%.2f)", c, t, u, f)

    # -- Equilibrium / Purushartha --
    if (f >= th["equilibrium_f_min"] and u >= th["equilibrium_u_min"]
            and abs(d) >= th["equilibrium_d_min"] and abs(s) >= th["equilibrium_s_min"]):
        alerts.append({
            "name":     "Purushartha Equilibrium",
            "level":    "success",
            "icon":     "🪷",
            "headline": "Purushartha Blueprint — Holistic Synthesis / Equilibrium Zone",
            "detail":   (
                f"Balanced high-magnitude convergence: F={f:+.2f}, U={u:+.2f}, "
                f"D={d:+.2f}, S={s:+.2f}. This text achieves integration of worldly "
                "efficiency and transcendent purpose — the gold standard of the framework."
            ),
        })
        logger.info("🪷  Diagnostic: Purushartha Equilibrium triggered")

    # -- Nyaya Meta-Condition (balanced across ALL 8 dims) --
    vals = np.array([u, f, p, m, t, s, d, c])
    sigma = float(np.std(np.abs(vals)))
    mu    = float(np.mean(np.abs(vals)))
    if sigma <= th["nyaya_sigma_max"] and mu >= th["nyaya_mu_min"]:
        alerts.append({
            "name":     "Nyaya Meta-Condition",
            "level":    "info",
            "icon":     "🔷",
            "headline": "Nyaya Meta-Condition — Epistemological Stability",
            "detail":   (
                f"σ={sigma:.3f} (≤{th['nyaya_sigma_max']}) and μ={mu:.3f} "
                f"(≥{th['nyaya_mu_min']}) across all 8 dimensions. "
                "This corpus reflects a harmonised, epistemologically stable worldview "
                "consistent with classical Nyaya analytical equilibrium."
            ),
        })
        logger.info("🔷 Diagnostic: Nyaya Meta-Condition triggered (σ=%.3f, μ=%.3f)", sigma, mu)

    if not alerts:
        logger.info("📊 Diagnostics: no thresholds breached")
    return alerts


def render_diagnostics(alerts: list):
    """Render alert banners in the UI. Called after radar charts."""
    if not alerts:
        return
    st.markdown("---")
    st.markdown("### 🔬 Diagnostic Alerts")
    for a in alerts:
        fn = {"error": st.error, "warning": st.warning,
              "success": st.success, "info": st.info}[a["level"]]
        fn(f"{a['icon']} **{a['headline']}**\n\n{a['detail']}")


def make_flutter_frames(keys_list, data_dict, n_frames=12, noise_sigma=0.013):
    """
    Generate Plotly animation frames for the 'flutter' effect.
    Each frame adds tiny Gaussian noise to the aligned trace only —
    visually communicating that weights are approximations, not fixed truth.
    noise_sigma=0.013 is subtle enough not to distort shape.
    """
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})
    labels, base_aligned, base_antag = [], [], []
    for k in keys_list:
        raw = data_dict.get(k, 0)
        m   = lineage_map.get(k.lower(), {})
        friendly = m.get("friendly_display", k)
        label = f"↙ {friendly}<br><i>(Antagonistic)</i>" if raw < 0 else friendly.replace(" (", "<br>(")
        labels.append(label)
        base_aligned.append(max(raw, 0))
        base_antag.append(abs(min(raw, 0)))

    labels_c    = labels       + [labels[0]]
    base_antag_c = base_antag  + [base_antag[0]]

    frames = []
    for i in range(n_frames):
        noise = np.random.normal(0, noise_sigma, len(base_aligned))
        noisy = np.clip(np.array(base_aligned) + noise, 0, 1).tolist()
        noisy_c = noisy + [noisy[0]]
        frames.append(go.Frame(
            data=[
                go.Scatterpolar(r=noisy_c,    theta=labels_c),   # trace 0: aligned (flutter)
                go.Scatterpolar(r=base_antag_c, theta=labels_c), # trace 1: antagonistic (stable)
            ],
            name=str(i)
        ))
    return frames, labels_c, base_aligned, base_antag


def make_radar_figure_animated(keys_list, data_dict, fillcolor=None, line_color=None, height=420):
    """
    Static dual-trace radar for Main Analysis page.
    Flutter removed — was consuming vertical space with buttons.
    Canvas fills ~90% of the figure via domain + tight margins.
    """
    return make_radar_figure(keys_list, data_dict,
                             fillcolor=fillcolor, line_color=line_color, height=height)


# --- 3. LOGIC ENGINES ---

def make_radar_figure(keys_list, data_dict, title=None, fillcolor=None, line_color=None, height=420):
    """
    Dual-trace Scatterpolar.
    - Trace 1 (blue): aligned dimensions (raw >= 0), clamped to 0 where negative.
    - Trace 2 (orange): antagonistic dimensions (raw < 0), abs() value, clamped to 0 where positive.
    Angular labels carry '↙ (Antagonistic)' marker on negative spokes.
    Range [0,1] — spoke length = intensity; colour = polarity.
    """
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})
    labels, aligned_vals, antag_vals = [], [], []

    for k in keys_list:
        raw = data_dict.get(k, 0)
        mapping = lineage_map.get(k.lower(), {})
        friendly = mapping.get("friendly_display", k)
        if raw < 0:
            label_text = f"↙ {friendly}<br><i>(Antagonistic)</i>"
            aligned_vals.append(0)
            antag_vals.append(abs(raw))
        else:
            label_text = friendly.replace(" (", "<br>(")
            aligned_vals.append(raw)
            antag_vals.append(0)
        logger.debug("📍 Radar '%s' raw=%.3f antagonistic=%s", k, raw, raw < 0)
        labels.append(label_text)

    # Close polygon
    labels_c       = labels       + [labels[0]]
    aligned_vals_c = aligned_vals + [aligned_vals[0]]
    antag_vals_c   = antag_vals   + [antag_vals[0]]

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
                range=[0, 0.75],
                tickfont=dict(size=9),
                tickvals=[0, 0.25, 0.5, 0.75],
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


def make_overlay_figure(mat_dict, dharmic_dict, height=520):
    """Synthesis view: both lenses on a single 8-axis radar, dual-trace per lens."""
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})

    def extract(keys, d):
        labs, aligned, antag = [], [], []
        for k in keys:
            raw = d.get(k, 0)
            m = lineage_map.get(k.lower(), {})
            friendly = m.get("friendly_display", k)
            label = f"↙ {friendly}<br><i>(Antagonistic)</i>" if raw < 0 else friendly.replace(" (", "<br>(")
            labs.append(label)
            aligned.append(max(raw, 0))
            antag.append(abs(min(raw, 0)))
        return labs, aligned, antag

    ml, ma, mx = extract(MAT_DIMS, mat_dict)
    el, ea, ex = extract(DHARMIC_DIMS, dharmic_dict)

    fig = go.Figure()
    # Materialist aligned
    fig.add_trace(go.Scatterpolar(
        r=ma + [ma[0]], theta=ml + [ml[0]],
        fill='toself', fillcolor='rgba(255,80,80,0.2)',
        line=dict(color='rgba(255,80,80,0.9)', width=2),
        name='Materialist — Aligned'
    ))
    # Materialist antagonistic
    fig.add_trace(go.Scatterpolar(
        r=mx + [mx[0]], theta=ml + [ml[0]],
        fill='toself', fillcolor='rgba(255,140,0,0.15)',
        line=dict(color='rgba(255,140,0,0.9)', width=2, dash='dot'),
        name='Materialist — Antagonistic'
    ))
    # Dharmic aligned
    fig.add_trace(go.Scatterpolar(
        r=ea + [ea[0]], theta=el + [el[0]],
        fill='toself', fillcolor='rgba(80,130,255,0.2)',
        line=dict(color='rgba(80,130,255,0.9)', width=2),
        name='Dharmic — Aligned'
    ))
    # Dharmic antagonistic
    fig.add_trace(go.Scatterpolar(
        r=ex + [ex[0]], theta=el + [el[0]],
        fill='toself', fillcolor='rgba(160,80,255,0.15)',
        line=dict(color='rgba(160,80,255,0.9)', width=2, dash='dot'),
        name='Dharmic — Antagonistic'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 0.75], tickfont=dict(size=9),
                            tickvals=[0, 0.25, 0.5, 0.75]),
            angularaxis=dict(tickfont=dict(size=11)),
            domain=dict(x=[0.0, 1.0], y=[0.0, 1.0]),
        ),
        height=height,
        margin=dict(l=70, r=70, t=50, b=70),
        legend=dict(orientation='h', y=-0.18, font=dict(size=10)),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig


def get_cached_synthesis(text_content, vector_dict):
    unique_str = text_content + str(sorted(vector_dict.items()))
    text_hash  = hashlib.md5(unique_str.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    res  = conn.execute("SELECT response FROM synthesis_cache WHERE hash = ?", (text_hash,)).fetchone()
    conn.close()
    return (res[0] if res else None), text_hash


def generate_triangulated_meaning(vector_dict, source_context):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("generate_triangulated_meaning: OPENAI_API_KEY not set")
        return "⚠️ API Key Missing. Set OPENAI_API_KEY in your environment."
    prompt = f"""
Topology: {vector_dict}
Snippet: "{source_context[:1000]}"

Construct a single, dense paragraph triangulating the 'essence' of this text.
Explain its internal friction using the philosophical schools represented in the topology.
DO NOT list weights or dimensions by name. Focus on the conceptual synthesis.
"""
    logger.info("🤖 Calling GPT-4o for synthesis (snippet len=%d)", len(source_context))
    try:
        client = openai.OpenAI(api_key=api_key, http_client=httpx.Client())
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a master of comparative philosophy."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.4
        )
        result = res.choices[0].message.content
        logger.info("✅ GPT-4o synthesis returned %d chars", len(result))
        return result
    except Exception as e:
        logger.error("GPT-4o error: %s", str(e))
        return f"⚠️ Error: {str(e)}"


def load_all_nontranslatables():
    """
    Load ALL Sanskrit non-translatables from the DB (source = Rajiv_Malhotra_Non_Translatables).
    Returns dict {word: {u,f,p,m,t,s,d,c}} — the single source of truth.
    DB has 63 terms; weights.json (14 terms) is a subset and is now a fallback only.
    """
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute(
        "SELECT word, u, f, p, m, t, s, d, c FROM lexicon "
        "WHERE source = 'Rajiv_Malhotra_Non_Translatables' ORDER BY word"
    ).fetchall()
    conn.close()
    terms = {r[0]: dict(zip(DIMS, r[1:])) for r in rows}
    logger.info("📚 Loaded %d Sanskrit non-translatables from DB", len(terms))
    if not terms:
        # Fallback to weights.json
        logger.warning("DB had no nontranslatables — falling back to weights.json")
        if os.path.exists("weights.json"):
            with open("weights.json") as f:
                w = json.load(f)
            raw = w.get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
            terms = {k: dict(zip(DIMS, v)) for k, v in raw.items()}
    return terms


# --- 3. UI ---

page = st.sidebar.selectbox("Navigation", ["Main Analysis", "Sanskrit Non-Translatables", "Admin & Logs"])

# ===========================================================================
# PAGE: MAIN ANALYSIS
# ===========================================================================
if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")

    choice = st.sidebar.selectbox("Benchmark Document", list(CORPORA.keys()) + ["Custom Text..."])
    if choice != "Custom Text...":
        input_text = CORPORA.get(choice, {}).get("text", "")
        st.sidebar.markdown(f"**Source Context:**\n\n{input_text}")
    else:
        input_text = st.sidebar.text_area("Passage", height=300)

    if input_text:
        conn   = sqlite3.connect(DB_NAME)
        tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
        logger.info("🔍 Analysing '%s' — %d tokens", choice, len(tokens))
        df = pd.read_sql_query(
            f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(tokens))})",
            conn, params=tokens
        )
        conn.close()
        logger.info("📊 Matched %d lexicon rows for analysis", len(df))

        if df.empty:
            st.warning("No lexicon matches found for this text. Try a different passage or expand the lexicon.")
        else:
            avg_dict = df[DIMS].mean().to_dict()
            logger.info("📐 Avg vector: %s", {k: round(v,3) for k,v in avg_dict.items()})

            if st.session_state.get('synth_active', False):
                # --- SYNTHESIS (MERGED) VIEW ---
                st.plotly_chart(make_overlay_figure(avg_dict, avg_dict), use_container_width=True)
                render_diagnostics(run_diagnostics(avg_dict))
                _, btn_col, _ = st.columns([2, 1, 2])
                with btn_col:
                    if st.button("🔓 De-Merge Lenses", use_container_width=True):
                        st.session_state.synth_active = False
                        st.rerun()
                st.markdown("### 🌪️ Synthesized Topological Meaning")
                res, h = get_cached_synthesis(input_text, avg_dict)
                if res:
                    st.info(res)
                else:
                    with st.spinner("⏳ Triangulating..."):
                        new_res = generate_triangulated_meaning(avg_dict, input_text)
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("INSERT OR REPLACE INTO synthesis_cache VALUES (?,?)", (h, new_res))
                        conn.commit(); conn.close()
                        st.info(new_res)
            else:
                # --- SPLIT VIEW ---
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### MATERIALIST LENS")
                    fig = make_radar_figure_animated(
                        MAT_DIMS, avg_dict,
                        fillcolor='rgba(255,80,80,0.2)',
                        line_color='rgba(255,80,80,0.9)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.markdown("### DHARMIC-ESSENTIALIST LENS")
                    fig = make_radar_figure_animated(
                        DHARMIC_DIMS, avg_dict,
                        fillcolor='rgba(80,130,255,0.2)',
                        line_color='rgba(80,130,255,0.9)'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                render_diagnostics(run_diagnostics(avg_dict))

                _, btn_col, _ = st.columns([2, 1, 2])
                with btn_col:
                    if st.button("🌪️ Synthesize (Overlay Lenses)", use_container_width=True):
                        st.session_state.synth_active = True
                        st.rerun()

                st.markdown("---")
                st.markdown("### 📜 Philosophical Lineage & Narration")
                lin  = SCHEMA.get("LINEAGE_MAP", {})
                n1, n2 = st.columns(2)
                with n1:
                    st.markdown("**Materialist Lens**")
                    for k in MAT_DIMS:
                        st.write(f"• **{avg_dict[k]:.2f}** {lin.get(k,{}).get('school','?')}: {lin.get(k,{}).get('desc','')}")
                with n2:
                    st.markdown("**Dharmic-Essentialist Lens**")
                    for k in DHARMIC_DIMS:
                        st.write(f"• **{avg_dict[k]:.2f}** {lin.get(k,{}).get('school','?')}: {lin.get(k,{}).get('desc','')}")

# ===========================================================================
# PAGE: SANSKRIT NON-TRANSLATABLES
# ===========================================================================
elif page == "Sanskrit Non-Translatables":
    st.title("📜 Sanskrit Non-Translatables")

    all_terms = load_all_nontranslatables()   # dict {word: vector_dict}
    term_names = sorted(all_terms.keys())
    total = len(term_names)
    PAGE_SIZE = 10

    if 'p_idx' not in st.session_state:
        st.session_state.p_idx = 0

    # Clamp page index in case data changes
    max_page = max(0, (total - 1) // PAGE_SIZE)
    st.session_state.p_idx = min(st.session_state.p_idx, max_page)

    start = st.session_state.p_idx * PAGE_SIZE
    page_terms = term_names[start : start + PAGE_SIZE]

    c_nav, c_main = st.columns([1, 3])
    with c_nav:
        st.caption(f"Terms {start+1}–{min(start+PAGE_SIZE, total)} of {total}")
        selected_term = st.radio("Terms:", page_terms, key=f"term_radio_{st.session_state.p_idx}")

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️", disabled=(st.session_state.p_idx == 0)):
                st.session_state.p_idx -= 1
                st.rerun()
        with col_next:
            if st.button("➡️", disabled=(st.session_state.p_idx >= max_page)):
                st.session_state.p_idx += 1
                st.rerun()

    with c_main:
        if selected_term:
            v_dict = all_terms[selected_term]
            logger.info("🔬 Viewing non-translatable: %s | vector: %s",
                        selected_term, {k: round(v,3) for k,v in v_dict.items()})

            fig = make_radar_figure(DIMS, v_dict, title=selected_term, height=480)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### 📐 Dimensional Breakdown")
            lin = SCHEMA.get("LINEAGE_MAP", {})
            rows_disp = []
            for k in DIMS:
                raw = v_dict[k]
                rows_disp.append({
                    "Dim": k.upper(),
                    "School": lin.get(k, {}).get("school", "?"),
                    "Score": f"{raw:+.3f}",
                    "Polarity": "↙ Antagonistic" if raw < 0 else "▲ Aligned",
                    "Label": lin.get(k, {}).get("friendly_display", ""),
                })
            st.dataframe(pd.DataFrame(rows_disp), use_container_width=True, hide_index=True)

            res, h = get_cached_synthesis(selected_term, v_dict)
            if res:
                st.info(res)
            else:
                with st.spinner("⏳ Triangulating term..."):
                    new_res = generate_triangulated_meaning(v_dict, selected_term)
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT OR REPLACE INTO synthesis_cache VALUES (?,?)", (h, new_res))
                    conn.commit(); conn.close()
                    st.info(new_res)

# ===========================================================================
# PAGE: ADMIN & LOGS
# ===========================================================================
elif page == "Admin & Logs":
    st.title("🛠️ Admin & Logs")

    t_db, t_lexicon, t_logs, t_maintenance, t_scripts = st.tabs([
        "🗃️ Cache Viewer",
        "📚 Lexicon Browser",
        "📋 Live Log",
        "⚙️ Maintenance",
        "🚀 Script Runner",
    ])

    # ---- TAB: Cache Viewer ------------------------------------------------
    with t_db:
        st.markdown("### AI Synthesis Cache")
        conn = sqlite3.connect(DB_NAME)
        df_cache = pd.read_sql_query("SELECT * FROM synthesis_cache", conn)
        conn.close()
        st.caption(f"{len(df_cache)} cached responses")
        st.dataframe(df_cache, use_container_width=True)

    # ---- TAB: Lexicon Browser ---------------------------------------------
    with t_lexicon:
        st.markdown("### Lexicon Browser")
        conn = sqlite3.connect(DB_NAME)
        df_lex = pd.read_sql_query("SELECT word, source, u, f, p, m, t, s, d, c FROM lexicon ORDER BY source, word", conn)
        conn.close()

        sources = ["All"] + sorted(df_lex['source'].unique().tolist())
        sel_src = st.selectbox("Filter by source", sources)
        if sel_src != "All":
            df_lex = df_lex[df_lex['source'] == sel_src]

        search = st.text_input("Search word")
        if search:
            df_lex = df_lex[df_lex['word'].str.contains(search, case=False)]

        st.caption(f"{len(df_lex)} entries shown")
        st.dataframe(df_lex, use_container_width=True, hide_index=True)

        # Quick per-word radar
        st.markdown("#### 🔭 Quick Radar for any word")
        all_words = sorted(df_lex['word'].tolist())
        if all_words:
            pick = st.selectbox("Pick word", all_words)
            row  = df_lex[df_lex['word'] == pick].iloc[0]
            vd   = {k: row[k] for k in DIMS}
            st.plotly_chart(make_radar_figure(DIMS, vd, title=pick, height=380), use_container_width=True)

        # ---- Add new word
        st.markdown("---")
        st.markdown("#### ➕ Add / Update Word")
        with st.expander("Enter new word vector"):
            new_word   = st.text_input("Word / term")
            new_source = st.text_input("Source label", value="Manual Entry")
            cols = st.columns(8)
            new_vals = {}
            for i, dim in enumerate(DIMS):
                label = SCHEMA.get("LINEAGE_MAP", {}).get(dim, {}).get("school", dim.upper())
                new_vals[dim] = cols[i].number_input(label, min_value=-1.0, max_value=1.0, value=0.0, step=0.05, key=f"nw_{dim}")
            if st.button("💾 Save to DB") and new_word.strip():
                conn = sqlite3.connect(DB_NAME)
                conn.execute(
                    "INSERT OR REPLACE INTO lexicon (word, u, f, p, m, t, s, d, c, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [new_word.strip()] + [new_vals[d] for d in DIMS] + [new_source]
                )
                conn.commit(); conn.close()
                logger.info("✅ Word '%s' saved to DB (source=%s)", new_word, new_source)
                st.success(f"Saved '{new_word}'")
                st.rerun()

    # ---- TAB: Live Log ----------------------------------------------------
    with t_logs:
        st.markdown("### 📋 Session Log")
        st.caption("All INFO/WARNING/ERROR events captured since app start.")

        level_filter = st.selectbox("Level filter", ["ALL", "INFO", "WARNING", "ERROR"])
        records = memory_handler.records
        if level_filter != "ALL":
            records = [r for r in records if r["level"] == level_filter]

        if not records:
            st.info("No log entries yet.")
        else:
            log_df = pd.DataFrame(records)[["ts", "level", "msg"]]
            log_df.columns = ["Time", "Level", "Message"]
            # Colour rows by level
            def level_color(val):
                colors = {"ERROR": "background-color:#5c1a1a", "WARNING": "background-color:#4a3a00", "INFO": ""}
                return colors.get(val, "")
            st.dataframe(
                log_df.style.applymap(level_color, subset=["Level"]),
                use_container_width=True, hide_index=True
            )
            if st.button("🔃 Refresh Log"):
                st.rerun()

    # ---- TAB: Maintenance -------------------------------------------------
    with t_maintenance:
        st.markdown("### ⚙️ Database Maintenance")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🔥 Nuke AI Cache")
            st.caption("Clears all GPT-4o synthesis cache. Re-analysis will re-call the API.")
            if st.button("🔥 NUKE CACHE"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM synthesis_cache")
                conn.commit(); conn.close()
                logger.warning("⚠️  Synthesis cache NUKED by admin")
                st.success("Cache cleared.")

        with col2:
            st.markdown("#### 🗑️ Delete a Word")
            st.caption("Remove a single entry from the lexicon.")
            conn = sqlite3.connect(DB_NAME)
            all_lex_words = [r[0] for r in conn.execute("SELECT word FROM lexicon ORDER BY word").fetchall()]
            conn.close()
            del_word = st.selectbox("Word to delete", all_lex_words)
            if st.button(f"🗑️ Delete '{del_word}'"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM lexicon WHERE word = ?", (del_word,))
                conn.commit(); conn.close()
                logger.warning("🗑️ Word '%s' deleted from lexicon by admin", del_word)
                st.success(f"Deleted '{del_word}'")
                st.rerun()

        st.markdown("---")
        st.markdown("#### 📤 Export Lexicon as CSV")
        conn = sqlite3.connect(DB_NAME)
        df_exp = pd.read_sql_query("SELECT * FROM lexicon", conn)
        conn.close()
        csv_bytes = df_exp.to_csv(index=False).encode()
        st.download_button("⬇️ Download lexicon.csv", csv_bytes, "lexicon.csv", "text/csv")

        st.markdown("#### 📥 Import Words from CSV")
        st.caption("CSV must have columns: word, u, f, p, m, t, s, d, c, source")
        uploaded_csv = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_csv:
            df_import = pd.read_csv(uploaded_csv)
            required = set(DIMS + ['word'])
            if not required.issubset(set(df_import.columns)):
                st.error(f"CSV missing columns. Need at minimum: {required}")
            else:
                if 'source' not in df_import.columns:
                    df_import['source'] = 'CSV Import'
                if st.button(f"📥 Import {len(df_import)} rows"):
                    conn = sqlite3.connect(DB_NAME)
                    inserted = 0
                    for _, row in df_import.iterrows():
                        conn.execute(
                            "INSERT OR REPLACE INTO lexicon (word, u, f, p, m, t, s, d, c, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
                            [row['word']] + [row[d] for d in DIMS] + [row.get('source','CSV Import')]
                        )
                        inserted += 1
                    conn.commit(); conn.close()
                    logger.info("📥 CSV import: %d rows added", inserted)
                    st.success(f"Imported {inserted} rows")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### 🏷️ DB Stats")
        conn = sqlite3.connect(DB_NAME)
        stats = pd.read_sql_query("SELECT source, COUNT(*) as count FROM lexicon GROUP BY source ORDER BY count DESC", conn)
        cache_count = conn.execute("SELECT COUNT(*) FROM synthesis_cache").fetchone()[0]
        conn.close()
        st.dataframe(stats, use_container_width=True, hide_index=True)
        st.caption(f"Synthesis cache: {cache_count} entries")

    # ---- TAB: Script Runner -----------------------------------------------
    with t_scripts:
        import subprocess, threading, queue, time as _time

        st.markdown("### 🚀 Script Runner")
        st.caption("Run seeding and ingestion scripts directly. Output streams live below.")

        SCRIPTS = {
            "engine_db.py — Seed DB from tranche_master (fast, no API)": {
                "cmd": ["python3", "engine_db.py"],
                "warn": None,
            },
            "agent_expand.py — DRY RUN (preview only, no DB write)": {
                "cmd": ["python3", "agent_expand.py"],
                "env_override": {"DRY_RUN": "1"},   # script reads DRY_RUN from source; we patch via sed
                "warn": None,
                "dry_patch": True,
            },
            "agent_expand.py — LIVE RUN (writes to DB, calls OpenAI API 💰)": {
                "cmd": ["python3", "agent_expand.py"],
                "warn": "⚠️ This will call the OpenAI API and WRITE to epistemic_lexicon.db. API costs apply (~$0.10–0.30). Are you sure?",
                "dry_patch": False,
            },
        }

        chosen = st.selectbox("Select script", list(SCRIPTS.keys()))
        script_cfg = SCRIPTS[chosen]

        if script_cfg["warn"]:
            st.warning(script_cfg["warn"])
            confirmed = st.checkbox("Yes, I confirm — run it")
        else:
            confirmed = True

        run_btn = st.button("▶️ Run", disabled=not confirmed)
        log_area = st.empty()

        if run_btn:
            import os as _os
            env = _os.environ.copy()

            # For dry-run variant: patch DRY_RUN=True in agent_expand.py via a temp copy
            script_path = script_cfg["cmd"][1]
            run_cmd = list(script_cfg["cmd"])

            if script_cfg.get("dry_patch") is True:
                # Create a temp patched copy with DRY_RUN = True guaranteed
                with open(script_path) as f:
                    src = f.read()
                patched = src.replace("DRY_RUN = False", "DRY_RUN = True")
                tmp_path = "_tmp_dry_run.py"
                with open(tmp_path, "w") as f:
                    f.write(patched)
                run_cmd = ["python3", tmp_path]
            elif script_cfg.get("dry_patch") is False:
                # Live run: patch DRY_RUN = False guaranteed
                with open(script_path) as f:
                    src = f.read()
                patched = src.replace("DRY_RUN = True", "DRY_RUN = False")
                tmp_path = "_tmp_live_run.py"
                with open(tmp_path, "w") as f:
                    f.write(patched)
                run_cmd = ["python3", tmp_path]

            logger.info("🚀 Admin launched script: %s", " ".join(run_cmd))
            output_lines = []

            try:
                proc = subprocess.Popen(
                    run_cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                    cwd=_os.path.dirname(_os.path.abspath(__file__)) or "."
                )
                for line in proc.stdout:
                    line = line.rstrip()
                    output_lines.append(line)
                    logger.info("[script] %s", line)
                    # Stream last 60 lines live
                    log_area.code("\n".join(output_lines[-60:]), language="")
                proc.wait()
                rc = proc.returncode
                if rc == 0:
                    st.success(f"✅ Script finished (exit 0)")
                    logger.info("✅ Script exited cleanly")
                else:
                    st.error(f"❌ Script exited with code {rc}")
                    logger.error("Script exited %d", rc)
            except Exception as e:
                st.error(f"Failed to launch: {e}")
                logger.error("Script launch error: %s", e)
            finally:
                # Clean up temp files
                for tmp in ["_tmp_dry_run.py", "_tmp_live_run.py"]:
                    if _os.path.exists(tmp):
                        _os.remove(tmp)