"""
# ⛵ THE FLUTTERING SAIL: HYBRID MATRIX EXPANSION ENGINE
# Project: A Dynamical Multi-Polar Ethics Framework
# Academic Companion Pipeline // Methodology: Curated-Empirical Hybrid Merge

## METHODOLOGICAL INTENT
To eliminate arbitrary LLM drift while capturing real-world semantic context,
this script executes a weighted fusion between an axiomatically calibrated 
philosophical baseline (Curated Core) and an LLM's contextual extraction 
(Empirical Core).

## MATHEMATICAL SPECIFICATION
For tokens intersecting both matrices: V_final = (W_c * V_c) + (W_e * V_e)
For net-new empirical tokens: V_final = V_e * Damping_Factor
"""

import sqlite3
import json
import os
import numpy as np
import requests

# --- 1. CONFIGURATION & HYPERPARAMETERS ---
DB_NAME = "epistemic_lexicon.db"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
# Run $ export OPENAI_API_KEY="actual_key" in console BEFORE running this scrpt

WEIGHT_CURATED = 0.6   # Alpha: Framework anchoring weight
WEIGHT_EMPIRICAL = 0.4 # Beta: Real-world contextual variance weight
NEW_TOKEN_DAMPING = 0.9 # Boundary constraint for un-anchored tokens

# --- 2. CURATED CORE BASELINE (Axiomatic Seed Matrix) ---
# Hardcoded subset representing the structural anchors discussed for blending
CURATED_SEED_VAULT = {
    "essence": [0.3, 0.0, 0.2, 0.0, 0.8, 0.9, 0.0, 0.4],
    "accident": [0.6, 0.0, 0.1, 0.1, 0.1, 0.8, 0.0, 0.0],
    "complexity": [0.2, 0.0, 0.4, 0.2, 0.3, 0.9, 0.1, 0.1],
    "worship": [0.0, 0.4, 0.1, 0.3, 0.8, 0.3, 0.2, 0.9],
    "freedom": [0.2, 0.8, 0.3, 0.1, 0.9, 0.2, 0.3, 0.8],
    "justice": [0.2, 0.9, 0.4, 0.1, 0.8, 0.8, 0.8, 0.4],
    "fraternity": [0.1, 0.8, 0.2, 0.6, 0.7, 0.5, 0.9, 0.5],
    "danda": [0.6, 0.4, 0.9, 0.3, 0.5, 0.8, 0.8, 0.1],
    "eudaimonia": [0.6, 0.6, 0.2, 0.3, 0.9, 0.5, 0.6, 0.7],
    "desire": [0.5, 0.2, 0.5, 0.9, 0.5, 0.4, 0.3, 0.6],
    "axiom": [0.5, 0.3, 0.3, 0.0, 0.7, 0.9, 0.4, 0.4],
    "commodity": [0.9, 0.4, 0.5, 0.4, 0.3, 0.7, 0.2, 0.1]
}

# Targeted text corpora mapping for the live calibration
CORPORA_PROMPTS = {
    "Fred Brooks (No Silver Bullet)": "software engineering, essence, accident, complexity, conceptual conformity",
    "Bertrand Russell (Humanism)": "worship, freedom, intellect, truth, indignation, logical resignation",
    "Chanakya (Arthashastra)": "danda, amatya, kosha, vijigishu, statecraft, alignment, duty",
    "Adam Smith (Wealth of Nations)": "commodity, labor, market, revenue, capital, profit, transaction"
}

# --- 3. EMPIRICAL EXTRACTION LAYER (LLM Gateway) ---

def fetch_empirical_vectors(author_context, keywords):
    """
    Queries OpenAI to harvest contextually grounded vectors from the source text.
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    You are an advanced computational philologist working on a multi-polar ethics framework.
    Analyze the text footprint of '{author_context}', specifically focusing on themes like: {keywords}.
    
    Extract exactly 20 high-density tokens frequently utilized or implied in this philosophy.
    For EACH token, output an 8D vector [U, F, P, M, T, S, D, C] strictly bounded between -1.0 and 1.0.
    
    Lens Dimensions:
    U: Utility, F: Fairness, P: Power, M: Mimetic (Materialist Axis)
    T: Telos, S: Structure, D: Dharma, C: Consciousness (Dharmic Axis)
    
    Output your analysis strictly as raw valid JSON matching this schema, no prose:
    {{
        "token_word": [0.12, -0.45, 0.80, 0.23, 0.11, 0.90, -0.10, 0.05]
    }}
    """
    
    data = {
        "model": "gpt-4o",
        "response_format": { "type": "json_object" },
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response_json = response.json()
        raw_content = response_json['choices'][0]['message']['content']
        return json.loads(raw_content)
    except Exception as e:
        print(f"❌ API extraction failed for {author_context}: {e}")
        return {}

# --- 4. HYBRID MERGE PIPELINE ---

def execute_hybrid_merge(author, empirical_data):
    """
    Executes the math blend between Curated Baseline and Empirical extraction.
    """
    merged_vectors = {}
    
    for token, empirical_vec in empirical_data.items():
        token_clean = token.strip().lower()
        
        # Verify vector shape integrity
        if len(empirical_vec) != 8:
            continue
            
        empirical_arr = np.array(empirical_vec)
        
        if token_clean in CURATED_SEED_VAULT:
            # INTERSECTING NODE: Execute Weighted Blending Equation
            curated_arr = np.array(CURATED_SEED_VAULT[token_clean])
            blended_arr = (WEIGHT_CURATED * curated_arr) + (WEIGHT_EMPIRICAL * empirical_arr)
            merged_vectors[token_clean] = np.clip(blended_arr, -1.0, 1.0).tolist()
            print(f"🧬 Blended Intersection: '{token_clean}'")
        else:
            # DISJOINT NODE: New empirical entry discovered; apply boundary damping
            damped_arr = empirical_arr * NEW_TOKEN_DAMPING
            merged_vectors[token_clean] = np.clip(damped_arr, -1.0, 1.0).tolist()
            print(f"🌱 Damped Net-New Token: '{token_clean}'")
            
    return merged_vectors

# --- 5. DATA PERSISTENCE LAYER ---

def save_to_lexicon(merged_data, source_label):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    for token, vec in merged_data.items():
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO lexicon (word, u, f, p, m, t, s, d, c, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (token, *vec, f"Hybrid Merge: {source_label}"))
        except Exception as e:
            print(f"Database write error for {token}: {e}")
            
    conn.commit()
    conn.close()

# --- 6. EXECUTION RUNTIME ---

if __name__ == "__main__":
    if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
        print("🛑 Critical Error: Please inject your OpenAI API key to execute the calibration.")
    else:
        print("⛵ Starting Hybrid Epistemic Ingestion...")
        
        for author, keywords in CORPORA_PROMPTS.items():
            print(f"\nTargeting Layer: {author}")
            
            # Step 1: Extract empirical vector array from live LLM context
            empirical_payload = fetch_empirical_vectors(author, keywords)
            
            if empirical_payload:
                # Step 2: Run mathematical blend against seed definitions
                final_matrix = execute_hybrid_merge(author, empirical_payload)
                
                # Step 3: Persist into active SQLite schema
                save_to_lexicon(final_matrix, author)
                
        print("\n✓ Verification: Matrix expansion complete. Check active DB via app.py UI.")