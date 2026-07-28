# DocTalk 📄

A RAG-based document Q&A system over Amii/UAlberta research papers. Ask questions in plain English, get grounded answers with source citations (paper + page number).

Built **without LangChain** — every layer of the RAG pipeline is implemented from scratch so each architectural decision is explicit and explainable.

**Accuracy: 85% strict / 87.5% weighted on 20 domain-specific eval questions** — up from 70% before two-stage retrieval (see [Evaluation](#evaluation)).

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │                  INGESTION                  │
  PDF ──► PyMuPDF ──► word-based chunking ──► all-MiniLM-L6-v2 ──► ChromaDB
                    │  (100-word window,       (384-dim vectors)  │ (persistent)
                    │   10-word overlap)                          │
                    └─────────────────────────────────────────────┘

                    ┌─────────────────────────────────────────────┐
                    │                    QUERY                    │
 question ──► embed ──► retrieve top 10 ──► LLM rerank ──► top 3 ──► gpt-4o-mini ──► answer
                    │    (ChromaDB)       (gpt-4o-mini,            │   (grounded      + sources
                    │                      1–10 scoring)           │    prompt)
                    └─────────────────────────────────────────────┘
```

**Stack:** Python · PyMuPDF · sentence-transformers · ChromaDB · OpenAI gpt-4o-mini · FastAPI · Streamlit · Docker

## Key design decisions

- **No LangChain.** Raw implementation of chunking, embedding, retrieval, reranking, and prompting. Full control, full explainability.
- **Word-based windowed chunking** (100-word window, stride 90) instead of character-based — eliminates mid-word fragment artifacts in retrieved context.
- **Namespaced chunk IDs** (`{source}_chunk_{i}`) — ChromaDB silently drops duplicate IDs on `add()`, so per-file IDs like `chunk_0` caused silent data loss across files.
- **LLM reranking** — embedding similarity retrieves bibliography/reference-list chunks that mention topic keywords but answer nothing. A second-stage gpt-4o-mini pass scores each of 10 candidates 1–10 for "does this passage answer the question" and keeps the top 3.
- **Grounded prompting** — the answer prompt requires citations (source + page) and permits "I don't have enough information" rather than hallucinating.

## Run locally

```bash
git clone https://github.com/ibr2309/doctalk.git
cd doctalk
python -m venv venv
venv\Scripts\activate        # Windows (source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
echo OPENAI_API_KEY=sk-... > .env

python ingest_all.py         # build the vector DB from data/pdfs/
uvicorn api:app --reload     # backend on :8000
streamlit run ui.py          # UI on :8501 (second terminal)
```

## Run with Docker

```bash
docker compose up --build
```

- UI: http://localhost:8501
- API docs: http://localhost:8000/docs

## API

| Method | Endpoint   | Body                                                             | Returns                  |
|--------|------------|------------------------------------------------------------------|--------------------------|
| POST   | `/upload`  | multipart PDF file                                               | filename, chunks added   |
| POST   | `/query`   | `{"question": "...", "use_rerank": true, "source": "file.pdf"?}` | answer + source chunks   |
| GET    | `/sources` | —                                                                | documents in the KB      |
| GET    | `/health`  | —                                                                | `{"status": "ok"}`       |

`source` scopes retrieval to a single document (ChromaDB metadata filter) — without it, questions search the whole knowledge base.

## Evaluation

20 domain-specific questions across the 5 papers — per-paper factual, cross-paper, meta, summarization, and negative-control — graded pass/partial/fail against the source texts (`eval.py` → `eval_results.txt`).

| Run | Setup | Strict pass | Weighted (partial = 0.5) |
|-----|-------|-------------|--------------------------|
| 1 | original prompt, k=5 | 15/20 (75%) | 82.5% |
| 2 | rewritten grounded prompt, k=5 | 14/20 (70%) | 80% |
| 3 | + LLM reranking (k=10 → top 3), prompt fixes | **17/20 (85%)** | **87.5%** |

Eval failures drove the fixes: every bug found by the eval is documented in `BUGS.md` with cause and resolution.

## Papers in the knowledge base

1. DMMGAN — diverse human motion prediction (GANs)
2. Multi-label tweet emotion classification
3. Time-discretization in reinforcement learning (De Asis & Sutton)
4. Convergence of average-reward RVI Q-learning (Wan, Yu & Sutton)
5. AI/ML cybersecurity for autonomous vehicles (capstone)
