"""
app.py — The Fluttering Sail
=============================
A hermeneutic framework for projecting text into a curated
8-dimensional philosophical coordinate space, with real-time synthesis.

Architecture
------------
This file implements the Streamlit UI and core analysis pipeline.
It is intentionally kept as a thin UI layer:
  - Visualisation: make_radar_figure(), make_overlay_figure()
  - Tokenisation: tokenise() with Unicode diacritic normalisation
  - LLM synthesis: generate_triangulated_meaning()
  - Diagnostics: delegated entirely to diagnostics_engine.py

Configuration files (edit these, not Python, for routine tuning)
  prompts.json       — LLM model, temperature, role, prompt templates
  diagnostics.json   — diagnostic threshold values (Table 1 in paper)
  tranche_master.json — anchor seeds + expansion vocabulary
  corpora.json       — benchmark corpus texts + linked_corpora pointer
  sanskrit_corpora.json — extended Sanskrit texts (linked, not benchmarks)
  epistemic_schema.json — dimension labels and lineage map
  epistemic_lexicon.db  — SQLite lexicon (618+ entries)

Live app  : https://the-fluttering-sail.onrender.com
Repository: https://github.com/prakar/the-fluttering-sail

Companion paper
  "An 8-Dimensional Quantised Hermeneutic Ethics Framework"
  Submitted to: Ethics and Information Technology (Springer)

Dependencies: see requirements.txt
Licence     : see LICENSE
"""

# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
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
import unicodedata
import sys
from datetime import datetime

# Diagnostic engine is a standalone module — see diagnostics_engine.py
# Importing here registers its logger into the same logging hierarchy
from diagnostics_engine import run_diagnostics, render_diagnostics, render_proximity_meters
from ingestion_engine import ingest_words, CHUNK_SIZE as _CHUNK_SIZE, filter_stopwords, is_stopword, STOPWORDS
from radar import make_radar_figure, make_overlay_figure

# ---------------------------------------------------------------------------
# 1. LOGGING — in-memory capture for the Admin log viewer
# ---------------------------------------------------------------------------
class MemoryLogHandler(logging.Handler):
    """Captures log records in memory for display in the Admin Live Log tab."""
    MAX_LINES = 500

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append({
            "ts":    datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
            "level": record.levelname,
            "msg":   self.format(record)
        })
        if len(self.records) > self.MAX_LINES:
            self.records = self.records[-self.MAX_LINES:]


memory_handler = MemoryLogHandler()
memory_handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(memory_handler)
# Attach to root so diagnostics_engine and other modules also appear in the live log
logging.getLogger().addHandler(memory_handler)

# ---------------------------------------------------------------------------
# 2. STREAMLIT PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(page_title="The Fluttering Sail", page_icon="⛵", layout="wide")

# ---------------------------------------------------------------------------
# 3. CONSTANTS
# ---------------------------------------------------------------------------
DB_NAME      = "epistemic_lexicon.db"
DIMS         = ['u', 'f', 'p', 'm', 't', 's', 'd', 'c']
MAT_DIMS     = ['u', 'f', 'p', 'm']   # Materialist Lens axes
DHARMIC_DIMS = ['t', 's', 'd', 'c']   # Dharmic-Essentialist Lens axes

SCHEMA: dict = {}
CORPORA: dict = {}
_RAW_CORPORA: dict = {}

# ---------------------------------------------------------------------------
# 3b. LLM PROVIDER CONFIG (from llm_config.json)
# ---------------------------------------------------------------------------
_LLM_CONFIG_FILE = "llm_config.json"
_LLM_CFG: dict = {}
if os.path.exists(_LLM_CONFIG_FILE):
    with open(_LLM_CONFIG_FILE) as _f:
        _LLM_CFG = {k: v for k, v in json.load(_f).items() if not k.startswith("_note_")}
    logger.info("✅ LLM config: provider=%s base_url=%s key_var=%s",
                _LLM_CFG.get("provider"), _LLM_CFG.get("base_url"), _LLM_CFG.get("api_key_env_var"))
else:
    logger.warning("⚠️  llm_config.json not found — synthesis will fall back to LLM_API_KEY env var + default endpoint")

LLM_KEY_ENV_VAR = _LLM_CFG.get("api_key_env_var", "OPENAI_API_KEY")  # fallback if llm_config.json absent
LLM_BASE_URL    = _LLM_CFG.get("base_url", "https://api.openai.com/v1")

# ---------------------------------------------------------------------------
# 4. ASSET LOADING
# ---------------------------------------------------------------------------
def load_assets():
    """
    Load epistemic_schema.json and corpora.json into module-level globals.
    Logs success/failure for each file — visible in Admin > Live Log.
    The raw corpora dict (including __ metadata keys) is preserved in
    _RAW_CORPORA so load_linked_corpora() can access the pointer.
    """
    global SCHEMA, CORPORA, _RAW_CORPORA

    # Schema
    if os.path.exists("epistemic_schema.json"):
        try:
            with open("epistemic_schema.json") as f:
                SCHEMA = json.load(f)
            logger.info("✅ Schema loaded — %d lineage entries", len(SCHEMA.get("LINEAGE_MAP", {})))
        except Exception as exc:
            logger.error("❌ Failed to parse epistemic_schema.json: %s", exc)
    else:
        logger.warning("⚠️  epistemic_schema.json not found — dimension labels will be missing")

    # Corpora
    if os.path.exists("corpora.json"):
        try:
            with open("corpora.json") as f:
                _RAW_CORPORA = json.load(f)
            # Strip __ metadata keys for the public CORPORA dict used by the UI
            CORPORA = {k: v for k, v in _RAW_CORPORA.items() if not k.startswith("__")}
            logger.info(
                "✅ Corpora loaded — %d benchmark texts | linked_corpora: %s",
                len(CORPORA),
                _RAW_CORPORA.get("__linked_corpora__", "none")
            )
        except Exception as exc:
            logger.error("❌ Failed to parse corpora.json: %s", exc)
    else:
        logger.warning("⚠️  corpora.json not found — benchmark dropdown will be empty")


