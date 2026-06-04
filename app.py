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
import io
import sys
from datetime import datetime

# --- 1. CORE CONFIG & LOGGING ---
# In-memory log capture for the Admin log viewer
class MemoryLogHandler(logging.Handler):
    MAX_LINES = 500
    def __init__(self):
        super().__init__()
        self.records = []
    def emit(self, record):
        self.records.append({
            "ts": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
            "level": record.levelname,
            "msg": self.format(record)
        })
        if len(self.records) > self.MAX_LINES:
            self.records = self.records[-self.MAX_LINES:]

memory_handler = MemoryLogHandler()
memory_handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(memory_handler)
# Also capture root so plotly/sqlite noise is visible if needed
logging.getLogger().addHandler(memory_handler)

st.set_page_config(page_title="The Fluttering Sail", page_icon="⛵", layout="wide")

DB_NAME = "epistemic_lexicon.db"
SCHEMA, CORPORA = {}, {}

DIMS = ['u', 'f', 'p', 'm', 't', 's', 'd', 'c']
MAT_DIMS  = ['u', 'f', 'p', 'm']   # Materialist Lens
DHARMIC_DIMS = ['t', 's', 'd', 'c'] # Dharmic-Essentialist Lens

def load_assets():
    global SCHEMA, CORPORA
    if os.path.exists("epistemic_schema.json"):
        with open("epistemic_schema.json", "r") as f:
            SCHEMA = json.load(f)
        logger.info("✅ Schema loaded — %d lineage entries", len(SCHEMA.get("LINEAGE_MAP", {})))
    else:
        logger.warning("⚠️  epistemic_schema.json not found")
    if os.path.exists("corpora.json"):
        with open("corpora.json", "r") as f:
            CORPORA = json.load(f)
        logger.info("✅ Corpora loaded — %d documents", len(CORPORA))
    else:
        logger.warning("⚠️  corpora.json not found")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("CREATE TABLE IF NOT EXISTS synthesis_cache (hash TEXT PRIMARY KEY, response TEXT)")
    conn.commit()
    conn.close()
    logger.info("✅ DB initialised: %s", DB_NAME)

load_assets()
init_db()

# --- 2. LOGIC ENGINES ---

def make_radar_figure(keys_list, data_dict, title=None, fillcolor=None, line_color=None, height=420):
    """
    Build a Plotly Scatterpolar figure.
    - radialaxis range is ALWAYS [-1, 1] because DB values span that range.
    - automargin=True on angularaxis so labels never clip.
    - Slightly smaller default height so charts fit without scrolling.
    """
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})
    labels, values = [], []
    for k in keys_list:
        mapping = lineage_map.get(k.lower(), {})
        friendly = mapping.get("friendly_display", k)
        logger.debug("📍 Radar map '%s' → '%s' = %.3f", k, friendly, data_dict.get(k, 0))
        labels.append(friendly.replace(" (", "<br>("))
        values.append(data_dict.get(k, 0))

    fc  = fillcolor  or 'rgba(100,160,255,0.25)'
    lc  = line_color or 'rgba(100,160,255,0.9)'

    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]],          # close the polygon
        theta=labels + [labels[0]],
        fill='toself',
        fillcolor=fc,
        line=dict(color=lc, width=2),
        name=title or "",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[-1, 1],           # ← FIX: negative values now visible
                tickfont=dict(size=9),
                tickvals=[-1, -0.5, 0, 0.5, 1],
            ),
            angularaxis=dict(
                tickfont=dict(size=11),
            ),
            # Pull the chart in slightly so labels have breathing room
            hole=0.08,
        ),
        height=height,
        margin=dict(l=80, r=80, t=40, b=80),  # generous margins for label text
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    if title:
        fig.update_layout(showlegend=True)
    return fig


