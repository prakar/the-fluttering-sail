# Changes in Software

| Task | Description |
|------|-------------|
| \#9 — Confidence intervals everywhere | Add ±σ confidence intervals to every vector output based on variance across the ingestion run; implement in Fluttering Sail app and report in paper [original] |
| \#10 — Sensitivity analysis with plots | Run stability/weight sweep (0.3/0.7 through 0.7/0.3) and generate actual visual plots instead of just describing them [original] |
| \#12 — Ablation studies | Remove anchors, diagnostics, Sanskrit tranche, and hybrid merge one at a time to measure degradation; entirely in-software [original] |
| \#13 — Separate framework/dataset/application | Structurally rewrite the paper's contribution framing to explicitly state three distinct contributions; no new experiments needed [original] |
| \#14 — Formalize the geometry | Write distance/similarity functions as equations (cosine similarity, Euclidean distance, diagnostic boundary conditions) already implicit in code [original] |
| \#15 — Diagnostics as formal functions | Convert `if U > ...` logic into `Diagnostic_i(V)` notation; already implemented, needs mathematical expression in paper [original] |
| \#16 — Uncertainty propagation model | Formalize token → word → text → diagnostic uncertainty chain from existing variance data [original] |
| \#17 — Lexical coverage confidence | Implement coverage coefficient to attenuate confidence scores for texts with low lexicon hit-rate [original] |
| \#18 — Replace "first framework" claims | Purely editorial: swap phrasing and strengthen literature review; no experiments needed [original] |
| **Problem 2 — Tighten quantisation definition** | Conceptual/editorial: commit to one position (metaphor or measurement) and hold consistently throughout [original] |
| \#3 partial — Test-retest (intra-model) | Run same texts through existing pipeline multiple times at different temperatures to show intra-model stability; pure software, addresses "stochastic art" critique at low cost [original][flag] |
| **Random vector control** | Generate 20 random vectors through synthesis, compare to 20 genuine vectors on coherence ratings; negative control the paper currently lacks [future][software] |
| **Dimension perturbation** | Invert moksha's dominant dimensions, compare outputs, test null hypothesis explicitly; no external collaborators needed [future][software] |

# Changes Requiring Real World Interaction

| Task | Description | Requirements |
|------|-------------|--------------|
| \#1 — Independent annotation studies | Conduct annotation studies measuring Cohen's κ and Krippendorff's α | External annotators [original] |
| \#2 — Inter-rater reliability on anchor vault | Assess reliability across raters on the anchor vault | Philosophers, Sanskritists, computational linguists [original] |
| \#4 — Benchmark against human expert judgement | Compare framework outputs against expert human evaluations | Expert participants [original] |
| \#5 — Benchmark against competing frameworks | Benchmark against MFT, ValueLex, and other frameworks | Access to those datasets and comparative methodology [original] |
| \#6 — Cross-cultural corpus validation | Validate framework across curated multi-civilisational corpora | Curated multi-civilisational corpora [original] |
| \#7 — Publish lexicon as citable dataset | Deposit lexicon on Zenodo/HuggingFace as citable dataset | Zenodo/HuggingFace deposit (low effort, outside manuscript) [original] |
| \#8 — Recruit hostile scholars | Conduct genuine expert adversarial review | Hostile scholars for adversarial review [original] |
| **Problem 1 — Dimensional independence** | Perform PCA, covariance matrix analysis, and factor analysis | Corpus-scale data first [original] |
| **Problem 3 — Lexicon author's worldview vs text** | Rebut concerns about author worldview influencing text interpretation | Needs inter-rater studies from \#1/\#2 to rebut [original] |
| **Blind expert reconstruction study** | Experts given vector only, asked to identify concept from 20 candidates; attacks circularity, arbitrariness, information content, and interpretability | Domain experts (highest priority) [future] |
| **Baseline comparison study** | Compare dictionary vs. embeddings vs. vector portraits, rated by independent evaluators | Human evaluators [future] |