import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import openai
import httpx 

# --- 1. CORE UTILITIES ---

def wrap_label(label):
    """Inserts a line break before the parenthesis to prevent truncation."""
    return label.replace(" (", "<br>(")

def get_radar_data(keys_list, data_dict):
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})
    # Using the wrap_label helper here
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
        if match:
            active_failures.append(mode_data)
    return active_failures

def generate_unified_synthesis(subject_name, vector_dict, source_context=""):
    """REVERTED: Returns to the original triangulation logic."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: return "⚠️ API Key not found."
    
    prompt = f"""
    Subject: '{subject_name}'. Vector topology: {vector_dict}.
    Context: {source_context[:1000]}
    
    Using these philosophical alignments, construct a synthesis passage that explains the essence 
    of this text. Do not list weights. Instead, triangulate the meaning using the specific 
    thinkers and schools. The goal is to build meaning through context-rich philosophical friction. 
    Use up to 100 words, prefer density over grammar, do not use fillers like introductions (e.g., 'Based on...'), 
    or conversational sign-offs.
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
    except Exception as e: return f"⚠️ Error: {str(e)}"

# --- 2. MAIN ANALYSIS PAGE ---

if page == "Main Analysis":
    # ... (keeping your existing data loading logic) ...

    if not df_vectors.empty:
        avg_vec = df_vectors[['u', 'f', 'p', 'm', 't', 's', 'd', 'c']].mean()
        avg_dict = avg_vec.to_dict()
        
        # --- DIAGNOSTIC HEADER (New!) ---
        failures = check_failure_modes(avg_dict)
        for f in failures:
            st.error(f"**{f['title']}**")
            with st.expander("Diagnostic Details"):
                st.write(f["desc"])

        mat_keys, ess_keys = ['u', 'f', 'p', 'm'], ['t', 's', 'd', 'c']

        if st.session_state.synth_active:
            m_labels, m_values = get_radar_data(mat_keys, avg_dict)
            e_labels, e_values = get_radar_data(ess_keys, avg_dict)
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=m_values, theta=m_labels, fill='toself', name='Materialist', line=dict(color='red')))
            fig.add_trace(go.Scatterpolar(r=e_values, theta=e_labels, fill='toself', name='Dharmic', line=dict(color='blue')))
            
            # UI FIX: Reduced margins, increased height to accommodate wrapped labels
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                margin=dict(l=50, r=50, t=30, b=30), 
                height=550 
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # UI FIX: Button placement
            if st.button("🔓 De-Merge The Lenses", use_container_width=True):
                st.session_state.synth_active = False
                st.rerun()

            st.markdown(f'<div class="synthesis-box">{generate_unified_synthesis(selected_doc, avg_dict, input_text)}</div>', unsafe_allow_html=True)
        
        else:
            # --- SPLIT VIEW ---
            m_labels, m_values = get_radar_data(mat_keys, avg_dict)
            e_labels, e_values = get_radar_data(ess_keys, avg_dict)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<p class="centered-label">MATERIALIST LENS</p>', unsafe_allow_html=True)
                f1 = go.Figure(go.Scatterpolar(r=m_values, theta=m_labels, fill='toself', fillcolor='rgba(255, 65, 54, 0.3)'))
                f1.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), margin=dict(l=50, r=50, t=20, b=20), height=450)
                st.plotly_chart(f1, use_container_width=True)
            with c2:
                st.markdown('<p class="centered-label">DHARMIC LENS</p>', unsafe_allow_html=True)
                f2 = go.Figure(go.Scatterpolar(r=e_values, theta=e_labels, fill='toself', fillcolor='rgba(0, 116, 217, 0.3)'))
                f2.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), margin=dict(l=50, r=50, t=20, b=20), height=450)
                st.plotly_chart(f2, use_container_width=True)
            
            if st.button("🌪️ Synthesize (Overlay Lenses)", use_container_width=True):
                st.session_state.synth_active = True
                st.rerun()

            # ... (Narration Section Remains) ...

# --- 3. CODEX FIX ---
# Inside "Sanskrit Non-Translatables" main column:
            all_keys = ['u','f','p','m','t','s','d','c'] # Force explicit order
            c_labels, c_values = get_radar_data(all_keys, val_dict)
            
            f_codex = go.Figure(data=go.Scatterpolar(r=c_values, theta=c_labels, fill='toself'))
            f_codex.update_layout(polar=dict(radialaxis=dict(range=[-1, 1])), height=500, margin=dict(l=60, r=60))
            st.plotly_chart(f_codex, use_container_width=True)
            
            # FIX: Ensure dimensional meaning iterates through ALL 8 keys
            st.markdown("### 🧬 Dimensional Meaning")
            m_s, d_s = generate_philosophical_narration(val_dict) # Pass dict directly
            for s in m_s + d_s: st.write(f"• {s}")