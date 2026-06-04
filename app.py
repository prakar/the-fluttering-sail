import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import openai
import httpx 

# --- 1. GLOBAL APP CONFIGURATION & STATE ---
st.set_page_config(
    page_title="The Fluttering Sail — Dynamical Multi-Polar Ethical Framework",
    page_icon="⛵",
    layout="wide"
)

DB_NAME = "epistemic_lexicon.db"
LOG_FILE = "framework.log"
SCHEMA = {}
CORPORA = {}

def load_assets():
    global SCHEMA, CORPORA
    if os.path.exists("epistemic_schema.json"):
        with open("epistemic_schema.json", "r") as f: SCHEMA = json.load(f)
    if os.path.exists("corpora.json"):
        with open("corpora.json", "r") as f: CORPORA = json.load(f)

load_assets()

# --- CSS & UI STYLING ---
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { font-size: 1.7rem !important; margin-bottom: 0.2rem !important; padding-top: 0px !important; }
    .centered-label { text-align: center; font-weight: bold; font-size: 1.0rem; margin-bottom: -10px; }
    .synthesis-box { 
        background-color: rgba(240, 242, 246, 0.1); 
        padding: 20px; border-radius: 10px; 
        border-left: 5px solid #9333ea; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC ENGINES ---

def wrap_label(label):
    """Prevents radar plot truncation by wrapping friendly labels."""
    return label.replace(" (", "<br>(")

def get_intensity_label(val):
    if val < 0: return "Divergent"
    for entry in SCHEMA.get("INTENSITY_SCALE", []):
        if val >= entry["threshold"]: return entry["label"]
    return "Neutral"

def get_radar_data(keys_list, data_dict):
    """Source of Truth for Plotly: Maps keys to wrapped friendly labels."""
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})
    labels = [wrap_label(lineage_map.get(k, {}).get("friendly_display", k)) for k in keys_list]
    values = [data_dict.get(k, 0) for k in keys_list]
    return labels, values

def check_failure_modes(avg_dict):
    """Opinionated Diagnostic: Checks vector against JSON-defined risk triggers."""
    active_failures = []
    modes = SCHEMA.get("FAILURE_MODES", {})
    for mode_key, mode_data in modes.items():
        conditions = mode_data.get("conditions", {})
        if not conditions: continue
        match = True
        for key, bounds in conditions.items():
            val = avg_dict.get(key, 0)
            if not (bounds[0] <= val <= bounds[1]):
                match = False
                break
        if match: active_failures.append(mode_data)
    return active_failures

def generate_philosophical_narration(vector_data):
    """Standardized 8-dimension narration."""
    dim_keys = ['u', 'f', 'p', 'm', 't', 's', 'd', 'c']
    mat_sentences, dha_sentences = [], []
    lineage_defs = SCHEMA.get("LINEAGE_MAP", {}) 
    
    for idx, key in enumerate(dim_keys):
        score = vector_data.get(key, 0) if isinstance(vector_data, dict) else vector_data[idx]
        intensity = get_intensity_label(score)
        mapping = lineage_defs.get(key, {})
        if intensity == "Vestigial" and abs(score) < 0.05: continue
        
        name = mapping.get('thinker') if mapping.get('thinker') else mapping.get('school')
        line = f"Exhibits a **{intensity}** ({score:.2f}) alignment with {name}, indicating a pattern of {mapping.get('desc')}"
        if idx < 4: mat_sentences.append(line)
        else: dha_sentences.append(line)
    return mat_sentences, dha_sentences

