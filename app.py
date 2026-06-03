import streamlit as st
import json
import os
import sqlite3
import pandas as pd

# --- LOAD ASSETS ---
def load_json(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

CORPORA = load_json("corpora.json")
DB_NAME = "epistemic_lexicon.db"

st.set_page_config(page_title="The Fluttering Sail", layout="wide")

# Navigation logic to keep Admin separate from Visuals
page = st.sidebar.selectbox("Navigation", ["Main Analysis", "Under the Hood"])

if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")
    
    with st.sidebar:
        st.header("Engine Configuration")
        # 1. Popular names used in selectbox
        selected_popular_name = st.selectbox("Select Benchmark Document", list(CORPORA.keys()))
        doc_data = CORPORA[selected_popular_name]
        input_text = doc_data["text"]
        taxonomy_label = doc_data["taxonomy"]

    # 2. Re-instated labeling logic & 3. Full text display
    st.subheader(f"📝 Corpus Under Evaluation is Sourced from {taxonomy_label}:")
    st.markdown(f"**{selected_popular_name}**")
    st.info(input_text)

    # --- METRICS & RADAR ---
    st.markdown("### 📊 Engine Diagnostics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tokens", len(input_text.split()))
    
    st.markdown("---")
    st.markdown("### 🕸️ Multi-Polar Ethics Topology")
    # Radar rendering logic would go here
    st.info("The Radar Canvas is now cleared of Admin clutter and ready for coordinates.")

elif page == "Under the Hood":
    st.title("🛠️ Administrative Inspectability")
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        st.dataframe(pd.read_sql_query("SELECT * FROM lexicon", conn), use_container_width=True)
        conn.close()
    else:
        st.warning("Database not found. Run agent_expand.py first.")