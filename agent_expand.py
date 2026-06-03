"""
# ⛵ THE FLUTTERING SAIL: HYBRID MATRIX EXPANSION ENGINE (v2.0)
# Methodology: Curated-Empirical Hybrid Merge with Fully Externalized Epistemic Architecture
"""

import sqlite3
import json
import os
import numpy as np
import requests

# --- 1. CONFIGURATION & HYPERPARAMETERS ---
DB_NAME = "epistemic_lexicon.db"
WEIGHTS_FILE = "weights.json"
BLUEPRINT_FILE = "calibration_blueprint.json"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

WEIGHT_CURATED = 0.6   # Alpha
WEIGHT_EMPIRICAL = 0.4 # Beta
NEW_TOKEN_DAMPING = 0.9 # Gamma boundary constraint

# --- 2. DYNAMIC SPECIFICATION LOADING ---
def load_external_specifications():
    """Loads weights and external philological mappings from tracking JSON files."""
    if not os.path.exists(WEIGHTS_FILE) or not os.path.exists(BLUEPRINT_FILE):
        print(f"🛑 Critical Error: Ensure {WEIGHTS_FILE} and {BLUEPRINT_FILE} exist.")
        return None, None, None, None

    with open(WEIGHTS_FILE, 'r') as f:
        w_data = json.load(f)
    with open(BLUEPRINT_FILE, 'r') as f:
        b_data = json.load(f)

    return (
        w_data.get("CURATED_SEED_VAULT", {}),
        w_data.get("UNTRANSLATABLE_OPEN_WEIGHTS", {}),
        b_data.get("ANCHOR_DISCOVERY_MANIFEST", {}),
        b_data.get("THEMATIC_ALIGNMENT_MAP", {})
    )

# Unpack the modular external configurations
res = load_external_specifications()
if res[0] is not None:
    CURATED_SEED_VAULT, UNTRANSLATABLE_OPEN_WEIGHTS, ANCHOR_DISCOVERY_MANIFEST, THEMATIC_ALIGNMENT_MAP = res
else:
    exit(1)

# --- 3. THEMATIC LOOKUP ENGINE ---

def resolve_anchor_weights(token_clean):
    """
    Evaluates tokens against the seed matrices, scanning the thematic mapping
    layer to ensure Sanskrit equivalents match their translation fragments.
    """
    if token_clean in CURATED_SEED_VAULT:
        return np.array(CURATED_SEED_VAULT[token_clean])
        
    # Search externalized structural translation alignments
    for weight_key, alignments in THEMATIC_ALIGNMENT_MAP.items():
        if any(alignment in token_clean for alignment in alignments):
            print(f"🔱 Mapping Extracted Paradigm Variant: '{token_clean}' -> Open Weights Key: [{weight_key}]")
            return np.array(UNTRANSLATABLE_OPEN_WEIGHTS[weight_key])
            
    return None

# --- 4. EMPIRICAL EXTRACTION LAYER ---

def fetch_empirical_vectors(author_context, keywords):
    if not OPENAI_API_KEY:
        return {}
        
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Analyze the philosophy of '{author_context}'. Key themes: {keywords}.
    If the text contains apophatic elements (negation-based structural paradoxes), emphasize Consciousness (C) and Telos (T).
    Extract 20 tokens as JSON: {{ "token": [U, F, P, M, T, S, D, C] }}
    """
    
    data = {
        "model": "gpt-4o",
        "response_format": { "type": "json_object" },
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        return json.loads(response.json()['choices'][0]['message']['content'])
    except Exception as e:
        print(f"❌ API failure for context [{author_context}]: {e}")
        return {}

# --- 5. HYBRID MERGE PIPELINE ---

def execute_hybrid_merge(author, empirical_data):
    merged_vectors = {}
    for token, empirical_vec in empirical_data.items():
        token_clean = token.strip().lower()
        if len(empirical_vec) != 8: continue
        
        empirical_arr = np.array(empirical_vec)
        curated_arr = resolve_anchor_weights(token_clean)
        
        if curated_arr is not None:
            # INTERSECTING NODE: Weighted Blending Equation
            blended_arr = (WEIGHT_CURATED * curated_arr) + (WEIGHT_EMPIRICAL * empirical_arr)
            merged_vectors[token_clean] = np.clip(blended_arr, -1.0, 1.0).tolist()
            print(f"🧬 Blended Intersection: '{token_clean}'")
        else:
            # DISJOINT NODE: New empirical entry discovered; apply boundary damping
            merged_vectors[token_clean] = (empirical_arr * NEW_TOKEN_DAMPING).tolist()
            print(f"🌱 Damped Net-New: '{token_clean}'")
            
    return merged_vectors

# --- 6. DATA PERSISTENCE & RUNTIME ---

def save_to_lexicon(merged_data, source_label):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lexicon (
            word TEXT PRIMARY KEY, u REAL, f REAL, p REAL, m REAL, t REAL, s REAL, d REAL, c REAL, source TEXT
        )
    """)
    for token, vec in merged_data.items():
        cursor.execute('INSERT OR REPLACE INTO lexicon VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (token, *vec, source_label))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("🛑 Missing OPENAI_API_KEY environment variable. Run 'export OPENAI_API_KEY=...' before executing.")
    else:
        print("⛵ Starting Hybrid Epistemic Ingestion Pipeline...")
        for author, keywords in ANCHOR_DISCOVERY_MANIFEST.items():
            print(f"\nProcessing Boundary Manifest Layer: {author}")
            empirical_payload = fetch_empirical_vectors(author, keywords)
            if empirical_payload:
                final_matrix = execute_hybrid_merge(author, empirical_payload)
                save_to_lexicon(final_matrix, author)
        print("\n✓ Verification: Matrix expansion complete. Operational database seeded.")