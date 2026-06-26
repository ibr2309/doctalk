import os
from dotenv import load_dotenv
from openai import OpenAI
from src.embed import retrieve

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def answer(question):
    chunks = retrieve(question)
    
    context = ""
    for chunk in chunks:
        context += f"Source: {chunk['source']}, Page: {chunk['page']}\n"
        context += f"{chunk['text']}\n\n"
    
    prompt = f"""You are a helpful research assistant. Answer the question using only the context provided below.
If the answer is not in the context, say "I don't have enough information to answer that."

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