def make_overlay_figure(mat_dict, dharmic_dict, height=520):
    """Synthesis view: both lenses on a single 8-axis radar."""
    lineage_map = SCHEMA.get("LINEAGE_MAP", {})

    def extract(keys, d):
        labs, vals = [], []
        for k in keys:
            m = lineage_map.get(k.lower(), {})
            labs.append(m.get("friendly_display", k).replace(" (", "<br>("))
            vals.append(d.get(k, 0))
        return labs, vals

    ml, mv = extract(MAT_DIMS, mat_dict)
    el, ev = extract(DHARMIC_DIMS, dharmic_dict)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=mv + [mv[0]], theta=ml + [ml[0]],
        fill='toself', fillcolor='rgba(255,80,80,0.2)',
        line=dict(color='rgba(255,80,80,0.9)', width=2),
        name='Materialist Lens'
    ))
    fig.add_trace(go.Scatterpolar(
        r=ev + [ev[0]], theta=el + [el[0]],
        fill='toself', fillcolor='rgba(80,130,255,0.2)',
        line=dict(color='rgba(80,130,255,0.9)', width=2),
        name='Dharmic-Essentialist Lens'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[-1, 1], tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=11)),
        ),
        height=height,
        margin=dict(l=80, r=80, t=50, b=80),
        legend=dict(orientation='h', y=-0.15),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig


