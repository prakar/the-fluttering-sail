"""
⛵ THE FLUTTERING SAIL: HARDENED INGESTION PIPELINE (v3.3)

FIXES OVER v3.0 (on disk) and v3.2 (draft):
  1. DRY_RUN flag with in-memory DB snapshot (from v3.2)
  2. cleanse_corrupted_records() — purges rolling-permutation corruption (from v3.2)
  3. calibration_blueprint.json now has 67-key THEMATIC_ALIGNMENT_MAP (was 4 keys on disk)
  4. Rajiv_Malhotra batch CHUNKED into groups of 10 — prevents GPT token overrun / partial returns
  5. Validation: each GPT-returned vector must be exactly 8 floats; bad returns are skipped with warning
  6. Hybrid blend guard: if DB vector is corrupted (flagged during cleanse), use empirical-only (0.9x damping)
  7. OPENAI_API_KEY checked once at startup with clear message
  8. DRY_RUN prints a full preview table and exits without touching the real DB
  9. Type annotations retained from v3.2
"""

import sqlite3
import json
import os
import sys
import numpy as np
import requests
import logging
from typing import Dict, List, Tuple, Optional

# --- 1. RUNTIME CONTROLS ---
DRY_RUN = True   # ← set False to write to disk for real

DB_NAME         = "epistemic_lexicon.db"
WEIGHTS_FILE    = "weights.json"
BLUEPRINT_FILE  = "calibration_blueprint.json"
LOG_FILE        = "framework.log"
CHUNK_SIZE      = 10   # max terms per GPT call for Rajiv batch
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode='a'), logging.StreamHandler()]
)
logger = logging.getLogger("EpistemicFirewall")

if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY not set in environment. Export it before running:\n"
                 "    export OPENAI_API_KEY=sk-...")
    sys.exit(1)


# --- 2. CORRUPTION DETECTION & PURGE ---
CORRUPTED_POOL = {0.81, 0.72, 0.63, 0.54, 0.09, 0.18, 0.27, 0.36}

def is_corrupted(vector_vals: list) -> bool:
    """True if vector matches the rolling-permutation corruption signature."""
    if any(v is None for v in vector_vals):
        return False
    mags = np.abs(np.array(vector_vals, dtype=float))
    unique_mags = set(np.round(mags, 2))
    in_pool = unique_mags.issubset(CORRUPTED_POOL) and len(unique_mags) > 1
    signs = np.sign(np.array(vector_vals, dtype=float))
    nonzero_signs = [s for s in signs if s != 0]
    alternating = len(nonzero_signs) > 1 and all(
        nonzero_signs[i] != nonzero_signs[i+1] for i in range(len(nonzero_signs)-1)
    )
    return in_pool or alternating

def cleanse_corrupted_records(conn: sqlite3.Connection) -> set:
    """
    Scans lexicon for rolling-permutation corruption and deletes those rows.
    Returns the set of purged words so execute_hybrid_merge can skip anchor blending for them.
    """
    logger.info("⚡ Starting corruption audit...")
    try:
        rows = conn.execute("SELECT word, u, f, p, m, t, s, d, c FROM lexicon").fetchall()
    except sqlite3.OperationalError:
        logger.info("ℹ️  Lexicon table absent — nothing to cleanse.")
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
        logger.warning("⚠️  Cleanse complete: %d corrupted rows removed: %s", len(purged), sorted(purged))
    else:
        logger.info("✅ Audit clean — zero rolling-permutation rows found.")
    return purged


# --- 3. SPEC LOADING ---
def load_specifications() -> Tuple[dict, dict, dict, dict]:
    for f in [WEIGHTS_FILE, BLUEPRINT_FILE]:
        if not os.path.exists(f):
            logger.error("Missing required file: %s", f)
            sys.exit(1)
    with open(WEIGHTS_FILE)    as f: w = json.load(f)
    with open(BLUEPRINT_FILE)  as f: b = json.load(f)
    axiomatic  = w.get("AXIOMATIC_SEED_VAULT", {})
    sanskrit_w = w.get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {})
    manifest   = b.get("ANCHOR_DISCOVERY_MANIFEST", {})
    alignment  = b.get("THEMATIC_ALIGNMENT_MAP", {})
    logger.info("✅ Specs loaded — AXIOMATIC:%d  SANSKRIT_WEIGHTS:%d  MANIFEST:%d  ALIGNMENT:%d",
                len(axiomatic), len(sanskrit_w), len(manifest), len(alignment))
    return axiomatic, sanskrit_w, manifest, alignment

