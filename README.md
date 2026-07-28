# DocTalk

Ask questions about your PDFs in plain English and get answers grounded in the actual documents, with source and page citations.

I built the whole RAG pipeline from scratch, no LangChain. Every layer (chunking, embedding, retrieval, reranking, prompting) is my own code, so I can explain exactly why each piece works the way it does.

**85% strict / 87.5% weighted accuracy on a 20-question eval set**, up from 70% before I added two-stage retrieval. Details below.

## How it works

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
                    │                      1-10 scoring)           │    prompt)
                    └─────────────────────────────────────────────┘
```

Stack: Python, PyMuPDF, sentence-transformers, ChromaDB, OpenAI gpt-4o-mini, FastAPI, Streamlit, Docker.

## Design decisions worth explaining

**No LangChain.** I wanted to understand every layer, not glue framework calls together. This paid off multiple times when debugging (see BUGS.md).

**Word-based windowed chunking** (100-word window, 90-word stride) instead of character-based. Character chunks kept cutting words in half at the boundaries, which polluted both the embeddings and the displayed sources.

**Namespaced chunk IDs** like `rp2.pdf_chunk_14`. ChromaDB's `add()` silently drops any ID that already exists, no error, no warning. With per-file IDs like `chunk_0`, three of my five papers ended up with zero chunks in the database while the logs looked completely fine. Hardest bug in the project.

**LLM reranking.** Plain embedding similarity kept retrieving bibliography chunks, since a reference list mentions all the right keywords without answering anything. So retrieval now pulls 10 candidates and a second gpt-4o-mini pass scores each one on whether it actually answers the question, keeping the top 3. This took eval accuracy from 70% to 85%.

**Grounded prompting.** The answer prompt requires full-sentence answers with source and page citations, and explicitly allows "I don't have enough information" instead of making something up.

**Session-scoped knowledge base.** Each browser session only sees the PDFs it uploaded, enforced with a ChromaDB metadata filter rather than separate collections. Same pattern multi-tenant RAG systems use in production.

## Run it locally

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

Or with Docker:

```bash
docker compose up --build
```

UI at http://localhost:8501, API docs at http://localhost:8000/docs.

## API

| Method | Endpoint   | Body                                                             | Returns                  |
|--------|------------|------------------------------------------------------------------|--------------------------|
| POST   | `/upload`  | multipart PDF file                                               | filename, chunks added   |
| POST   | `/query`   | `{"question": "...", "use_rerank": true, "source": "file.pdf"?}` | answer + source chunks   |
| GET    | `/sources` | none                                                             | documents in the KB      |
| GET    | `/health`  | none                                                             | `{"status": "ok"}`       |

`source` restricts retrieval to one document (or a list of them) using a ChromaDB metadata filter. Without it, questions search everything.

## Evaluation

I benchmarked on 5 Amii/UAlberta research papers with 20 questions covering per-paper facts, cross-paper questions, meta questions, summarization, and a couple of trick questions. Answers were graded pass/partial/fail against the source texts (`eval.py` writes the transcript to `eval_results.txt`).

| Run | Setup | Strict pass | Weighted (partial = 0.5) |
|-----|-------|-------------|--------------------------|
| 1 | original prompt, k=5 | 15/20 (75%) | 82.5% |
| 2 | rewritten grounded prompt, k=5 | 14/20 (70%) | 80% |
| 3 | added LLM reranking (k=10 to top 3) plus prompt fixes | **17/20 (85%)** | **87.5%** |

Every failure the eval caught turned into a documented bug with a root cause and fix in `BUGS.md`. The two remaining failures (bibliography pollution on "which papers discuss X" questions, and misreading a capstone report as a journal paper) are analyzed there too.

## The eval corpus

1. DMMGAN, diverse human motion prediction with GANs
2. Multi-label tweet emotion classification
3. Time-discretization in reinforcement learning (De Asis and Sutton)
4. Convergence of average-reward RVI Q-learning (Wan, Yu and Sutton)
5. AI/ML cybersecurity for autonomous vehicles (MSc capstone report)
