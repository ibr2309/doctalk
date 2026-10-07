import os
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer('all-MiniLM-L6-v2')
CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_db")
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="doctalk")

def reset_db():
    global collection
    client.delete_collection(name="doctalk")
    collection = client.get_or_create_collection(name="doctalk")

def delete_source(source):
    """Remove all chunks belonging to one source file.

    collection.add() silently drops duplicate ids (no upsert, no error), so
    re-ingesting an updated PDF would silently keep the stale chunks. Deleting
    the source's chunks first gives /upload proper refresh semantics.
    """
    collection.delete(where={"source": source})

def embed_chunks(chunks):
    for i, chunk in enumerate(chunks):
        vector = model.encode(chunk["text"])
        chunk_id = f"{chunk['source']}_chunk_{i}"
        collection.add(
            ids=[chunk_id],
            documents=[chunk["text"]],
            embeddings=[vector],
            metadatas=[{"page": chunk["page"], "source": chunk["source"]}]
        )

def list_sources():
    """Distinct source filenames currently in the collection."""
    metadatas = collection.get(include=["metadatas"])["metadatas"]
    return sorted(set(m["source"] for m in metadatas))

def retrieve(question, k=5, source=None):
    """Top-k chunks for a question.

    source=None        -> search the whole collection
    source="file.pdf"  -> restrict to one file (metadata filter)
    source=[...]       -> restrict to a set of files ($in filter) — used for
                          session isolation: a UI session only sees its own uploads
    """
    query_vector = model.encode(question)
    if isinstance(source, list):
        where = {"source": {"$in": source}}
    elif source:
        where = {"source": source}
    else:
        where = None
    results = collection.query(
    query_embeddings=[query_vector],
    n_results=k,
    where=where)

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "page": results["metadatas"][0][i]["page"]
        })
    
    return chunks
    

if __name__ == "__main__":
    from ingest import ingest
    chunks = ingest("data/pdfs/rp1.pdf")
    embed_chunks(chunks)
    results = retrieve("what is the main contribution of this paper?")
    for chunk in results:
        print(f"Page {chunk['page']} | {chunk['source']}\n{chunk['text'][:150]}\n")