def get_cached_synthesis(text_content, vector_dict):
    unique_str = text_content + str(sorted(vector_dict.items()))
    text_hash  = hashlib.md5(unique_str.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    res  = conn.execute("SELECT response FROM synthesis_cache WHERE hash = ?", (text_hash,)).fetchone()
    conn.close()
    return (res[0] if res else None), text_hash


def generate_triangulated_meaning(vector_dict, source_context):
    api_key = os.environ.get("OPENAI_API_KEY")
<<<<<<< HEAD
    if not api_key:
        logger.warning("generate_triangulated_meaning: OPENAI_API_KEY not set")
        return "⚠️ API Key Missing. Set OPENAI_API_KEY in your environment."
=======
    if not api_key: return "⚠️ API Key Missing."
>>>>>>> 6898de0b30c341bd36a87f08558cfea7fec8941b
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
            messages=[
                {"role": "system", "content": "You are a master of comparative philosophy."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.4
        )
        result = res.choices[0].message.content
        logger.info("✅ GPT-4o synthesis returned %d chars", len(result))
        return result
    except Exception as e:
        logger.error("GPT-4o error: %s", str(e))
        return f"⚠️ Error: {str(e)}"


def load_all_nontranslatables():
    """
    Load ALL Sanskrit non-translatables from the DB (source = Rajiv_Malhotra_Non_Translatables).
    Returns dict {word: {u,f,p,m,t,s,d,c}} — the single source of truth.
    DB has 63 terms; weights.json (14 terms) is a subset and is now a fallback only.
    """
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute(
        "SELECT word, u, f, p, m, t, s, d, c FROM lexicon "
        "WHERE source = 'Rajiv_Malhotra_Non_Translatables' ORDER BY word"
    ).fetchall()
    conn.close()
    terms = {r[0]: dict(zip(DIMS, r[1:])) for r in rows}
    logger.info("📚 Loaded %d Sanskrit non-translatables from DB", len(terms))
    if not terms:
        # Fallback to weights.json
        logger.warning("DB had no nontranslatables — falling back to weights.json")
        if os.path.exists("weights.json"):
            with open("weights.json") as f:
                w = json.load(f)
            raw = w.get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
            terms = {k: dict(zip(DIMS, v)) for k, v in raw.items()}
    return terms


# --- 3. UI ---

page = st.sidebar.selectbox("Navigation", ["Main Analysis", "Sanskrit Non-Translatables", "Admin & Logs"])

# ===========================================================================
# PAGE: MAIN ANALYSIS
# ===========================================================================
if page == "Main Analysis":
    st.title("⛵ THE FLUTTERING SAIL")

    choice = st.sidebar.selectbox("Benchmark Document", list(CORPORA.keys()) + ["Custom Text..."])
    if choice != "Custom Text...":
        input_text = CORPORA.get(choice, {}).get("text", "")
        st.sidebar.markdown(f"**Source Context:**\n\n{input_text}")
    else:
        input_text = st.sidebar.text_area("Passage", height=300)

    if input_text:
        conn   = sqlite3.connect(DB_NAME)
        tokens = [w.lower().strip(".,!?;:\"()") for w in input_text.split()]
        logger.info("🔍 Analysing '%s' — %d tokens", choice, len(tokens))
        df = pd.read_sql_query(
            f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(tokens))})",
            conn, params=tokens
        )
        conn.close()
        logger.info("📊 Matched %d lexicon rows for analysis", len(df))

        if df.empty:
            st.warning("No lexicon matches found for this text. Try a different passage or expand the lexicon.")
        else:
            avg_dict = df[DIMS].mean().to_dict()
            logger.info("📐 Avg vector: %s", {k: round(v,3) for k,v in avg_dict.items()})

            if st.session_state.get('synth_active', False):
                # --- SYNTHESIS (MERGED) VIEW ---
                st.plotly_chart(make_overlay_figure(avg_dict, avg_dict), use_container_width=True)
                if st.button("🔓 De-Merge Lenses"):
                    st.session_state.synth_active = False
                    st.rerun()
                st.markdown("### 🌪️ Synthesized Topological Meaning")
                res, h = get_cached_synthesis(input_text, avg_dict)
                if res:
                    st.info(res)
                else:
                    with st.spinner("⏳ Triangulating..."):
                        new_res = generate_triangulated_meaning(avg_dict, input_text)
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("INSERT OR REPLACE INTO synthesis_cache VALUES (?,?)", (h, new_res))
                        conn.commit(); conn.close()
                        st.info(new_res)
            else:
                # --- SPLIT VIEW ---
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### MATERIALIST LENS")
                    fig = make_radar_figure(
                        MAT_DIMS, avg_dict,
                        fillcolor='rgba(255,80,80,0.2)',
                        line_color='rgba(255,80,80,0.9)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.markdown("### DHARMIC-ESSENTIALIST LENS")
                    fig = make_radar_figure(
                        DHARMIC_DIMS, avg_dict,
                        fillcolor='rgba(80,130,255,0.2)',
                        line_color='rgba(80,130,255,0.9)'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                if st.button("🌪️ Synthesize (Overlay Lenses)"):
                    st.session_state.synth_active = True
                    st.rerun()

                st.markdown("---")
                st.markdown("### 📜 Philosophical Lineage & Narration")
                lin  = SCHEMA.get("LINEAGE_MAP", {})
                n1, n2 = st.columns(2)
                with n1:
                    st.markdown("**Materialist Lens**")
                    for k in MAT_DIMS:
                        st.write(f"• **{avg_dict[k]:.2f}** {lin.get(k,{}).get('school','?')}: {lin.get(k,{}).get('desc','')}")
                with n2:
                    st.markdown("**Dharmic-Essentialist Lens**")
                    for k in DHARMIC_DIMS:
                        st.write(f"• **{avg_dict[k]:.2f}** {lin.get(k,{}).get('school','?')}: {lin.get(k,{}).get('desc','')}")

# ===========================================================================
# PAGE: SANSKRIT NON-TRANSLATABLES
# ===========================================================================
elif page == "Sanskrit Non-Translatables":
    st.title("📜 Sanskrit Non-Translatables")

    all_terms = load_all_nontranslatables()   # dict {word: vector_dict}
    term_names = sorted(all_terms.keys())
    total = len(term_names)
    PAGE_SIZE = 10

    if 'p_idx' not in st.session_state:
        st.session_state.p_idx = 0

    # Clamp page index in case data changes
    max_page = max(0, (total - 1) // PAGE_SIZE)
    st.session_state.p_idx = min(st.session_state.p_idx, max_page)

    start = st.session_state.p_idx * PAGE_SIZE
    page_terms = term_names[start : start + PAGE_SIZE]

    c_nav, c_main = st.columns([1, 3])
    with c_nav:
        st.caption(f"Terms {start+1}–{min(start+PAGE_SIZE, total)} of {total}")
        selected_term = st.radio("Terms:", page_terms, key=f"term_radio_{st.session_state.p_idx}")

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️", disabled=(st.session_state.p_idx == 0)):
                st.session_state.p_idx -= 1
                st.rerun()
        with col_next:
            if st.button("➡️", disabled=(st.session_state.p_idx >= max_page)):
                st.session_state.p_idx += 1
                st.rerun()

    with c_main:
        if selected_term:
            v_dict = all_terms[selected_term]
            logger.info("🔬 Viewing non-translatable: %s | vector: %s",
                        selected_term, {k: round(v,3) for k,v in v_dict.items()})

            fig = make_radar_figure(DIMS, v_dict, title=selected_term, height=480)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### 📐 Dimensional Breakdown")
            lin = SCHEMA.get("LINEAGE_MAP", {})
            rows_disp = []
            for k in DIMS:
                rows_disp.append({
                    "Dim": k.upper(),
                    "School": lin.get(k, {}).get("school", "?"),
                    "Score": f"{v_dict[k]:.3f}",
                    "Label": lin.get(k, {}).get("friendly_display", ""),
                })
            st.dataframe(pd.DataFrame(rows_disp), use_container_width=True, hide_index=True)

            res, h = get_cached_synthesis(selected_term, v_dict)
            if res:
                st.info(res)
            else:
                with st.spinner("⏳ Triangulating term..."):
                    new_res = generate_triangulated_meaning(v_dict, selected_term)
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT OR REPLACE INTO synthesis_cache VALUES (?,?)", (h, new_res))
                    conn.commit(); conn.close()
                    st.info(new_res)

# ===========================================================================
# PAGE: ADMIN & LOGS
# ===========================================================================
elif page == "Admin & Logs":
    st.title("🛠️ Admin & Logs")

    t_db, t_lexicon, t_logs, t_maintenance = st.tabs([
        "🗃️ Cache Viewer",
        "📚 Lexicon Browser",
        "📋 Live Log",
        "⚙️ Maintenance"
    ])

    # ---- TAB: Cache Viewer ------------------------------------------------
    with t_db:
        st.markdown("### AI Synthesis Cache")
        conn = sqlite3.connect(DB_NAME)
        df_cache = pd.read_sql_query("SELECT * FROM synthesis_cache", conn)
        conn.close()
        st.caption(f"{len(df_cache)} cached responses")
        st.dataframe(df_cache, use_container_width=True)

    # ---- TAB: Lexicon Browser ---------------------------------------------
    with t_lexicon:
        st.markdown("### Lexicon Browser")
        conn = sqlite3.connect(DB_NAME)
        df_lex = pd.read_sql_query("SELECT word, source, u, f, p, m, t, s, d, c FROM lexicon ORDER BY source, word", conn)
        conn.close()

        sources = ["All"] + sorted(df_lex['source'].unique().tolist())
        sel_src = st.selectbox("Filter by source", sources)
        if sel_src != "All":
            df_lex = df_lex[df_lex['source'] == sel_src]

        search = st.text_input("Search word")
        if search:
            df_lex = df_lex[df_lex['word'].str.contains(search, case=False)]

        st.caption(f"{len(df_lex)} entries shown")
        st.dataframe(df_lex, use_container_width=True, hide_index=True)

        # Quick per-word radar
        st.markdown("#### 🔭 Quick Radar for any word")
        all_words = sorted(df_lex['word'].tolist())
        if all_words:
            pick = st.selectbox("Pick word", all_words)
            row  = df_lex[df_lex['word'] == pick].iloc[0]
            vd   = {k: row[k] for k in DIMS}
            st.plotly_chart(make_radar_figure(DIMS, vd, title=pick, height=380), use_container_width=True)

        # ---- Add new word
        st.markdown("---")
        st.markdown("#### ➕ Add / Update Word")
        with st.expander("Enter new word vector"):
            new_word   = st.text_input("Word / term")
            new_source = st.text_input("Source label", value="Manual Entry")
            cols = st.columns(8)
            new_vals = {}
            for i, dim in enumerate(DIMS):
                label = SCHEMA.get("LINEAGE_MAP", {}).get(dim, {}).get("school", dim.upper())
                new_vals[dim] = cols[i].number_input(label, min_value=-1.0, max_value=1.0, value=0.0, step=0.05, key=f"nw_{dim}")
            if st.button("💾 Save to DB") and new_word.strip():
                conn = sqlite3.connect(DB_NAME)
                conn.execute(
                    "INSERT OR REPLACE INTO lexicon (word, u, f, p, m, t, s, d, c, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [new_word.strip()] + [new_vals[d] for d in DIMS] + [new_source]
                )
                conn.commit(); conn.close()
                logger.info("✅ Word '%s' saved to DB (source=%s)", new_word, new_source)
                st.success(f"Saved '{new_word}'")
                st.rerun()

    # ---- TAB: Live Log ----------------------------------------------------
    with t_logs:
        st.markdown("### 📋 Session Log")
        st.caption("All INFO/WARNING/ERROR events captured since app start.")

        level_filter = st.selectbox("Level filter", ["ALL", "INFO", "WARNING", "ERROR"])
        records = memory_handler.records
        if level_filter != "ALL":
            records = [r for r in records if r["level"] == level_filter]

        if not records:
            st.info("No log entries yet.")
        else:
            log_df = pd.DataFrame(records)[["ts", "level", "msg"]]
            log_df.columns = ["Time", "Level", "Message"]
            # Colour rows by level
            def level_color(val):
                colors = {"ERROR": "background-color:#5c1a1a", "WARNING": "background-color:#4a3a00", "INFO": ""}
                return colors.get(val, "")
            st.dataframe(
                log_df.style.applymap(level_color, subset=["Level"]),
                use_container_width=True, hide_index=True
            )
            if st.button("🔃 Refresh Log"):
                st.rerun()

    # ---- TAB: Maintenance -------------------------------------------------
    with t_maintenance:
        st.markdown("### ⚙️ Database Maintenance")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🔥 Nuke AI Cache")
            st.caption("Clears all GPT-4o synthesis cache. Re-analysis will re-call the API.")
            if st.button("🔥 NUKE CACHE"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM synthesis_cache")
                conn.commit(); conn.close()
                logger.warning("⚠️  Synthesis cache NUKED by admin")
                st.success("Cache cleared.")

        with col2:
            st.markdown("#### 🗑️ Delete a Word")
            st.caption("Remove a single entry from the lexicon.")
            conn = sqlite3.connect(DB_NAME)
            all_lex_words = [r[0] for r in conn.execute("SELECT word FROM lexicon ORDER BY word").fetchall()]
            conn.close()
            del_word = st.selectbox("Word to delete", all_lex_words)
            if st.button(f"🗑️ Delete '{del_word}'"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM lexicon WHERE word = ?", (del_word,))
                conn.commit(); conn.close()
                logger.warning("🗑️ Word '%s' deleted from lexicon by admin", del_word)
                st.success(f"Deleted '{del_word}'")
                st.rerun()

        st.markdown("---")
        st.markdown("#### 📤 Export Lexicon as CSV")
        conn = sqlite3.connect(DB_NAME)
        df_exp = pd.read_sql_query("SELECT * FROM lexicon", conn)
        conn.close()
        csv_bytes = df_exp.to_csv(index=False).encode()
        st.download_button("⬇️ Download lexicon.csv", csv_bytes, "lexicon.csv", "text/csv")

        st.markdown("#### 📥 Import Words from CSV")
        st.caption("CSV must have columns: word, u, f, p, m, t, s, d, c, source")
        uploaded_csv = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_csv:
            df_import = pd.read_csv(uploaded_csv)
            required = set(DIMS + ['word'])
            if not required.issubset(set(df_import.columns)):
                st.error(f"CSV missing columns. Need at minimum: {required}")
            else:
                if 'source' not in df_import.columns:
                    df_import['source'] = 'CSV Import'
                if st.button(f"📥 Import {len(df_import)} rows"):
                    conn = sqlite3.connect(DB_NAME)
                    inserted = 0
                    for _, row in df_import.iterrows():
                        conn.execute(
                            "INSERT OR REPLACE INTO lexicon (word, u, f, p, m, t, s, d, c, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
                            [row['word']] + [row[d] for d in DIMS] + [row.get('source','CSV Import')]
                        )
                        inserted += 1
                    conn.commit(); conn.close()
                    logger.info("📥 CSV import: %d rows added", inserted)
                    st.success(f"Imported {inserted} rows")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### 🏷️ DB Stats")
        conn = sqlite3.connect(DB_NAME)
        stats = pd.read_sql_query("SELECT source, COUNT(*) as count FROM lexicon GROUP BY source ORDER BY count DESC", conn)
        cache_count = conn.execute("SELECT COUNT(*) FROM synthesis_cache").fetchone()[0]
        conn.close()
        st.dataframe(stats, use_container_width=True, hide_index=True)
        st.caption(f"Synthesis cache: {cache_count} entries")
