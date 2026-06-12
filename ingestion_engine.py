"""
ingestion_engine.py — The Fluttering Sail
==========================================
Shared LLM ingestion core used by both agent_expand.py (batch pipeline)
and app.py (UI-triggered queue ingestion).

Previously this logic was duplicated: agent_expand.py had fetch_empirical_vectors()
and app.py had an inline version in the Ingestion Queue tab. They are now unified here.

Public API
----------
    fetch_vectors(terms, source_label, context_line=None) -> dict[str, list]
        Call the LLM for a list of terms. Returns {word: [u,f,p,m,t,s,d,c]}.

    ingest_words(words, source_label, db_name, api_key, base_url,
                 progress_cb=None) -> int
        Fetch vectors for words in chunks and write directly to the lexicon table.
        Returns count of words successfully ingested.
        progress_cb(current, total, label) is called after each chunk if provided.

Configuration
-------------
All LLM parameters are read from prompts.json (ingestion section) at call time —
no module-level state. The caller supplies api_key and base_url from their own
config loading (llm_config.json).

Author  : see repository
Licence : see LICENSE
"""

import json
import logging
import os
import sqlite3

import requests

logger = logging.getLogger(__name__)

CHUNK_SIZE = 10   # words per LLM call — matches agent_expand.py

# ---------------------------------------------------------------------------
# STOPWORD LIST — loaded from stopwords.json
# ---------------------------------------------------------------------------
_STOPWORDS_FILE = "stopwords.json"


def _load_stopwords() -> frozenset:
    """
    Load stopword list from stopwords.json.
    Words are drawn from all category groups (keys that don't start with __ or _note).
    Falls back to an empty set if the file is missing — all words are then
    treated as philosophical vocabulary (no filtering).
    """
    if not os.path.exists(_STOPWORDS_FILE):
        logger.warning(
            "⚠️  %s not found — stopword filtering disabled. "
            "All words will be treated as philosophical vocabulary.",
            _STOPWORDS_FILE
        )
        return frozenset()
    try:
        with open(_STOPWORDS_FILE) as f:
            data = json.load(f)
        words = set()
        for key, val in data.items():
            if key.startswith("__") or key.startswith("_note"):
                continue
            if isinstance(val, dict) and "words" in val:
                words.update(w.lower().strip() for w in val["words"])
        logger.info("✅ Stopwords loaded from %s — %d words across %d categories",
                    _STOPWORDS_FILE,
                    len(words),
                    sum(1 for k, v in data.items()
                        if not k.startswith("_") and isinstance(v, dict) and "words" in v))
        return frozenset(words)
    except Exception as exc:
        logger.error("❌ Failed to parse %s: %s — stopword filtering disabled", _STOPWORDS_FILE, exc)
        return frozenset()


# Module-level singleton — loaded once at import time.
# Call reload_stopwords() to pick up edits without restarting.
STOPWORDS: frozenset = _load_stopwords()


def reload_stopwords() -> int:
    """Re-read stopwords.json at runtime. Returns word count."""
    global STOPWORDS
    STOPWORDS = _load_stopwords()
    return len(STOPWORDS)


def is_stopword(word: str) -> bool:
    """Return True if word should be excluded from philosophical ingestion."""
    return word.lower().strip() in STOPWORDS


def filter_stopwords(words: list) -> tuple[list, list]:
    """
    Split a word list into (philosophical, stopwords).
    Returns (keep_list, stopword_list).
    """
    keep = [w for w in words if not is_stopword(w)]
    stop = [w for w in words if is_stopword(w)]
    return keep, stop

# ---------------------------------------------------------------------------
# CONFIG LOADING
# ---------------------------------------------------------------------------

