"""
⛵ THE FLUTTERING SAIL: HARDENED INGESTION PIPELINE (v3.4)

Changes over v3.3:
  - Five thematic tranches added to MANIFEST for 500-token lexicon expansion
  - Communist Manifesto added as corpus anchor domain
  - René Girard removed from corpus anchors
  - Tranche definitions are self-documenting for reproducibility
  - All other fixes from v3.3 retained (DRY_RUN, cleanse, chunking, validation)
"""

import sqlite3, json, os, sys, numpy as np, requests, logging
from typing import Dict, List, Tuple, Optional

# --- 1. RUNTIME CONTROLS ---
DRY_RUN = True   # ← set False to write to disk

DB_NAME        = "epistemic_lexicon.db"
WEIGHTS_FILE   = "weights.json"
BLUEPRINT_FILE = "calibration_blueprint.json"
LLM_CONFIG_FILE = "llm_config.json"
LOG_FILE       = "framework.log"
CHUNK_SIZE     = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode='a'), logging.StreamHandler()]
)
logger = logging.getLogger("EpistemicFirewall")

# --- LLM PROVIDER CONFIG (from llm_config.json) ---
if not os.path.exists(LLM_CONFIG_FILE):
    logger.error("❌ %s not found. Cannot determine API key or endpoint.", LLM_CONFIG_FILE)
    sys.exit(1)

with open(LLM_CONFIG_FILE) as f:
    _llm_cfg = json.load(f)

LLM_PROVIDER    = _llm_cfg.get("provider", "openai")
KEY_ENV_VAR     = _llm_cfg.get("api_key_env_var", "OPENAI_API_KEY")
LLM_BASE_URL    = _llm_cfg.get("base_url", "https://api.openai.com/v1").rstrip("/")
LLM_TIMEOUT     = _llm_cfg.get("timeout_seconds", 60)
API_KEY         = os.environ.get(KEY_ENV_VAR)

if not API_KEY:
    logger.error(
        "❌ API key not set. Export it before running:\n"
        "    export %s=your-key-here\n"
        "    (Key variable name comes from llm_config.json → api_key_env_var)\n"
        "    Current provider: %s | Endpoint: %s",
        KEY_ENV_VAR, LLM_PROVIDER, LLM_BASE_URL
    )
    sys.exit(1)

logger.info("✅ LLM provider: %s | endpoint: %s | key_var: %s",
            LLM_PROVIDER, LLM_BASE_URL, KEY_ENV_VAR)


# --- 2. THEMATIC TRANCHES & PROMPTS — loaded from JSON ---
# Edit tranche_master.json to add/remove/modify tranches.
# Edit prompts.json to tune model, temperature, role, or prompt text.
# Neither file should need Python changes for routine experimentation.
TRANCHE_FILE = "tranche_master.json"
PROMPTS_FILE = "prompts.json"

for _required in [TRANCHE_FILE, PROMPTS_FILE]:
    if not os.path.exists(_required):
        logger.error("❌ Required file not found: %s", _required)
        sys.exit(1)

with open(TRANCHE_FILE) as f:
    _tranche_data = json.load(f)
with open(PROMPTS_FILE) as f:
    _prompts = json.load(f)

THEMATIC_TRANCHES: Dict[str, List[str]] = _tranche_data.get("TRANCHES", {})
# Filter _note_ annotation keys — they are documentation only, not active config
INGESTION_PROMPT: dict = {
    k: v for k, v in _prompts["ingestion"].items()
    if not k.startswith("_note_") and k != "meta"
}

if not THEMATIC_TRANCHES:
    logger.error("❌ No TRANCHES key found in %s.", TRANCHE_FILE)
    sys.exit(1)

total_terms = sum(len(v) for v in THEMATIC_TRANCHES.values())
logger.info("✅ Loaded %d tranches, %d total terms from %s",
            len(THEMATIC_TRANCHES), total_terms, TRANCHE_FILE)
logger.info("✅ Prompts loaded from %s (ingestion model=%s, temp=%s)",
            PROMPTS_FILE, INGESTION_PROMPT["model"], INGESTION_PROMPT["temperature"])

