from src.ingest import chunk_text


def make_page(n_words, page=0, source="doc.pdf"):
    return {"text": " ".join(f"w{i}" for i in range(n_words)), "page": page, "source": source}


def test_chunks_are_at_most_100_words():
    chunks = chunk_text([make_page(250)])
    assert all(len(c["text"].split()) <= 100 for c in chunks)


def test_windows_overlap_by_10_words():
    chunks = chunk_text([make_page(250)])
    first, second = chunks[0]["text"].split(), chunks[1]["text"].split()
    assert first[-10:] == second[:10]


def test_no_words_are_lost():
    chunks = chunk_text([make_page(250)])
    seen = {w for c in chunks for w in c["text"].split()}
    assert seen == {f"w{i}" for i in range(250)}


def test_chunks_keep_page_and_source_metadata():
    chunks = chunk_text([make_page(120, page=3, source="a.pdf"), make_page(50, page=4, source="a.pdf")])
    assert {(c["page"], c["source"]) for c in chunks} == {(3, "a.pdf"), (4, "a.pdf")}


def test_chunks_never_span_pages():
    chunks = chunk_text([make_page(30, page=0), make_page(30, page=1)])
    assert len(chunks) == 2


def test_empty_page_produces_no_chunks():
    assert chunk_text([{"text": "   ", "page": 0, "source": "blank.pdf"}]) == []