AXIOMATIC, SANSKRIT_WEIGHTS, MANIFEST, ALIGNMENT = load_specifications()


# --- 4. ANCHOR RESOLUTION ---
def resolve_anchor_weights(token: str, purged_words: set) -> Optional[np.ndarray]:
    """
    Resolution chain: Axiomatic → Sanskrit direct → normalised hyphen → THEMATIC_ALIGNMENT_MAP.
    If the word was in purged_words (corrupted), returns None so caller uses empirical-only.
    """
    t = token.lower().strip()
    if t in purged_words:
        logger.info("🚫 '%s' was corrupted — skipping anchor blend, using empirical only.", t)
        return None
    if t in AXIOMATIC:
        return np.array(AXIOMATIC[t], dtype=float)
    if t in SANSKRIT_WEIGHTS:
        logger.info("💎 Direct anchor: '%s'", t)
        return np.array(SANSKRIT_WEIGHTS[t], dtype=float)
    t_norm = t.replace("-", " ")
    if t_norm in SANSKRIT_WEIGHTS:
        logger.info("🔱 Normalised anchor: '%s' → '%s'", t, t_norm)
        return np.array(SANSKRIT_WEIGHTS[t_norm], dtype=float)
    for key, variants in ALIGNMENT.items():
        if any(v.lower() in t for v in variants):
            if key in SANSKRIT_WEIGHTS:
                logger.info("⏳ Alignment match: '%s' → '%s'", t, key)
                return np.array(SANSKRIT_WEIGHTS[key], dtype=float)
    return None


# --- 5. GPT CALL (with chunking support) ---
def fetch_empirical_vectors(author: str, terms: List[str]) -> Dict[str, list]:
    """
    Call GPT-4o for a list of terms. Returns {term: [8 floats]}.
    Only accepts responses where each value is a list of exactly 8 floats.
    """
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    terms_str = ", ".join(terms)

    prompt = (
        f"Perform a rigorous philosophical and conceptual audit of the following terms "
        f"in the context of: {author}.\n"
        f"Terms to evaluate: {terms_str}\n\n"
        f"For each term, assign an analytical weight score across exactly 8 dimensions "
        f"in the order [u, f, p, m, t, s, d, c]:\n"
        f"  u — Unifying/Integral (+1) vs Fragmented (-1)\n"
        f"  f — Functional/Kinetic (+1) vs Static (-1)\n"
        f"  p — Pluralistic/Open (+1) vs Monolithic (-1)\n"
        f"  m — Material/Immanent (+1) vs Transcendent (-1)\n"
        f"  t — Temporal/Linear (+1) vs Cyclical (-1)\n"
        f"  s — Structural/Systemic (+1) vs Organic (-1)\n"
        f"  d — Deconstructive/Disruptive (+1) vs Stabilising (-1)\n"
        f"  c — Contextual/Relational (+1) vs Absolute (-1)\n\n"
        f"Use the full continuous range [-1.0, +1.0] based on careful philosophical analysis. "
        f"Do NOT use repeating or symmetric patterns. Each term must have a genuinely distinct vector.\n\n"
        f"Return ONLY a flat JSON object: {{\"term\": [f, f, f, f, f, f, f, f], ...}} "
        f"with exactly {len(terms)} keys matching the exact term strings above. "
        f"No nesting, no markdown, no explanation."
    )

    data = {
        "model": "gpt-4o",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are an expert epistemic validator specialising in cross-cultural philosophy."},
            {"role": "user",   "content": prompt}
        ],
        "temperature": 0.25
    }

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=60)
        r.raise_for_status()
        raw = json.loads(r.json()['choices'][0]['message']['content'])
        # Validate: each key must map to exactly 8 numeric values
        validated = {}
        for k, v in raw.items():
            if isinstance(v, list) and len(v) == 8 and all(isinstance(x, (int, float)) for x in v):
                validated[k.lower().strip()] = v
            else:
                logger.warning("⚠️  GPT returned bad vector for '%s': %s — skipped", k, v)
        logger.info("✅ GPT returned %d/%d valid vectors for %s", len(validated), len(terms), author)
        return validated
    except Exception as e:
        logger.error("❌ GPT call failed for '%s': %s", author, e)
        return {}


