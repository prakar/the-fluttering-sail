"""
# ⛵ THE FLUTTERING SAIL: PERSISTENCE LAYER
# Project: DeScideratum
# Author: Prasanna Varun Karmarkar

## INTENT
To transition the 8D seed lexicon from static Python memory to a persistent 
SQLite environment. This allows for runtime expansion via LLM and 
decentralized updates without re-deploying code.

## SCHEMA DESIGN
- word: PRIMARY KEY (The anchor token)
- u, f, p, m, t, s, d, c: The 8D coordinates (-1.0 to 1.0)
- metadata: JSON string capturing 'Tranche' and 'Source' (e.g., 'Initial Seed')
"""

import sqlite3
import json
from tranche_master import SEEDS

DB_NAME = "epistemic_lexicon.db"

def initialize_database():
    """
    Creates the lexicon table and populates it with the initial 35 seeds.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create the table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lexicon (
            word TEXT PRIMARY KEY,
            u REAL, f REAL, p REAL, m REAL,
            t REAL, s REAL, d REAL, c REAL,
            source TEXT
        )
    ''')

    # Migration: Inject seeds from tranche_master.py
    for word, vec in SEEDS.items():
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO lexicon VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (word, *vec, "Initial Seed Core"))
        except Exception as e:
            print(f"Error seeding {word}: {e}")

    conn.commit()
    conn.close()
    print(f"✓ Database {DB_NAME} initialized and seeded.")

def get_vector(word):
    """
    Retrieves the 8D vector for a word from the SQLite store.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT u, f, p, m, t, s, d, c FROM lexicon WHERE word = ?", (word.lower(),))
    result = cursor.fetchone()
    conn.close()
    return result

if __name__ == "__main__":
    initialize_database()
