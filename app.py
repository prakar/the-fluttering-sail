# ⛵ THE FLUTTERING SAIL: TOTAL SYSTEM INTEGRATION (v3.1)
# 
# LITERATE DESIGN: APOPHATIC LOGIC + EXPANDABLE CORPUS.
# Status: Canonical Lockdown.

import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import logging

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

# --- CSS INJECTION FOR COMPACTNESS ---
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { font-size: 1.7rem !important; margin-bottom: 0.2rem !important; padding-top: 0px !important; }
    .stMetric { padding: 0px !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    .centered-label { text-align: center; font-weight: bold; font-size: 1.0rem; margin-bottom: -10px; }
    hr { margin: 0.4rem 0px !important; }
    .streamlit-expanderHeader { font-size: 0.85rem !important; color: #555; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC ENGINES ---

def get_intensity_label(val):
    if val < 0:
        return "Divergent"
    for entry in SCHEMA.get("INTENSITY_SCALE", []):
        if val >= entry["threshold"]: return entry["label"]
    return "Neutral"

def evaluate_geometric_failures(vector_dict):
    u, f, p, m = vector_dict['u'], vector_dict['f'], vector_dict['p'], vector_dict['m']
    t, s, d, c = vector_dict['t'], vector_dict['s'], vector_dict['d'], vector_dict['c']
    alerts = []
    modes = SCHEMA.get("FAILURE_MODES", {})
    if u >= 0.80 and t <= 0.15 and s <= 0.10: alerts.append(("error", modes.get("baconian_collapse", {})))
    if p >= 0.75 and m >= 0.70 and d <= 0.20 and c <= 0.15: alerts.append(("error", modes.get("mimetic_shear", {})))
    if c >= 0.90 and t >= 0.85 and u <= 0.20 and f <= 0.20: alerts.append(("warning", modes.get("ascetic_drift", {})))
    if f >= 0.70 and u >= 0.60 and d >= 0.75 and t >= 0.75: alerts.append(("success", modes.get("equilibrium_zone", {})))
    return alerts

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
            
    nyaya_triggered = np.std(vector) < 0.15 and np.mean(vector) > 0.4
    return mat_sentences, dha_sentences, nyaya_triggered

import openai

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
    TASK: Write a 2-paragraph "Synthesized Philosophical Narration". Juxtapose the lenses. 
    Be wise, opinionated, and describe the 'shape' of thought without listing raw numbers.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an elite philosophical synthesizer."},
                      {"role": "user", "content": prompt}],
            temperature=0.3
        )
        return f"### 🌪️ Opinion Synthesized by AI:\n\n{response.choices[0].message.content}"
    except Exception as e:
        logging.error(f"Synthesis Failure: {e}")
        return "⚠️ **Synthesis Error**: An unexpected issue occurred during narration generation."

# --- 3. NAVIGATION & MAIN UI ---
# Added "Sanskrit Non-Translatables" as a primary route choice
page = st.sidebar.selectbox("Navigation Bridge", ["Main Analysis", "Sanskrit Non-Translatables", "Under the Hood"])

