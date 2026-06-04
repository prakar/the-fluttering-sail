import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import logging
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

# --- CANONICAL STATE UI & CSS ---
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { font-size: 1.7rem !important; margin-bottom: 0.2rem !important; padding-top: 0px !important; }
    .stMetric { padding: 0px !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    .centered-label { text-align: center; font-weight: bold; font-size: 1.0rem; margin-bottom: -10px; }
    .synthesis-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #9333ea; margin-top: 20px; }
    hr { margin: 0.4rem 0px !important; }
    .synthesis-box { 
        background-color: rgba(240, 242, 246, 0.1); 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #9333ea; 
        margin-top: 20px;
        color: inherit;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC ENGINES ---

def get_intensity_label(val):
    if val < 0: return "Divergent"
    for entry in SCHEMA.get("INTENSITY_SCALE", []):
        if val >= entry["threshold"]: return entry["label"]
    return "Neutral"

def generate_philosophical_narration(vector):
    dim_keys = ['u', 'f', 'p', 'm', 't', 's', 'd', 'c']
    mat_sentences, dha_sentences = [], []
    lineage_defs = SCHEMA.get("LINEAGE_MAP", {}) 
    vec_vals = [vector.get(k, 0) if isinstance(vector, dict) else vector[i] for i, k in enumerate(dim_keys)]

    for idx, key in enumerate(dim_keys):
        score = vec_vals[idx]
        intensity = get_intensity_label(score)
        mapping = lineage_defs.get(key, {})
        if intensity == "Vestigial" and abs(score) < 0.05: continue
        name = mapping.get('thinker') if mapping.get('thinker') else mapping.get('school')
        line = f"Exhibits a **{intensity}** ({score:.2f}) alignment with {name} ({mapping.get('school')}), indicating a pattern of {mapping.get('desc')}"
        if idx < 4: mat_sentences.append(line)
        else: dha_sentences.append(line)
    return mat_sentences, dha_sentences

def generate_unified_synthesis(subject_name, vector_dict, source_context=""):
    """UNIFIED & HIGH-DENSITY SYNTHESIS ENGINE: Hard-coded for strict token spend and precision."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: return "⚠️ **Synthesis Unavailable**: API Key not found."
    
    system_prompt = (
        "You are a professional multi-polar philosophical synthesizer. Rules: "
        "1. Be extremely concise. "
        "2. Max 50 words. "
        "3. Sacrifice grammar for density. "
        "4. No filler, no introductions ('Based on...'), no conversational sign-offs. "
        "5. Directly triangulate target meaning by creating critical analytical friction "
        "using the specific philosophical weights and descriptions provided."
    )
    
    # Pack schema contextual metadata directly into the generation layer
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})
    detailed_weights = {}
    for k, v in vector_dict.items():
        sch = lineage_map.get(k, {})
        label = sch.get("friendly_display", k)
        desc = sch.get("desc", "")
        detailed_weights[label] = {"weight": f"{v:.2f}", "context": desc}

    user_prompt = f"Subject/Word: {subject_name}. Weight System Map: {detailed_weights}. Source Context Extract: {source_context[:600]}"
    
    try:
        client = openai.OpenAI(api_key=api_key, http_client=httpx.Client())
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"⚠️ **Synthesis Engine Error**: {str(e)}"

def get_radar_data(keys_list, data_dict):
    """SINGLE SOURCE OF TRUTH: Dynamically extracts labels and data paths to lock trace alignment."""
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})
    labels = [lineage_map.get(k, {}).get("friendly_display", k) for k in keys_list]
    values = [data_dict.get(k, 0) for k in keys_list]
    return labels, values

# --- 3. NAVIGATION BRIDGE ---
page = st.sidebar.selectbox("Navigation Bridge", ["Main Analysis", "Sanskrit Non-Translatables", "Under the Hood"])

# --- 4. PAGE: MAIN ANALYSIS ---
if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")

    if 'synth_active' not in st.session_state: 
        st.session_state.synth_active = False

    # PERSISTENT DOCUMENT SELECTION & SIDEBAR CUSTOM TEXT CONSTRAINTS
    doc_options = list(CORPORA.keys()) + ["Custom Text..."]
    selected_doc = st.sidebar.selectbox("Benchmark Document", doc_options, key="persistent_doc")
    
    input_text = ""
    if selected_doc == "Custom Text...":
        input_text = st.sidebar.text_area("Input passage:", height=150, placeholder="Paste and hit Ctrl+Enter")
    else:
        input_text = CORPORA.get(selected_doc, {}).get("text", "")
        with st.expander("📄 View Source Corpus", expanded=False):
            st.write(input_text)

    df_vectors = pd.DataFrame()
    if os.path.exists(DB_NAME) and input_text:
        conn = sqlite3.connect(DB_NAME)
        tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
        df_vectors = pd.read_sql_query(f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(tokens))})", conn, params=tokens)
        conn.close()

    if not df_vectors.empty:
        avg_vec = df_vectors[['u', 'f', 'p', 'm', 't', 's', 'd', 'c']].mean()
        avg_dict = avg_vec.to_dict()
        
        # Segment definitions out dynamically via schema structures
        mat_keys = ['u', 'f', 'p', 'm']
        ess_keys = ['t', 's', 'd', 'c']
        
        if st.session_state.synth_active:
            # --- OVERLAY GRAPH VIEW ---
            m_labels, m_values = get_radar_data(mat_keys, avg_dict)
            e_labels, e_values = get_radar_data(ess_keys, avg_dict)
            
            fig_synth = go.Figure()
            fig_synth.add_trace(go.Scatterpolar(r=m_values, theta=m_labels, fill='toself', name='Materialist', line=dict(color='red')))
            fig_synth.add_trace(go.Scatterpolar(r=e_values, theta=e_labels, fill='toself', name='Dharmic', line=dict(color='blue')))
            fig_synth.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                margin=dict(l=100, r=100, t=40, b=40), 
                height=500 
            )
            st.plotly_chart(fig_synth, use_container_width=True)
            
            # Button Location: Rendered directly beneath the overlay chart canvas
            if st.button("🔓 De-Merge The Lenses"):
                st.session_state.synth_active = False
                st.rerun()
                
            st.markdown("### 🌪️ Synthesized Topological Meaning")
            with st.spinner("Compiling cross-lens summary matrix..."):
                synthesis_passage = generate_unified_synthesis(selected_doc, avg_dict, input_text)
                st.markdown(f'<div class="synthesis-box">{synthesis_passage}</div>', unsafe_allow_html=True)
        else:
            # --- SPLIT GRAPH VIEW ---
            m_labels, m_values = get_radar_data(mat_keys, avg_dict)
            e_labels, e_values = get_radar_data(ess_keys, avg_dict)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<p class="centered-label">MATERIALIST LENS</p>', unsafe_allow_html=True)
                fig_mat = go.Figure(go.Scatterpolar(r=m_values, theta=m_labels, fill='toself', fillcolor='rgba(255, 65, 54, 0.3)'))
                fig_mat.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), margin=dict(l=100, r=100, t=40, b=40), height=500)
                st.plotly_chart(fig_mat, use_container_width=True)
            with c2:
                st.markdown('<p class="centered-label">DHARMIC–ESSENTIALIST LENS</p>', unsafe_allow_html=True)
                fig_ess = go.Figure(go.Scatterpolar(r=e_values, theta=e_labels, fill='toself', fillcolor='rgba(0, 116, 217, 0.3)'))
                fig_ess.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), margin=dict(l=100, r=100, t=40, b=40), height=500)
                st.plotly_chart(fig_ess, use_container_width=True)
            
            # Button Location: Rendered below the discrete dual-lens layouts
            if st.button("🌪️ Synthesize (Overlay Lenses)"):
                st.session_state.synth_active = True
                st.rerun()
            
            st.markdown("---")
            st.markdown("### 📜 Philosophical Lineage & Narration")
            m_s, d_s = generate_philosophical_narration(avg_vec.values)
            n1, n2 = st.columns(2)
            with n1: 
                for s in m_s: st.write(f"• {s}")
            with n2: 
                for s in d_s: st.write(f"• {s}")

# --- 5. PAGE: SANSKRIT NON-TRANSLATABLES CODEX ---
elif page == "Sanskrit Non-Translatables":
    st.title("📜 Sanskrit Non-Translatables Codex")
    if os.path.exists("weights.json"):
        with open("weights.json", "r") as f: 
            weights = json.load(f).get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
        all_terms = sorted(list(weights.keys()))
        total_words = len(all_terms)
        words_per_page = 10
        
        # FIXED PAGINATION BOUNDARY MATH
        total_pages = (total_words + words_per_page - 1) // words_per_page
        if 'page_index' not in st.session_state: st.session_state.page_index = 0
        
        col_list, col_main = st.columns([1, 2])
        with col_list:
            start = st.session_state.page_index * words_per_page
            end = min(start + words_per_page, total_words)
            selected_term = st.radio("Terms (Discovery List):", all_terms[start:end])
            
            p1, p2 = st.columns(2)
            if p1.button("⬅️ Back") and st.session_state.page_index > 0:
                st.session_state.page_index -= 1
                st.rerun()
            if p2.button("Next ➡️") and (st.session_state.page_index + 1) < total_pages:
                st.session_state.page_index += 1
                st.rerun()
            st.caption(f"Page {st.session_state.page_index + 1} of {total_pages}")

        with col_main:
            if selected_term:
                st.subheader(f"🎯 Vector Topology: {selected_term.upper()}")
                vals = weights[selected_term]
                val_dict = dict(zip(['u','f','p','m','t','s','d','c'], vals))
                
                # Dynamic full trace resolution
                all_keys = ['u','f','p','m','t','s','d','c']
                c_labels, c_values = get_radar_data(all_keys, val_dict)
                
                # Codex Polar Visualization - maps out to full 8-spoke schema labels
                f_codex = go.Figure(data=go.Scatterpolar(r=c_values, theta=c_labels, fill='toself', fillcolor='rgba(147,51,234,0.2)'))
                f_codex.update_layout(polar=dict(radialaxis=dict(visible=True, range=[-1, 1])), margin=dict(l=100, r=100, t=40, b=40), height=500)
                st.plotly_chart(f_codex, use_container_width=True)
                
                # --- INTEGRATED UNIFIED RECONSTRUCTION PASSAGE ---
                st.markdown("### 🌪️ Semantic Reconstruction (The Nontranslatable Essence)")
                with st.spinner(f"Triangulating meaning for {selected_term}..."):
                    reconstruction = generate_unified_synthesis(selected_term, val_dict)
                    st.markdown(f'<div class="synthesis-box">{reconstruction}</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### 🧬 Dimensional Meaning")
                m_s, d_s = generate_philosophical_narration(vals)
                for s in m_s + d_s: st.write(f"• {s}")

# --- 6. PAGE: UNDER THE HOOD (ADMIN VIEW) ---
elif page == "Under the Hood":
    st.title("🛠️ Administrative Inspectability")
    tab1, tab2 = st.tabs(["🗄️ SQLite Data Store", "📜 System Logs"])
    
    with tab1:
        if os.path.exists(DB_NAME):
            conn = sqlite3.connect(DB_NAME)
            st.dataframe(pd.read_sql_query("SELECT * FROM lexicon", conn), use_container_width=True)
            conn.close()
        else:
            st.warning(f"Database file '{DB_NAME}' not found.")
            
    with tab2:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                st.code(f.read(), language="text")
        else:
            st.info("System log file (framework.log) not found.")