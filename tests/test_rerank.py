from types import SimpleNamespace

import src.answer as answer_module


def fake_client(scores):
    """OpenAI client stub that returns the given reply for each successive call."""
    replies = iter(scores)

    def create(**kwargs):
        content = next(replies)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


CHUNKS = [{"text": t, "source": "x.pdf", "page": i} for i, t in enumerate(["ref list", "answer", "partial"])]


def test_rerank_orders_by_score_and_keeps_top_k(monkeypatch):
    monkeypatch.setattr(answer_module, "client", fake_client(["2", "9", "5"]))
    result = answer_module.rerank("q", CHUNKS, top_k=2)
    assert [c["text"] for c in result] == ["answer", "partial"]


def test_unparseable_score_counts_as_zero(monkeypatch):
    monkeypatch.setattr(answer_module, "client", fake_client(["n/a", "7", "3"]))
    result = answer_module.rerank("q", CHUNKS, top_k=3)
    assert [c["text"] for c in result] == ["answer", "partial", "ref list"]