# --- 6. HYBRID MERGE ---
def execute_hybrid_merge(empirical_data: Dict[str, list], purged_words: set) -> Dict[str, list]:
    """
    Blend: 0.6 × anchor + 0.4 × empirical if anchor exists and wasn't corrupted.
    Empirical-only (0.9×) if no anchor or anchor was purged.
    """
    merged = {}
    for token, emp_vec in empirical_data.items():
        try:
            emp_arr = np.array(emp_vec, dtype=float)
            if len(emp_arr) != 8:
                logger.error("❌ Wrong dimension (%d) for '%s' — skipped", len(emp_arr), token)
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


# --- 7. PERSISTENCE ---
def save_to_lexicon(conn: sqlite3.Connection, data: Dict[str, list], source: str):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lexicon
        (word TEXT PRIMARY KEY, u REAL, f REAL, p REAL, m REAL, t REAL, s REAL, d REAL, c REAL, source TEXT)
    """)
    for token, vec in data.items():
        if vec is None or len(vec) != 8:
            logger.error("❌ DB write skipped for '%s' — bad vector", token)
            continue
        conn.execute(
            "INSERT OR REPLACE INTO lexicon (word, u, f, p, m, t, s, d, c, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
            [token] + vec + [source]
        )
    conn.commit()
    logger.info("💾 Saved %d entries to lexicon (source=%s)", len(data), source)


def print_preview(conn: sqlite3.Connection, limit: int = 15):
    print("\n🔬 --- DATA INTEGRITY PREVIEW (first %d rows) ---" % limit)
    print(f"{'Word':<20} | {'u':>6} | {'f':>6} | {'p':>6} | {'m':>6} | {'t':>6} | {'s':>6} | {'d':>6} | {'c':>6} | source")
    print("-" * 110)
    rows = conn.execute("SELECT word, u, f, p, m, t, s, d, c, source FROM lexicon ORDER BY word LIMIT ?", (limit,)).fetchall()
    for r in rows:
        nums = " | ".join(f"{x:+.3f}" if isinstance(x, float) else f"{str(x):>6}" for x in r[1:9])
        print(f"{r[0]:<20} | {nums} | {r[9]}")
    total = conn.execute("SELECT COUNT(*) FROM lexicon").fetchone()[0]
    print(f"\n  Total rows in lexicon: {total}")


# --- 8. MAIN ---
if __name__ == "__main__":
    logger.info("⛵ Ingestion Pipeline v3.3 starting — DRY_RUN=%s", DRY_RUN)

    # Open working connection
    if DRY_RUN:
        logger.info("🛡️  DRY RUN: working in :memory: snapshot")
        working_conn = sqlite3.connect(":memory:")
        if os.path.exists(DB_NAME):
            src = sqlite3.connect(DB_NAME)
            src.backup(working_conn)
            src.close()
            logger.info("📋 Cloned '%s' into memory.", DB_NAME)
    else:
        logger.warning("⚠️  LIVE MODE: writing to %s", DB_NAME)
        working_conn = sqlite3.connect(DB_NAME)

    # Cleanse corruption first
    purged = cleanse_corrupted_records(working_conn)

    # Process each manifest entry
    for author, keywords_raw in MANIFEST.items():
        # keywords_raw can be a string "a, b, c" or a list
        if isinstance(keywords_raw, str):
            all_terms = [t.strip() for t in keywords_raw.split(",") if t.strip()]
        else:
            all_terms = list(keywords_raw)

        logger.info("🔍 Processing: %s (%d terms)", author, len(all_terms))

        # Chunk into groups of CHUNK_SIZE to avoid GPT token overrun
        all_merged = {}
        for i in range(0, len(all_terms), CHUNK_SIZE):
            chunk = all_terms[i : i + CHUNK_SIZE]
            logger.info("  📦 Chunk %d-%d: %s", i+1, i+len(chunk), chunk)
            raw = fetch_empirical_vectors(author, chunk)
            if raw:
                merged_chunk = execute_hybrid_merge(raw, purged)
                all_merged.update(merged_chunk)

        if all_merged:
            save_to_lexicon(working_conn, all_merged, author)
            logger.info("✅ Done: %s — %d entries written", author, len(all_merged))
        else:
            logger.warning("⚠️  No data produced for: %s", author)

    print_preview(working_conn)

    if DRY_RUN:
        logger.info("🛡️  DRY RUN complete — NO changes written to %s. Set DRY_RUN=False to persist.", DB_NAME)
    else:
        logger.info("✓ LIVE run complete. %s updated.", DB_NAME)

    working_conn.close()