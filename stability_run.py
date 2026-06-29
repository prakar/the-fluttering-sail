"""
stability_run.py — Mini-Submission 1: Philosophical Anchoring Stability Pilot
===============================================================================
PAIRED WITHIN-WORD DESIGN (v2 — supersedes the between-group v1 design).

Why this redesign exists
-------------------------
The original (v1) design compared two different vocabularies — anchored
Primal Anchor words vs. separately-chosen unanchored control words — and
showed the anchored group had lower run-to-run spread. That result cannot
distinguish "anchoring reduces drift" from "the words we happened to pick
as anchors are just inherently easier for the LLM to score consistently."
It also used n=5 runs, which is not enough to support a statistical claim
either way.

This version fixes both problems:

  1. WITHIN-WORD PAIRING. For every word in the Primal Anchor vault, each
     run produces TWO vectors from the same LLM call:
       - the raw, unblended empirical vector (what v1 called "alpha=0.0")
       - the Hybrid Merge blend of that same empirical vector with the
         word's fixed anchor (alpha=0.6, per the manuscript's default)
     Because both conditions come from the same word, same model call,
     same run, the only thing that differs between them is the presence
     of the anchor in the blend. This isolates the mechanism.

  2. ADEQUATE SAMPLE SIZE. 20 words (the full Primal Anchor vault) x 10
     runs = 200 paired observations, run as 10 batched calls of 20 words
     each (within ingestion_engine's CHUNK_SIZE-per-call assumption —
     see the chunking note below). This supports a real paired
     significance test (paired t-test or Wilcoxon signed-rank, computed
     per-dimension or on vector magnitude) rather than an eyeballed
     5-row table.

This script reports whatever it finds, including a null result. If the
blended condition does not show significantly lower spread than the
unblended condition, that is the honest finding and belongs in the paper
as evidence against the stability claim, not as something to re-run
until it looks better.

Data sources (externalised — see manuscript §A.1):
    --anchors-file   baseline_evaluation_subset.json   (the Primal Anchor
                      vault; all 20 words are used as the evaluation
                      vocabulary in this design — see note below)

LLM calls:
    Real calls via ingestion_engine.fetch_vectors(), batched per run.
    fetch_vectors() has no temperature parameter — temperature is read
    from prompts.json's ingestion.temperature. --expected-temperature is
    a PREFLIGHT CHECK only; it does not override the actual call. Edit
    prompts.json directly if the configured value doesn't match.

Chunking note:
    ingestion_engine.CHUNK_SIZE is 10. With 20 words, each run requires
    TWO batched calls (10 words each), not one. This script chunks
    automatically and treats both chunks as belonging to the same run_id.
    A failure in either chunk is logged as a partial-run failure, not a
    silent drop.

Usage:
    python stability_run.py --runs 10 --expected-temperature 0.2 --strict

Output:
    stability_run_results.csv — one row per (word, run, condition), where
    condition is "empirical" or "blended". 20 words x 10 runs x 2
    conditions = 400 rows if every call succeeds.
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict

from ingestion_engine import fetch_vectors, CHUNK_SIZE

DIMS = ["u", "f", "p", "m", "t", "s", "d", "c"]
PROMPTS_FILE = "prompts.json"


# ---------------------------------------------------------------------------
# PREFLIGHT: temperature check against prompts.json
# ---------------------------------------------------------------------------
def preflight_check_temperature(expected: float, strict: bool) -> float:
    """
    Read prompts.json's ingestion.temperature and compare against what this
    pilot run expects. fetch_vectors() has no per-call override — the only
    way to change the value actually used is to edit prompts.json directly.
    This function never edits that file; it only warns (or aborts, with
    --strict) on a mismatch, so a run is never silently conducted at the
    wrong temperature.
    """
    try:
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            prompts = json.load(f)
    except FileNotFoundError:
        sys.exit(f"\u274c {PROMPTS_FILE} not found \u2014 cannot verify temperature before running.")
    except json.JSONDecodeError as exc:
        sys.exit(f"\u274c {PROMPTS_FILE} is not valid JSON: {exc}")

    actual = prompts.get("ingestion", {}).get("temperature")
    if actual is None:
        sys.exit(f"\u274c No ingestion.temperature found in {PROMPTS_FILE} \u2014 cannot verify.")

    if abs(actual - expected) > 1e-9:
        msg = (
            f"Temperature mismatch: {PROMPTS_FILE} has ingestion.temperature={actual}, "
            f"but this pilot run expects {expected}. fetch_vectors() has no per-call "
            f"override \u2014 edit {PROMPTS_FILE} directly to match before running, or pass "
            f"--expected-temperature {actual} to acknowledge the current setting."
        )
        if strict:
            sys.exit(f"\u274c {msg}")
        else:
            print(f"\u26a0\ufe0f  {msg}\n   Proceeding anyway (use --strict to abort instead).")
    else:
        print(f"\u2705 Preflight: {PROMPTS_FILE} ingestion.temperature={actual} matches expected {expected}")

    return actual


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------
def load_anchors(path: str) -> dict:
    """
    Load the full Primal Anchor vault from baseline_evaluation_subset.json.
    In this paired design, every word in the vault is used as evaluation
    vocabulary — there is no separate "unanchored controls" list, because
    every word's own unblended empirical vector serves as its paired
    control. (Contrast with v1, which used a different, smaller vocabulary
    for the unanchored condition.)
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    anchors = data.get("anchors", {})
    if not anchors:
        sys.exit(f"No 'anchors' block found in {path}")
    return anchors


