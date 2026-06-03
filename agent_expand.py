"""
# ⛵ THE FLUTTERING SAIL: HARDENED INGESTION PIPELINE (v2.3.2)
# 
# PHILOSOPHY: This script is the 'Empiricist' layer. It must be resilient 
# to the 'fuzzy' nature of LLM outputs. We implement strict type-casting 
# to ensure the mathematical blending of axiomatic and empirical vectors 
# does not fail due to string-encoded JSON values.
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

# --- 2. ROBUST DATA INGESTION ---
def load_specifications():
    """Extracts research blueprints with error trapping for missing assets."""
    try:
        if not all(os.path.exists(f) for f in [WEIGHTS_FILE, BLUEPRINT_FILE]):
            logging.error("Missing JSON configuration files in workspace.")
            return None, None, None, None
            
        with open(WEIGHTS_FILE, 'r') as f: w = json.load(f)
        with open(BLUEPRINT_FILE, 'r') as f: b = json.load(f)
        logging.info("Research specifications successfully loaded.")
        return (
            w.get("CURATED_SEED_VAULT", {}), 
            w.get("UNTRANSLATABLE_OPEN_WEIGHTS", {}), 
            b.get("ANCHOR_DISCOVERY_MANIFEST", {}), 
            b.get("THEMATIC_ALIGNMENT_MAP", {})
        )
    except Exception as e:
        logging.error(f"Critical failure loading research specifications: {e}")
        return None, None, None, None

CURATED, UNTRANSLATABLES, MANIFEST, ALIGNMENT = load_specifications()

# --- 3. THEMATIC RESOLUTION ---
def resolve_anchor_weights(token):
    """Maps empirical tokens back to the axiomatic seed vault."""
    token_clean = token.lower().strip()
    if token_clean in CURATED:
        return np.array(CURATED[token_clean], dtype=float)
    
    for key, variants in ALIGNMENT.items():
        if any(v in token_clean for v in variants):
            logging.info(f"🔱 Aligning untranslatable: '{token_clean}' -> [{key}]")
            return np.array(UNTRANSLATABLES[key], dtype=float)
    return None

# --- 4. API & NUMERIC SANITIZATION ---
def fetch_empirical_vectors(author, keywords):
    """Communicates with the LLM to extract the empirical vector layer."""
    if not OPENAI_API_KEY:
        logging.error("API Key missing. Cannot fetch empirical vectors.")
        return {}

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    # Explicitly requesting numbers in the prompt to reduce string-wrapping
    prompt = (f"Analyze the philosophy of {author}. Focus on: {keywords}. "
              "Output EXACTLY 20 tokens as JSON. Format: { 'token': [8 floats between -1.0 and 1.0] }")
    
    data = {
        "model": "gpt-4o",
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        # Literate check: Ensure the response contains the expected data structure
        response_json = r.json()
        if 'choices' not in response_json:
            logging.error(f"Unexpected API Response for {author}: {response_json}")
            return {}
        return json.loads(response_json['choices'][0]['message']['content'])
    except Exception as e:
        logging.error(f"Network or JSON parse failure for {author}: {e}")
        return {}

def execute_hybrid_merge(empirical_data):
    """
    Performs the core mathematical synthesis. 
    Includes a 'Sanitization Loop' to handle string-encoded numbers.
    """
    merged = {}
    for token, emp_vec in empirical_data.items():
        try:
            # FIX: Force cast the empirical vector to float to prevent UFuncNoLoopError
            emp_arr = np.array(emp_vec, dtype=float)
            
            if len(emp_arr) != 8:
                logging.warning(f"Skipping '{token}': Vector length {len(emp_arr)} != 8")
                continue

            cur_vec = resolve_anchor_weights(token)
            
            if cur_vec is not None:
                # Blending (Alpha=0.6, Beta=0.4)
                blended = (0.6 * cur_vec) + (0.4 * emp_arr)
                merged[token.lower()] = np.clip(blended, -1, 1).tolist()
                logging.info(f"🧬 Hybridized: '{token}'")
            else:
                # Damping (Gamma=0.9)
                merged[token.lower()] = (emp_arr * 0.9).tolist()
        
        except (ValueError, TypeError) as e:
            logging.error(f"Numeric conversion failed for token '{token}': {e}")
            continue
            
    return merged

# --- 5. PERSISTENCE ---
def save_to_lexicon(data, source):
    """Commits the resulting vectors to the SQLite storage layer."""
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
        logging.error(f"Database write failure for {source}: {e}")

# --- 6. MAIN EXECUTION ---
if __name__ == "__main__":
    logging.info("⛵ Starting Hybrid Epistemic Ingestion Pipeline...")
    
    if not MANIFEST:
        logging.error("Ingestion halted: Manifest is empty.")
    else:
        for author, keywords in MANIFEST.items():
            logging.info(f"🔍 Processing: {author}...")
            # The API returns the raw JSON object
            raw_payload = fetch_empirical_vectors(author, keywords)
            
            if raw_payload:
                # Check if the LLM wrapped tokens in a nested key like 'tokens' or 'analysis'
                # and flatten if necessary.
                actual_data = raw_payload.get("tokens", raw_payload) if isinstance(raw_payload, dict) else {}
                
                processed_data = execute_hybrid_merge(actual_data)
                
                if processed_data:
                    save_to_lexicon(processed_data, author)
                    logging.info(f"✅ Completed: {author}. {len(processed_data)} tokens stored.")
                else:
                    logging.warning(f"⚠️ No valid tokens processed for {author}.")
        
        logging.info("✓ Verification: Matrix expansion complete.")