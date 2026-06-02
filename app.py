"""
# ⛵ THE FLUTTERING SAIL: 8D EPISTEMIC ENGINE (v1.6)
# Project: A Dynamical Multi-Polar Ethics Framework

## ARCHITECTURAL INTENT:
1. UNIVERSAL CONTEXT DISPLAY: Retains the explicit corpus visualization area.
2. PERMANENT COLUMNS: Adds distinct 'Materialist Score' and 'Dharmic Score' headers.
3. NARRATION ENGINE: Maps 8D metrics to the Shad-Darshanas and Western philosophy.
4. SANITIZED INTERFACE: Cleanses all non-existent framework references.
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

# --- 3. NARRATION ENGINE CONSTANTS & LOGIC ---

PHILOSOPHICAL_MAP = {
    "Utility": {"school": "Utilitarianism (Consequentialism)", "thinker": "Jeremy Bentham", "desc": "maximizing transactional outcomes, utility, and systemic efficiency."},
    "Fairness": {"school": "Deontological Ethics", "thinker": "John Rawls", "desc": "structural equity, rights, and fairness under a veil of ignorance."},
    "Power": {"school": "Realpolitik / Conflict Theory", "thinker": "Machiavelli / Marx", "desc": "the consolidation of material leverage, systemic control, and competitive struggle."},
    "Mimetic": {"school": "Mimetic Theory", "thinker": "René Girard", "desc": "the undercurrents of social imitation, competitive desire, and collective trends."},
    "Telos": {"school": "Virtue Ethics / Yoga School", "thinker": "Aristotle", "desc": "the pursuit of a 'Final Cause', ultimate purpose, and practical self-realization."},
    "Structure": {"school": "Vaisheshika / Structuralism", "thinker": "Kanada / Aquinas", "desc": "organizing reality into strict categories, atomic blocks, and structural hierarchies."},
    "Dharma": {"school": "Purva Mimamsa", "thinker": "Jaimini", "desc": "unwavering adherence to cosmic ritual duty, scriptural rules, and linguistic execution."},
    "Consciousness": {"school": "Advaita Vedanta / Sankhya", "thinker": "Shankara / Kapila", "desc": "the absolute primacy of pure subjective awareness and the field of internal consciousness."}
}

def get_intensity_label(score):
    if score < 0.2: return "Vestigial"
    elif score < 0.4: return "Emergent"
    elif score < 0.7: return "Significant"
    else: return "Dominant"

def generate_philosophical_narration(vector):
    dimensions = ["Utility", "Fairness", "Power", "Mimetic", "Telos", "Structure", "Dharma", "Consciousness"]
    mat_insights = []
    dha_insights = []
    
    for idx, dim in enumerate(dimensions):
        score = vector[idx]
        intensity = get_intensity_label(score)
        mapping = PHILOSOPHICAL_MAP[dim]
        
        # Skip vestigial strings to keep output readable and highly informative
        if intensity == "Vestigial":
            continue
            
        narrative_sentence = f"Exhibits a **{intensity}** ({score:.2f}) alignment with **{mapping['thinker'] if mapping['thinker'] else mapping['school']}** ({mapping['school']}), indicating a clear pattern of {mapping['desc']}"
        
        if idx < 4:
            mat_insights.append(narrative_sentence)
        else:
            dha_insights.append(narrative_sentence)
            
    # Meta Nyaya Logic check for reasoning/epistemological balance
    nyaya_triggered = np.std(vector) < 0.15 and np.mean(vector) > 0.4
    
    return mat_insights, dha_insights, nyaya_triggered

# --- 4. VISUALIZATION ENGINE ---

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

# --- 5. UI CONFIGURATION ---

st.set_page_config(page_title="The Fluttering Sail", layout="wide")
st.sidebar.title("Engine Configuration")

input_mode = st.sidebar.radio("Input Source", ["Custom Text Entry", "Preloaded Core Corpora"])

corpora_samples = {
    "Baconian Strategy (Modern)": "We must execute a strategy to leverage systemic throughput and optimize asset scale. Exploiting these process efficiencies will yield immediate margin improvements.",
    "Dharmic Fragment (Classical)": "Our alignment with natural rhythm and duty preserves communal wholeness. True justice requires fraternity and a shared sacrifice to secure liberty for every single citizen.",
    "Lexicon Bootstrap (Seed List)": " ".join(SEEDS.keys())
}

if input_mode == "Preloaded Core Corpora":
    selected_corpus = st.sidebar.selectbox("Choose a preloaded document:", list(corpora_samples.keys()))
    user_text = corpora_samples[selected_corpus]
else:
    user_text = st.sidebar.text_area("Paste Corpus Segment here:", height=200)

# --- MAIN DASHBOARD DISPLAY ---
st.title("⛵ THE FLUTTERING SAIL")
st.markdown("### *A Dynamical Multi-Polar Ethics Framework*")

# Universal Text View Component
with st.container():
    st.subheader("📝 Corpus Under Evaluation")
    st.info(user_text)

st.divider()

view_mode = st.radio("Display Mode", ["Stereo Radar (De-Merged)", "Synthesis Canvas (Merged)"], horizontal=True)

avg_vec, matches = evaluate_text(user_text)

if avg_vec is not None:
    if view_mode == "Stereo Radar (De-Merged)":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🟥 Materialist Score")
            st.plotly_chart(draw_radar([avg_vec[0:4]], ["Materialist"], ["#FF4B4B"]), use_container_width=True)
        with col2:
            st.markdown("#### 🟦 Dharmic Score")
            st.plotly_chart(draw_radar([avg_vec[4:8]], ["Dharmic"], ["#1C83E1"]), use_container_width=True)
    else:
        st.markdown("#### ⚛️ Superimposed Synthesis Canvas")
        st.plotly_chart(draw_radar([avg_vec[0:4], avg_vec[4:8]], ["Materialist", "Dharmic"], ["#FF4B4B", "#1C83E1"], True), use_container_width=True)
    
    st.success(f"**Detected Anchor Tokens:** {', '.join(set(matches))}")
    
    # --- 6. DYNAMIC NARRATION COMPONENT ---
    st.divider()
    st.subheader("📜 Philosophical Lineage & Narration")
    
    mat_sentences, dha_sentences, nyaya_active = generate_philosophical_narration(avg_vec)
    
    ncol1, ncol2 = st.columns(2)
    with ncol1:
        st.markdown("##### Materialist Lens Insights")
        if mat_sentences:
            for s in mat_sentences: st.write(f"- {s}")
        else:
            st.write("*No pronounced materialist leanings detected above baseline thresholds.*")
            
    with ncol2:
        st.markdown("##### Dharmic Lens Insights")
        if dha_sentences:
            for s in dha_sentences: st.write(f"- {s}")
        else:
            st.write("*No pronounced dharmic leanings detected above baseline thresholds.*")
            
    if nyaya_active:
        st.warning("⚠️ **Nyaya Logic Meta-Condition Triggered:** The system detects tightly integrated multi-polar metrics, showing an epistemologically balanced structure reminiscent of Nyaya analytical logic.")

else:
    st.warning("No anchor tokens found in the current corpus.")

st.divider()
st.caption("Metadata: SQLite Powered // Literate Execution")