# --- 3. CORRUPTION DETECTION ---
CORRUPTED_POOL = {0.81, 0.72, 0.63, 0.54, 0.09, 0.18, 0.27, 0.36}

def is_corrupted(vector_vals: list) -> bool:
    if any(v is None for v in vector_vals):
        return False
    mags = np.abs(np.array(vector_vals, dtype=float))
    unique_mags = set(np.round(mags, 2))
    in_pool = unique_mags.issubset(CORRUPTED_POOL) and len(unique_mags) > 1
    signs = np.sign(np.array(vector_vals, dtype=float))
    nonzero = [s for s in signs if s != 0]
    alternating = len(nonzero) > 1 and all(nonzero[i] != nonzero[i+1] for i in range(len(nonzero)-1))
    return in_pool or alternating

def cleanse_corrupted_records(conn: sqlite3.Connection) -> set:
    logger.info("⚡ Starting corruption audit...")
    try:
        rows = conn.execute("SELECT word, u, f, p, m, t, s, d, c FROM lexicon").fetchall()
    except sqlite3.OperationalError:
        logger.info("ℹ️  Lexicon table absent — skipping cleanse.")
        return set()
    purged = set()
    for row in rows:
        word, *vec = row
        if is_corrupted(vec):
            conn.execute("DELETE FROM lexicon WHERE word = ?", (word,))
            purged.add(word)
            logger.info("🗑️  Purged corrupted: '%s'", word)
    if purged:
        conn.commit()
        logger.warning("⚠️  Cleanse complete: %d corrupted rows removed.", len(purged))
    else:
        logger.info("✅ Audit clean.")
    return purged


# --- 4. SPEC LOADING ---
def load_specifications() -> Tuple[dict, dict, dict, dict]:
    for fn in [WEIGHTS_FILE, BLUEPRINT_FILE]:
        if not os.path.exists(fn):
            logger.error("Missing required file: %s", fn)
            sys.exit(1)
    with open(WEIGHTS_FILE)   as f: w = json.load(f)
    with open(BLUEPRINT_FILE) as f: b = json.load(f)
    axiomatic  = w.get("AXIOMATIC_SEED_VAULT", {})
    sanskrit_w = w.get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
    manifest   = b.get("ANCHOR_DISCOVERY_MANIFEST", {})
    alignment  = b.get("THEMATIC_ALIGNMENT_MAP", {})
    logger.info("✅ Specs loaded — AXIOMATIC:%d  SANSKRIT:%d  MANIFEST:%d  ALIGNMENT:%d",
                len(axiomatic), len(sanskrit_w), len(manifest), len(alignment))
    return axiomatic, sanskrit_w, manifest, alignment

AXIOMATIC, SANSKRIT_WEIGHTS, MANIFEST, ALIGNMENT = load_specifications()


# --- 5. ANCHOR RESOLUTION ---
def resolve_anchor_weights(token: str, purged_words: set) -> Optional[np.ndarray]:
    t = token.lower().strip()
    if t in purged_words:
        return None
    if t in AXIOMATIC:
        return np.array(AXIOMATIC[t], dtype=float)
    if t in SANSKRIT_WEIGHTS:
        logger.info("💎 Direct anchor: '%s'", t)
        return np.array(SANSKRIT_WEIGHTS[t], dtype=float)
    t_norm = t.replace("-", " ")
    if t_norm in SANSKRIT_WEIGHTS:
        return np.array(SANSKRIT_WEIGHTS[t_norm], dtype=float)
    for key, variants in ALIGNMENT.items():
        if any(v.lower() in t for v in variants):
            if key in SANSKRIT_WEIGHTS:
                logger.info("⏳ Alignment match: '%s' → '%s'", t, key)
                return np.array(SANSKRIT_WEIGHTS[key], dtype=float)
    return None