def init_db():
    """
    Ensure required tables exist. Safe to call on every startup.

    Tables:
      synthesis_cache   — cached LLM narration responses (hash → text)
      ingestion_queue   — persistent queue of unrecognised words awaiting ingestion
                          Records are never deleted; status flag controls visibility.
                          status: 'pending' | 'ingested'
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS synthesis_cache "
            "(hash TEXT PRIMARY KEY, response TEXT)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_queue (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                source_label  TEXT NOT NULL,
                words_json    TEXT NOT NULL,
                word_count    INTEGER NOT NULL,
                queued_at     TEXT NOT NULL,
                status        TEXT NOT NULL DEFAULT 'pending',
                ingested_at   TEXT,
                notes         TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("✅ DB ready: %s", DB_NAME)
    except Exception as exc:
        logger.error("❌ DB init failed for %s: %s", DB_NAME, exc)


load_assets()
init_db()

# ---------------------------------------------------------------------------
# INGESTION QUEUE HELPERS
# ---------------------------------------------------------------------------
_GPT4O_INPUT_PRICE_PER_1M = 5.00   # USD — update if pricing changes
_PROMPT_OVERHEAD_TOKENS   = 850    # system prompt + instruction overhead per chunk
_CHUNK_SIZE               = 10     # words per API call

def estimate_cost(n_words: int) -> tuple[int, float]:
    """Return (estimated_tokens, estimated_usd) for ingesting n_words."""
    n_chunks = max(1, -(-n_words // _CHUNK_SIZE))   # ceiling division
    tokens   = n_chunks * (_PROMPT_OVERHEAD_TOKENS + _CHUNK_SIZE * 15)
    cost     = tokens * _GPT4O_INPUT_PRICE_PER_1M / 1_000_000
    return tokens, cost


def add_to_queue(source_label: str, words: list) -> bool:
    """
    Add a batch of unrecognised words to the persistent ingestion queue.
    Deduplicates: if an identical (source_label, word_set) entry with status='pending'
    already exists, it is replaced rather than duplicated.
    Returns True on success.
    """
    if not words:
        return False
    try:
        from datetime import datetime as _dt
        conn = sqlite3.connect(DB_NAME)
        # Remove any existing pending entry for same source
        conn.execute(
            "DELETE FROM ingestion_queue WHERE source_label=? AND status='pending'",
            (source_label,)
        )
        conn.execute(
            "INSERT INTO ingestion_queue "
            "(source_label, words_json, word_count, queued_at, status) "
            "VALUES (?,?,?,?,?)",
            (source_label, json.dumps(words), len(words),
             _dt.now().strftime("%Y-%m-%d %H:%M:%S"), "pending")
        )
        conn.commit()
        conn.close()
        logger.info("📥 Queue: added %d words for '%s'", len(words), source_label)
        return True
    except Exception as exc:
        logger.error("❌ Queue add failed: %s", exc)
        return False


def get_queue(include_ingested: bool = False) -> list:
    """Return queue entries as list of dicts, newest first."""
    try:
        conn = sqlite3.connect(DB_NAME)
        if include_ingested:
            rows = conn.execute(
                "SELECT id,source_label,word_count,queued_at,status,ingested_at "
                "FROM ingestion_queue ORDER BY id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id,source_label,word_count,queued_at,status,ingested_at "
                "FROM ingestion_queue WHERE status='pending' ORDER BY id DESC"
            ).fetchall()
        conn.close()
        return [
            dict(id=r[0], source_label=r[1], word_count=r[2],
                 queued_at=r[3], status=r[4], ingested_at=r[5])
            for r in rows
        ]
    except Exception as exc:
        logger.error("❌ Queue fetch failed: %s", exc)
        return []

# ---------------------------------------------------------------------------
# 5. TOKENISATION
# ---------------------------------------------------------------------------
def normalise_token(w: str) -> str:
    """
    Strip Unicode diacritics (IAST romanised Sanskrit, accented Latin, etc.)
    so 'kāmas' matches lexicon key 'kamas', 'tapas' → 'tapas', etc.

    Mechanism: NFD decomposition separates base character from combining marks;
    we drop all characters in Unicode category Mn (Mark, Nonspacing).
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', w)
        if unicodedata.category(c) != 'Mn'
    )


def tokenise(text: str) -> list[str]:
    """
    Split text into lowercase tokens, strip punctuation and diacritics.
    Strips: standard ASCII punctuation + em-dash, Devanagari dandas (।॥|).
    Returns list of non-empty normalised strings.
    """
    strip_chars = ".,!?;:\"()[]'—।॥|ḥ"
    tokens = [
        normalise_token(w.lower().strip(strip_chars))
        for w in text.split()
        if w.strip(strip_chars)
    ]
    non_empty = [t for t in tokens if t]
    logger.debug("tokenise(): %d raw → %d tokens", len(text.split()), len(non_empty))
    return non_empty

# ---------------------------------------------------------------------------
# 6. LINKED CORPORA
# ---------------------------------------------------------------------------
def load_linked_corpora() -> dict:
    """
    Follow the __linked_corpora__ pointer in corpora.json (stored in _RAW_CORPORA)
    and load the referenced file.

    Design note: _RAW_CORPORA (not CORPORA) must be used here because CORPORA
    has already had __ keys stripped. This was the original bug — CORPORA.get()
    would always return '' for __linked_corpora__.

    Returns {title: corpus_data_dict} — empty dict if file missing or unreadable.
    """
    linked_file = _RAW_CORPORA.get("__linked_corpora__", "")
    if not linked_file:
        logger.debug("load_linked_corpora: no __linked_corpora__ key in corpora.json")
        return {}
    if not os.path.exists(linked_file):
        logger.warning(
            "⚠️  Linked corpora file '%s' not found in working directory. "
            "Ensure it is committed to the repository.", linked_file
        )
        return {}
    try:
        with open(linked_file) as f:
            data = json.load(f)
        result = {k: v for k, v in data.items() if not k.startswith("__")}
        logger.info("✅ Linked corpora loaded from %s — %d texts", linked_file, len(result))
        return result
    except Exception as exc:
        logger.error("❌ Failed to load linked corpora from %s: %s", linked_file, exc)
        return {}

# Load externalised prompts — filter _note_ annotation keys (documentation only, not active config)
_PROMPTS_FILE = "prompts.json"
_SYNTHESIS_PROMPT: dict = {}
_SANSKRIT_ESSENCE_PROMPT: dict = {}
if os.path.exists(_PROMPTS_FILE):
    with open(_PROMPTS_FILE) as _f:
        _raw_prompts = json.load(_f)
    _SYNTHESIS_PROMPT = {
        k: v for k, v in _raw_prompts.get("synthesis", {}).items()
        if not k.startswith("_note_") and k != "meta"
    }
    _SANSKRIT_ESSENCE_PROMPT = {
        k: v for k, v in _raw_prompts.get("sanskrit_essence", {}).items()
        if not k.startswith("_note_") and k != "meta"
    }
    logger.info("✅ Prompts loaded from %s (synthesis model=%s | sanskrit_essence model=%s)",
                _PROMPTS_FILE,
                _SYNTHESIS_PROMPT.get("model", "?"),
                _SANSKRIT_ESSENCE_PROMPT.get("model", "—not configured—"))
else:
    logger.warning("⚠️  %s not found — synthesis will use hardcoded fallback", _PROMPTS_FILE)

import numpy as np  # needed for radar figure computations

# ---------------------------------------------------------------------------
# 7. PROMPTS LOADING
# ---------------------------------------------------------------------------


# --- 3. LOGIC ENGINES ---

