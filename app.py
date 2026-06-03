# ⛵ THE FLUTTERING SAIL: TOTAL SYSTEM INTEGRATION (v4.2)
# Refactored for Discovery-Based Pagination and Shared Philosophical Narratives.

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
SCHEMA = {}
CORPORA = {}

def load_assets():
    global SCHEMA, CORPORA
    if os.path.exists("epistemic_schema.json"):
        with open("epistemic_schema.json", "r") as f: SCHEMA = json.load(f)
    if os.path.exists("corpora.json"):
        with open("corpora.json", "r") as f: CORPORA = json.load(f)

load_assets()

# --- 2. LOGIC ENGINES ---

def get_intensity_label(val):
    if val < 0: return "Divergent"
    for entry in SCHEMA.get("INTENSITY_SCALE", []):
        if val >= entry["threshold"]: return entry["label"]
    return "Neutral"

def generate_philosophical_narration(vector):
    """Shared narrative engine for both Main Analysis and Sanskrit Codex."""
    dim_keys = ['u', 'f', 'p', 'm', 't', 's', 'd', 'c']
    mat_sentences, dha_sentences = [], []
    lineage_defs = SCHEMA.get("LINEAGE_MAP", {}) 
    
    # Normalize input: handle both list/array and dictionary
    vec_vals = [vector.get(k, 0) if isinstance(vector, dict) else vector[i] for i, k in enumerate(dim_keys)]

    for idx, key in enumerate(dim_keys):
        score = vec_vals[idx]
        intensity = get_intensity_label(score)
        mapping = lineage_defs.get(key, {})
        if intensity == "Vestigial" and abs(score) < 0.05: continue
        name = mapping.get('thinker') if mapping.get('thinker') else mapping.get('school')
        line = f"**{intensity}** ({score:.2f}) alignment with {name} ({mapping.get('school')})"
        
        if idx < 4: mat_sentences.append(line)
        else: dha_sentences.append(line)
    
    return mat_sentences, dha_sentences

def generate_llm_synthesis(corpus_title, avg_dict, source_text):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: return "⚠️ API Key missing."
    client = openai.OpenAI(api_key=api_key)
    prompt = f"Synthesize analysis for {corpus_title}. Metrics: {avg_dict}. Text: {source_text[:1000]}"
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return f"#### 🤖 Synthesized Opinion from AI:\n\n{res.choices[0].message.content}"
    except Exception as e: return f"⚠️ Error: {str(e)}"

# --- 3. NAVIGATION ---
page = st.sidebar.selectbox("Navigation Bridge", ["Main Analysis", "Sanskrit Non-Translatables", "Under the Hood"])

# --- 4. MAIN ANALYSIS VIEW ---
if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")

    if 'synth_active' not in st.session_state: st.session_state.synth_active = False
    
    # Persistent State Toggle
    btn_label = "🔓 De-Merge The Lenses" if st.session_state.synth_active else "🌪️ Synthesize (Overlay Lenses)"
    if st.sidebar.button(btn_label):
        st.session_state.synth_active = not st.session_state.synth_active
        st.rerun()

    doc_options = list(CORPORA.keys()) + ["Custom Text..."]
    selected_doc = st.sidebar.selectbox("Benchmark Document", doc_options, key="doc_selection")
    
    input_text = ""
    if selected_doc == "Custom Text...":
        input_text = st.sidebar.text_area("Input passage:", height=150)
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
        
        if st.session_state.synth_active:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=[avg_dict[d] for d in ['f','p','m','u']], theta=['Fairness','Power','Mimetic','Utility'], fill='toself', name='Materialist', line=dict(color='red')))
            fig.add_trace(go.Scatterpolar(r=[avg_dict[d] for d in ['s','t','c','d']], theta=['Structure','Telos','Non-Dual','Dharma'], fill='toself', name='Dharmic', line=dict(color='blue')))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(generate_llm_synthesis(selected_doc, avg_dict, input_text))
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(go.Figure(go.Scatterpolar(r=[avg_dict[d] for d in ['f','p','m','u']], theta=['Fairness','Power','Mimetic','Utility'], fill='toself')), use_container_width=True)
            with c2:
                st.plotly_chart(go.Figure(go.Scatterpolar(r=[avg_dict[d] for d in ['s','t','c','d']], theta=['Structure','Telos','Non-Dual','Dharma'], fill='toself')), use_container_width=True)
            
            mat_s, dha_s = generate_philosophical_narration(avg_vec.values)
            n1, n2 = st.columns(2)
            with n1: 
                st.markdown("**Materialist Lens**")
                for s in mat_s: st.write(f"• {s}")
            with n2: 
                st.markdown("**Dharmic Lens**")
                for s in dha_s: st.write(f"• {s}")

# --- 5. SANSKRIT CODEX VIEW (Discovery & Pagination) ---
elif page == "Sanskrit Non-Translatables":
    st.title("📜 Sanskrit Non-Translatables Codex")
    
    if os.path.exists("weights.json"):
        with open("weights.json", "r") as f: 
            weights = json.load(f).get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
        
        all_terms = sorted(list(weights.keys()))
        total_words = len(all_terms)
        words_per_page = 10
        
        # Pagination State Handling
        if 'page_index' not in st.session_state: st.session_state.page_index = 0
        
        col_list, col_main = st.columns([1, 2])
        
        with col_list:
            st.subheader("Discovery List")
            start = st.session_state.page_index * words_per_page
            end = start + words_per_page
            current_batch = all_terms[start:end]
            
            # Selection within the current batch
            selected_term = st.radio("Terms on this page:", current_batch, label_visibility="collapsed")
            
            # Pagination Controls
            p_col1, p_col2 = st.columns(2)
            if p_col1.button("⬅️ Back") and st.session_state.page_index > 0:
                st.session_state.page_index -= 1
                st.rerun()
            if p_col2.button("Next ➡️") and end < total_words:
                st.session_state.page_index += 1
                st.rerun()
                
            st.caption(f"Page {st.session_state.page_index + 1} of {(total_words // words_per_page) + 1} ({total_words} total)")

        with col_main:
            if selected_term:
                vals = weights[selected_term]
                st.subheader(f"🎯 Vector Topology: {selected_term.upper()}")
                
                # Radar Plot
                f_codex = go.Figure(data=go.Scatterpolar(r=vals, theta=['u','f','p','m','t','s','d','c'], fill='toself', fillcolor='rgba(147,51,234,0.2)'))
                f_codex.update_layout(polar=dict(radialaxis=dict(visible=True, range=[-1, 1])), height=400)
                st.plotly_chart(f_codex, use_container_width=True)
                
                # Shared Philosophical Narration logic applied here
                st.markdown("### 🧬 Dimensional Meaning")
                m_s, d_s = generate_philosophical_narration(vals)
                for s in m_s + d_s: st.write(f"• {s}")

elif page == "Under the Hood":
    st.title("🛠️ Administrative Inspectability")
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        st.dataframe(pd.read_sql_query("SELECT * FROM lexicon", conn), use_container_width=True)
        conn.close()