# ---------------------------------------------------------------------------
# HYBRID MERGE (mirrors agent_expand.py execute_hybrid_merge)
# ---------------------------------------------------------------------------
def blend(anchor_vec: list[float], empirical_vec: list[float], alpha: float) -> list[float]:
    """Hybrid Merge blend: V_final = clip(alpha * V_anchor + (1 - alpha) * V_empirical, -1, 1)."""
    blended = [
        alpha * a + (1.0 - alpha) * e
        for a, e in zip(anchor_vec, empirical_vec)
    ]
    return [max(-1.0, min(1.0, v)) for v in blended]


def chunk_list(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


# ---------------------------------------------------------------------------
# PILOT RUN — paired empirical/blended observation per word per run
# ---------------------------------------------------------------------------
def run_stability_pilot(
    n_runs: int,
    api_key: str,
    base_url: str,
    primal_anchors: dict,
    alpha_anchored: float,
) -> tuple[list[dict], list[str]]:
    """
    For each run, fetches empirical vectors for ALL words in primal_anchors
    (chunked at CHUNK_SIZE), then emits two rows per word: the raw
    empirical vector ("empirical" condition) and the Hybrid Merge blend
    with that word's fixed anchor ("blended" condition).

    Returns (rows, failure_log). A failed chunk within a run means the
    words in that chunk contribute no rows for that run_id — logged
    explicitly, not silently dropped. The other chunk's words in the same
    run are unaffected.
    """
    rows = []
    failure_log = []
    words = list(primal_anchors.keys())
    chunks = chunk_list(words, CHUNK_SIZE)

    print(f"{len(words)} words split into {len(chunks)} chunk(s) of up to {CHUNK_SIZE} per call.")

    for run_id in range(1, n_runs + 1):
        print(f"\n--- Run {run_id}/{n_runs} ---")
        for chunk_idx, chunk in enumerate(chunks, start=1):
            print(f"  Chunk {chunk_idx}/{len(chunks)}: {len(chunk)} words")
            empirical = fetch_vectors(
                terms=chunk,
                source_label="QHE.1_Formalization_stability_pilot_paired",
                api_key=api_key,
                base_url=base_url,
            )

            if not empirical:
                failure_log.append(
                    f"Run {run_id}, chunk {chunk_idx}: no data returned for {chunk}"
                )
                print(f"    \u274c Chunk {chunk_idx} failed \u2014 no data for {len(chunk)} words this run.")
                continue

            missing = [w for w in chunk if w not in empirical]
            if missing:
                failure_log.append(
                    f"Run {run_id}, chunk {chunk_idx}: {len(missing)} word(s) missing from response: {missing}"
                )

            for word in chunk:
                if word not in empirical:
                    continue

                emp_vec = empirical[word]
                anchor_vec = primal_anchors[word]
                blended_vec = blend(anchor_vec, emp_vec, alpha_anchored)

                rows.append({
                    "Word": word,
                    "Run_ID": run_id,
                    "Condition": "empirical",
                    "Alpha": 0.0,
                    **{f"Dim_{d.upper()}": round(v, 4) for d, v in zip(DIMS, emp_vec)},
                })
                rows.append({
                    "Word": word,
                    "Run_ID": run_id,
                    "Condition": "blended",
                    "Alpha": alpha_anchored,
                    **{f"Dim_{d.upper()}": round(v, 4) for d, v in zip(DIMS, blended_vec)},
                })

            print(f"    \u2705 Chunk {chunk_idx}: {len(empirical)}/{len(chunk)} words returned")

    return rows, failure_log


def write_csv(rows: list[dict], path: str) -> None:
    if not rows:
        print("\u26a0\ufe0f  No rows to write \u2014 every run failed or returned no data. CSV not created.")
        return
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    fieldnames = ["Word", "Run_ID", "Condition", "Alpha"] + [f"Dim_{d.upper()}" for d in DIMS]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# STATISTICAL SUMMARY — paired comparison, per word and pooled
# ---------------------------------------------------------------------------
def vector_magnitude_spread(vectors: list[list[float]]) -> float:
    """
    Per-dimension stdev across a list of vectors, averaged across the 8
    dimensions. A single scalar summary of "how much this set of vectors
    disagrees with itself" — used to compare empirical vs blended spread
    for the same word.
    """
    import statistics
    if len(vectors) < 2:
        return 0.0
    per_dim_stdev = []
    for dim_idx in range(len(DIMS)):
        vals = [v[dim_idx] for v in vectors]
        per_dim_stdev.append(statistics.stdev(vals))
    return sum(per_dim_stdev) / len(per_dim_stdev)


def paired_significance_test(empirical_spreads: list[float], blended_spreads: list[float]) -> dict:
    """
    Paired comparison across words: for each word, is blended spread lower
    than empirical spread? Uses a Wilcoxon signed-rank test if scipy is
    available (robust to non-normality, appropriate for n=20 words),
    falling back to a sign test count if scipy is not installed.

    Returns a dict with the test statistic, p-value (if computed), and a
    plain-language summary. Does NOT decide significance for you beyond
    reporting the p-value against alpha=0.05 — the paper should state the
    threshold and the result, not just a verdict.
    """
    diffs = [b - e for e, b in zip(empirical_spreads, blended_spreads)]
    n_lower = sum(1 for d in diffs if d < 0)   # blended spread lower than empirical
    n_higher = sum(1 for d in diffs if d > 0)
    n_tied = sum(1 for d in diffs if d == 0)

    result = {
        "n_words": len(diffs),
        "n_blended_lower": n_lower,
        "n_blended_higher": n_higher,
        "n_tied": n_tied,
        "mean_diff": sum(diffs) / len(diffs) if diffs else 0.0,
    }

    try:
        from scipy.stats import wilcoxon
        if n_tied == len(diffs):
            result["test"] = "wilcoxon"
            result["statistic"] = None
            result["p_value"] = None
            result["note"] = "All differences are zero — test not applicable."
        else:
            stat, p = wilcoxon(empirical_spreads, blended_spreads)
            result["test"] = "wilcoxon"
            result["statistic"] = stat
            result["p_value"] = p
    except ImportError:
        result["test"] = "sign_test_fallback"
        result["statistic"] = None
        result["p_value"] = None
        result["note"] = (
            "scipy not installed \u2014 reporting sign-test counts only "
            "(words where blended < empirical vs. words where blended > empirical). "
            "Install scipy for a proper Wilcoxon signed-rank p-value: pip install scipy"
        )

    return result


def summarise_paired_results(rows: list[dict]) -> None:
    if not rows:
        return

    by_word = defaultdict(lambda: {"empirical": [], "blended": []})
    for row in rows:
        vec = [row[f"Dim_{d.upper()}"] for d in DIMS]
        by_word[row["Word"]][row["Condition"]].append(vec)

    print(f"\n{'Word':<16} {'N_emp':<7} {'N_blend':<8} {'SpreadEmp':<12} {'SpreadBlend':<12} {'Lower?':<8}")
    print("-" * 70)

    empirical_spreads = []
    blended_spreads = []
    words_with_both = []

    for word, conds in sorted(by_word.items()):
        emp_vecs = conds["empirical"]
        blend_vecs = conds["blended"]
        if len(emp_vecs) < 2 or len(blend_vecs) < 2:
            print(f"{word:<16} {len(emp_vecs):<7} {len(blend_vecs):<8} {'(n<2, skipped)':<12}")
            continue

        spread_emp = vector_magnitude_spread(emp_vecs)
        spread_blend = vector_magnitude_spread(blend_vecs)
        lower = "yes" if spread_blend < spread_emp else ("tie" if spread_blend == spread_emp else "no")

        print(f"{word:<16} {len(emp_vecs):<7} {len(blend_vecs):<8} {spread_emp:<12.4f} {spread_blend:<12.4f} {lower:<8}")

        empirical_spreads.append(spread_emp)
        blended_spreads.append(spread_blend)
        words_with_both.append(word)

    if len(words_with_both) < 2:
        print("\n\u26a0\ufe0f  Fewer than 2 words have complete data \u2014 cannot run a paired significance test.")
        return

    print(f"\n--- Paired significance test across {len(words_with_both)} words ---")
    result = paired_significance_test(empirical_spreads, blended_spreads)
    print(f"  Words where blended spread < empirical spread: {result['n_blended_lower']}/{result['n_words']}")
    print(f"  Words where blended spread > empirical spread: {result['n_blended_higher']}/{result['n_words']}")
    print(f"  Tied: {result['n_tied']}")
    print(f"  Mean (blended - empirical) spread difference: {result['mean_diff']:.4f}  (negative = blended tighter)")
    if result.get("p_value") is not None:
        print(f"  Wilcoxon signed-rank statistic: {result['statistic']:.4f}, p = {result['p_value']:.4f}")
        sig = "SIGNIFICANT at alpha=0.05" if result["p_value"] < 0.05 else "NOT significant at alpha=0.05"
        print(f"  \u2192 {sig}")
    if result.get("note"):
        print(f"  Note: {result['note']}")


def main():
    parser = argparse.ArgumentParser(
        description="Philosophical anchoring stability pilot \u2014 paired within-word design (Mini-Submission 1, v2)."
    )
    parser.add_argument("--runs", type=int, default=10, help="Number of repeated runs (default 10).")
    parser.add_argument("--expected-temperature", type=float, default=0.2,
                         help="Temperature this pilot run expects to be configured in prompts.json "
                              "(preflight check only \u2014 does not override the actual call).")
    parser.add_argument("--strict", action="store_true",
                         help="Abort instead of warning if prompts.json temperature doesn't match --expected-temperature.")
    parser.add_argument("--alpha", type=float, default=0.6, help="Anchored blend ratio (default 0.6, per manuscript).")
    parser.add_argument("--anchors-file", type=str, default="baseline_evaluation_subset.json",
                         help="Path to the Primal Anchor vault JSON. All words in it are used as the evaluation vocabulary.")
    parser.add_argument("--llm-config-file", type=str, default="llm_config.json",
                         help="Path to llm_config.json (for api_key_env_var and base_url).")
    parser.add_argument("--out", type=str, default="pilot_outputs/stability_run_results.csv", help="Output CSV path.")
    args = parser.parse_args()

    actual_temp = preflight_check_temperature(args.expected_temperature, args.strict)

    try:
        with open(args.llm_config_file, "r", encoding="utf-8") as f:
            llm_cfg = json.load(f)
    except FileNotFoundError:
        sys.exit(f"\u274c {args.llm_config_file} not found.")
    key_env_var = llm_cfg.get("api_key_env_var", "OPENAI_API_KEY")
    base_url = llm_cfg.get("base_url", "https://api.openai.com/v1").rstrip("/")
    api_key = os.environ.get(key_env_var)
    if not api_key:
        sys.exit(f"\u274c API key not set. Export {key_env_var} before running.")

    primal_anchors = load_anchors(args.anchors_file)

    print(f"\nLoaded {len(primal_anchors)} words from {args.anchors_file} (full anchor vault \u2014 paired design)")
    print(f"Running {args.runs} runs at prompts.json temperature={actual_temp}, alpha={args.alpha}")
    print(f"Expected total paired observations: {len(primal_anchors)} words x {args.runs} runs x 2 conditions "
          f"= {len(primal_anchors) * args.runs * 2} rows (if every call succeeds)")

    rows, failures = run_stability_pilot(
        n_runs=args.runs,
        api_key=api_key,
        base_url=base_url,
        primal_anchors=primal_anchors,
        alpha_anchored=args.alpha,
    )

    write_csv(rows, args.out)
    print(f"\nWrote {len(rows)} rows to {args.out}")

    if failures:
        print(f"\n\u26a0\ufe0f  {len(failures)} failure(s) logged:")
        for f in failures:
            print(f"   - {f}")

    summarise_paired_results(rows)


if __name__ == "__main__":
    main()