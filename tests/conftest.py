import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# src.answer builds an OpenAI client at import time and src.embed loads an
# embedding model; neither is needed to unit-test the pure logic, so fake them.
os.environ.setdefault("OPENAI_API_KEY", "test-key")

if "src.embed" not in sys.modules:
    fake_embed = types.ModuleType("src.embed")
    fake_embed.retrieve = lambda *args, **kwargs: []
    sys.modules["src.embed"] = fake_embed
