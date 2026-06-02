"""
# ⛵ THE FLUTTERING SAIL: 8D EPISTEMIC ENGINE (v1.5)
# Project: DeScideratum 

## ARCHITECTURAL INTENT:
1. UNIVERSAL CONTEXT DISPLAY: Ensures 'user_text' is visible for both Custom and Preloaded inputs.
2. DUAL-MODE VISUALIZATION: Maintains 'Stereo Radar' and 'Synthesis Canvas' toggles.
3. SELF-BOOTSTRAP: Auto-initializes SQLite for persistent token management.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
import sqlite3
import os
from tranche_master import SEEDS

# --- 1. BOOTSTRAP LAYER ---

def bootstrap_db():
    db_path = "epistemic_lexicon.db"
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS lexicon 
                          (word TEXT PRIMARY KEY, u REAL, f REAL, p REAL, m REAL, 
                           t REAL, s REAL, d REAL, c REAL, source TEXT)''')
        for word, vec in SEEDS.items():
            cursor.execute("INSERT OR REPLACE INTO lexicon VALUES (?,?,?,?,?,?,?,?,?,?)", 
                           (word, *vec, "Initial Seed Core"))
        conn.commit()
        conn.close()

bootstrap_db()

# --- 2. COMPUTATIONAL ENGINE ---

def get_token_vector(word):
    conn = sqlite3.connect("epistemic_lexicon.db")
    cursor = conn.cursor()
    cursor.execute("SELECT u, f, p, m, t, s, d, c FROM lexicon WHERE word = ?", (word.lower(),))
    result = cursor.fetchone()
    conn.close()
    return np.array(result) if result else None

def evaluate_text(text):
    clean_text = re.sub(r'[^\w\s]', '', text.lower())
    tokens = clean_text.split()
    cumulative_vector = np.zeros(8)
    matches = []
    for token in tokens:
        vec = get_token_vector(token)
        if vec is not None:
            matches.append(token)
            cumulative_vector += vec
    if not matches: return None, []
    return (cumulative_vector / len(matches)), matches

# --- 3. VISUALIZATION ENGINE ---

def draw_radar(vectors, titles, colors, is_merged=False):
    fig = go.Figure()
    theta_labels = ["Utility", "Fairness", "Power", "Mimetic"] if not is_merged else \
                   ["Utility", "Telos", "Structure", "Power", "Mimetic", "Dharma", "Consciousness", "Fairness"]
    
    for vec, title, color in zip(vectors, titles, colors):
        fig.add_trace(go.Scatterpolar(
            r=vec, theta=theta_labels,
            fill='toself', name=title, line_color=color, opacity=0.4
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], gridcolor="rgba(255,255,255,0.1)")),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=20, b=20)
    )
    return fig

# --- 4. UI CONFIGURATION ---

st.set_page_config(page_title="The Fluttering Sail", layout="wide")
st.sidebar.title("Engine Configuration")

input_mode = st.sidebar.radio("Input Source", ["Custom Text Entry", "Preloaded Core Corpora"])

corpora_samples = {
    "Baconian Strategy (Modern)": "We must execute a strategy to leverage systemic throughput and optimize asset scale. Exploiting these process efficiencies will yield immediate margin improvements.",
    "Dharmic Fragment (Classical)": "Our alignment with natural rhythm and duty preserves communal wholeness. True justice requires fraternity and a shared sacrifice to secure liberty for every single citizen.",
    "Lexicon Bootstrap (Seed List)": " ".join(SEEDS.keys())
}

# Unified user_text capture logic
if input_mode == "Preloaded Core Corpora":
    selected_corpus = st.sidebar.selectbox("Choose a preloaded document:", list(corpora_samples.keys()))
    user_text = corpora_samples[selected_corpus]
else:
    user_text = st.sidebar.text_area("Paste Corpus Segment here:", height=200)

# --- MAIN DASHBOARD ---
st.title("⛵ THE FLUTTERING SAIL")
st.markdown("### *DeScideratum Primitive: Stereo Radar Diagnostic*")

# The Universal Display: Visible for both modes
with st.container():
    st.subheader("📝 Corpus Under Evaluation")
    st.info(user_text)

st.divider()

# View Mode Toggle
view_mode = st.radio("Display Mode", ["Stereo Radar (De-Merged)", "Synthesis Canvas (Merged)"], horizontal=True)

avg_vec, matches = evaluate_text(user_text)

if avg_vec is not None:
    if view_mode == "Stereo Radar (De-Merged)":
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(draw_radar([avg_vec[0:4]], ["Materialist"], ["#FF4B4B"]), use_container_width=True)
        with col2:
            st.plotly_chart(draw_radar([avg_vec[4:8]], ["Dharmic"], ["#1C83E1"]), use_container_width=True)
    else:
        st.plotly_chart(draw_radar([avg_vec[0:4], avg_vec[4:8]], ["Materialist", "Dharmic"], ["#FF4B4B", "#1C83E1"], True), use_container_width=True)
    
    st.success(f"**Detected Anchor Tokens:** {', '.join(set(matches))}")
else:
    st.warning("No anchor tokens found in the current corpus.")

st.divider()
st.caption("DeScideratum Primitive v1.5 // Metadata: SQLite Powered // Literate Execution")
