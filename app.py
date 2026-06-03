# ⛵ THE FLUTTERING SAIL: TOTAL SYSTEM INTEGRATION (v4.0)
# 
# LITERATE DESIGN: APOPHATIC LOGIC + EXPANDABLE CORPUS + DYNAMIC SYNTHESIS.
# Features: Sanskrit Codex, Custom Input, and LLM Synthesis.

import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import logging
import openai

# --- 1. GLOBAL APP CONFIGURATION ---
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

# --- CSS INJECTION ---
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { font-size: 1.7rem !important; margin-bottom: 0.2rem !important; padding-top: 0px !important; }
    .stMetric { padding: 0px !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    .centered-label { text-align: center; font-weight: bold; font-size: 1.0rem; margin-bottom: -10px; }
    hr { margin: 0.4rem 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC ENGINES ---

def generate_llm_synthesis(corpus_title, avg_dict, source_text):
    """Live hook for opinionated synthesis using OpenAI."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ **Synthesis Unavailable**: `OPENAI_API_KEY` not found in environment."

    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
    Synthesize an analysis of "{corpus_title}".
    Passage: "{source_text[:1200]}"
    METRICS: Materialist (u:{avg_dict['u']:.2f}, f:{avg_dict['f']:.2f}, p:{avg_dict['p']:.2f}, m:{avg_dict['m']:.2f}) 
             Dharmic (t:{avg_dict['t']:.2f}, s:{avg_dict['s']:.2f}, d:{avg_dict['d']:.2f}, c:{avg_dict['c']:.2f})
    TASK: Write a 2-paragraph "Synthesized Philosophical Narration". 
    Juxtapose the lenses. Be wise, opinionated, and describe the 'shape' of thought without listing numbers.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an elite philosophical synthesizer."},
                      {"role": "user", "content": prompt}],
            temperature=0.3
        )
        return f"#### 🤖 Synthesized Opinion from AI:\n\n{response.choices[0].message.content}"
    except Exception as e:
        return f"⚠️ **Synthesis Error**: {str(e)}"

def get_intensity_label(val):
    if val < 0: return "Divergent"
    for entry in SCHEMA.get("INTENSITY_SCALE", []):
        if val >= entry["threshold"]: return entry["label"]
    return "Neutral"

def generate_philosophical_narration(vector):
    dim_keys = ['u', 'f', 'p', 'm', 't', 's', 'd', 'c']
    mat_sentences, dha_sentences = [], []
    lineage_defs = SCHEMA.get("LINEAGE_MAP", {}) 
    for idx, key in enumerate(dim_keys):
        score = vector[idx]
        intensity = get_intensity_label(score)
        mapping = lineage_defs.get(key, {})
        if intensity == "Vestigial" and abs(score) < 0.05: continue
        name = mapping.get('thinker') if mapping.get('thinker') else mapping.get('school')
        narrative_sentence = f"Exhibits a **{intensity}** ({score:.2f}) alignment with {name} ({mapping.get('school')}), indicating a pattern of {mapping.get('desc')}"
        if idx < 4: mat_sentences.append(narrative_sentence)
        else: dha_sentences.append(narrative_sentence)
    return mat_sentences, dha_sentences, (np.std(vector) < 0.15 and np.mean(vector) > 0.4)

# --- 3. NAVIGATION & MAIN UI ---
page = st.sidebar.selectbox("Navigation Bridge", ["Main Analysis", "Sanskrit Non-Translatables", "Under the Hood"])

if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")
    
    # 3. SYNTHESIZE / DE-MERGE BUTTON LOGIC
    is_synth = st.session_state.get('synth_active', False)
    btn_label = "🔓 De-Merge The Lenses" if is_synth else "🌪️ Synthesize (Overlay Lenses)"
    if st.sidebar.button(btn_label):
        st.session_state['synth_active'] = not is_synth
        st.rerun()

    # 2. CUSTOM TEXT DROPDOWN LOGIC
    doc_options = ["Custom Text..."] + list(CORPORA.keys())
    selected_doc_name = st.sidebar.selectbox("Benchmark Document", doc_options)
    
    if selected_doc_name == "Custom Text...":
        input_text = st.text_area("Input passage for ethical quantization:", height=200, placeholder="Paste text here and press Ctrl+Enter...")
        source_label = "User Provided"
    else:
        doc_data = CORPORA.get(selected_doc_name, {})
        input_text = doc_data.get("text", "")
        source_label = doc_data.get("taxonomy", "General")
        with st.expander(f"📄 View Source Corpus: {source_label}", expanded=False):
            st.write(input_text)

    # Metrics Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    df_vectors = pd.DataFrame()
    if os.path.exists(DB_NAME) and input_text:
        conn = sqlite3.connect(DB_NAME)
        tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
        df_vectors = pd.read_sql_query(f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(tokens))})", conn, params=tokens)
        vault_count = pd.read_sql_query("SELECT count(*) as count FROM lexicon", conn).iloc[0]['count']
        conn.close()
        
        m_col1.metric("Tokens", len(input_text.split()))
        m_col2.metric("Hits", len(df_vectors))
        m_col3.metric("Density", f"{(len(df_vectors)/max(len(input_text.split()),1))*100:.1f}%")
        m_col4.metric("Vault", f"{vault_count}")

    st.markdown("---")

    if not df_vectors.empty:
        avg_vec = df_vectors[['u', 'f', 'p', 'm', 't', 's', 'd', 'c']].mean()
        avg_dict = avg_vec.to_dict()
        
        if st.session_state.get('synth_active', False):
            # --- SYNTHESIZED VIEW ---
            st.markdown('<p class="centered-label">SYNTHESIZED PARADIGM OVERLAY</p>', unsafe_allow_html=True)
            fig_synth = go.Figure()
            fig_synth.add_trace(go.Scatterpolar(r=[avg_dict[d] for d in ['f','p','m','u']], theta=['Fairness','Power','Mimetic','Utility'], fill='toself', fillcolor='rgba(255, 65, 54, 0.2)', name='Materialist'))
            fig_synth.add_trace(go.Scatterpolar(r=[avg_dict[d] for d in ['s','t','c','d']], theta=['Structure','Telos','Non-Dual','Dharma'], fill='toself', fillcolor='rgba(0, 116, 217, 0.2)', name='Dharmic'))
            fig_synth.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400, margin=dict(t=30, b=30))
            st.plotly_chart(fig_synth, use_container_width=True)
            st.markdown("---")
            with st.spinner("Synthesizing..."):
                st.markdown(generate_llm_synthesis(selected_doc_name, avg_dict, input_text))
        else:
            # --- SPLIT VIEW ---
            c_l, c_r = st.columns(2)
            with c_l:
                st.markdown('<p class="centered-label">MATERIALIST LENS</p>', unsafe_allow_html=True)
                f1 = go.Figure(data=go.Scatterpolar(r=[avg_dict[d] for d in ['f','p','m','u']], theta=['Fairness','Power','Mimetic','Utility'], fill='toself', fillcolor='rgba(255, 65, 54, 0.3)'))
                f1.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, height=300, margin=dict(t=25, b=25))
                st.plotly_chart(f1, use_container_width=True)
            with c_r:
                st.markdown('<p class="centered-label">DHARMIC–ESSENTIALIST LENS</p>', unsafe_allow_html=True)
                f2 = go.Figure(data=go.Scatterpolar(r=[avg_dict[d] for d in ['s','t','c','d']], theta=['Structure','Telos','Non-Dual','Dharma'], fill='toself', fillcolor='rgba(0, 116, 217, 0.3)'))
                f2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, height=300, margin=dict(t=25, b=25))
                st.plotly_chart(f2, use_container_width=True)
            
            st.markdown("### 📜 Philosophical Lineage & Narration")
            mat_s, dha_s, nyaya = generate_philosophical_narration(avg_vec.values)
            n1, n2 = st.columns(2)
            with n1: 
                for s in mat_s: st.write(f"• {s}")
            with n2: 
                for s in dha_s: st.write(f"• {s}")
    elif input_text:
        st.warning("Insufficient hits to render topology.")

# --- 1. SANSKRIT NON-TRANSLATABLES CODEX ROUTE ---
elif page == "Sanskrit Non-Translatables":
    st.title("📜 Sanskrit Non-Translatables Codex")
    if os.path.exists("weights.json"):
        with open("weights.json", "r") as f: weights = json.load(f).get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
        col_ls, col_chart = st.columns([1, 2])
        with col_ls:
            term = st.radio("Select a term:", sorted(list(weights.keys())))
        with col_chart:
            st.subheader(f"🎯 Vector Topology: {term.upper()}")
            vals = weights[term]
            f_codex = go.Figure(data=go.Scatterpolar(r=vals, theta=['u','f','p','m','t','s','d','c'], fill='toself', fillcolor='rgba(147, 51, 234, 0.2)'))
            f_codex.update_layout(polar=dict(radialaxis=dict(visible=True, range=[-1, 1])), height=400)
            st.plotly_chart(f_codex, use_container_width=True)
            st.write(f"**Fingerprint:** `{vals}`")

elif page == "Under the Hood":
    st.title("🛠️ Administrative Inspectability")
    tab1, tab2 = st.tabs(["🗄️ SQLite Data Store", "📜 System Logs"])
    with tab1:
        if os.path.exists(DB_NAME):
            conn = sqlite3.connect(DB_NAME)
            st.dataframe(pd.read_sql_query("SELECT * FROM lexicon", conn), use_container_width=True)
            conn.close()
    with tab2:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: st.code(f.read(), language="text")