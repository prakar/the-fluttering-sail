"""
# ⛵ THE FLUTTERING SAIL: PERSISTENCE LAYER (v2.1)
# 
# PHILOSOPHY: This script serves as the 'Ground Truth' for the Epistemic Lexicon.
# It transitions the 8D seed lexicon from static memory to SQLite.
#
# LITERATE DESIGN:
# 1. Context-managed connections to prevent database locking.
# 2. Defensive seeding to ensure numeric integrity (float casting).
# 3. Standardized logging for auditability in the framework.log.
"""

import sqlite3
import json
import logging
import os

# --- 1. CONFIGURATION & AUDIT ---
DB_NAME          = "epistemic_lexicon.db"
LOG_FILE         = "framework.log"
TRANCHE_FILE     = "tranche_master.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode='a'), logging.StreamHandler()]
)

# Load SEEDS from tranche_master.json (replaces: from tranche_master import SEEDS)
if not os.path.exists(TRANCHE_FILE):
    logging.error("❌ %s not found. Cannot seed database.", TRANCHE_FILE)
    raise SystemExit(1)

with open(TRANCHE_FILE) as f:
    _tranche_data = json.load(f)

SEEDS = _tranche_data.get("SEEDS", {})
logging.info("✅ Loaded %d seeds from %s", len(SEEDS), TRANCHE_FILE)

# --- 2. CORE DATABASE OPERATIONS ---

def initialize_database():
    """
    Creates the lexicon table and performs the initial migration from Tranche Master.
    Includes error trapping for duplicate keys and malformed vectors.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            # Create the table with explicit column constraints
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lexicon (
                    word TEXT PRIMARY KEY,
                    u REAL, f REAL, p REAL, m REAL,
                    t REAL, s REAL, d REAL, c REAL,
                    source TEXT
                )
            ''')

            logging.info(f"Synchronizing {len(SEEDS)} seeds from tranche_master...")

            # Migration: Inject seeds with numeric sanitization
            for word, vec in SEEDS.items():
                try:
                    # Defensive Check: Ensure we have exactly 8 dimensions + word + source
                    if len(vec) != 8:
                        logging.warning(f"Skipping '{word}': Vector length {len(vec)} is invalid.")
                        continue
                    
                    # Force conversion to float to maintain SQLite REAL affinity
                    sanitized_vec = [float(x) for x in vec]
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO lexicon VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (word.lower().strip(), *sanitized_vec, "Initial Seed Core"))
                    
                except (ValueError, TypeError) as ve:
                    logging.error(f"Data integrity error for token '{word}': {ve}")
            
            conn.commit()
            logging.info("✓ Epistemic Lexicon database initialized and synchronized.")

    except sqlite3.Error as e:
        logging.error(f"Critical SQLite failure during initialization: {e}")

def get_vector(word):
    """
    Retrieves the 8D vector for a word. 
    Returns None if the word is not in the anchor vault.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT u, f, p, m, t, s, d, c FROM lexicon WHERE word = ?", (word.lower().strip(),))
            return cursor.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Database read error for word '{word}': {e}")
        return None

# --- 3. EXECUTION ---
if __name__ == "__main__":
    # Safety Check: If DB exists, log that we are updating; if not, creating.
    if not os.path.exists(DB_NAME):
        logging.info("No existing Lexicon found. Creating fresh persistence layer...")
    
    initialize_database()