# --- 6. GPT CALL ---
def fetch_empirical_vectors(domain: str, terms: List[str]) -> Dict[str, list]:
    """
    Call LLM for a list of terms. Model, temperature, role, and prompt template
    all read from prompts.json — edit there, not here.
    """
    cfg = INGESTION_PROMPT
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    context_line = (
        "Evaluate each term as a standalone philosophical concept."
        if domain.startswith("Tranche_")
        else f"Evaluate these terms in the context of: {domain}."
    )

    prompt = (cfg["prompt_template"]
              .replace("{context_line}", context_line)
              .replace("{terms}", ", ".join(terms))
              .replace("{n_terms}", str(len(terms))))

    payload = {
        "model": cfg["model"],
        "temperature": cfg["temperature"],
        "messages": [
            {"role": "system", "content": cfg["system_role"]},
            {"role": "user",   "content": prompt},
        ],
    }
    if cfg.get("response_format"):
        payload["response_format"] = cfg["response_format"]

    try:
        r = requests.post(f"{LLM_BASE_URL}/chat/completions",
                          headers=headers, json=payload, timeout=LLM_TIMEOUT)
        r.raise_for_status()
        raw = json.loads(r.json()['choices'][0]['message']['content'])
        validated = {}
        for k, v in raw.items():
            if isinstance(v, list) and len(v) == 8 and all(isinstance(x, (int, float)) for x in v):
                validated[k.lower().strip()] = v
            else:
                logger.warning("⚠️  Bad vector for '%s': %s — skipped", k, v)
        logger.info("✅ LLM returned %d/%d valid vectors for [%s]", len(validated), len(terms), domain[:40])
        return validated
    except Exception as e:
        logger.error("❌ LLM call failed for '%s': %s", domain, e)
        return {}


# --- 7. HYBRID MERGE ---
def execute_hybrid_merge(empirical_data: Dict[str, list], purged_words: set) -> Dict[str, list]:
    merged = {}
    for token, emp_vec in empirical_data.items():
        try:
            emp_arr = np.array(emp_vec, dtype=float)
            if len(emp_arr) != 8:
                logger.error("❌ Wrong dimension for '%s' — skipped", token)
                continue
            anchor = resolve_anchor_weights(token, purged_words)
            if anchor is not None:
                blended = np.clip(0.6 * anchor + 0.4 * emp_arr, -1.0, 1.0)
                merged[token] = blended.tolist()
                logger.info("🧬 Blend (0.6A+0.4E): '%s'", token)
            else:
                damped = np.clip(emp_arr * 0.9, -1.0, 1.0)
                merged[token] = damped.tolist()
                logger.info("📡 Empirical-only (0.9×): '%s'", token)
        except Exception as e:
            logger.error("❌ Merge error for '%s': %s", token, e)
    return merged


