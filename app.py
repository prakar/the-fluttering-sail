import streamlit as st
import json
import os
import sqlite3
import pandas as pd
import hashlib
import plotly.graph_objects as go
import openai
import httpx 
import logging

# --- 1. CORE CONFIG & LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
st.set_page_config(page_title="The Fluttering Sail", page_icon="⛵", layout="wide")

DB_NAME = "epistemic_lexicon.db"
SCHEMA, CORPORA = {}, {}

def load_assets():
    global SCHEMA, CORPORA
    if os.path.exists("epistemic_schema.json"):
        with open("epistemic_schema.json", "r") as f: SCHEMA = json.load(f)
        logger.info("✅ Schema Loaded with Friendly Labels")
    if os.path.exists("corpora.json"):
        with open("corpora.json", "r") as f: CORPORA = json.load(f)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("CREATE TABLE IF NOT EXISTS synthesis_cache (hash TEXT PRIMARY KEY, response TEXT)")
    conn.commit()
    conn.close()

load_assets()
init_db()

# --- 2. LOGIC ENGINES ---

def get_radar_data(keys_list, data_dict):
    """STRICT MAPPING: Prioritizes friendly_display from the locked schema."""
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})
    labels, values = [], []
    for k in keys_list:
        mapping = lineage_map.get(k.lower(), {})
        # Pull friendly_display as per the locked-down JSON
        friendly = mapping.get("friendly_display", k) 
        logger.info(f"📍 Mapping '{k}' -> '{friendly}'")
        # Inject break for better plot layout
        labels.append(friendly.replace(" (", "<br>("))
        values.append(data_dict.get(k, 0))
    return labels, values

def get_cached_synthesis(text_content, vector_dict):
    unique_str = text_content + str(sorted(vector_dict.items()))
    text_hash = hashlib.md5(unique_str.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT response FROM synthesis_cache WHERE hash = ?", (text_hash,)).fetchone()
    conn.close()
    return res[0] if res else None, text_hash

def generate_triangulated_meaning(vector_dict, source_context):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: return "⚠️ API Key Missing."
    prompt = f"""
    Topology: {vector_dict}
    Text: "{source_context[:1000]}"
    
    Write from 1 to 3 dense paragraphs, none exceeding 50 words, triangulating the essence of Text above.
    Use all the philosophical schools represented in Topology to understand Text, and construct a narrative without mentioning the philosophies by name.
    Be concise, choose density over niceties like saying hello and signing off.
    Call out friction between the dimensions when you see it, also note alignment and consilience. Be absolutely unbiased.
    DO NOT list or mention the weights or dimensions given to you, instead weave use the concepts they signify into the narrative. 
    At the end write an opinionated one-line verdict from Text — for example, is it balanced, fair, biased, or equitable?
    """
    try:
        client = openai.OpenAI(api_key=api_key, http_client=httpx.Client())
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a master of comparative philosophy."},
                      {"role": "user", "content": prompt}],
            temperature=0.4
        )
        return res.choices[0].message.content
    except Exception as e: return f"⚠️ Error: {str(e)}"

# --- 3. UI NAVIGATION ---

page = st.sidebar.selectbox("Navigation", ["Main Analysis", "Sanskrit Non-Translatables", "Admin & Logs"])