if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")
    
    selected_doc_name = st.sidebar.selectbox("Benchmark Document", list(CORPORA.keys()))
    doc_data = CORPORA.get(selected_doc_name, {})
    input_text = doc_data.get("text", "")
    source_label = doc_data.get("taxonomy", "General")

    with st.expander(f"📄 View Source Corpus: {source_label}", expanded=False):
        st.write(input_text)

    # Ingesting DB metrics
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    df_vectors = pd.DataFrame()
    vault_count = 0
    if os.path.exists(DB_NAME):
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
        
        # FEATURE RESTORED: Blended Interface Toggle Checkbox
        synthesized_view = st.sidebar.checkbox("Synthesized View (Overlap Lenses)", value=False)
        
        if synthesized_view:
            st.markdown('<p class="centered-label">SYNTHESIZED PARADIGM OVERLAY</p>', unsafe_allow_html=True)
            
            # Create unified radar configuration tracking all 8 variables on a single axis
            fig_synth = go.Figure()
            
            # Materialist Layer (Red Trace)
            fig_synth.add_trace(go.Scatterpolar(
                r=[avg_dict[d] for d in ['f','p','m','u']],
                theta=[SCHEMA['LINEAGE_MAP'][d]['label'] for d in ['f','p','m','u']],
                fill='toself', fillcolor='rgba(255, 65, 54, 0.2)', line=dict(color='rgba(255, 65, 54, 1)'),
                name='Materialist Lens'
            ))
            # Dharmic-Essentialist Layer (Blue Trace)
            fig_synth.add_trace(go.Scatterpolar(
                r=[avg_dict[d] for d in ['s','t','c','d']],
                theta=[SCHEMA['LINEAGE_MAP'][d]['label'] for d in ['s','t','c','d']],
                fill='toself', fillcolor='rgba(0, 116, 217, 0.2)', line=dict(color='rgba(0, 116, 217, 1)'),
                name='Dharmic-Essentialist Lens'
            ))
            
            fig_synth.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=True, margin=dict(t=30, b=30, l=50, r=50), height=400
            )
            st.plotly_chart(fig_synth, use_container_width=True)
            st.markdown("---")
            
            # Switch view to opinionated, integrated narrative commentary block, which is from LLM
            # st.markdown(generate_llm_synthesis_stub(selected_doc_name, avg_dict, input_text)) ——— THE OLD STUB, replaced with the following
            with st.spinner("Synthesizing cross-paradigmatic analysis..."):
                narrative = generate_llm_synthesis(selected_doc_name, avg_dict, input_text)
                st.markdown(narrative)
            
        else:
            # Standard Split Screen View Execution
            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown('<p class="centered-label">MATERIALIST LENS</p>', unsafe_allow_html=True)
                fig1 = go.Figure(data=go.Scatterpolar(
                    r=[avg_dict[d] for d in ['f','p','m','u']],
                    theta=[SCHEMA['LINEAGE_MAP'][d]['label'] for d in ['f','p','m','u']],
                    fill='toself', fillcolor='rgba(255, 65, 54, 0.3)', line=dict(color='rgba(255, 65, 54, 1)')
                ))
                fig1.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, margin=dict(t=25, b=25, l=40, r=40), height=300)
                st.plotly_chart(fig1, use_container_width=True)

            with c_right:
                st.markdown('<p class="centered-label">DHARMIC–ESSENTIALIST LENS</p>', unsafe_allow_html=True)
                fig2 = go.Figure(data=go.Scatterpolar(
                    r=[avg_dict[d] for d in ['s','t','c','d']],
                    theta=[SCHEMA['LINEAGE_MAP'][d]['label'] for d in ['s','t','c','d']],
                    fill='toself', fillcolor='rgba(0, 116, 217, 0.3)', line=dict(color='rgba(0, 116, 217, 1)')
                ))
                fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, margin=dict(t=25, b=25, l=40, r=40), height=300)
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")
            st.markdown("### 📜 Philosophical Lineage & Narration")
            
            for a_type, a_meta in evaluate_geometric_failures(avg_dict):
                getattr(st, a_type)(f"**{a_meta.get('title')}**\n\n{a_meta.get('desc')}")

            mat_s, dha_s, nyaya = generate_philosophical_narration(avg_vec.values)
            if nyaya: st.success("⚖️ **NYAYA EQUILIBRIUM**: Harmonized system detected.")
            
            n_col1, n_col2 = st.columns(2)
            with n_col1:
                st.markdown("**Materialist Lens**")
                for s in mat_s: st.write(f"• {s}") 
            with n_col2:
                st.markdown("**Dharmic–Essentialist Lens**")
                for s in dha_s: st.write(f"• {s}")
    else:
        st.warning("Insufficient hits to render topology.")

# --- NEW ROUTE: SANSKRIT NON-TRANSLATABLES EXPANSION VIEW ---
elif page == "Sanskrit Non-Translatables":
    st.title("📜 Sanskrit Non-Translatables Codex")
    st.markdown("Explore individual terms from Malhotra's framework mapped directly to our 8-dimensional ethical vector geometry.")
    
    # Securely read file directly from local source configs
    if os.path.exists("weights.json"):
        with open("weights.json", "r") as f:
            weights_data = json.load(f)
        nontranslatables = weights_data.get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
        
        if nontranslatables:
            # Layout definition: Left scrolling list, Right active data canvas
            codex_col1, codex_col2 = st.columns([1, 2])
            
            with codex_col1:
                st.subheader("Terms Explorer")
                sorted_terms = sorted(list(nontranslatables.keys()))
                selected_term = st.radio("Select a term to unpack:", sorted_terms, label_visibility="collapsed")
                
            with codex_col2:
                if selected_term:
                    st.subheader(f"🎯 Vector Topology: {selected_term.upper()}")
                    
                    # Convert list array back to explicit 8 dimensions
                    vector_vals = nontranslatables[selected_term]
                    labels = ['Utility (u)', 'Fairness (f)', 'Power (p)', 'Mimetic (m)', 'Telos (t)', 'Structure (s)', 'Dharma (d)', 'Consciousness (c)']
                    
                    # Render dedicated interactive radar plot
                    fig_codex = go.Figure(data=go.Scatterpolar(
                        r=vector_vals,
                        theta=labels,
                        fill='toself',
                        fillcolor='rgba(147, 51, 234, 0.2)', 
                        line=dict(color='rgba(147, 51, 234, 1)')
                    ))
                    fig_codex.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[-1, 1])),
                        showlegend=False, height=350, margin=dict(t=20, b=20, l=40, r=40)
                    )
                    st.plotly_chart(fig_codex, use_container_width=True)
                    
                    # Deterministic structural text breakdown
                    st.markdown("### 🧬 Structural Quantization Mapping")
                    st.write(f"**Raw Metric Fingerprint:** `{vector_vals}`")
                    
                    # Basic inline layout narrative mapping logic
                    if vector_vals[7] > 0.6:
                        st.info(f"✨ **High Apophatic Core:** '{selected_term}' registers an elevated Consciousness value ({vector_vals[7]}). This explicitly confirms its resistance to Western reductionist models.")
                    if vector_vals[0] < -0.3:
                        st.warning(f"🪞 **Anti-Utility Signature:** The term repels immediate material or commercial consequence ({vector_vals[0]}), prioritizing ontological reality over transaction.")
        else:
            st.error("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS array is missing or empty inside weights.json.")
    else:
        st.error("Critical Configuration Missing: Cannot locate weights.json.")

# --- 5. ADMINISTRATIVE ---
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