def _load_ingestion_config() -> dict:
    """
    Read prompts.json ingestion section, filtering _note_ and meta keys.
    Called fresh on each ingest_words() call so runtime edits to the file
    are picked up without restarting.
    """
    try:
        with open("prompts.json") as f:
            raw = json.load(f).get("ingestion", {})
        cfg = {k: v for k, v in raw.items()
               if not k.startswith("_note_") and k != "meta"}
        return cfg
    except Exception as exc:
        logger.error("❌ Failed to load prompts.json: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# VECTOR FETCHING
# ---------------------------------------------------------------------------

def fetch_vectors(
    terms: list,
    source_label: str,
    api_key: str,
    base_url: str,
    context_line: str | None = None,
    timeout: int = 60,
) -> dict:
    """
    Call the LLM for a list of terms and return validated 8-dimensional vectors.

    Parameters
    ----------
    terms        : list of str — tokens to vectorise (max CHUNK_SIZE recommended)
    source_label : str — provenance label (used for context and logging)
    api_key      : str — LLM API key
    base_url     : str — OpenAI-compatible base URL
    context_line : str | None — if None, derives from source_label
    timeout      : int — request timeout in seconds

    Returns
    -------
    dict {word: [u,f,p,m,t,s,d,c]} — only validated 8-element vectors included
    """
    cfg = _load_ingestion_config()
    if not cfg:
        logger.error("fetch_vectors: empty config — aborting")
        return {}

    if context_line is None:
        context_line = (
            "Evaluate each term as a standalone philosophical concept."
            if source_label.startswith("Tranche_") or source_label.startswith("Custom")
            else f"Evaluate these terms in the context of: {source_label}."
        )

    prompt = (
        cfg.get("prompt_template", "")
        .replace("{context_line}", context_line)
        .replace("{terms}", ", ".join(terms))
        .replace("{n_terms}", str(len(terms)))
    )

    payload = {
        "model":       cfg.get("model", "gpt-4o"),
        "temperature": cfg.get("temperature", 0.25),
        "messages": [
            {"role": "system", "content": cfg.get("system_role", "")},
            {"role": "user",   "content": prompt},
        ],
    }
    if cfg.get("response_format"):
        payload["response_format"] = cfg["response_format"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }

    try:
        r = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers, json=payload, timeout=timeout
        )
        r.raise_for_status()
        raw = json.loads(r.json()["choices"][0]["message"]["content"])
        validated = {}
        for k, v in raw.items():
            if (isinstance(v, list) and len(v) == 8
                    and all(isinstance(x, (int, float)) for x in v)):
                validated[k.lower().strip()] = v
            else:
                logger.warning("⚠️  Bad vector for '%s': %s — skipped", k, v)
        logger.info(
            "✅ LLM returned %d/%d valid vectors for [%s]",
            len(validated), len(terms), source_label[:50]
        )
        return validated
    except Exception as exc:
        logger.error("❌ LLM call failed for '%s': %s", source_label, exc)
        return {}


# ---------------------------------------------------------------------------
# CHUNKED INGESTION WITH DB WRITE
# ---------------------------------------------------------------------------

def ingest_words(
    words: list,
    source_label: str,
    db_name: str,
    api_key: str,
    base_url: str,
    context_line: str | None = None,
    timeout: int = 60,
    progress_cb=None,
) -> int:
    """
    Fetch vectors for all words in CHUNK_SIZE batches and write to the lexicon.

    Parameters
    ----------
    words        : list of str — unrecognised tokens to ingest
    source_label : str — written to lexicon.source column for provenance
    db_name      : str — path to SQLite database
    api_key      : str — LLM API key
    base_url     : str — OpenAI-compatible base URL
    context_line : str | None — passed to fetch_vectors
    timeout      : int — per-request timeout
    progress_cb  : callable(current, total, label) | None — progress hook

    Returns
    -------
    int — number of words successfully ingested
    """
    if not words:
        return 0

    # Filter stopwords before any API calls
    keep, skipped = filter_stopwords(words)
    if skipped:
        logger.info("⏭ Skipping %d stopwords for '%s': %s",
                    len(skipped), source_label, ", ".join(skipped[:10]) +
                    (f" … +{len(skipped)-10}" if len(skipped) > 10 else ""))
    if not keep:
        logger.info("ingest_words: all words were stopwords — nothing to ingest")
        return 0

    words = keep
    total_words = len(words)
    total_chunks = max(1, -(-total_words // CHUNK_SIZE))   # ceiling division
    ingested = 0

    for chunk_idx, i in enumerate(range(0, total_words, CHUNK_SIZE)):
        chunk = words[i: i + CHUNK_SIZE]

        if progress_cb:
            progress_cb(chunk_idx, total_chunks, f"{source_label} ({chunk_idx * CHUNK_SIZE}/{total_words})")

        vectors = fetch_vectors(
            terms=chunk,
            source_label=source_label,
            api_key=api_key,
            base_url=base_url,
            context_line=context_line,
            timeout=timeout,
        )

        if not vectors:
            logger.warning("No vectors returned for chunk %d of '%s'",
                           chunk_idx, source_label)
            continue

        try:
            conn = sqlite3.connect(db_name)
            for word, vec in vectors.items():
                # INSERT OR IGNORE: never overwrite an existing entry's source label.
                # The MANIFEST (agent_expand.py) uses INSERT OR REPLACE and runs first
                # to establish authoritative provenance. Queue-based ingestion only
                # adds genuinely new vocabulary — it does not re-label existing terms.
                conn.execute(
                    "INSERT OR IGNORE INTO lexicon "
                    "(word, u, f, p, m, t, s, d, c, source) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [word] + vec + [source_label]
                )
                ingested += 1
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.error("❌ DB write error (chunk %d, '%s'): %s",
                         chunk_idx, source_label, exc)

    logger.info("✅ ingest_words complete: %d/%d words for '%s'",
                ingested, total_words, source_label)
    return ingested