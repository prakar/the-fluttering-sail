"""
# ⛵ THE FLUTTERING SAIL: TOTAL SYSTEM INTEGRATION (v2.6)
# 
# LITERATE DESIGN: This module acts as the 'Synthesizer'. It pulls data from 
# the Lexicon (SQLite), the Blueprint (JSON), and the Schema (JSON) 
# to create a comprehensive, multi-modal analysis of ethics.
"""

import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import logging

# --- 1. AUDIT & ASSET INITIALIZATION ---
LOG_FILE = "framework.log"
DB_NAME = "epistemic_lexicon.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode='a'), logging.StreamHandler()]
)

def load_json_asset(filename):
    """Safely ingests structural assets with error trapping and logging."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Asset Load Failure ({filename}): {e}")
    return {}

CORPORA = load_json_asset("corpora.json")
SCHEMA = load_json_asset("epistemic_schema.json")

st.set_page_config(page_title="The Fluttering Sail", layout="wide")
page = st.sidebar.selectbox("Navigation Bridge", ["Main Analysis", "Under the Hood"])

# --- 2. THE NARRATIVE ENGINE (Qualitative Synthesis) ---

def generate_epistemic_narrative(avg_vec):
    """
    Translates raw 8D vectors into a qualitative philosophical profile.
    This function is now 'Dial-Aware', meaning it reads thresholds and 
    lineage mappings from the external epistemic_schema.json.
    """
    def get_intensity_label(val):
        for entry in SCHEMA.get("INTENSITY_SCALE", []):
            if val >= entry["threshold"]:
                return entry["label"]
        return "Unknown"

    lineage_map = SCHEMA.get("LINEAGE_MAP", {})
    narrative_results = []
    
    for key, val in avg_vec.items():
        intensity = get_intensity_label(val)
        # We only surface 'Significant' or 'Dominant' influences for the summary
        if intensity in ["Significant", "Dominant"]:
            meta = lineage_map.get(key, {"label": key, "lineage": "Unknown Source"})
            narrative_results.append({
                "label": meta["label"],
                "intensity": intensity,
                "lineage": meta["lineage"],
                "score": val
            })
            
    return narrative_results

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
    vault_count = 0
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        input_tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
        query = f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(input_tokens))})"
        df_vectors = pd.read_sql_query(query, conn, params=input_tokens)
        
        # Audit the full vault size
        v_res = pd.read_sql_query("SELECT count(*) as count FROM lexicon", conn)
        vault_count = v_res.iloc[0]['count']
        conn.close()

    total_tokens = len(input_text.split()) if input_text else 0
    m_col1.metric("Total Tokens Evaluated", total_tokens)
    m_col2.metric("Unique Anchor Hits", len(df_vectors))
    m_col3.metric("Lexical Hit Density", f"{(len(df_vectors)/total_tokens)*100:.1f}%" if total_tokens > 0 else "0%")
    m_col4.metric("Active Seed Vault Volume", f"{vault_count} entries")

    st.markdown("---")

    # --- 5. TOPOLOGY & QUALITATIVE SYNTHESIS ---
    if not df_vectors.empty:
        # Calculate mean vectors across the 8 dimensions
        avg_vec = df_vectors[['u', 'f', 'p', 'm', 't', 's', 'd', 'c']].mean()
        
        st.markdown("### 🕸️ Multi-Polar Ethics Topology")
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.markdown("#### LENS_01: MATERIALIST")
            fig1 = go.Figure(data=go.Scatterpolar(
                r=[avg_vec['f'], avg_vec['p'], avg_vec['m'], avg_vec['u']],
                theta=['Fairness', 'Power', 'Mimetic', 'Utility'],
                fill='toself', fillcolor='rgba(255, 65, 54, 0.3)', line=dict(color='#FF4136')
            ))
            fig1.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)

        with c_right:
            st.markdown("#### LENS_02: DHARMIC")
            fig2 = go.Figure(data=go.Scatterpolar(
                r=[avg_vec['s'], avg_vec['t'], avg_vec['c'], avg_vec['d']],
                theta=['Structure', 'Telos', 'Consciousness', 'Dharma'],
                fill='toself', fillcolor='rgba(0, 116, 217, 0.3)', line=dict(color='#0074D9')
            ))
            fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        # RESTORED FEATURE: THE QUALITATIVE NARRATIVE LAYER
        st.markdown("### 🧩 Epistemic Synthesis")
        st.write("Quantitative indicators translated through the current scientific schema:")
        
        narrative_data = generate_epistemic_narrative(avg_vec)
        
        if narrative_data:
            narrative_cols = st.columns(2)
            for i, item in enumerate(narrative_data):
                with narrative_cols[i % 2]:
                    st.success(f"**{item['intensity']} {item['label']} ({item['score']:.2f})**")
                    st.caption(f"Conceptual Lineage: {item['lineage']}")
        else:
            st.write("*No dimensions currently meet the 'Significant' threshold for narrative synthesis.*")
            
        logging.info("Visual Topology and Narrative Synthesis successfully rendered.")
    else:
        st.warning("Awaiting anchor hits to initialize the topology.")

# --- 6. ADMINISTRATIVE UNDER THE HOOD ---
elif page == "Under the Hood":
    st.title("🛠️ Administrative Inspectability")
    tab1, tab2 = st.tabs(["🗄️ SQLite Data Store", "📜 System Logs"])
    with tab1:
        if os.path.exists(DB_NAME):
            conn = sqlite3.connect(DB_NAME)
            st.dataframe(pd.read_sql_query("SELECT * FROM lexicon", conn), use_container_width=True)
            if st.button("⚠️ Purge Database"):
                conn.close()
                os.remove(DB_NAME)
                st.rerun()
            conn.close()
    with tab2:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                st.code(f.read(), language="text")