if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")
    choice = st.sidebar.selectbox("Benchmark Document", list(CORPORA.keys()) + ["Custom Text..."])
    input_text = CORPORA.get(choice, {}).get("text", "") if choice != "Custom Text..." else st.sidebar.text_area("Passage", height=300)
    
    if choice != "Custom Text...":
        st.sidebar.markdown(f"**Source Context:**\n\n{input_text}")

    if input_text:
        conn = sqlite3.connect(DB_NAME)
        tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
        df = pd.read_sql_query(f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(tokens))})", conn, params=tokens)
        conn.close()

        if not df.empty:
            avg_dict = df[['u', 'f', 'p', 'm', 't', 's', 'd', 'c']].mean().to_dict()
            
            if st.session_state.get('synth_active', False):
                # --- SYNTHESIS (MERGED) VIEW ---
                m_lab, m_val = get_radar_data(['u','f','p','m'], avg_dict)
                e_lab, e_val = get_radar_data(['t','s','d','c'], avg_dict)
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=m_val, theta=m_lab, fill='toself', name='Materialist Lens', line=dict(color='red')))
                fig.add_trace(go.Scatterpolar(r=e_val, theta=e_lab, fill='toself', name='Dharmic-Essentialist Lens', line=dict(color='blue')))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True)), height=550, margin=dict(l=50, r=50, t=50, b=50))
                st.plotly_chart(fig, use_container_width=True)
                
                if st.button("🔓 De-Merge Lenses"):
                    st.session_state.synth_active = False; st.rerun()

                st.markdown("### 🌪️ Synthesized Topological Meaning")
                res, h = get_cached_synthesis(input_text, avg_dict)
                if res: st.info(res)
                else:
                    with st.spinner("⏳ Triangulating..."):
                        new_res = generate_triangulated_meaning(avg_dict, input_text)
                        conn = sqlite3.connect(DB_NAME); conn.execute("INSERT OR REPLACE INTO synthesis_cache VALUES (?,?)", (h, new_res)); conn.commit(); conn.close()
                        st.info(new_res)
            else:
                # --- SPLIT VIEW ---
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### MATERIALIST LENS")
                    l, v = get_radar_data(['u','f','p','m'], avg_dict)
                    st.plotly_chart(go.Figure(go.Scatterpolar(r=v, theta=l, fill='toself', fillcolor='rgba(255,0,0,0.2)')).update_layout(height=450, margin=dict(l=15,r=15,t=15,b=15)), use_container_width=True)
                with c2:
                    st.markdown("### DHARMIC-ESSENTIALIST LENS")
                    l, v = get_radar_data(['t','s','d','c'], avg_dict)
                    st.plotly_chart(go.Figure(go.Scatterpolar(r=v, theta=l, fill='toself', fillcolor='rgba(0,0,255,0.2)')).update_layout(height=450, margin=dict(l=15,r=15,t=15,b=15)), use_container_width=True)
                
                if st.button("🌪️ Synthesize (Overlay Lenses)"):
                    st.session_state.synth_active = True; st.rerun()

                # Narration Section with Headers
                st.markdown("---")
                st.markdown("### 📜 Philosophical Lineage & Narration")
                lin = SCHEMA.get("LINEAGE_MAP", {})
                n1, n2 = st.columns(2)
                with n1:
                    st.markdown("**Materialist Lens**")
                    for k in ['u','f','p','m']: st.write(f"• **{avg_dict[k]:.2f}** {lin.get(k,{}).get('school','?')}: {lin.get(k,{}).get('desc','')}")
                with n2:
                    st.markdown("**Dharmic-Essentialist Lens**")
                    for k in ['t','s','d','c']: st.write(f"• **{avg_dict[k]:.2f}** {lin.get(k,{}).get('school','?')}: {lin.get(k,{}).get('desc','')}")

elif page == "Sanskrit Non-Translatables":
    st.title("📜 Sanskrit Non-Translatables")
    if os.path.exists("weights.json"):
        with open("weights.json", "r") as f: weights = json.load(f).get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
        terms = sorted(list(weights.keys()))
        
        # RESTORED PAGINATION LOGIC
        if 'p_idx' not in st.session_state: st.session_state.p_idx = 0
        start = st.session_state.p_idx * 10
        
        c_nav, c_main = st.columns([1, 3])
        with c_nav:
            selected_term = st.radio("Terms:", terms[start:start+10])
            if st.button("Next 10 ➡️") and (start+10) < len(terms): st.session_state.p_idx += 1; st.rerun()
            if st.button("⬅️ Prev 10"): st.session_state.p_idx = max(0, st.session_state.p_idx - 1); st.rerun()
            
        with c_main:
            if selected_term:
                v_dict = dict(zip(['u','f','p','m','t','s','d','c'], weights[selected_term]))
                l, v = get_radar_data(['u','f','p','m','t','s','d','c'], v_dict)
                st.plotly_chart(go.Figure(go.Scatterpolar(r=v, theta=l, fill='toself')).update_layout(height=500, margin=dict(l=40,r=40,t=40,b=40)), use_container_width=True)
                
                # CACHED AI SYNTHESIS FOR TERMS
                res, h = get_cached_synthesis(selected_term, v_dict)
                if res: st.info(res)
                else:
                    with st.spinner("⏳ Triangulating term..."):
                        new_res = generate_triangulated_meaning(v_dict, selected_term)
                        conn = sqlite3.connect(DB_NAME); conn.execute("INSERT OR REPLACE INTO synthesis_cache VALUES (?,?)", (h, new_res)); conn.commit(); conn.close()
                        st.info(new_res)

elif page == "Admin & Logs":
    st.title("🛠️ Admin Panel")
    t1, t2 = st.tabs(["Database Viewer", "Maintenance"])
    with t1:
        conn = sqlite3.connect(DB_NAME)
        st.write("### AI Synthesis Cache")
        st.dataframe(pd.read_sql_query("SELECT * FROM synthesis_cache", conn), use_container_width=True)
        conn.close()
    with t2:
        if st.button("🔥 NUKE CACHE"):
            conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM synthesis_cache"); conn.commit(); conn.close()
            st.success("Cache cleared.")