# --- 8. PERSISTENCE ---
def save_to_lexicon(conn: sqlite3.Connection, data: Dict[str, list], source: str):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lexicon
        (word TEXT PRIMARY KEY, u REAL, f REAL, p REAL, m REAL,
         t REAL, s REAL, d REAL, c REAL, source TEXT)
    """)
    saved = 0
    for token, vec in data.items():
        if vec is None or len(vec) != 8:
            logger.error("❌ Bad vector for '%s' — skipped", token)
            continue
        conn.execute(
            "INSERT OR REPLACE INTO lexicon (word, u, f, p, m, t, s, d, c, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
            [token] + vec + [source]
        )
        saved += 1
    conn.commit()
    logger.info("💾 Saved %d entries (source=%s)", saved, source)


def print_preview(conn: sqlite3.Connection, limit: int = 20):
    print(f"\n🔬 --- PREVIEW (first {limit} rows by source) ---")
    print(f"{'Word':<22} | {'u':>6} | {'f':>6} | {'p':>6} | {'m':>6} | {'t':>6} | {'s':>6} | {'d':>6} | {'c':>6} | source")
    print("-" * 120)
    rows = conn.execute(
        "SELECT word, u, f, p, m, t, s, d, c, source FROM lexicon ORDER BY source, word LIMIT ?", (limit,)
    ).fetchall()
    for r in rows:
        nums = " | ".join(f"{x:+.3f}" if isinstance(x, float) else f"{str(x):>6}" for x in r[1:9])
        print(f"{r[0]:<22} | {nums} | {r[9][:30]}")
    # Stats by source
    print("\n📊 Stats by source:")
    for row in conn.execute("SELECT source, COUNT(*) as n FROM lexicon GROUP BY source ORDER BY n DESC"):
        print(f"  {row[0]:<45}: {row[1]} entries")
    total = conn.execute("SELECT COUNT(*) FROM lexicon").fetchone()[0]
    print(f"\n  TOTAL: {total} lexicon entries")


# --- 9. MAIN ---
if __name__ == "__main__":
    logger.info("⛵ Ingestion Pipeline v3.4 starting — DRY_RUN=%s", DRY_RUN)

    if DRY_RUN:
        logger.info("🛡️  DRY RUN: working in :memory:")
        working_conn = sqlite3.connect(":memory:")
        if os.path.exists(DB_NAME):
            src = sqlite3.connect(DB_NAME)
            src.backup(working_conn)
            src.close()
            logger.info("📋 Cloned '%s' into memory.", DB_NAME)
    else:
        logger.warning("⚠️  LIVE MODE: writing to %s", DB_NAME)
        working_conn = sqlite3.connect(DB_NAME)

    # Step 1: Cleanse corruption
    purged = cleanse_corrupted_records(working_conn)

    # Step 2: Process MANIFEST (corpus-anchored entries)
    logger.info("\n━━━ PHASE 1: MANIFEST (corpus-anchored) ━━━")
    for author, keywords_raw in MANIFEST.items():
        all_terms = [t.strip() for t in keywords_raw.split(",") if t.strip()] \
                    if isinstance(keywords_raw, str) else list(keywords_raw)
        logger.info("🔍 %s (%d terms)", author, len(all_terms))
        all_merged = {}
        for i in range(0, len(all_terms), CHUNK_SIZE):
            chunk = all_terms[i: i + CHUNK_SIZE]
            raw = fetch_empirical_vectors(author, chunk)
            if raw:
                all_merged.update(execute_hybrid_merge(raw, purged))
        if all_merged:
            save_to_lexicon(working_conn, all_merged, author)
            logger.info("✅ %s — %d entries saved", author, len(all_merged))

    # Step 3: Process THEMATIC TRANCHES (lexicon expansion)
    logger.info("\n━━━ PHASE 2: THEMATIC TRANCHES (500-token expansion) ━━━")
    for tranche_name, terms in THEMATIC_TRANCHES.items():
        # Deduplicate against existing DB entries to avoid redundant API calls
        existing = set(
            r[0] for r in working_conn.execute("SELECT word FROM lexicon").fetchall()
        )
        new_terms = [t for t in terms if t not in existing]
        # Further deduplicate the list itself (some terms repeat across tranches intentionally for emphasis)
        seen = set()
        deduped = []
        for t in new_terms:
            if t not in seen:
                seen.add(t)
                deduped.append(t)

        if not deduped:
            logger.info("⏭️  %s — all %d terms already in DB, skipping", tranche_name, len(terms))
            continue

        logger.info("🔍 %s — %d new terms to process", tranche_name, len(deduped))
        all_merged = {}
        for i in range(0, len(deduped), CHUNK_SIZE):
            chunk = deduped[i: i + CHUNK_SIZE]
            logger.info("  📦 Chunk %d–%d: %s", i+1, i+len(chunk), chunk)
            raw = fetch_empirical_vectors(tranche_name, chunk)
            if raw:
                all_merged.update(execute_hybrid_merge(raw, purged))

        if all_merged:
            save_to_lexicon(working_conn, all_merged, tranche_name)
            logger.info("✅ %s — %d entries saved", tranche_name, len(all_merged))

    # Preview
    print_preview(working_conn)

    if DRY_RUN:
        logger.info("🛡️  DRY RUN complete — nothing written to %s. Set DRY_RUN=False to persist.", DB_NAME)
    else:
        logger.info("✓ LIVE run complete. %s updated.", DB_NAME)

    working_conn.close()