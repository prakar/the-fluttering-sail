"""
# ⛵ THE FLUTTERING SAIL: ARCHITECTURAL WORKBENCH (v1.7)
# Project: A Dynamical Multi-Polar Ethics Framework
# Academic Companion Component

## ARCHITECTURAL INTENT:
1. THE CALIBRATION TEN: Houses the definitive historical text excerpts across 10 fields.
2. ENGINE DIAGNOSTICS: Calculates token-hit density and database saturation metrics.
3. HYBRID MERGE COMPATIBILITY: Reads the expanded 8D high-resolution vectors cleanly.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
import sqlite3
import os

# --- 1. COMPUTATIONAL CORE ---

DB_PATH = "epistemic_lexicon.db"

def get_total_lexicon_count():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM lexicon")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0

def get_token_vector(word):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT u, f, p, m, t, s, d, c FROM lexicon WHERE word = ?", (word.lower().strip(),))
        result = cursor.fetchone()
        conn.close()
        return np.array(result) if result else None
    except Exception:
        return None

def evaluate_text(text):
    # Strip punctuation and tokenize
    clean_text = re.sub(r'[^\w\s]', '', text.lower())
    tokens = clean_text.split()
    if not tokens:
        return None, [], 0
        
    cumulative_vector = np.zeros(8)
    matches = []
    
    for token in tokens:
        vec = get_token_vector(token)
        if vec is not None:
            matches.append(token)
            cumulative_vector += vec
            
    if not matches: 
        return None, [], len(tokens)
        
    avg_vector = cumulative_vector / len(matches)
    # Clip to keep normalized bounds safe
    avg_vector = np.clip(avg_vector, 0.0, 1.0)
    
    return avg_vector, matches, len(tokens)

# --- 2. NARRATION ENGINE DICTIONARIES ---

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
    mat_sentences = []  # Renamed to match the return statement
    dha_sentences = []  # Renamed to match the return statement
    
    for idx, dim in enumerate(dimensions):
        score = vector[idx]
        intensity = get_intensity_label(score)
        mapping = PHILOSOPHICAL_MAP[dim]
        
        if intensity == "Vestigial":
            continue
            
        narrative_sentence = f"Exhibits a **{intensity}** ({score:.2f}) alignment with **{mapping['thinker'] if mapping['thinker'] else mapping['school']}** ({mapping['school']}), indicating a clear pattern of {mapping['desc']}"
        
        if idx < 4:
            mat_sentences.append(narrative_sentence)
        else:
            dha_sentences.append(narrative_sentence)
            
    # Nyaya Meta-Check: Standard Deviation < 0.15 indicates a "balanced" or "harmonized" system
    nyaya_triggered = np.std(vector) < 0.15 and np.mean(vector) > 0.4
    return mat_sentences, dha_sentences, nyaya_triggered

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

# --- 4. THE CALIBRATION TEN DATABASE ---

CORPORA_SAMPLES = {
    "1. Software Essence (Fred Brooks)": 
        "With software systems, the fundamental complexity is an essential property, not an accidental one. "
        "Hence, descriptions of a software entity that abstract away its complexity often abstract away its essence. "
        "Software engineering is plagued by conformity to arbitrary interfaces, severe changeability, and complete invisibility. "
        "We create complex, conceptual abstractions that must map precisely to mathematical specifications without structural deviation.",
        
    "2. Rational Humanism (Bertrand Russell)": 
        "A Free Man's Worship requires that we acknowledge a world destitute of ultimate purpose, yet refuse to bow our intellect to tyranny. "
        "True human freedom is born when we abandon indignation and replace it with a logical resignation to truth. "
        "Through reason and skepticism, humanity preserves morality and science. Ethical knowledge and rationality remain our "
        "only shields against absolute despair, demanding justice for the individual within an indifferent society.",
        
    "3. Modern Deontology (Indian Constitution)": 
        "WE, THE PEOPLE OF INDIA, having solemnly resolved to constitute India into a SOVEREIGN SOCIALIST SECULAR DEMOCRATIC REPUBLIC "
        "and to secure to all its citizens: JUSTICE, social, economic and political; LIBERTY of thought, expression, belief, faith and worship; "
        "EQUALITY of status and of opportunity; and to promote among them all FRATERNITY assuring the dignity of the individual "
        "and the unity and integrity of the Nation.",
        
    "4. Sacrificial Liberty (Gettysburg Address)": 
        "Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in Liberty, "
        "and dedicated to the proposition that all men are created equal. We cannot dedicate—we cannot consecrate—we cannot hallow—this ground. "
        "The brave men, living and dead, who struggled here, have consecrated it, far above our poor power to add or detract. "
        "We highly resolve that these dead shall not have died in vain—that this nation, under God, shall have a new birth of freedom.",
        
    "5. Political Realism (Chanakya Arthashastra)": 
        "The statecraft of a king relies entirely on Danda (punishment and law), which preserves the stability of the realm. "
        "The sovereign must secure his Kosha (treasury) and Amatya (ministers) while monitoring the moves of the Vijigishu (aspiring conqueror). "
        "Through strategic alliances (Sandhi) or deliberate conflict (Vigraha), a state enforces internal order and external balance, "
        "aligning material resources with the preservation of institutional duty.",
        
    "6. Cosmic Mystery (Rig Veda Nasadiya Sukta)": 
        "Then there was neither non-existence nor existence; there was no realm of air, no sky beyond it. "
        "Darkness was hidden by darkness in the beginning, with no distinguishing sign; all this was water. "
        "Desire (Kama) arose in the beginning, which was the first seed of mind. Svadha (creative energy) was below, "
        "and vital force was above. The Adhyaksha (overseer) in the highest heaven, he surely knows—or perhaps he knows not.",
        
    "7. Virtue Ethics (Aristotle Nicomachean Ethics)": 
        "Eudaimonia (human flourishing) is an activity of the soul in accordance with excellence or virtue (Arete). "
        "Practical wisdom (Phronesis) guides us to find the golden mean (Mesotes) between excess and deficiency. "
        "This habitual disposition (Hexis) defines our characteristic function (Ergon). Justice (Dikaiosyne) and philosophical wisdom "
        "protect the human intellect against the moral weakness of Akrasia.",
        
    "8. Mimetic Foundation (René Girard)": 
        "Human desire is never authentic or direct; it is inherently mimetic, copied entirely from a social model. "
        "This structural imitation generates inescapable rivalry, plunging communities into destabilizing crises of violence. "
        "To restore order, collective panic identifies a single scapegoat, whose sacrificial exclusion is viewed as sacred. "
        "All human myth, prohibition, and social structure are born to mask this foundational cycle of competitive contagion.",
        
    "9. Scientific Categories (Isaac Newton Principia)": 
        "The mathematical principles of natural philosophy require clear axioms of motion. Every body perseveres in its state of rest "
        "or uniform motion unless compelled to change by forces impressed. Mass and acceleration dictate the structural framework of gravity. "
        "Absolute space and mathematical time exist independent of external observation, keeping the cosmic clockwork running in precise order.",
        
    "10. Economic Baseline (Adam Smith Wealth of Nations)": 
        "Every individual endeavors to employ his capital so that its produce may be of the greatest value. "
        "The market price of any specific commodity is regulated by the proportion between the quantity brought to market and effectual demand. "
        "Through commerce, division of labor, and investment of stock, revenue and profit are maximized. The transaction of wages and rent "
        "governs systemic progress through clear economic utility."
}

# --- 5. UI CONFIGURATION ---

st.set_page_config(page_title="The Fluttering Sail", layout="wide")
st.sidebar.title("Engine Configuration")

input_mode = st.sidebar.radio("Input Source", ["Preloaded Calibration Corpora", "Custom Text Entry"])

if input_mode == "Preloaded Calibration Corpora":
    selected_corpus = st.sidebar.selectbox("Select Benchmark Document:", list(CORPORA_SAMPLES.keys()))
    user_text = CORPORA_SAMPLES[selected_corpus]
else:
    user_text = st.sidebar.text_area("Paste Custom Corpus Segment here:", height=200, 
                                     placeholder="Type or paste your analytical text segment here...")

# --- MAIN DASHBOARD DISPLAY ---
st.title("⛵ THE FLUTTERING SAIL")
st.markdown("### *A Dynamical Multi-Polar Ethics Framework*")

# Universal Text View Component
with st.container():
    st.subheader("📝 Corpus Under Evaluation")
    st.info(user_text if user_text.strip() else "*(Workspace empty. Please input or select text in the sidebar.)*")

st.divider()

# --- 6. DIAGNOSTIC PANEL LAYER ---
avg_vec, matches, total_tokens = evaluate_text(user_text)
total_db_words = get_total_lexicon_count()

with st.container():
    st.subheader("📊 Engine Diagnostics & Reproducibility Metrics")
    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    
    with d_col1:
        st.metric("Total Tokens Evaluated", f"{total_tokens}")
    with d_col2:
        st.metric("Unique Anchor Hits", f"{len(set(matches))}")
    with d_col3:
        hit_density = (len(matches) / total_tokens * 100) if total_tokens > 0 else 0
        st.metric("Lexical Hit Density", f"{hit_density:.1f}%")
    with d_col4:
        st.metric("Active Seed Vault Volume", f"{total_db_words} words")

st.divider()

# --- 7. GRAPHICS AND ANALYSIS LOOP ---
if avg_vec is not None and user_text.strip():
    view_mode = st.radio("Display Mode", ["Stereo Radar (De-Merged)", "Synthesis Canvas (Merged)"], horizontal=True)
    
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
    
    st.success(f"**Identified Anchors:** {', '.join(sorted(list(set(matches))))}")
    
    # --- 8. DYNAMIC NARRATION ENGINE ---
    st.divider()
    st.subheader("📜 Philosophical Lineage & Narration")
    
    mat_sentences, dha_sentences, nyaya_active = generate_philosophical_narration(avg_vec)
    
    ncol1, ncol2 = st.columns(2)
    with ncol1:
        st.markdown("##### Materialist Lens Insights")
        if mat_sentences:
            for s in mat_sentences: st.write(f"- {s}")
        else:
            st.write("*No pronounced materialist dimensions detected above framework baselines.*")
            
    with ncol2:
        st.markdown("##### Dharmic Lens Insights")
        if dha_sentences:
            for s in dha_sentences: st.write(f"- {s}")
        else:
            st.write("*No pronounced dharmic dimensions detected above framework baselines.*")
            
    if nyaya_active:
        st.warning("⚠️ **Nyaya Logic Meta-Condition Triggered:** The system detects tightly integrated multi-polar metrics, showing an epistemologically balanced structure reminiscent of Nyaya analytical logic.")

else:
    st.warning("Awaiting a text footprint with valid anchor tokens to initialize the multi-polar vectors.")

st.divider()
st.caption("Metadata: SQLite Powered // Literate Execution // Matrix Calibration Version 1.7")