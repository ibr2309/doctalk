import fitz     
import os 

def parse_pdf(pdf_path):

    doc = fitz.open(pdf_path)
    pages = []
    filename = os.path.basename(pdf_path)

    for page in doc:

        dic = {}
        text = page.get_text()
        dic["text"] = text
        dic["page"] = page.number
        dic["source"] = filename
        pages.append(dic)

    return pages

def chunk_text(pages):

    all_chunks = []

    for i in pages:
        text = i["text"]

        for start in range(0, len(text), 450):
            chunk_info = {}
            chunk = text[start:start + 500]
            chunk_info["text"] = chunk
            chunk_info["page"] = i["page"]
            chunk_info["source"] = i["source"]
            all_chunks.append(chunk_info)

    return all_chunks

def ingest(pdf_path):
    pages = parse_pdf(pdf_path)
    chunks = chunk_text(pages)
    return chunks

if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    chunks = ingest(path)
    print(f"Total chunks: {len(chunks)}")
    print(f"First chunk preview:\n{chunks[0]['text'][:200]}")




