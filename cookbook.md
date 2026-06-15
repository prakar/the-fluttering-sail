# BACK UP DATABASE with TIMESTAMP
    ```bash
    cp epistemic_lexicon.db epistemic_lexicon_backup_$(date +%Y%m%d_%H%M%S).db
    ```
# sed to change text
    ```bash
    sed -i 's/DRY_RUN = False/DRY_RUN = True/' agent_expand.py
    grep "^DRY_RUN" agent_expand.py
    ```
# Encoding-safe utf-8 VERY IMP POINT, python-sql script to protect from delete/insert
    ```bash
    cd /workspaces/the-fluttering-sail
    python3 << 'EOF'
    import sqlite3, subprocess, sys

    # ── 1. Snapshot live DB BEFORE ───────────────────────────────────────────
    conn = sqlite3.connect('epistemic_lexicon.db')
    malhotra_before = set(r[0] for r in conn.execute(
        "SELECT word FROM lexicon WHERE source='Rajiv_Malhotra_Non_Translatables'"
    ).fetchall())
    total_before = conn.execute("SELECT COUNT(*) FROM lexicon").fetchone()[0]
    conn.close()

    print(f"Before run:")
    print(f"  Rajiv_Malhotra_Non_Translatables: {len(malhotra_before)} words")
    print(f"  Total entries: {total_before}")

    # ── 2. Confirm DRY_RUN is True ───────────────────────────────────────────
    with open('agent_expand.py', encoding='utf-8') as f:
        content = f.read(1000)
    assert 'DRY_RUN = True' in content, \
        f"❌ DRY_RUN not True. Found: {[l for l in content.split(chr(10)) if 'DRY_RUN' in l]}"
    print("✅ DRY_RUN = True confirmed")

    # ── 3. Run agent_expand.py as subprocess ────────────────────────────────
    print("Running pipeline (dry run)...\n")
    result = subprocess.run(
        [sys.executable, 'agent_expand.py'],
        capture_output=True, text=True
    )
    output = result.stdout + result.stderr
    print(output[-3000:])

    # ── 4. Check for protected entries guard firing ──────────────────────────
    protected_lines = [l for l in output.split('\n') if 'protected entries preserved' in l]
    print(f"\n🔒 Protected source guard fired {len(protected_lines)} time(s):")
    for line in protected_lines:
        print(f"  {line.strip()}")

    # ── 5. Confirm live DB UNCHANGED ─────────────────────────────────────────
    conn = sqlite3.connect('epistemic_lexicon.db')
    malhotra_after = set(r[0] for r in conn.execute(
        "SELECT word FROM lexicon WHERE source='Rajiv_Malhotra_Non_Translatables'"
    ).fetchall())
    total_after = conn.execute("SELECT COUNT(*) FROM lexicon").fetchone()[0]
    conn.close()

    print(f"\nLive DB after dry run:")
    print(f"  Total: {total_after} {'✅ unchanged' if total_after == total_before else '❌ CHANGED'}")
    print(f"  Malhotra: {len(malhotra_after)} {'✅ unchanged' if malhotra_after == malhotra_before else '❌ CHANGED'}")
    if malhotra_after != malhotra_before:
        print(f"  Lost: {malhotra_before - malhotra_after}")
        print(f"  Gained: {malhotra_after - malhotra_before}")
    EOF
    ```
# Verify DB change removal of RAjiv Malhotra took (after uploading)
    ```python 
    python3 -c "
    import sqlite3
    conn = sqlite3.connect('epistemic_lexicon.db')
    print(conn.execute(\"SELECT COUNT(*) FROM lexicon WHERE source='Sanskrit_Ontology_Dependent'\").fetchone())
    print(conn.execute(\"SELECT COUNT(*) FROM lexicon WHERE source='Rajiv_Malhotra_Non_Translatables'\").fetchone())
    conn.close()
    "
    ``` # Should print (81,) and (0,)
# 