def _radar_range(keys_list: list, *data_dicts) -> float:
    """Retained for any internal callers — delegates to radar.py."""
    from radar import _radar_range as _rr
    return _rr(keys_list, *data_dicts)


def _make_radar(keys_list, data_dict, **kwargs):
    """Thin wrapper that passes SCHEMA through to radar.py."""
    return make_radar_figure(keys_list, data_dict, schema=SCHEMA, **kwargs)


def _make_overlay(mat_dict, dharmic_dict, **kwargs):
    """Thin wrapper that passes SCHEMA and dim lists through to radar.py."""
    return make_overlay_figure(mat_dict, dharmic_dict,
                               schema=SCHEMA,
                               mat_dims=MAT_DIMS,
                               dharmic_dims=DHARMIC_DIMS,
                               **kwargs)


# Alias — call sites use these names unchanged
make_radar_figure_animated = _make_radar


def get_cached_synthesis(text_content, vector_dict):
    unique_str = text_content + str(sorted(vector_dict.items()))
    text_hash  = hashlib.md5(unique_str.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    res  = conn.execute("SELECT response FROM synthesis_cache WHERE hash = ?", (text_hash,)).fetchone()
    conn.close()
    return (res[0] if res else None), text_hash


def generate_triangulated_meaning(vector_dict: dict, source_context: str,
                                  prompt_cfg: dict | None = None) -> str:
    """
    Generate philosophical narration via LLM.
    prompt_cfg defaults to _SYNTHESIS_PROMPT (text passage narration).
    Pass _SANSKRIT_ESSENCE_PROMPT for single-term Sanskrit essence descriptions.
    Provider, endpoint, and API key name all read from llm_config.json.
    """
    api_key = os.environ.get(LLM_KEY_ENV_VAR)
    if not api_key:
        logger.warning("generate_triangulated_meaning: %s not set", LLM_KEY_ENV_VAR)
        return f"⚠️ API Key Missing. Set {LLM_KEY_ENV_VAR} in your environment."

    cfg         = prompt_cfg if prompt_cfg else _SYNTHESIS_PROMPT
    model       = cfg.get("model", "gpt-4o")
    temperature = cfg.get("temperature", 0.4)
    system_role = cfg.get("system_role", "You are a master of comparative philosophy.")
    template    = cfg.get("prompt_template",
        'Topology: {vector_dict}\nSnippet: "{source_context}"\n\n'
        "Construct a single, dense paragraph triangulating the 'essence' of this text. "
        "Explain its internal friction using the philosophical schools represented in the topology. "
        "DO NOT list weights or dimensions by name. Focus on the conceptual synthesis.")

    # vector_dict may be a pre-formatted string (Sanskrit page passes vertical key:value)
    # or a dict (main analysis page passes avg_dict). Handle both.
    vec_str = vector_dict if isinstance(vector_dict, str) else str(vector_dict)

    prompt = (template
              .replace("{vector_dict}", vec_str)
              .replace("{source_context}", source_context[:1000]))

    logger.info("🤖 Synthesis — provider=%s model=%s temp=%s",
                _LLM_CFG.get("provider", "openai"), model, temperature)
    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url=LLM_BASE_URL,
            http_client=httpx.Client()
        )
        res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user",   "content": prompt}
            ],
            temperature=temperature,
        )
        result = res.choices[0].message.content
        logger.info("✅ Synthesis returned %d chars", len(result))
        return result
    except Exception as e:
        logger.error("Synthesis error: %s", str(e))
        return f"⚠️ Error: {str(e)}"


def load_all_sanskrit_concepts():
    """
    Load ALL Sanskrit ontology-dependent philosophical concepts from the DB
    (source = Sanskrit_Ontology_Dependent).
    Returns dict {word: {u,f,p,m,t,s,d,c}} — the single source of truth.
    weights.json is a subset and is now a fallback only.
    """
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute(
        "SELECT word, u, f, p, m, t, s, d, c FROM lexicon "
        "WHERE source = 'Sanskrit_Ontology_Dependent' ORDER BY word"
    ).fetchall()
    conn.close()
    terms = {r[0]: dict(zip(DIMS, r[1:])) for r in rows}
    logger.info("📚 Loaded %d Sanskrit ontology-dependent concepts from DB", len(terms))
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

# ── ROUTING ──────────────────────────────────────────────────────────────────
# First visit: show splash. User chooses 'direct' or 'tour'.
# 'direct' → straight to main app (sidebar + analysis)
# 'tour'   → orientation home page
# 'onboarded' persists for the session — back button on home page clears it.
from home import render_splash, render_home

if 'onboarded' not in st.session_state:
    render_splash()
    st.stop()

if st.session_state['onboarded'] == 'tour':
    render_home()
    st.stop()

# ── MAIN APP (onboarded == 'direct') ─────────────────────────────────────────

page_options = ["Main Analysis", "Sanskrit Concepts", "Admin & Logs", "Home"]
_override = st.session_state.pop('_page_override', None)
_default_idx = page_options.index(_override) if _override in page_options else 0
page = st.sidebar.selectbox("Navigation", page_options, index=_default_idx)

