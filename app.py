"""
# ⛵ THE FLUTTERING SAIL: LITERATE UI & ACADEMIC WORKBENCH (v2.4)
# 
# PHILOSOPHY: This module serves as the 'Observational Deck'. Its primary duty
# is to maintain a stateful bridge between the SQLite vector store and the 
# visual radar topology. It prioritizes data integrity and clear audit trails.
"""

import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import logging

# --- 1. THE AUDIT INFRASTRUCTURE ---
# We treat logging as a first-class citizen to ensure every UI interaction 
# and database query is traceable for academic verification.
LOG_FILE = "framework.log"
DB_NAME = "epistemic_lexicon.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode='a'), logging.StreamHandler()]
)

def load_json_asset(filename):
    """Safely ingests JSON assets with robust error trapping for missing files."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                logging.info(f"Asset Ingested: {filename}")
                return json.load(f)
        logging.warning(f"Expected asset {filename} not found. Utilizing empty state.")
    except Exception as e:
        logging.error(f"Critical failure reading {filename}: {e}")
    return {}

# --- 2. ASSET INITIALIZATION ---
# 'CORPORA' provides the text and taxonomy mapping.
# 'PHILOSOPHICAL_MAP' provides the 8-dimensional axis definitions.
CORPORA = load_json_asset("corpora.json")
PHILOSOPHICAL_MAP = load_json_asset("taxonomy.json")

st.set_page_config(page_title="The Fluttering Sail", layout="wide")

# Navigation Bridge: Isolating execution (Main) from introspection (Under the Hood).
page = st.sidebar.selectbox("Navigation Bridge", ["Main Analysis", "Under the Hood"])

# --- 3. PRIMARY ANALYSIS INTERFACE ---
if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")
    st.markdown("---")
    
    with st.sidebar:
        st.header("Engine Configuration")
        # We display the Popular Name (UI-friendly) but resolve to the Taxonomy (Model-friendly).
        selected_popular_name = st.selectbox("Select Benchmark Document", list(CORPORA.keys()))
        doc_data = CORPORA.get(selected_popular_name, {})
        input_text = doc_data.get("text", "No text found.")
        taxonomy_label = doc_data.get("taxonomy", "Unknown Paradigm")
        logging.info(f"Observer context shifted to: {selected_popular_name}")

    # LITERATE DISPLAY: Explicitly defining the source and taxonomy hierarchy.
    st.subheader(f"📝 Corpus Under Evaluation is Sourced from {taxonomy_label}:")
    st.markdown(f"**Document Identifier:** {selected_popular_name}")
    st.info(input_text) # Full text rendering, no truncation.

    # --- 4. DIAGNOSTIC METRIC CALCULATION ---
    # This block performs real-time intersections between the UI selection and the DB.
    st.markdown("### 📊 Engine Diagnostics & Reproducibility Metrics")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    total_tokens = len(input_text.split()) if input_text else 0
    unique_hits = 0
    df_vectors = pd.DataFrame()

    if os.path.exists(DB_NAME):
        try:
            conn = sqlite3.connect(DB_NAME)
            # Sanitize input tokens for precise DB lookup matching
            input_tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
            query = f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(input_tokens))})"
            df_vectors = pd.read_sql_query(query, conn, params=input_tokens)
            unique_hits = len(df_vectors)
            
            # Count total lexicon size for the Seed Vault metric
            vault_count = pd.read_sql_query("SELECT count(*) as count FROM lexicon", conn).iloc[0]['count']
            conn.close()
        except Exception as e:
            logging.error(f"Database intersection error: {e}")
            vault_count = 0

    m_col1.metric("Total Tokens Evaluated", total_tokens)
    m_col2.metric("Unique Anchor Hits", unique_hits)
    m_col3.metric("Lexical Hit Density", f"{(unique_hits/total_tokens)*100:.1f}%" if total_tokens > 0 else "0%")
    m_col4.metric("Active Seed Vault Volume", f"{vault_count} entries")

    st.markdown("---")

    # --- 5. TOPOLOGICAL RADAR RENDERING ---
    # Mapping the 8D space into two semantic lenses: Materialist and Dharmic.
    st.markdown("### 🕸️ Multi-Polar Ethics Topology")
    
    if not df_vectors.empty:
        # Calculate the Mean Epistemic Center for the selection
        avg_vec = df_vectors[['u', 'f', 'p', 'm', 't', 's', 'd', 'c']].mean()
        
        c_left, c_right = st.columns(2)
        
        # LENS 01: The Materialist Perspective (U, F, P, M)
        with c_left:
            st.markdown("#### LENS_01: MATERIALIST")
            fig1 = go.Figure(data=go.Scatterpolar(
                r=[avg_vec['f'], avg_vec['p'], avg_vec['m'], avg_vec['u']],
                theta=['Fairness', 'Power', 'Mimetic', 'Utility'],
                fill='toself', fillcolor='rgba(255, 65, 54, 0.3)', line=dict(color='#FF4136')
            ))
            fig1.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)

        # LENS 02: The Dharmic Perspective (S, T, C, D)
        with c_right:
            st.markdown("#### LENS_02: DHARMIC")
            fig2 = go.Figure(data=go.Scatterpolar(
                r=[avg_vec['s'], avg_vec['t'], avg_vec['c'], avg_vec['d']],
                theta=['Structure', 'Telos', 'Consciousness', 'Dharma'],
                fill='toself', fillcolor='rgba(0, 116, 217, 0.3)', line=dict(color='#0074D9')
            ))
            fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            
        logging.info("Vector topology successfully rendered.")
    else:
        st.warning("Awaiting anchor hits to initialize topology. Ensure your lexicon is seeded.")

# --- 6. ADMINISTRATIVE UNDER THE HOOD ---
elif page == "Under the Hood":
    st.title("🛠️ Administrative Inspectability")
    st.markdown("Accessing the raw structural state of the framework.")
    
    tab1, tab2 = st.tabs(["🗄️ SQLite Data Store", "📜 System Logs"])
    
    with tab1:
        if os.path.exists(DB_NAME):
            conn = sqlite3.connect(DB_NAME)
            st.dataframe(pd.read_sql_query("SELECT * FROM lexicon", conn), use_container_width=True)
            conn.close()
            
            if st.button("⚠️ Purge Database"):
                os.remove(DB_NAME)
                st.success("Database purged.")
                logging.warning("Manual purge executed.")
        else:
            st.warning("Database not found.")
            
    with tab2:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                st.code(f.read(), language="text")