from pathlib import Path

from app.embedding_indexer import EmbeddingIndexer


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CODE_INDEX_PATH = (
    PROJECT_ROOT
    / "data"
    / "code_index.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "semantic_index.json"
)


indexer = EmbeddingIndexer(
    str(CODE_INDEX_PATH),
    str(OUTPUT_PATH),
)

indexer.save()