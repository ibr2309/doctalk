import os
from dotenv import load_dotenv
from openai import OpenAI
from src.embed import retrieve

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def rerank(question, chunks, top_k=3):
    """Score each retrieved chunk 1-10 for relevance via gpt-4o-mini, keep top_k.

    Fixes the bibliography-pollution failure: reference-list chunks embed close
    to topic questions but score low on 'does this passage ANSWER the question'.
    """
    scored = []
    for chunk in chunks:
        prompt = f"""Rate how useful this passage is for answering the question, on a scale of 1 to 10.
A passage that directly answers the question scores high. A passage that merely mentions related words (e.g. a reference list or bibliography) scores low.
Respond with a single integer from 1 to 10 and nothing else.

Question: {question}

Passage:
{chunk['text']}

Score:"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=3
        )
        try:
            score = int(response.choices[0].message.content.strip())
        except ValueError:
            score = 0
        scored.append((score, chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in scored[:top_k]]

def answer(question, use_rerank=True, source=None):
    if use_rerank:
        candidates = retrieve(question, k=10, source=source)
        chunks = rerank(question, candidates, top_k=3)
    else:
        chunks = retrieve(question, k=5, source=source)

    context = ""
    for chunk in chunks:
        context += f"Source: {chunk['source']}, Page: {chunk['page']}\n"
        context += f"{chunk['text']}\n\n"
    
    prompt = f"""You are a research assistant answering questions about a collection of academic papers. Each piece of context below is tagged with the source filename it came from.

Answer the question using only the information in the context below. Follow these rules:

1. If the question asks which paper(s) or document(s) discuss/involve/cover a topic, answer using the "Source:" filenames of the context chunks themselves — not any bibliography, citations, or references that appear *inside* the paper text. A paper mentioning another paper in its reference list does not mean that other paper is part of this collection.

2. If the question refers to "this paper" or "the paper" without naming one, and all the context comes from a single source file, assume the question is about that paper.

3. Only say "I don't have enough information to answer that" if the context truly does not address the question — not just because the exact wording isn't present. If the context implies or states the answer indirectly, answer using that information.

4. Always state the answer in one or more full sentences — a citation alone is never a valid answer. Then cite the source filename and page number for each claim.

Context:
{context}

Question: {question}

Answer:"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    
    return {
        "answer": response.choices[0].message.content,
        "sources": chunks
    }