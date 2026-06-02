"""
# ⛵ THE FLUTTERING SAIL: 8D EPISTEMIC ENGINE
# Project: DeScideratum 
# Version: 1.2 (Corrected & Database-Aware)

## INTENT
This script is the primary UI and logic coordinator. It performs three roles:
1. TOKENIZATION: Scans text for anchor points.
2. PERSISTENCE CHECK: Pulls 8D vectors from SQLite (Primary) or Tranche Master (Fallback).
3. VISUALIZATION: Renders Stereo Radars to visualize metaphysical tension.

## LITERATE UPDATES:
- Fixed SyntaxError: Re-established full string literals for metrics.
- Hybrid Data Access: Implemented a 'Try-DB-then-Dict' pattern for tokens.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
import sqlite3
import os
from tranche_master import SEEDS

# --- DATA ACCESS LAYER (LITERATE PATTERN) ---

def get_token_vector(word):
    """
    Attempts to fetch vector from SQLite database. 
    Falls back to static dictionary if DB is missing or token is not found.
    """
    db_path = "epistemic_lexicon.db"
    
    # 1. Attempt SQLite Lookup
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT u, f, p, m, t, s, d, c FROM lexicon WHERE word = ?", (word.lower(),))
            result = cursor.fetchone()
            conn.close()
            if result:
                return np.array(result)
        except Exception:
            pass # Silent fallback to dictionary
            
    # 2. Dictionary Fallback
    if word.lower() in SEEDS:
        return np.array(SEEDS[word.lower()])
        
    return None

def evaluate_text(text):
    """
    Parses input text and calculates the 8D mean vector using hybrid lookup.
    """
    clean_text = re.sub(r'[^\w\s]', '', text.lower())
    tokens = clean_text.split()
    
    cumulative_vector = np.zeros(8)
    matched_tokens = []
    
    for token in tokens:
        vec = get_token_vector(token)
        if vec is not None:
            matched_tokens.append(token)
            cumulative_vector += vec
            
    if not matched_tokens:
        return None, []
        
    return (cumulative_vector / len(matched_tokens)), matched_tokens

# --- VISUALIZATION LAYER ---

def create_stereo_radar(vector, dimensions, title, color):
    """
    Generates the 'Fluttering Sail' style Plotly Radar chart.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vector,
        theta=dimensions,
        fill='toself',
        name=title,
        line_color=color,
        fillcolor=color,
        opacity=0.4
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(size=12))
        ),
        showlegend=False,
        title=dict(text=title, font=dict(size=16, color=color)),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

# --- STREAMLIT UI EXECUTION ---

st.set_page_config(page_title="The Fluttering Sail Engine", layout="wide")

st.title("⛵ THE FLUTTERING SAIL")
st.markdown("### *DeScideratum Primitive: Stereo Radar Diagnostic*")
st.divider()

# Sidebar Setup
SAMPLES = {
    "Corporate Baconian": "We must execute a strategy to leverage systemic throughput and optimize asset scale.",
    "Classical Dharmic": "Our alignment with natural rhythm and duty preserves communal wholeness and sacrifice."
}
user_text = st.sidebar.text_area("Analysis Target:", value=SAMPLES["Corporate Baconian"], height=200)

avg_vec, matches = evaluate_text(user_text)

if avg_vec is not None:
    # 8D -> 4D/4D Split
    lens1_vec = avg_vec[0:4]
    lens1_dims = ["Utility", "Fairness", "Power", "Mimetic"]
    
    lens2_vec = avg_vec[4:8]
    lens2_dims = ["Telos", "Structure", "Dharma", "Consciousness"]

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_stereo_radar(lens1_vec, lens1_dims, "LENS_01: MATERIALIST", "#FF4B4B"), use_container_width=True)
    with col2:
        st.plotly_chart(create_stereo_radar(lens2_vec, lens2_dims, "LENS_02: DHARMIC", "#1C83E1"), use_container_width=True)

    # Metrics Section (Fixed from previous SyntaxError)
    st.divider()
    m_axis = np.mean(np.abs(lens1_vec))
    d_axis = np.mean(np.abs(lens2_vec))
    shear = abs(m_axis - d_axis)

    m1, m2, m3 = st.columns(3)
    m1.metric("Materialist Intensity (M)", f"{m_axis:.2f}")
    m2.metric("Dharmic Resonance (D)", f"{d_axis:.2f}")
    m3.metric("Shear Tension", f"{shear:.2f}")

    with st.expander("Identified Anchor Tokens"):
        st.write(f"Tokens found: {', '.join(set(matches))}")
else:
    st.warning("Awaiting anchor tokens...")

st.divider()
st.caption("DeScideratum Primitive v1.2 // Open-Source Metaphysical Alignment")
