"""
# ⛵ THE FLUTTERING SAIL: TOTAL SYSTEM INTEGRATION (v3.0)
# 
# LITERATE DESIGN: APOPHATIC LOGIC + EXPANDABLE CORPUS.
# Status: Canonical Lockdown.
"""

import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import logging

# --- 1. GLOBAL APP CONFIGURATION ---
st.set_page_config(
    page_title="The Fluttering Sail — Dynamical Multi-Polar Ethical Framework",
    page_icon="⛵",
    layout="wide"
)

DB_NAME = "epistemic_lexicon.db"
LOG_FILE = "framework.log"
SCHEMA = {}
CORPORA = {}

def load_assets():
    global SCHEMA, CORPORA
    if os.path.exists("epistemic_schema.json"):
        with open("epistemic_schema.json", "r") as f: SCHEMA = json.load(f)
    if os.path.exists("corpora.json"):
        with open("corpora.json", "r") as f: CORPORA = json.load(f)

load_assets()

# --- CSS INJECTION FOR COMPACTNESS ---
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { font-size: 1.7rem !important; margin-bottom: 0.2rem !important; padding-top: 0px !important; }
    .stMetric { padding: 0px !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    .centered-label { text-align: center; font-weight: bold; font-size: 1.0rem; margin-bottom: -10px; }
    hr { margin: 0.4rem 0px !important; }
    /* Style for the expander to keep it subtle */
    .streamlit-expanderHeader { font-size: 0.85rem !important; color: #555; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC ENGINES ---

def get_intensity_label(val):
    """Handles both positive alignment and apophatic (negative) divergence."""
    if val < 0:
        return "Divergent" # Indicates the text explicitly moves away from this pole
    for entry in SCHEMA.get("INTENSITY_SCALE", []):
        if val >= entry["threshold"]: return entry["label"]
    return "Neutral"

def evaluate_geometric_failures(vector_dict):
    u, f, p, m = vector_dict['u'], vector_dict['f'], vector_dict['p'], vector_dict['m']
    t, s, d, c = vector_dict['t'], vector_dict['s'], vector_dict['d'], vector_dict['c']
    alerts = []
    modes = SCHEMA.get("FAILURE_MODES", {})
    if u >= 0.80 and t <= 0.15 and s <= 0.10: alerts.append(("error", modes.get("baconian_collapse", {})))
    if p >= 0.75 and m >= 0.70 and d <= 0.20 and c <= 0.15: alerts.append(("error", modes.get("mimetic_shear", {})))
    if c >= 0.90 and t >= 0.85 and u <= 0.20 and f <= 0.20: alerts.append(("warning", modes.get("ascetic_drift", {})))
    if f >= 0.70 and u >= 0.60 and d >= 0.75 and t >= 0.75: alerts.append(("success", modes.get("equilibrium_zone", {})))
    return alerts

def generate_philosophical_narration(vector):
    dim_keys = ['u', 'f', 'p', 'm', 't', 's', 'd', 'c']
    mat_sentences, dha_sentences = [], []
    lineage_defs = SCHEMA.get("LINEAGE_MAP", {}) 

    for idx, key in enumerate(dim_keys):
        score = vector[idx]
        intensity = get_intensity_label(score)
        mapping = lineage_defs.get(key, {})
        
        # We only skip if truly 'Vestigial' or extremely near zero
        if intensity == "Vestigial" and abs(score) < 0.05: continue
            
        name = mapping.get('thinker') if mapping.get('thinker') else mapping.get('school')
        narrative_sentence = f"Exhibits a **{intensity}** ({score:.2f}) alignment with {name} ({mapping.get('school')}), indicating a pattern of {mapping.get('desc')}"
        
        if idx < 4: mat_sentences.append(narrative_sentence)
        else: dha_sentences.append(narrative_sentence)
            
    nyaya_triggered = np.std(vector) < 0.15 and np.mean(vector) > 0.4
    return mat_sentences, dha_sentences, nyaya_triggered

# --- 3. NAVIGATION & MAIN UI ---
page = st.sidebar.selectbox("Navigation Bridge", ["Main Analysis", "Under the Hood"])

if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")
    
    selected_doc_name = st.sidebar.selectbox("Benchmark Document", list(CORPORA.keys()))
    doc_data = CORPORA.get(selected_doc_name, {})
    input_text = doc_data.get("text", "")
    source_label = doc_data.get("taxonomy", "General")

    # RESTORED: Expandable Text Container
    with st.expander(f"📄 View Source Corpus: {source_label}", expanded=False):
        st.write(input_text)

    # Engine Metrics (Proportionally reduced)
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    df_vectors = pd.DataFrame()
    vault_count = 0
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
        df_vectors = pd.read_sql_query(f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(tokens))})", conn, params=tokens)
        vault_count = pd.read_sql_query("SELECT count(*) as count FROM lexicon", conn).iloc[0]['count']
        conn.close()

    m_col1.metric("Tokens", len(input_text.split()))
    m_col2.metric("Hits", len(df_vectors))
    m_col3.metric("Density", f"{(len(df_vectors)/max(len(input_text.split()),1))*100:.1f}%")
    m_col4.metric("Vault", f"{vault_count}")

    st.markdown("---")

    if not df_vectors.empty:
        avg_vec = df_vectors[['u', 'f', 'p', 'm', 't', 's', 'd', 'c']].mean()
        avg_dict = avg_vec.to_dict()
        
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown('<p class="centered-label">MATERIALIST LENS</p>', unsafe_allow_html=True)
            fig1 = go.Figure(data=go.Scatterpolar(
                r=[avg_dict[d] for d in ['f','p','m','u']],
                theta=[SCHEMA['LINEAGE_MAP'][d]['label'] for d in ['f','p','m','u']],
                fill='toself', fillcolor='rgba(255, 65, 54, 0.3)', line=dict(color='rgba(255, 65, 54, 1)')
            ))
            fig1.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, margin=dict(t=25, b=25, l=40, r=40), height=300)
            st.plotly_chart(fig1, use_container_width=True)

        with c_right:
            st.markdown('<p class="centered-label">DHARMIC LENS</p>', unsafe_allow_html=True)
            fig2 = go.Figure(data=go.Scatterpolar(
                r=[avg_dict[d] for d in ['s','t','c','d']],
                theta=[SCHEMA['LINEAGE_MAP'][d]['label'] for d in ['s','t','c','d']],
                fill='toself', fillcolor='rgba(0, 116, 217, 0.3)', line=dict(color='rgba(0, 116, 217, 1)')
            ))
            fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, margin=dict(t=25, b=25, l=40, r=40), height=300)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📜 Philosophical Lineage & Narration")
        
        for a_type, a_meta in evaluate_geometric_failures(avg_dict):
            getattr(st, a_type)(f"**{a_meta.get('title')}**\n\n{a_meta.get('desc')}")

        mat_s, dha_s, nyaya = generate_philosophical_narration(avg_vec.values)
        if nyaya: st.success("⚖️ **NYAYA EQUILIBRIUM**: Harmonized system detected.")
        
        n_col1, n_col2 = st.columns(2)
        with n_col1:
            st.markdown("**Materialist Lens**")
            for s in mat_sentences: st.write(f"• {s}") # Fix: ensure var name match
        with n_col2:
            st.markdown("**Dharmic Lens**")
            for s in dha_sentences: st.write(f"• {s}") # Fix: ensure var name match
    else:
        st.warning("Insufficient hits to render topology.")

# --- 4. ADMINISTRATIVE ---
elif page == "Under the Hood":
    st.title("🛠️ Administrative Inspectability")
    tab1, tab2 = st.tabs(["🗄️ SQLite Data Store", "📜 System Logs"])
    with tab1:
        if os.path.exists(DB_NAME):
            conn = sqlite3.connect(DB_NAME)
            st.dataframe(pd.read_sql_query("SELECT * FROM lexicon", conn), use_container_width=True)
            conn.close()
    with tab2:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: st.code(f.read(), language="text")