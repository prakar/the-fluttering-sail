"""
# ⛵ THE FLUTTERING SAIL: TOTAL SYSTEM INTEGRATION (v2.8)
# 
# LITERATE DESIGN: This module acts as the 'Synthesizer & Diagnostic Engine'.
# It evaluates raw coordinate topologies against mathematical failure boundaries.
# FEATURE MANIFEST: 
# 1. Radar Plots (Materialist/Dharmic)
# 2. Nyaya Meta-Check (Equilibrium detection)
# 3. Geometric Failure Diagnostics (Baconian, Mimetic Shear, Ascetic, Purushartha)
# 4. Descriptive Narrative Engine (Prose mapping)
"""

import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import logging

# --- 1. AUDIT INFRASTRUCTURE ---
LOG_FILE = "framework.log"
DB_NAME = "epistemic_lexicon.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode='a'), logging.StreamHandler()]
)

def load_json_asset(filename):
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f: return json.load(f)
    except Exception as e:
        logging.error(f"Asset Load Failure ({filename}): {e}")
    return {}

CORPORA = load_json_asset("corpora.json")
SCHEMA = load_json_asset("epistemic_schema.json")

st.set_page_config(page_title="The Fluttering Sail", layout="wide")
page = st.sidebar.selectbox("Navigation Bridge", ["Main Analysis", "Under the Hood"])

# --- 2. DIAGNOSTIC LOGIC ENGINES ---

def get_intensity_label(val):
    for entry in SCHEMA.get("INTENSITY_SCALE", []):
        if val >= entry["threshold"]: return entry["label"]
    return "Unknown"

def evaluate_geometric_failures(vector_dict):
    """
    Evaluates vector coordinates against known geometric collapse zones
    and holistic synthesis thresholds defined in the framework specifications.
    """
    u, f, p, m = vector_dict['u'], vector_dict['f'], vector_dict['p'], vector_dict['m']
    t, s, d, c = vector_dict['t'], vector_dict['s'], vector_dict['d'], vector_dict['c']
    
    alerts = []
    modes = SCHEMA.get("FAILURE_MODES", {})
    
    # 1. Baconian Collapse Rule
    if u >= 0.80 and t <= 0.15 and s <= 0.10:
        alerts.append(("error", modes.get("baconian_collapse", {})))
        
    # 2. Mimetic Shear Rule
    if p >= 0.75 and m >= 0.70 and d <= 0.20 and c <= 0.15:
        alerts.append(("error", modes.get("mimetic_shear", {})))
        
    # 3. Ascetic Drift Rule
    if c >= 0.90 and t >= 0.85 and u <= 0.20 and f <= 0.20:
        alerts.append(("warning", modes.get("ascetic_drift", {})))
        
    # 4. Equilibrium Zone Rule
    if f >= 0.70 and u >= 0.60 and d >= 0.75 and t >= 0.75:
        alerts.append(("success", modes.get("equilibrium_zone", {})))
        
    return alerts

def generate_philosophical_narration(vector):
    """
    Maps vector magnitudes to verbal intensity tags and auto-generates descriptive prose.
    """
    dim_keys = ['u', 'f', 'p', 'm', 't', 's', 'd', 'c']
    mat_sentences = []  
    dha_sentences = []  
    lineage_defs = SCHEMA.get("LINEAGE_MAP", {}) 

    for idx, key in enumerate(dim_keys):
        score = vector[idx]
        intensity = get_intensity_label(score)
        mapping = lineage_defs.get(key, {})
        
        if intensity == "Vestigial": continue
            
        name = mapping.get('thinker') if mapping.get('thinker') else mapping.get('school')
        narrative_sentence = (
            f"Exhibits a **{intensity}** ({score:.2f}) alignment with **{name}** "
            f"({mapping.get('school')}), indicating a clear pattern of {mapping.get('desc')}"
        )
        
        if idx < 4: mat_sentences.append(narrative_sentence)
        else: dha_sentences.append(narrative_sentence)
            
    nyaya_triggered = np.std(vector) < 0.15 and np.mean(vector) > 0.4
    return mat_sentences, dha_sentences, nyaya_triggered

