# Bug Log

Running log of bugs found while building DocTalk. Keep every entry, even fixed
ones — this doubles as interview prep material ("hardest bugs and how you
fixed them").

Format per entry: what broke, where, why, status, fix (if any).

---

## Bug #1 — Chunking off-by-one (FIXED)
- **Found:** Day 4, reviewing eval_results.txt
- **File:** `src/ingest.py`, `chunk_text()`
- **Symptom:** only the first ~2 chunks per document had real text; every
  chunk after that was empty.
- **Cause:** `chunk = " ".join(word[start:100])` — fixed upper bound of 100
  instead of a sliding window, so once `start > 100` the slice is empty.
- **Fix:** `word[start:start + 100]`
- **Verified:** re-ran `chunk_text()` on a 250-word mock page — got 3 chunks
  of 100/100/70 words with correct 10-word overlap, zero empty chunks.

## Bug #2 — ChromaDB collection was ephemeral (FIXED)
- **Found:** while reviewing `src/embed.py`
- **File:** `src/embed.py`
- **Symptom:** every new Python process started with a totally empty
  collection — Day 2/3 testing was silently re-ingesting from scratch every
  single run.
- **Cause:** used `chromadb.Client()` (in-memory) instead of a persistent
  client.
- **Fix:** switched to `chromadb.PersistentClient(path="chroma_db")`.

## Bug #3 — `collection.add()` silently drops duplicate IDs (OPEN)
- **Found:** manual test — added 3 items with ids `chunk_0/1/2`, then added 3
  *different* items with the same ids. Collection kept the original data. No
  exception, no warning.
- **Symptom:** this is the opposite of an upsert. Re-ingesting an updated PDF
  through a future `/upload` endpoint would silently fail to refresh its
  chunks unless `reset_db()` wipes the whole collection first.
- **Status:** FIXED (Day 5) — went with explicit delete-then-add by source
  filename: `delete_source()` in `src/embed.py` runs
  `collection.delete(where={"source": source})` before `/upload` re-ingests.
  Chose this over `upsert()` because re-chunking a changed PDF can produce a
  *different number* of chunks — upsert would update overlapping ids but
  leave orphaned stale chunks past the new count.

## Bug #4 — "Which papers" answered with in-document bibliography (FIXED, see #6)
- **Found:** eval run 1, Q16 ("Which papers involve reinforcement learning?")
- **Symptom:** model returned the *reference list* cited inside rp3/rp4
  (Sutton, Barreto, Doya, etc.) instead of identifying rp3.pdf/rp4.pdf as the
  actual corpus documents about RL.
- **Cause:** prompt didn't distinguish "the source filename this chunk came
  from" vs. "papers this chunk's author cites."
- **Fix:** rewrote prompt to explicitly say to use `Source:` filenames, not
  in-text citations, for "which document" questions.
- **Result:** fixed the misidentification, but introduced Bug #6 (below).

## Bug #5 — Unnecessary refusal despite retrieved context (FIXED, see #7)
- **Found:** eval run 1, Q17 ("What is the main contribution of this
  paper?") — answered "I don't have enough information," despite rp4.pdf
  being retrieved and its abstract stating clear contributions.
- **Fix:** prompt rewrite told the model to assume single-source context
  answers "this paper" rather than refusing.
- **Result:** stopped refusing, but see Bug #7 — it started answering
  confidently with the *wrong* (too-narrow) content instead.

## Bug #6 — Degenerate "citation-only" answers (OPEN)
- **Found:** eval run 2, Q16 and Q20
- **Symptom:** model answers with literally just `Source: rp1.pdf` — no
  sentence actually stating the answer.
- **Cause:** the prompt's "cite source and page for any claim" instruction
  apparently lets the model satisfy the citation requirement without ever
  writing the claim itself.
- **Status:** FIXED (Day 5) — prompt rule 4 now reads "Always state the
  answer in one or more full sentences — a citation alone is never a valid
  answer." **Verified in run 3:** zero citation-only answers across all 20
  questions.

## Bug #7 — Retrieval gap on meta-questions (OPEN)
- **Found:** eval run 2, Q17. Confirmed with a manual `retrieve()` debug
  script — all 5 chunks returned for "what is the main contribution of this
  paper" came from rp4.pdf pages 23–48 (deep proof/theorem sections). None
  came from page 0–1, where the abstract's explicit contributions list
  lives.
- **Cause:** dense embedding similarity favors technical/proof-heavy prose
  over abstract-level language for generic "meta" questions — this is a
  retrieval problem, not a prompt problem.
- **Status:** ADDRESSED (Day 5) — implemented LLM reranking in
  `src/answer.py`: retrieve k=10 candidates, score each 1–10 with
  gpt-4o-mini ("does this passage ANSWER the question"), keep top 3. The
  wider k=10 net gives abstract/intro chunks a chance to enter the pool, and
  the reranker prefers explicit contribution statements over proof prose.
  **Run 3 result:** improved from fail to partial — Q17 now describes real
  rp4 results (solution structure, stability) but still misses the abstract's
  headline claim (convergence extended from unichain to weakly communicating
  MDPs). Root cause unchanged: the abstract chunk still doesn't crack the
  top-10 candidates. Structural fix remains section-aware chunking.

## Bug #8 — Retrieval gap on multi-part answers (OPEN)
- **Found:** eval run 1 & 2, Q4/Q19. Confirmed with the same debug script —
  paper's abstract names two classifiers ("a cost sensitive RankSVM
  algorithm and a Deep Learning model"), but retrieval only ever surfaces
  the RankSVM subsection (3.1), never the parallel Deep Learning Model
  subsection (likely 3.2).
- **Status:** FIXED (Day 5) — same fix as Bug #7 (k=10 + LLM rerank widens
  the candidate pool so both parallel subsections can surface).
  **Verified in run 3:** Q4 now names both the cost-sensitive RankSVM and the
  (attention-based) deep learning model.

## Bug #9 — Imprecise MDP-type answer (OPEN, minor)
- **Found:** eval run 1 & 2, Q11
- **Symptom:** answer conflates "weakly communicating MDPs" (correct — the
  actual class the paper's convergence analysis targets) with either
  "average-reward MDPs" (too generic, that's the reward criterion not an MDP
  class) or "communicating MDPs" (a real but distinct/subset class,
  mentioned in background, not the analysis's main focus).
- **Status:** RESOLVED in run 3 — Q11 now leads with "weakly communicating
  MDPs" (and mentions communicating MDPs, which the paper does also test).

## Not-a-bug #10 — DB integrity audit (PASSED, with a lesson about pooling)
- **What happened:** an independent audit re-encoded each stored chunk's
  text and compared against its stored embedding. It initially flagged 26%
  of rows as "corrupted" — but every flagged row was *short* text. The
  audit tool itself was wrong: its tokenizer had padding-to-128 enabled and
  it mean-pooled over `[PAD]` tokens, while the real
  sentence-transformers pipeline masks padding out of the mean pool.
  Short sequences (mostly pads) produced garbage vectors; sequences ≥128
  tokens matched exactly, which is what gave the bug away.
- **Result after fixing the audit:** 222/222 sampled rows match at cosine
  ≥ 0.9999999. The DB is fully consistent.
- **Lesson (great interview material):** mean pooling MUST be attention-
  masked. Padding tokens aren't neutral — they drag every short text's
  embedding toward a common "mostly-pad" direction, making unrelated short
  strings look ~0.88 similar to each other. This is exactly why
  sentence-transformers pools with the attention mask.

---

## Bug #11 — Run-3 residual failures (OPEN)
- **Q16 ("Which papers involve RL?") — bibliography pollution persists.**
  Despite prompt rule 1 AND reranking, the answer listed six papers cited
  *inside* rp3/rp4 (sources: rp3 p8, rp4 p52 — reference-list pages). Two
  compounding causes: (a) the reranker scores reference-list chunks high
  because for a "which papers" question they superficially *do* look like
  answers — the scoring prompt's "reference list scores low" hint loses to
  surface relevance; (b) given only citation-list context, the answer LLM
  follows the content over rule 1. Candidate fixes: filter chunks with high
  citation-density before ranking, tag reference-section chunks at ingest and
  exclude them for "which papers" questions, or answer corpus-level questions
  from collection metadata (list of distinct sources) rather than retrieval.
- **Q14 ("Is this an academic research paper?") — misclassified rp5.** Called
  the capstone project report an "academic research paper" even though rp5
  page 0 says "capstone project report" (and Q15 correctly extracted the MSc
  Internetworking program). Retrieved chunks came from paper-styled sections
  (abstract, related works), so the context looked paper-like. Same structural
  fix: metadata/front-page chunks need boosting for document-level questions.

---

## Eval accuracy over time
| Run | Strict pass | Weighted (partial=0.5) | Fails |
|---|---|---|---|
| 1 (original prompt) | 15/20 = 75% | 82.5% | Q16, Q17 |
| 2 (rewritten prompt) | 14/20 = 70% | 80% | Q17, Q20 |
| 3 (LLM rerank k=10→3, prompt rules 4/6 fixes) | **17/20 = 85%** | **87.5%** | Q14, Q16 (partial: Q17) |
