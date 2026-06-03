"""
# ⛵ THE FLUTTERING SAIL: MAIN UI & ACADEMIC WORKBENCH (v2.1)
# Features: Dynamic Asset Loading, Short-Label Dropdowns, and Under-The-Hood Admin View
"""

import streamlit as st
import json
import os
import numpy as np
import pandas as pd
import sqlite3
import logging

# --- 1. CENTRALIZED LOGGING INFRASTRUCTURE ---
LOG_FILE = "framework.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler() # Mirrors logs to the server terminal console
    ]
)

def read_execution_logs():
    if not os.path.exists(LOG_FILE):
        return "No execution logs recorded yet."
    with open(LOG_FILE, "r") as f:
        # Return last 100 log lines to keep the UI lightweight
        lines = f.readlines()
        return "".join(lines[-100:])

# --- 2. DYNAMIC DATA ASSET LOADERS ---
def load_json_asset(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    logging.error(f"Asset file {filename} could not be located.")
    return {}

PHILOSOPHICAL_MAP = load_json_asset("taxonomy.json")
CORPORA_SAMPLES = load_json_asset("corpora.json")
DB_NAME = "epistemic_lexicon.db"

# --- 3. UI INITIALIZATION & LAYOUT ---
st.set_page_config(page_title="The Fluttering Sail", layout="wide")

st.title("⛵ THE FLUTTERING SAIL")
st.markdown("### A Dynamical Multi-Polar Ethics Framework")
logging.info("Main dashboard execution frame rendered.")

# --- 4. ENGINE SIDEBAR INPUT COMPONENT ---
with st.sidebar:
    st.header("Engine Configuration")
    input_mode = st.radio("Input Source", ["Preloaded Calibration Corpora", "Custom Text Entry"])
    
    if input_mode == "Preloaded Calibration Corpora":
        # FIX: Shortened keys for the dropdown to eliminate visual truncation
        selected_key = st.selectbox("Select Benchmark Document", list(CORPORA_SAMPLES.keys()))
        input_text = CORPORA_SAMPLES[selected_key]
    else:
        selected_key = "Custom Analysis"
        input_text = st.text_area("Enter Text for Evaluation", height=200)

# --- 5. FIXED GEOMETRY CORRECTIONS (Ref: Screenshot 2026-06-03 at 11.35.16 AM.png) ---
# FIX: Append text type cleanly to header text frame
st.subheader(f"📝 Corpus Under Evaluation: {selected_key}")
st.info(input_text)

# --- 6. STATISTICAL METRICS ROW ---
st.markdown("### 📊 Engine Diagnostics & Reproducibility Metrics")
col1, col2, col3, col4 = st.columns(4)

total_tokens = len(input_text.split()) if input_text else 0

# Scan active SQLite database to check for real anchor matches dynamically
unique_hits = 0
try:
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        df_check = pd.read_sql_query("SELECT word FROM lexicon", conn)
        words_in_db = set(df_check['word'].str.lower().tolist())
        input_words = set(input_text.lower().replace(",", "").replace(".", "").split())
        unique_hits = len(words_in_db.intersection(input_words))
        conn.close()
except Exception as e:
    logging.warning(f"Failed parsing real-time hit densities from DB: {e}")

with col1: st.metric("Total Tokens Evaluated", total_tokens)
with col2: st.metric("Unique Anchor Hits", unique_hits)
with col3: st.metric("Lexical Hit Density", f"{(unique_hits/total_tokens)*100:.1f}%" if total_tokens > 0 else "0.0%")
with col4: st.metric("Active Seed Vault Volume", f"{len(PHILOSOPHICAL_MAP)} dimensions")

st.markdown("---")

# --- [Your existing complex Radar Charts, Synthesis Canvas drawings, and analytics logic live here] ---
display_mode = st.radio("Display Mode", ["Stereo Radar (De-Merged)", "Synthesis Canvas (Merged)"], horizontal=True)
st.write(f"*(Rendering active view configuration: {display_mode})*")


# ==============================================================================
# --- 7. QUALITY-OF-LIFE ADMIN COMPONENT: "UNDER THE HOOD" INSPECTABILITY ---
# ==============================================================================
st.markdown("---")
with st.expander("🛠️ Under the Hood: Administrative Inspectability Panel", expanded=False):
    st.markdown("This developer view provides raw tracking data, logging states, and analytical engine metrics.")
    
    tab1, tab2 = st.tabs(["🗄️ SQLite Database Reader", "📜 System Execution Logs"])
    
    # TAB 1: Live DB Viewer & Data Maintenance Matrix
    with tab1:
        st.markdown("#### Live Vector Lexicon Data Storefront")
        if not os.path.exists(DB_NAME):
            st.warning(f"No active database database footprint found matching name: `{DB_NAME}`. Run your ingestion scripts first.")
        else:
            try:
                conn = sqlite3.connect(DB_NAME)
                # Fetch data directly to populate a clean web layout
                df_lexicon = pd.read_sql_query("SELECT * FROM lexicon", conn)
                conn.close()
                
                # Add real-time text lookup filtering capability
                search_query = st.text_input("🔍 Filter Lexicon Tokens Matrix By Word Keyword:", "")
                if search_query:
                    df_lexicon = df_lexicon[df_lexicon['word'].str.contains(search_query.lower(), case=False)]
                
                st.dataframe(df_lexicon, use_container_width=True, hide_index=True)
                st.caption(f"Showing {len(df_lexicon)} tracked token vector states populated inside production storage asset.")
                
                # Destructive system management reset option
                st.markdown("##### Administrative Utilities")
                if st.button("⚠️ Purge Active Epistemic Database", type="secondary"):
                    os.remove(DB_NAME)
                    st.success("Operational database cache purged successfully. Refresh application context.")
                    logging.warning("Database asset intentionally purged via Web UI Admin Panel.")
                    
            except Exception as db_err:
                st.error(f"Error accessing underlying engine data structures: {db_err}")
    
    # TAB 2: Live Log Parsing System Viewer
    with tab2:
        st.markdown("#### Live Architectural Execution Pipeline Logs")
        log_content = read_execution_logs()
        
        # Display logs inside a clear code block replicating a Linux workspace console
        st.code(log_content, language="text", line_numbers=True)
        
        if st.button("Clear Log Console History"):
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
                st.success("Log tracking stream cleared.")
                logging.info("Workspace logger metrics intentionally flushed.")
                st.rerun()