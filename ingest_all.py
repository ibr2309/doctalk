import os
from src.ingest import ingest
from src.embed import embed_chunks, reset_db

def ingest_all(data_dir="data/pdfs"):
    reset_db()
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith(".pdf")]
    
    total_chunks = 0
    for filename in pdf_files:
        path = os.path.join(data_dir, filename)
        print(f"Ingesting {filename}...")
        chunks = ingest(path)
        embed_chunks(chunks)
        total_chunks += len(chunks)
        print(f"  -> {len(chunks)} chunks added")
    
    print(f"\nDone. {len(pdf_files)} PDFs, {total_chunks} total chunks.")

if __name__ == "__main__":
    ingest_all()