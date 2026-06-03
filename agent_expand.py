"""
# ⛵ THE FLUTTERING SAIL: SCALABLE INGESTION PIPELINE (v3.0)
# 
# PHILOSOPHY: Direct O(1) Mapping for Sanskrit Non-Translatables.
# We have eliminated the 'Archetypal Cluster' bottleneck in favor of 
# a high-performance hash-table resolution engine.
"""

import sqlite3
import json
import os
import numpy as np
import requests
import logging

# --- 1. AUDIT & ENVIRONMENT CONFIGURATION ---
DB_NAME = "epistemic_lexicon.db"
WEIGHTS_FILE = "weights.json"
BLUEPRINT_FILE = "calibration_blueprint.json"
LOG_FILE = "framework.log"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode='a'), logging.StreamHandler()]
)

# --- 2. ROBUST DATA INGESTION (O(1) REALIGNMENT) ---
def load_specifications():
    """Extracts unified data files with robust error trapping."""
    try:
        if not all(os.path.exists(f) for f in [WEIGHTS_FILE, BLUEPRINT_FILE]):
            logging.error("Missing JSON configuration files in workspace.")
            return None, None, None, None
            
        with open(WEIGHTS_FILE, 'r') as f: 
            w = json.load(f)
        with open(BLUEPRINT_FILE, 'r') as f: 
            b = json.load(f)
            
        logging.info("Unified configuration metrics successfully loaded.")
        
        # Pulling the newly designed primary data types
        return (
            w.get("AXIOMATIC_SEED_VAULT", {}), 
            w.get("SANSKRIT_NONTRANSLATABLES_OPEN_WEIGHTS", {}), 
            b.get("ANCHOR_DISCOVERY_MANIFEST", {}), 
            b.get("THEMATIC_ALIGNMENT_MAP", {}) # Preserved for legacy fallbacks
        )
    except Exception as e:
        logging.error(f"Critical failure during script initialization: {e}")
        return None, None, None, None

AXIOMATIC, SANSKRIT_WEIGHTS, MANIFEST, ALIGNMENT = load_specifications()

# --- 3. REFACTORED O(1) RESOLUTION ENGINE ---
def resolve_anchor_weights(token):
    """
    Maximally scalable Token Resolution Engine.
    Pathways: Axiomatic -> Sanskrit/Comparative -> Normalized Variant -> Fallback.
    """
    token_clean = token.lower().strip()
    
    # 1. Primary Western Axiomatic Check
    if token_clean in AXIOMATIC:
        return np.array(AXIOMATIC[token_clean], dtype=float)
        
    # 2. Primary Sanskrit Non-Translatable Direct Match
    if token_clean in SANSKRIT_WEIGHTS:
        logging.info(f"💎 Direct Anchor Found: '{token_clean}'")
        return np.array(SANSKRIT_WEIGHTS[token_clean], dtype=float)
        
    # 3. Normalization Fallback (e.g., "karma-yoga" -> "karma yoga")
    normalized_token = token_clean.replace("-", " ")
    if normalized_token in SANSKRIT_WEIGHTS:
        logging.info(f"🔱 Normalized Anchor Found: '{token_clean}' -> '{normalized_token}'")
        return np.array(SANSKRIT_WEIGHTS[normalized_token], dtype=float)

    # 4. Legacy Cluster Alignment (Preserved for compatibility)
    for key, variants in ALIGNMENT.items():
        if any(v in token_clean for v in variants):
            if key in SANSKRIT_WEIGHTS:
                return np.array(SANSKRIT_WEIGHTS[key], dtype=float)
                
    return None

# --- 4. API & NUMERIC SANITIZATION ---
def fetch_empirical_vectors(author, keywords):
    """Communicates with the LLM to extract the empirical vector layer."""
    if not OPENAI_API_KEY:
        logging.error("API Key missing. Cannot fetch empirical vectors.")
        return {}

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    
    # Updated Prompt: Enforces term preservation and exact JSON mapping
    prompt = (f"Analyze the philosophy and terminology of {author}. "
              f"Focus precisely on these terms: {keywords}. "
              "Output EXACTLY a JSON dictionary where keys are the exact terms provided, "
              "and values are an array of 8 floats between -1.0 and 1.0. "
              "Format: { 'token': [8 floats] }")
    
    data = {
        "model": "gpt-4o",
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response_json = r.json()
        if 'choices' not in response_json:
            logging.error(f"Unexpected API Response: {response_json}")
            return {}
        return json.loads(response_json['choices'][0]['message']['content'])
    except Exception as e:
        logging.error(f"Network or JSON parse failure: {e}")
        return {}

def execute_hybrid_merge(empirical_data):
    """Mathematical synthesis (0.6 Anchor / 0.4 Empirical)."""
    merged = {}
    for token, emp_vec in empirical_data.items():
        try:
            emp_arr = np.array(emp_vec, dtype=float)
            if len(emp_arr) != 8: continue

            cur_vec = resolve_anchor_weights(token)
            
            if cur_vec is not None:
                # Hybrid Blend
                blended = (0.6 * cur_vec) + (0.4 * emp_arr)
                merged[token.lower()] = np.clip(blended, -1, 1).tolist()
                logging.info(f"🧬 Hybridized: '{token}'")
            else:
                # Empirical Damping
                merged[token.lower()] = (emp_arr * 0.9).tolist()
        
        except (ValueError, TypeError) as e:
            logging.error(f"Numeric conversion failed for '{token}': {e}")
            continue
            
    return merged

# --- 5. PERSISTENCE ---
def save_to_lexicon(data, source):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lexicon 
            (word TEXT PRIMARY KEY, u REAL, f REAL, p REAL, m REAL, t REAL, s REAL, d REAL, c REAL, source TEXT)
        """)
        for token, vec in data.items():
            cursor.execute('INSERT OR REPLACE INTO lexicon VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                           (token, *vec, source))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Database write failure: {e}")

# --- 6. MAIN EXECUTION ---
if __name__ == "__main__":
    logging.info("⛵ Starting Scalable Ingestion Pipeline (v3.0)...")
    
    if not MANIFEST:
        logging.error("Ingestion halted: Manifest is empty.")
    else:
        for author, keywords in MANIFEST.items():
            logging.info(f"🔍 Processing: {author}...")
            raw_payload = fetch_empirical_vectors(author, keywords)
            
            if raw_payload:
                # Normalization check for nested LLM output
                actual_data = raw_payload.get("tokens", raw_payload) if isinstance(raw_payload, dict) else {}
                processed_data = execute_hybrid_merge(actual_data)
                
                if processed_data:
                    save_to_lexicon(processed_data, author)
                    logging.info(f"✅ Completed: {author}. {len(processed_data)} entries stored.")
        
        logging.info("✓ Final: Structural realigned expansion complete.")