# --- 3. MAIN ANALYSIS PAGE ---
if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")
    
    with st.sidebar:
        st.header("Engine Configuration")
        selected_popular_name = st.selectbox("Select Benchmark Document", list(CORPORA.keys()))
        doc_data = CORPORA.get(selected_popular_name, {})
        input_text = doc_data.get("text", "")
        taxonomy_label = doc_data.get("taxonomy", "Unspecified")

    st.subheader(f"📝 Corpus Under Evaluation is Sourced from {taxonomy_label}:")
    st.info(input_text)

    # --- 4. DIAGNOSTICS & METRICS ---
    st.markdown("### 📊 Engine Diagnostics")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    df_vectors = pd.DataFrame()
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        input_tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
        query = f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(input_tokens))})"
        df_vectors = pd.read_sql_query(query, conn, params=input_tokens)
        v_res = pd.read_sql_query("SELECT count(*) as count FROM lexicon", conn)
        vault_count = v_res.iloc[0]['count']
        conn.close()

    m_col1.metric("Total Tokens Evaluated", len(input_text.split()))
    m_col2.metric("Unique Anchor Hits", len(df_vectors))
    m_col3.metric("Lexical Hit Density", f"{(len(df_vectors)/len(input_text.split()))*100:.1f}%" if input_text else "0%")
    m_col4.metric("Active Seed Vault Volume", f"{vault_count if 'vault_count' in locals() else 0} entries")

    st.markdown("---")

    # --- 5. TOPOLOGY & QUALITATIVE SYNTHESIS ---
    if not df_vectors.empty:
        avg_vec = df_vectors[['u', 'f', 'p', 'm', 't', 's', 'd', 'c']].mean()
        avg_dict = avg_vec.to_dict()
        
        st.markdown("### 🕸️ Multi-Polar Ethics Topology")
        c_left, c_right = st.columns(2)
        
        # --- CORRECTED RADAR PLOTTING LOGIC ---
        # Plotting logic remains consistent with previous working version
        # Colors converted to explicit RGBA to satisfy Plotly validator
        lens_colors = {
            "MATERIALIST": "rgba(255, 65, 54, 1)",      # Solid Red
            "MATERIALIST_FILL": "rgba(255, 65, 54, 0.3)", # Transparent Red
            "DHARMIC": "rgba(0, 116, 217, 1)",          # Solid Blue
            "DHARMIC_FILL": "rgba(0, 116, 217, 0.3)"    # Transparent Blue
        }

        for col, lens_name, dims in zip([c_left, c_right], ["MATERIALIST", "DHARMIC"], 
                                               [['f','p','m','u'], ['s','t','c','d']]):
            with col:
                st.markdown(f"#### LENS: {lens_name}")
                
                # Fetch color based on lens name
                line_color = lens_colors[lens_name]
                fill_color = lens_colors[f"{lens_name}_FILL"]

                fig = go.Figure(data=go.Scatterpolar(
                    r=[avg_dict[d] for d in dims],
                    theta=[SCHEMA['LINEAGE_MAP'][d]['label'] for d in dims],
                    fill='toself', 
                    fillcolor=fill_color, 
                    line=dict(color=line_color)
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])), 
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

        # --- SYSTEM ALERT TRIGGERS & NARRATION CONTAINER ---
        st.markdown("---")
        with st.container():
            st.markdown("### 📜 Philosophical Lineage & Narration")
            
            # 1. Execute Geometric Checks
            geometric_alerts = evaluate_geometric_failures(avg_dict)
            for alert_type, alert_meta in geometric_alerts:
                if alert_type == "error":
                    st.error(f"**{alert_meta.get('title')}**\n\n{alert_meta.get('desc')}")
                elif alert_type == "warning":
                    st.warning(f"**{alert_meta.get('title')}**\n\n{alert_meta.get('desc')}")
                elif alert_type == "success":
                    st.success(f"**{alert_meta.get('title')}**\n\n{alert_meta.get('desc')}")

            # 2. Execute Nyaya and Prose Synthesis
            mat_s, dha_s, nyaya = generate_philosophical_narration(avg_vec.values)
            
            if nyaya:
                st.info("⚖️ **NYAYA EQUILIBRIUM COGNIZANCE**: This text exhibits high systematic harmony with tightly balanced global variance.")
            
            n_col1, n_col2 = st.columns(2)
            with n_col1:
                st.markdown("**Lens 01: Materialist Profile**")
                for s in mat_s: st.write(f"- {s}")
            with n_col2:
                st.markdown("**Lens 02: Dharmic Profile**")
                for s in dha_s: st.write(f"- {s}")
            
        logging.info(f"Analysis and structural failure modes parsed for {selected_popular_name}.")
    else:
        st.warning("Awaiting anchor hits to initialize the topology.")

elif page == "Under the Hood":
    st.title("🛠️ Administrative Inspectability")
    tab1, tab2 = st.tabs(["🗄️ SQLite Data Store", "📜 System Logs"])
    with tab1:
        if os.path.exists(DB_NAME):
            conn = sqlite3.connect(DB_NAME)
            st.dataframe(pd.read_sql_query("SELECT * FROM lexicon", conn), use_container_width=True)
            if st.button("⚠️ Purge Database"):
                conn.close(); os.remove(DB_NAME); st.rerun()
            conn.close()
    with tab2:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: st.code(f.read(), language="text")