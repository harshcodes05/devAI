from pathlib import Path

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
    top_k=5,
)

for result in results:
    print(
        f"\nScore: {result['score']:.4f}"
        f"\nPath: {result['path']}"
        f"\nType: {result['type']}"
        f"\nName: {result['name']}"
    )