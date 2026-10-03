import pytest
import json
from app.semantic_retriever import SemanticRetriever

class FakeEmbeddingService:
    def embed(self, text):
        return [1.0, 0.0, 0.0]

def test_semantic_retriever(tmp_path):
    index = [
        {"path": "a.py", "type": "function", "name": "a", "source": "a", "embedding": [0.9, 0.1, 0.0]},
        {"path": "b.py", "type": "function", "name": "b", "source": "b", "embedding": [0.0, 1.0, 0.0]},
        {"path": "c.py", "type": "function", "name": "c", "source": "c", "embedding": [1.0, 0.0, 0.0]}
    ]
    idx_file = tmp_path / "index.json"
    idx_file.write_text(json.dumps(index))
    
    retriever = SemanticRetriever(str(idx_file), embedding_service=FakeEmbeddingService())
    
    # Query is [1.0, 0.0, 0.0]
    results = retriever.search("Q", top_k=2)
    assert len(results) == 2
    assert results[0]["name"] == "c" # Exact match
    assert results[1]["name"] == "a" # Close match

def test_semantic_retriever_empty(tmp_path):
    idx_file = tmp_path / "index.json"
    idx_file.write_text("[]")
    retriever = SemanticRetriever(str(idx_file), embedding_service=FakeEmbeddingService())
    results = retriever.search("Q", top_k=5)
    assert len(results) == 0
