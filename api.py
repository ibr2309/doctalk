import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from src.ingest import ingest
from src.embed import embed_chunks, delete_source, list_sources
from src.answer import answer

app = FastAPI(title="DocTalk API", description="RAG-based Q&A over research papers")

UPLOAD_DIR = "data/pdfs"


class QueryRequest(BaseModel):
    question: str
    use_rerank: bool = True
    source: str | list[str] | None = None  # restrict search to one document or a set of documents


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sources")
def sources():
    return {"sources": list_sources()}


@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    delete_source(file.filename)  # refresh semantics: re-uploading a PDF replaces its chunks
    chunks = ingest(save_path)
    embed_chunks(chunks)
    return {"filename": file.filename, "chunks_added": len(chunks)}


@app.post("/query")
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = answer(request.question, use_rerank=request.use_rerank, source=request.source)
    return result
