import sys
from src.ingest import ingest
from src.embed import embed_chunks
from src.answer import answer

# Step 1 — ingest
chunks = ingest(sys.argv[1])

# Step 2 — embed
embed_chunks(chunks)

# Step 3 — ask
result = answer("What does DMMGAN predict?")
print(result["answer"])
print("---SOURCES---")
for chunk in result["sources"]:
    print(f"{chunk['source']} — page {chunk['page']}")

from src.embed import retrieve
test_chunks = retrieve("What is the main contribution of this paper?")
for c in test_chunks:
    print(c['text'][:200])
    print("---")    