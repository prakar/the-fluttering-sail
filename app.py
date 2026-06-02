"""
# ⛵ THE FLUTTERING SAIL: 8D EPISTEMIC ENGINE
# Project: DeScideratum (Initial Primitive)
# Author: Prasanna Varun Karmarkar
# License: MIT

## INTENT & ARCHITECTURE
This application serves as an interactive diagnostic for "Stereo Epistemic Alignment." 
It evaluates text corpora across two distinct 4D lenses, which together form an 
8-dimensional vector space.

### THE STEREO LENSES:
1. LENS_01 (Post-Enlightenment/Baconian): Utility, Fairness, Power, Mimetic.
   Maps the materialist, transactional, and systemic forces of modernity.
2. LENS_02 (Pre-Enlightenment/Dharmic): Telos, Structure, Dharma, Consciousness.
   Maps the essentialist, purposeful, and cosmic rhythms of tradition.

### TRANSITION TO LITERATE STATE:
- Unified Engine: Logic, seed data, and visualization parameters are co-located.
- Stereo Radar: Replaces 2D scatter plots with interactive polar tension charts.
- Dimensional Mapping: Uses the root-mean-square (RMS) of each lens to calculate
  the "Shear Tension" ($T_{shear}$) between material and dharmic axes.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from tranche_master import SEEDS

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="The Fluttering Sail Engine", layout="wide")

# Custom CSS for the "Sail" aesthetic
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CORE COMPUTATIONAL LOGIC ---

def evaluate_text(text):
    """
    Parses input text, matches tokens against the master seed lexicon,
    and returns the 8D mean vector.
    """
    clean_text = re.sub(r'[^\w\s]', '', text.lower())
    tokens = clean_text.split()
    
    cumulative_vector = np.zeros(8)
    matched_tokens = []
    
    for token in tokens:
        if token in SEEDS:
            matched_tokens.append(token)
            cumulative_vector += np.array(SEEDS[token])
            
    if not matched_tokens:
        return None, []
        
    return (cumulative_vector / len(matched_tokens)), matched_tokens

def create_stereo_radar(vector, dimensions, title, color):
    """
    Generates an interactive Plotly Polar chart representing a single Lens.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vector,
        theta=dimensions,
        fill='toself',
        name=title,
        line_color=color,
        fillcolor=color,
        opacity=0.6
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="gray"),
            angularaxis=dict(gridcolor="gray")
        ),
        showlegend=False,
        title=dict(text=title, font=dict(size=18, color=color)),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- UI HEADER ---
st.title("⛵ THE FLUTTERING SAIL")
st.markdown("### *DeScideratum Primitive v1.1: Stereo Radar Diagnostic*")
st.divider()

# --- INPUT HANDLING ---
SAMPLES = {
    "Baconian Strategy": "We must execute a strategy to leverage systemic throughput and optimize asset scale. Exploiting these process efficiencies will yield immediate margin improvements.",
    "Dharmic Alignment": "Our alignment with natural rhythm and duty preserves communal wholeness. True justice requires fraternity and a shared sacrifice to secure liberty for every single citizen."
}

user_text = st.sidebar.text_area("Analysis Target:", value=SAMPLES["Baconian Strategy"], height=200)

# --- EXECUTION ---
avg_vec, matches = evaluate_text(user_text)

if avg_vec is not None:
    # Split 8D into 4D + 4D
    lens1_vec = avg_vec[0:4]
    lens1_dims = ["Utility", "Fairness", "Power", "Mimetic"]
    
    lens2_vec = avg_vec[4:8]
    lens2_dims = ["Telos", "Structure", "Dharma", "Consciousness"]

    # Visual Layout
    col_viz1, col_viz2 = st.columns(2)
    
    with col_viz1:
        st.plotly_chart(create_stereo_radar(lens1_vec, lens1_dims, "LENS_01: POST-ENLIGHTENMENT", "#FF4B4B"), use_container_width=True)
        
    with col_viz2:
        st.plotly_chart(create_stereo_radar(lens2_vec, lens2_dims, "LENS_02: PRE-ENLIGHTENMENT", "#1C83E1"), use_container_width=True)

    # --- SYNTHESIS METRICS ---
    st.divider()
    m_axis = np.mean(np.abs(lens1_vec))
    d_axis = np.mean(np.abs(lens2_vec))
    shear = abs(m_axis - d_axis)

    m1, m2, m3 = st.columns(3)
    m1.metric("Materialist Intensity (M)", f"{m_axis:.2f}")
    m2.metric("Dharm