# ===========================================================================
# PAGE: MAIN ANALYSIS
# ===========================================================================
if page == "Main Analysis":
    # Dropdown: 10 canonical only — Custom Text is a separate mode, not a corpus
    main_keys      = [k for k in CORPORA.keys() if not k.startswith("__")]
    LINKED_CORPORA = load_linked_corpora()

    choice = st.sidebar.selectbox("Canonical Texts", main_keys)

    # Handle revisit from Ingestion Queue — pre-select the corpus
    if st.session_state.get('_revisit_corpus') in main_keys:
        _revisit = st.session_state.pop('_revisit_corpus')
        st.session_state['_last_dropdown_choice'] = None
        # Force selectbox to show the revisit corpus on next render
        st.session_state['_page_override'] = 'Main Analysis'
        choice = _revisit

    # Source card — immediately under dropdown
    if choice in CORPORA:
        _src = CORPORA[choice].get("source", "")
        st.sidebar.markdown(
            f"""<div style="background:#1e2a3a;border-left:3px solid #4a90d9;
                padding:10px 14px;border-radius:4px;margin:4px 0 4px 0">
                <span style="color:#7ab3e0;font-size:11px;font-weight:600;
                text-transform:uppercase;letter-spacing:0.08em">Source</span><br>
                <span style="color:#e8f0f8;font-size:14px;font-weight:500">{_src}</span>
            </div>""",
            unsafe_allow_html=True
        )

    # Custom Text — evergreen button, orthogonal to canonical dropdown
    st.sidebar.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    if st.sidebar.button("✏️  Show Custom Text Area", key="custom_text_btn",
                         help="Analyse your own passage",
                         width="stretch"):
        st.session_state['custom_mode'] = True
        st.session_state.pop('linked_choice', None)
        st.session_state.pop('custom_ran', None)
        st.session_state.pop('custom_text', None)
        st.session_state.pop('synth_active', None)
    st.sidebar.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    # --- Persistent Linked Texts section in sidebar ---
    if LINKED_CORPORA:
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            """<div style="color:#c39bd3;font-size:11px;font-weight:600;
               text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">
               📜 Linked Texts</div>""",
            unsafe_allow_html=True
        )
        for lt_name in LINKED_CORPORA:
            if st.sidebar.button(lt_name, key=f"lt_{lt_name}", width="stretch"):
                st.session_state['linked_choice'] = lt_name
                st.session_state.pop('custom_mode', None)
                st.session_state.pop('synth_active', None)

    # --- Resolve what to display ---
    input_text   = ""
    source_name  = ""
    active_title = ""

    linked_choice = st.session_state.get('linked_choice')
    custom_mode   = st.session_state.get('custom_mode', False)

    # Changing the canonical dropdown clears linked and custom modes
    if choice != st.session_state.get('_last_dropdown_choice'):
        st.session_state.pop('linked_choice', None)
        st.session_state.pop('custom_mode', None)
        st.session_state.pop('custom_ran', None)
        st.session_state.pop('custom_text', None)
        linked_choice = None
        custom_mode   = False
    st.session_state['_last_dropdown_choice'] = choice

    if custom_mode:
        # --- CUSTOM TEXT VIEW ---
        st.session_state.pop('linked_choice', None)
        active_title = '⛵ The Fluttering Sail — Custom Analysis'
        st.title(active_title)
        input_text = st.sidebar.text_area(
            "Paste any passage:",
            height=300,
            placeholder="Paste a speech, mission statement, policy document...",
            value=st.session_state.get('custom_text', ''),
        )
        source_name = "Custom"
        analyse_btn = st.sidebar.button("🔍 Analyse", type="primary")
        if analyse_btn:
            st.session_state['custom_text'] = input_text
            st.session_state['custom_ran'] = True
        elif st.session_state.get('custom_ran') and st.session_state.get('custom_text'):
            input_text = st.session_state['custom_text']
        else:
            input_text = ""
            if not st.session_state.get('custom_ran'):
                st.info("Paste a passage in the sidebar and click **Analyse** to begin.")

    elif linked_choice and linked_choice in LINKED_CORPORA:
        # --- LINKED TEXT VIEW ---
        lt_data     = LINKED_CORPORA[linked_choice]
        input_text  = lt_data.get("text", "")
        source_name = lt_data.get("source", "")
        active_title = f'⛵ The Fluttering Sail — "{linked_choice}"'
        st.title(active_title)
        st.sidebar.markdown(
            f"""<div style="background:#2a1e3a;border-left:3px solid #9b59b6;
                padding:10px 14px;border-radius:4px;margin:8px 0 12px 0">
                <span style="color:#c39bd3;font-size:11px;font-weight:600;
                text-transform:uppercase;letter-spacing:0.08em">Linked Source</span><br>
                <span style="color:#e8f0f8;font-size:14px;font-weight:500">{source_name}</span>
            </div>""",
            unsafe_allow_html=True
        )
        st.sidebar.markdown("**Text:**")
        st.sidebar.markdown(input_text)

    else:
        # --- CANONICAL CORPUS VIEW ---
        st.session_state.pop('linked_choice', None)
        st.session_state.pop('custom_ran', None)
        st.session_state.pop('custom_text', None)
        corpus_data  = CORPORA.get(choice, {})
        input_text   = corpus_data.get("text", "")
        source_name  = corpus_data.get("source", "")
        active_title = f'⛵ The Fluttering Sail — "{choice}"'
        st.title(active_title)
        st.sidebar.markdown("**Context:**")
        st.sidebar.markdown(input_text)

    # === ANALYSIS (shared by canonical, linked, and custom) ===
    if input_text:
        conn   = sqlite3.connect(DB_NAME)
        tokens = tokenise(input_text)
        # Deduplicate for lexicon lookup but preserve all for coverage calculation
        unique_tokens = list(dict.fromkeys(tokens))   # ordered deduplicated
        meaningful_tokens = [t for t in unique_tokens if len(t) > 2]  # skip stopwords <3 chars

        logger.info("🔍 Analysing — %d total tokens, %d unique, %d meaningful",
                    len(tokens), len(unique_tokens), len(meaningful_tokens))

        df = pd.read_sql_query(
            f"SELECT * FROM lexicon WHERE word IN ({','.join(['?']*len(meaningful_tokens))})",
            conn, params=meaningful_tokens
        )
        conn.close()

        matched_words = set(df['word'].tolist()) if not df.empty else set()
        unmatched_words = sorted([t for t in meaningful_tokens if t not in matched_words])
        coverage_pct = round(100 * len(matched_words) / len(meaningful_tokens), 1) if meaningful_tokens else 0
        avg_dict = None   # set below if matches found

        logger.info("📊 Coverage: %d/%d meaningful tokens matched (%.1f%%)",
                    len(matched_words), len(meaningful_tokens), coverage_pct)

        if df.empty:
            st.warning("No lexicon matches found. Try a different passage or expand the lexicon.")
            # Still show coverage report so user knows what to do
        else:
            avg_dict = df[DIMS].mean().to_dict()
            logger.info("📐 Avg vector: %s", {k: round(v,3) for k,v in avg_dict.items()})

            if st.session_state.get('synth_active', False):
                # --- SYNTHESIS (MERGED) VIEW ---
                st.plotly_chart(_make_overlay(avg_dict, avg_dict))
                render_proximity_meters(avg_dict)
                _, btn_col, _ = st.columns([2, 1, 2])
                with btn_col:
                    if st.button("🔓 De-Merge Lenses", width="stretch"):
                        st.session_state.synth_active = False
                        st.rerun()
                st.markdown("### 🌪️ Hermeneutic Synthesis")
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
                    st.plotly_chart(_make_radar(
                        MAT_DIMS, avg_dict,
                        fillcolor='rgba(255,80,80,0.2)',
                        line_color='rgba(255,80,80,0.9)'
                    ))
                with c2:
                    st.markdown("### DHARMIC-ESSENTIALIST LENS")
                    st.plotly_chart(_make_radar(
                        DHARMIC_DIMS, avg_dict,
                        fillcolor='rgba(80,130,255,0.2)',
                        line_color='rgba(80,130,255,0.9)'
                    ))

                render_proximity_meters(avg_dict)

                _, btn_col, _ = st.columns([2, 1, 2])
                with btn_col:
                    if st.button("🌪️ Synthesize (Overlay Lenses)", width="stretch"):
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

        # --- COVERAGE REPORT (always shown, regardless of match count) ---
        st.markdown("---")
        st.markdown("### 📊 Lexicon Coverage Report")

        # Coverage meter
        if coverage_pct >= 60:
            bar_colour = "#2ecc71"
            confidence = "High"
        elif coverage_pct >= 30:
            bar_colour = "#f39c12"
            confidence = "Moderate"
        else:
            bar_colour = "#e74c3c"
            confidence = "Low"

        # Low-mu interpretation — only shown when coverage is reasonable but magnitude is low
        if len(matched_words) >= 8 and not df.empty:
            mu = float(df[DIMS].abs().mean().mean())
            if mu < 0.25:
                st.info(
                    "🔮 **Low mean magnitude detected** (μ={:.3f}) — This text's vocabulary "
                    "approaches or transcends the framework's dimensional poles. "
                    "Concepts of radical renunciation, metaphysical abstraction, or pure "
                    "ontological negation systematically score near-zero across all axes "
                    "because they oppose or dissolve the distinctions the framework measures. "
                    "This is a philosophically coherent result, not a coverage gap.".format(mu)
                )

        st.markdown(
            f"""<div style="background:#1a1a2e;border-radius:8px;padding:16px 20px;margin-bottom:16px">
              <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px">
                <span style="color:#aaa;font-size:13px">Lexicon coverage</span>
                <span style="color:{bar_colour};font-size:22px;font-weight:700">{coverage_pct}%</span>
              </div>
              <div style="background:#333;border-radius:4px;height:8px;width:100%">
                <div style="background:{bar_colour};border-radius:4px;height:8px;width:{min(coverage_pct,100)}%"></div>
              </div>
              <div style="margin-top:8px;color:#888;font-size:12px">
                <b style="color:#ccc">{len(matched_words)}</b> of <b style="color:#ccc">{len(meaningful_tokens)}</b> meaningful tokens recognised
                &nbsp;·&nbsp; Confidence: <b style="color:{bar_colour}">{confidence}</b>
              </div>
            </div>""",
            unsafe_allow_html=True
        )

        # Low-μ interpretive note — shown when matched words average near-zero magnitude
        if avg_dict is not None:
            mu_val = float(np.mean(np.abs(np.array([avg_dict[d] for d in DIMS]))))
            if mu_val < 0.25:
                st.markdown(
                    f"""<div style="background:#1a2a1a;border-left:3px solid #5d8a5e;
                        padding:10px 14px;border-radius:4px;margin:8px 0 12px 0;font-size:13px">
                        <span style="color:#8db88e;font-weight:600">🔮 Low mean magnitude detected</span>
                        &nbsp;<span style="color:#666;font-size:11px">(μ={mu_val:.3f})</span><br>
                        <span style="color:#aaa">This text's vocabulary approaches or transcends the framework's
                        dimensional poles — a signature of radical renunciation, metaphysical abstraction,
                        or highly contextual language that points <em>beyond</em> the interpretive space
                        rather than filling it. The directional pattern across dimensions is still
                        meaningful; the absolute magnitudes are not the signal here.</span>
                    </div>""",
                    unsafe_allow_html=True
                )
                logger.info("🔮 Low-μ note rendered (μ=%.3f)", mu_val)

        if unmatched_words:
            with st.expander(f"🔍 {len(unmatched_words)} unrecognised words — expand to see & act"):
                # Show the words as pills
                pills_html = " ".join(
                    f'<span style="display:inline-block;background:#2a2a3e;border:1px solid #444;'
                    f'border-radius:12px;padding:3px 10px;margin:3px;font-size:12px;color:#ccc">'
                    f'{w}</span>'
                    for w in unmatched_words[:80]
                )
                if len(unmatched_words) > 80:
                    pills_html += f'<span style="color:#888;font-size:12px"> … and {len(unmatched_words)-80} more</span>'
                st.markdown(pills_html, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("#### 🛠️ How to add these words to the lexicon")
                st.markdown(
                    """**Option 1 — Add to an existing tranche** (fastest):

1. Open `tranche_master.json` in your fork
2. Find the most relevant tranche key (e.g. `Tranche_6_Political_Contemporary`)
3. Add your words to the list
4. Run: `python agent_expand.py` (with `DRY_RUN=True` first to preview, then `False` to commit)

**Option 2 — Create a new tranche** (for a distinct vocabulary domain):

1. Add a new key to `TRANCHES` in `tranche_master.json`, e.g. `"Tranche_7_My_Domain": ["word1", "word2", ...]`
2. Run `agent_expand.py` — it will process your new tranche automatically

**Option 3 — Add individual words via the Admin interface**:

Navigate to **Admin & Logs → Lexicon Browser → Add / Update Word** and enter vectors manually.
Use this for high-priority terms where you want precise philosophical control.

> 💡 You need an LLM API key for Options 1 & 2 (set the variable named in llm_config.json → api_key_env_var). See **Appendix A.5.3** in the paper.
> Fork the repo first so your additions are preserved: **github.com/prakar/the-fluttering-sail**"""
                )

                # Download the unmatched words as a text file for easy copy-paste into tranche
                unmatched_csv = "\n".join(f'"{w}",' for w in unmatched_words)
                st.download_button(
                    "⬇️ Download unrecognised words as JSON array fragment",
                    data=f"[\n{unmatched_csv}\n]",
                    file_name="unrecognised_words.txt",
                    mime="text/plain",
                    help="Paste directly into a tranche list in tranche_master.json"
                )

                st.markdown("---")
                # Determine source label
                _queue_source = (
                    f"Custom Text {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    if custom_mode else
                    linked_choice if (linked_choice and linked_choice in LINKED_CORPORA) else
                    choice
                )
                _est_tokens, _est_cost = estimate_cost(len(unmatched_words))

                # Split into philosophical vs stopwords for review
                _keep_words, _stop_words = filter_stopwords(unmatched_words)

                st.markdown("#### 📥 Review before queueing")
                st.caption(
                    f"Stopwords (pre-unchecked) carry no philosophical weight and cost tokens. "
                    f"Uncheck any words you don't want to ingest."
                )

                # Two-column word selection
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown(
                        "<div style='font-size:11px;font-weight:700;text-transform:uppercase;"
                        "letter-spacing:0.1em;color:#2ecc71;margin-bottom:6px'>"
                        "✅ Philosophical vocabulary</div>",
                        unsafe_allow_html=True
                    )
                    _selected = []
                    for w in _keep_words[:60]:
                        if st.checkbox(w, value=True, key=f"qw_{w}"):
                            _selected.append(w)
                    if len(_keep_words) > 60:
                        st.caption(f"… and {len(_keep_words)-60} more (all included)")
                        _selected.extend(_keep_words[60:])

                with rc2:
                    st.markdown(
                        "<div style='font-size:11px;font-weight:700;text-transform:uppercase;"
                        "letter-spacing:0.1em;color:#e74c3c;margin-bottom:6px'>"
                        "⏭ Stopwords (excluded by default)</div>",
                        unsafe_allow_html=True
                    )
                    _selected_stops = []
                    for w in _stop_words[:60]:
                        if st.checkbox(w, value=False, key=f"sw_{w}"):
                            _selected_stops.append(w)
                    if _stop_words:
                        st.caption(
                            f"{len(_stop_words)} stopwords detected — "
                            f"tick any you want to include anyway."
                        )

                _final_words = _selected + _selected_stops
                _est_tokens_f, _est_cost_f = estimate_cost(len(_final_words))

                st.markdown(
                    f"""<div style="background:#0d1b2e;border:1px solid #2a3a5a;
                        border-radius:8px;padding:14px 18px;margin-top:8px">
                      <div style="color:#7ab3e0;font-size:12px;margin-bottom:4px">
                        <b>{len(_final_words)} words selected</b> for ingestion
                        &nbsp;·&nbsp; ~{_est_tokens_f:,} tokens
                        &nbsp;·&nbsp;
                        <b style="color:#c8a96e">~${_est_cost_f:.3f} USD</b>
                      </div>
                      <div style="color:#556;font-size:11px">
                        Ingest from <b>Admin & Logs → Ingestion Queue</b> when ready
                      </div>
                    </div>""",
                    unsafe_allow_html=True
                )
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                if st.button(
                    f"📥  Add {len(_final_words)} words to Ingestion Queue",
                    key="add_to_queue_btn",
                    type="primary",
                    disabled=len(_final_words) == 0
                ):
                    if add_to_queue(_queue_source, _final_words):
                        st.success(
                            f"✅ {len(_final_words)} words queued from **{_queue_source}**. "
                            f"Ingest them in **Admin & Logs → Ingestion Queue**."
                        )
                        logger.info("📥 Queued %d words from '%s'",
                                    len(_final_words), _queue_source)
                    else:
                        st.error("❌ Failed to add to queue — check Admin logs.")
        else:
            st.success("✅ All meaningful tokens in this passage are recognised by the lexicon.")

# ===========================================================================
# PAGE: SANSKRIT NON-TRANSLATABLES
# ===========================================================================
elif page == "Sanskrit Concepts":
    st.title("📜 Sanskrit Ontology-Dependent Concepts")

    all_terms = load_all_sanskrit_concepts()   # dict {word: vector_dict}
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
            logger.info("🔬 Viewing Sanskrit concept: %s | vector: %s",
                        selected_term, {k: round(v,3) for k,v in v_dict.items()})

            fig = _make_radar(DIMS, v_dict, title=selected_term, height=480)
            st.plotly_chart(fig)

            st.markdown("#### 📐 Dimensional Breakdown")
            lin = SCHEMA.get("LINEAGE_MAP", {})
            rows_disp = []
            for k in DIMS:
                raw = v_dict[k]
                rows_disp.append({
                    "Dim": k.upper(),
                    "School": lin.get(k, {}).get("school", "?"),
                    "Score": f"{raw:+.3f}",
                    "Polarity": "↙ Antagonistic" if raw < 0 else "▲ Aligned",
                    "Label": lin.get(k, {}).get("friendly_display", ""),
                })
            st.dataframe(pd.DataFrame(rows_disp), width="stretch", hide_index=True)

            res, h = get_cached_synthesis(selected_term, v_dict)
            if res:
                st.info(res)
            else:
                with st.spinner("⏳ Triangulating term..."):
                    # Format vector as vertical key: +value string for sanskrit_essence prompt
                    dim_labels = {
                        'u': 'Utility/Consequentialism',
                        'f': 'Fairness/Justice',
                        'p': 'Power/Realism',
                        'm': 'Mimetic/Social',
                        't': 'Telos/Purpose',
                        's': 'Structure/Duty',
                        'd': 'Dharma/Cosmic Order',
                        'c': 'Non-Dual Consciousness',
                    }
                    vec_formatted = "\n".join(
                        f"  {dim_labels.get(k, k)}: {v:+.2f}"
                        for k, v in v_dict.items()
                    )
                    # Use sanskrit_essence prompt if configured, else fall back to synthesis
                    essence_cfg = _SANSKRIT_ESSENCE_PROMPT if _SANSKRIT_ESSENCE_PROMPT else None
                    new_res = generate_triangulated_meaning(
                        vec_formatted, selected_term, prompt_cfg=essence_cfg
                    )
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT OR REPLACE INTO synthesis_cache VALUES (?,?)", (h, new_res))
                    conn.commit(); conn.close()
                    st.info(new_res)

# ===========================================================================
# PAGE: ADMIN & LOGS
# ===========================================================================
elif page == "Admin & Logs":
    st.title("🛠️ Admin & Logs")

    t_db, t_lexicon, t_logs, t_maintenance, t_scripts, t_queue = st.tabs([
        "🗃️ Cache Viewer",
        "📚 Lexicon Browser",
        "📋 Live Log",
        "⚙️ Maintenance",
        "🚀 Script Runner",
        "📥 Ingestion Queue",
    ])

    # ---- TAB: Cache Viewer ------------------------------------------------
    with t_db:
        st.markdown("### AI Synthesis Cache")
        st.caption(
            "Each entry is a cached LLM synthesis response. "
            "Delete an entry to force regeneration — useful when tuning the synthesis prompt."
        )

        conn = sqlite3.connect(DB_NAME)
        df_cache = pd.read_sql_query("SELECT hash, response FROM synthesis_cache", conn)
        conn.close()

        if df_cache.empty:
            st.info("Cache is empty.")
        else:
            st.caption(f"{len(df_cache)} cached responses")
            for idx, row in df_cache.iterrows():
                h = row['hash']
                preview = str(row['response'])[:120].replace('\n', ' ')
                col_text, col_btn = st.columns([10, 1])
                with col_text:
                    st.markdown(
                        f"""<div style="background:#1a1a2e;border-left:3px solid #444;
                            padding:8px 12px;border-radius:4px;margin:4px 0;font-size:12px;color:#bbb">
                            <span style="color:#666;font-size:10px">{h[:12]}…</span><br>
                            {preview}…
                        </div>""",
                        unsafe_allow_html=True
                    )
                with col_btn:
                    if st.button("🗑️", key=f"del_cache_{h}", help="Delete this cache entry"):
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("DELETE FROM synthesis_cache WHERE hash = ?", (h,))
                        conn.commit(); conn.close()
                        logger.info("🗑️ Cache entry deleted: %s…", h[:12])
                        st.rerun()

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
        st.dataframe(df_lex, width="stretch", hide_index=True)

        # Quick per-word radar
        st.markdown("#### 🔭 Quick Radar for any word")
        all_words = sorted(df_lex['word'].tolist())
        if all_words:
            pick = st.selectbox("Pick word", all_words)
            row  = df_lex[df_lex['word'] == pick].iloc[0]
            vd   = {k: row[k] for k in DIMS}
            st.plotly_chart(_make_radar(DIMS, vd, title=pick, height=380))

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
                log_df.style.map(level_color, subset=["Level"]),
                width="stretch", hide_index=True
            )
            if st.button("🔃 Refresh Log"):
                st.rerun()

    # ---- TAB: Maintenance -------------------------------------------------
    with t_maintenance:
        st.markdown("### ⚙️ Database Maintenance")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🔥 Nuke AI Cache")
            st.caption("Clears all LLM synthesis cache. Re-analysis will re-call the configured provider.")
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
        st.markdown("#### 🔄 Runtime Reloads")
        st.caption("Re-read config files without restarting the app.")
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            if st.button("🔄 Reload Stopwords"):
                from ingestion_engine import reload_stopwords
                n = reload_stopwords()
                st.success(f"✅ {n} stopwords reloaded from stopwords.json")
        with rcol2:
            if st.button("🔄 Reload Thresholds"):
                from diagnostics_engine import reload_thresholds
                n = reload_thresholds()
                st.success(f"✅ {n} thresholds reloaded from diagnostics.json")

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
        st.dataframe(stats, width="stretch", hide_index=True)
        st.caption(f"Synthesis cache: {cache_count} entries")

    # ---- TAB: Script Runner -----------------------------------------------
    with t_scripts:
        import subprocess, threading, queue, time as _time

        st.markdown("### 🚀 Script Runner")
        st.caption("Run seeding and ingestion scripts directly. Output streams live below.")

        SCRIPTS = {
            "engine_db.py — Seed DB from tranche_master (fast, no API)": {
                "cmd": ["python3", "engine_db.py"],
                "warn": None,
            },
            "agent_expand.py — DRY RUN (preview only, no DB write)": {
                "cmd": ["python3", "agent_expand.py"],
                "env_override": {"DRY_RUN": "1"},   # script reads DRY_RUN from source; we patch via sed
                "warn": None,
                "dry_patch": True,
            },
            "agent_expand.py — LIVE RUN (writes to DB, calls LLM API 💰)": {
                "cmd": ["python3", "agent_expand.py"],
                "warn": "⚠️ This will call the LLM API and WRITE to epistemic_lexicon.db. API costs apply. Are you sure?",
                "dry_patch": False,
            },
        }

        chosen = st.selectbox("Select script", list(SCRIPTS.keys()))
        script_cfg = SCRIPTS[chosen]

        if script_cfg["warn"]:
            st.warning(script_cfg["warn"])
            confirmed = st.checkbox("Yes, I confirm — run it")
        else:
            confirmed = True

        run_btn = st.button("▶️ Run", disabled=not confirmed)
        log_area = st.empty()

        if run_btn:
            import os as _os
            env = _os.environ.copy()

            # For dry-run variant: patch DRY_RUN=True in agent_expand.py via a temp copy
            script_path = script_cfg["cmd"][1]
            run_cmd = list(script_cfg["cmd"])

            if script_cfg.get("dry_patch") is True:
                # Create a temp patched copy with DRY_RUN = True guaranteed
                with open(script_path) as f:
                    src = f.read()
                patched = src.replace("DRY_RUN = False", "DRY_RUN = True")
                tmp_path = "_tmp_dry_run.py"
                with open(tmp_path, "w") as f:
                    f.write(patched)
                run_cmd = ["python3", tmp_path]
            elif script_cfg.get("dry_patch") is False:
                # Live run: patch DRY_RUN = False guaranteed
                with open(script_path) as f:
                    src = f.read()
                patched = src.replace("DRY_RUN = True", "DRY_RUN = False")
                tmp_path = "_tmp_live_run.py"
                with open(tmp_path, "w") as f:
                    f.write(patched)
                run_cmd = ["python3", tmp_path]

            logger.info("🚀 Admin launched script: %s", " ".join(run_cmd))
            output_lines = []

            try:
                proc = subprocess.Popen(
                    run_cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                    cwd=_os.path.dirname(_os.path.abspath(__file__)) or "."
                )
                for line in proc.stdout:
                    line = line.rstrip()
                    output_lines.append(line)
                    logger.info("[script] %s", line)
                    # Stream last 60 lines live
                    log_area.code("\n".join(output_lines[-60:]), language="")
                proc.wait()
                rc = proc.returncode
                if rc == 0:
                    st.success(f"✅ Script finished (exit 0)")
                    logger.info("✅ Script exited cleanly")
                else:
                    st.error(f"❌ Script exited with code {rc}")
                    logger.error("Script exited %d", rc)
            except Exception as e:
                st.error(f"Failed to launch: {e}")
                logger.error("Script launch error: %s", e)
            finally:
                # Clean up temp files
                for tmp in ["_tmp_dry_run.py", "_tmp_live_run.py"]:
                    if _os.path.exists(tmp):
                        _os.remove(tmp)

    # ---- TAB: Ingestion Queue -------------------------------------------
    with t_queue:
        st.markdown("### 📥 Ingestion Queue")
        st.caption(
            "Words surfaced by the Coverage Report and queued for ingestion. "
            "Records are never deleted — ingested and stopword entries are archived for audit. "
            "Ingest per-bucket or all at once."
        )

        # One-time cleanup: mark any pending words that are stopwords
        # Runs on every page load but is fast — only touches pending entries
        try:
            conn = sqlite3.connect(DB_NAME)
            pending_rows = conn.execute(
                "SELECT id, words_json FROM ingestion_queue WHERE status='pending'"
            ).fetchall()
            from datetime import datetime as _dtnow
            cleaned = 0
            for row_id, wjson in pending_rows:
                words_in = json.loads(wjson)
                keep, stops = filter_stopwords(words_in)
                if stops:
                    # Update the words_json to remove stopwords
                    conn.execute(
                        "UPDATE ingestion_queue SET words_json=?, word_count=? WHERE id=?",
                        (json.dumps(keep), len(keep), row_id)
                    )
                    cleaned += len(stops)
            if cleaned:
                conn.execute(
                    "INSERT INTO ingestion_queue "
                    "(source_label, words_json, word_count, queued_at, status, notes) "
                    "VALUES (?,?,?,?,?,?)",
                    ("_stopword_cleanup",
                     json.dumps([]),
                     0,
                     _dtnow.now().strftime("%Y-%m-%d %H:%M:%S"),
                     "stopword",
                     f"Auto-removed {cleaned} stopwords from pending queue entries")
                )
                logger.info("🧹 Queue cleanup: removed %d stopwords from pending entries", cleaned)
            conn.commit()
            conn.close()
            if cleaned:
                st.info(f"🧹 Removed **{cleaned} stopwords** from pending queue entries — "
                        f"re-queued with philosophical vocabulary only.")
        except Exception as exc:
            logger.error("Queue stopword cleanup failed: %s", exc)

        show_ingested = st.checkbox("Show ingested and stopword (archived) entries", value=False)
        queue = get_queue(include_ingested=show_ingested)

        if not queue:
            st.info("Queue is empty. Run an analysis, expand the Coverage Report, "
                    "and click **Add to Ingestion Queue**.")
        else:
            pending = [e for e in queue if e['status'] == 'pending']
            if pending:
                # Summary cost estimate across all pending
                total_words = sum(e['word_count'] for e in pending)
                total_tokens, total_cost = estimate_cost(total_words)
                st.markdown(
                    f"""<div style="background:#0d1b2e;border:1px solid #2a3a5a;
                        border-radius:8px;padding:14px 18px;margin-bottom:16px;
                        display:flex;justify-content:space-between;align-items:center">
                      <div>
                        <span style="color:#7ab3e0;font-size:13px;font-weight:600">
                          {len(pending)} pending bucket{"s" if len(pending)!=1 else ""}
                          · {total_words} words total
                        </span><br>
                        <span style="color:#556;font-size:11px">
                          Estimated: ~{total_tokens:,} tokens
                          · <b style="color:#c8a96e">~${total_cost:.3f} USD</b>
                        </span>
                      </div>
                    </div>""",
                    unsafe_allow_html=True
                )
                if st.button("⚡ Ingest All Pending", type="primary",
                             key="ingest_all_btn"):
                    st.session_state['ingest_all'] = True

            # Per-bucket cards
            for entry in queue:
                is_pending = entry['status'] == 'pending'
                border_col = "#2a3a5a" if is_pending else "#1a2a1a"
                status_badge = (
                    '<span style="background:#1a3a2a;color:#2ecc71;font-size:10px;'
                    'padding:2px 8px;border-radius:10px;font-weight:600">INGESTED</span>'
                    if entry['status'] == 'ingested' else
                    '<span style="background:#2a1a1a;color:#e74c3c;font-size:10px;'
                    'padding:2px 8px;border-radius:10px;font-weight:600">STOPWORD</span>'
                    if entry['status'] == 'stopword' else
                    '<span style="background:#1a2a3a;color:#4a90d9;font-size:10px;'
                    'padding:2px 8px;border-radius:10px;font-weight:600">PENDING</span>'
                )
                et, ec = estimate_cost(entry['word_count'])

                with st.container():
                    st.markdown(
                        f"""<div style="background:#0d1420;border:1px solid {border_col};
                            border-radius:8px;padding:14px 18px;margin-bottom:10px">
                          <div style="display:flex;justify-content:space-between;
                               align-items:flex-start;margin-bottom:8px">
                            <div>
                              <span style="color:#e8f0f8;font-size:14px;font-weight:600">
                                {entry['source_label']}
                              </span>
                              &nbsp;&nbsp;{status_badge}
                            </div>
                            <div style="text-align:right;color:#556;font-size:11px">
                              {entry['word_count']} words
                              · ~{et:,} tokens
                              · <b style="color:#c8a96e">~${ec:.3f}</b><br>
                              Queued: {entry['queued_at']}
                              {"<br>Ingested: " + entry['ingested_at'] if entry['ingested_at'] else ""}
                            </div>
                          </div>
                        </div>""",
                        unsafe_allow_html=True
                    )

                    if is_pending:
                        btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 6])
                        with btn_col1:
                            if st.button("⚡ Ingest", key=f"ingest_{entry['id']}",
                                         type="primary"):
                                st.session_state[f'ingest_id'] = entry['id']
                                st.session_state[f'ingest_source'] = entry['source_label']
                        with btn_col2:
                            if st.button("🗑 Remove", key=f"remove_{entry['id']}"):
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute(
                                    "DELETE FROM ingestion_queue WHERE id=?",
                                    (entry['id'],)
                                )
                                conn.commit(); conn.close()
                                logger.info("🗑 Queue entry %d removed", entry['id'])
                                st.rerun()
                        # Revisit button — navigate back to source corpus
                        with btn_col3:
                            if entry['source_label'] in [k for k in CORPORA
                                                          if not k.startswith("__")]:
                                if st.button(f"↩ Revisit {entry['source_label'][:30]}",
                                             key=f"revisit_{entry['id']}"):
                                    st.session_state['_page_override'] = 'Main Analysis'
                                    st.session_state['_last_dropdown_choice'] = None
                                    st.session_state['_revisit_corpus'] = entry['source_label']
                                    st.rerun()

            # Handle ingest actions (done outside card loop to avoid stale state)
            _ingest_id = st.session_state.pop('ingest_id', None)
            _ingest_source = st.session_state.pop('ingest_source', None)
            _ingest_all = st.session_state.pop('ingest_all', False)

            targets = []
            if _ingest_id:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    row = conn.execute(
                        "SELECT id,source_label,words_json FROM ingestion_queue WHERE id=?",
                        (_ingest_id,)
                    ).fetchone()
                    conn.close()
                    if row:
                        targets = [(row[0], row[1], json.loads(row[2]))]
                except Exception as exc:
                    logger.error("Queue read error: %s", exc)
            elif _ingest_all:
                try:
                    conn = sqlite3.connect(DB_NAME)
                    rows = conn.execute(
                        "SELECT id,source_label,words_json FROM ingestion_queue "
                        "WHERE status='pending'"
                    ).fetchall()
                    conn.close()
                    targets = [(r[0], r[1], json.loads(r[2])) for r in rows]
                except Exception as exc:
                    logger.error("Queue read error: %s", exc)

            if targets:
                api_key = os.environ.get(LLM_KEY_ENV_VAR)
                if not api_key:
                    st.error(f"❌ {LLM_KEY_ENV_VAR} not set — cannot ingest.")
                else:
                    total_ingested = 0
                    prog = st.progress(0, text="Starting ingestion...")

                    def _prog_cb(current, total_chunks, label):
                        prog.progress(
                            min(current / max(total_chunks, 1), 0.99),
                            text=f"Ingesting {label}…"
                        )

                    for idx, (qid, src_label, words) in enumerate(targets):
                        ingested_this = ingest_words(
                            words=words,
                            source_label=src_label,
                            db_name=DB_NAME,
                            api_key=api_key,
                            base_url=LLM_BASE_URL,
                            progress_cb=_prog_cb,
                        )
                        # Mark as ingested — audit trail preserved
                        from datetime import datetime as _dti
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute(
                            "UPDATE ingestion_queue SET status='ingested', "
                            "ingested_at=?, notes=? WHERE id=?",
                            (_dti.now().strftime("%Y-%m-%d %H:%M:%S"),
                             f"{ingested_this} words ingested", qid)
                        )
                        conn.commit(); conn.close()
                        total_ingested += ingested_this
                        logger.info("✅ Queue entry %d: %d words ingested from '%s'",
                                    qid, ingested_this, src_label)

                    prog.progress(1.0, text="Done!")
                    st.success(
                        f"✅ Ingested **{total_ingested} words** across "
                        f"{len(targets)} bucket(s). "
                        f"Reload the analysis to see updated coverage."
                    )
                    st.rerun()

elif page == "Home":
    from home import render_home
    render_home()