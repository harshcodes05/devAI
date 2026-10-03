from pathlib import Path

from app.context_builder import ContextBuilder
from app.retriever import CodeRetriever


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INDEX_PATH = (
    PROJECT_ROOT
    / "data"
    / "code_index.json"
)


retriever = CodeRetriever(
    str(INDEX_PATH)
)

query = "How does fraud prediction work?"

results = retriever.search(
    query,
    top_k=3,
)

builder = ContextBuilder()

context = builder.build(
    query,
    results,
)

print(context)