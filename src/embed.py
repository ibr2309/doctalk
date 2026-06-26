from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.Client()
collection = client.get_or_create_collection(name="doctalk")

def embed_chunks(chunks):

    for i, chunk in enumerate(chunks):
        vector = model.encode(chunk["text"])
        collection.add(ids = [f"chunk_{i}"] ,documents = [chunk["text"]], embeddings= [vector], metadatas=[{"page": chunk["page"], "source": chunk["source"]}] )

def retrieve(question):

    query_vector = model.encode(question)
    results = collection.query(
    query_embeddings=[query_vector],
    n_results=5)
    
    return results

if __name__ == "__main__":
    from ingest import ingest
    chunks = ingest("data/pdfs/rp1.pdf")
    embed_chunks(chunks)
    results = retrieve("what is the main contribution of this paper?")
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"Page {meta['page']} | {meta['source']}\n{doc[:150]}\n")