def generate_unified_synthesis(subject_name, vector_dict, source_context=""):
    """Reverted to 'Philosophical Friction' triangulation prompt."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: return "⚠️ **Synthesis Unavailable**: API Key not found."
    prompt = f"""
    Subject: '{subject_name}'. Vector topology: {vector_dict}.
    Context Extract: {source_context[:1200]}
    
    Triangulate the 'essence' of this text using the philosophical alignments provided. 
    Explain the friction between its materialist goals and essentialist foundations.
    """
    try:
        client = openai.OpenAI(api_key=api_key, http_client=httpx.Client())
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a master of comparative philosophy."},
                      {"role": "user", "content": prompt}],
            temperature=0.3
        )
        return res.choices[0].message.content
    except Exception as e: return f"⚠️ **Synthesis Error**: {str(e)}"

# --- 3. NAVIGATION & SESSION STATE ---
if 'synth_active' not in st.session_state: 
    st.session_state.synth_active = False

page = st.sidebar.selectbox("Navigation Bridge", ["Main Analysis", "Sanskrit Non-Translatables", "Under the Hood"])

# --- 4. PAGE: MAIN ANALYSIS ---
if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")

    doc_options = list(CORPORA.keys()) + ["Custom Text..."]
    selected_doc = st.sidebar.selectbox("Benchmark Document", doc_options, key="persistent_doc")
    
    input_text = ""
    if selected_doc == "Custom Text...":
        input_text = st.sidebar.text_area("Input passage:", height=150)
    else:
        input_text = CORPORA.get(selected_doc, {}).get("text", "")
        with st.expander("📄 View Source Corpus"):
            st.write(input_text)

    if input_text:
        conn = sqlite3.connect(DB_NAME)
        tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
        df_vectors = pd.read_sql_query(f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(tokens))})", conn, params=tokens)
        conn.close()

        if not df_vectors.empty:
            avg_dict = df_vectors[['u', 'f', 'p', 'm', 't', 's', 'd', 'c']].mean().to_dict()
            
            # --- FAILURE MODE DIAGNOSTIC ---
            failures = check_failure_modes(avg_dict)
            for f in failures:
                st.error(f"**{f['title']}**")
                with st.expander("Diagnostic Reasoning"):
                    st.write(f["desc"])

            mat_keys, ess_keys = ['u', 'f', 'p', 'm'], ['t', 's', 'd', 'c']

            if st.session_state.synth_active:
                m_lab, m_val = get_radar_data(mat_keys, avg_dict)
                e_lab, e_val = get_radar_data(ess_keys, avg_dict)
                
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=m_val, theta=m_lab, fill='toself', name='Materialist', line=dict(color='red')))
                fig.add_trace(go.Scatterpolar(r=e_val, theta=e_lab, fill='toself', name='Dharmic', line=dict(color='blue')))
                fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), margin=dict(l=60, r=60, t=30, b=30), height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                if st.button("🔓 De-Merge The Lenses", use_container_width=True):
                    st.session_state.synth_active = False
                    st.rerun()
                
                st.markdown(f'<div class="synthesis-box">{generate_unified_synthesis(selected_doc, avg_dict, input_text)}</div>', unsafe_allow_html=True)
            else:
                c1, c2 = st.columns(2)
                with c1:
                    m_lab, m_val = get_radar_data(mat_keys, avg_dict)
                    st.markdown('<p class="centered-label">MATERIALIST LENS</p>', unsafe_allow_html=True)
                    f1 = go.Figure(go.Scatterpolar(r=m_val, theta=m_lab, fill='toself', fillcolor='rgba(255, 65, 54, 0.3)'))
                    f1.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), margin=dict(l=60, r=60, t=20, b=20), height=450)
                    st.plotly_chart(f1, use_container_width=True)
                with c2:
                    e_lab, e_val = get_radar_data(ess_keys, avg_dict)
                    st.markdown('<p class="centered-label">DHARMIC LENS</p>', unsafe_allow_html=True)
                    f2 = go.Figure(go.Scatterpolar(r=e_val, theta=e_lab, fill='toself', fillcolor='rgba(0, 116, 217, 0.3)'))
                    f2.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), margin=dict(l=60, r=60, t=20, b=20), height=450)
                    st.plotly_chart(f2, use_container_width=True)
                
                if st.button("🌪️ Synthesize (Overlay Lenses)", use_container_width=True):
                    st.session_state.synth_active = True
                    st.rerun()

                st.markdown("### 📜 Philosophical Lineage & Narration")
                m_s, d_s = generate_philosophical_narration(avg_dict)
                n1, n2 = st.columns(2)
                with n1: 
                    for s in m_s: st.write(f"• {s}")
                with n2: 
                    for s in d_s: st.write(f"• {s}")

# --- 5. PAGE: SANSKRIT NON-TRANSLATABLES ---
elif page == "Sanskrit Non-Translatables":
    st.title("📜 Sanskrit Non-Translatables Codex")
    if os.path.exists("weights.json"):
        with open("weights.json", "r") as f: 
            weights = json.load(f).get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
        
        all_terms = sorted(list(weights.keys()))
        if 'page_idx' not in st.session_state: st.session_state.page_idx = 0
        
        col_l, col_r = st.columns([1, 2])
        with col_l:
            start = st.session_state.page_idx * 10
            selected_term = st.radio("Terms:", all_terms[start:start+10])
            if st.button("Next Page ➡️") and (start + 10) < len(all_terms):
                st.session_state.page_idx += 1
                st.rerun()
            if st.button("⬅️ Prev Page") and st.session_state.page_idx > 0:
                st.session_state.page_idx -= 1
                st.rerun()

        with col_r:
            if selected_term:
                st.subheader(f"🎯 Vector Topology: {selected_term.upper()}")
                v_list = weights[selected_term]
                v_dict = dict(zip(['u','f','p','m','t','s','d','c'], v_list))
                
                c_lab, c_val = get_radar_data(['u','f','p','m','t','s','d','c'], v_dict)
                f_codex = go.Figure(data=go.Scatterpolar(r=c_val, theta=c_lab, fill='toself'))
                f_codex.update_layout(polar=dict(radialaxis=dict(range=[-1, 1])), height=500, margin=dict(l=80, r=80))
                st.plotly_chart(f_codex, use_container_width=True)
                
                st.markdown(f'<div class="synthesis-box">{generate_unified_synthesis(selected_term, v_dict)}</div>', unsafe_allow_html=True)
                
                st.markdown("### 🧬 Dimensional Meaning")
                m_s, d_s = generate_philosophical_narration(v_dict)
                for s in m_s + d_s: st.write(f"• {s}")

# --- 6. ADMIN VIEW ---
elif page == "Under the Hood":
    st.title("🛠️ Administrative Inspectability")
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        st.dataframe(pd.read_sql_query("SELECT * FROM lexicon", conn), use_container_width=True)
        conn.close()