import json
from unittest.mock import MagicMock
from app.embedding_indexer import EmbeddingIndexer

class FakeEmbeddingService:
    def embed_documents(self, docs):
        return [[1.0, 0.0] for _ in docs]

def test_embedding_indexer(tmp_path):
    idx_in = tmp_path / "in.json"
    idx_out = tmp_path / "out.json"
    
    idx_in.write_text(json.dumps([
        {"path": "a.py", "type": "function", "name": "f", "source": "def f(): pass"}
    ]))
    
    indexer = EmbeddingIndexer(str(idx_in), str(idx_out))
    indexer.embedding_service = FakeEmbeddingService()
    
    indexer.save()
    
    data = json.loads(idx_out.read_text())
    assert len(data) == 1
    assert "embedding" in data[0]
    assert data[0]["embedding"] == [1.0, 0.0]
