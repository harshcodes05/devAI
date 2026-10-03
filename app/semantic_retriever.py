import json
import math
import numpy as np
from pathlib import Path

from app.embedding_service import EmbeddingService


class SemanticRetriever:
    def __init__(self, index_path: str, embedding_service=None):
        self.index_path = Path(index_path)

        if not self.index_path.exists():
            raise FileNotFoundError(
                f"Semantic index not found: {self.index_path}"
            )

        with self.index_path.open("r", encoding="utf-8") as file:
            self.units = json.load(file)

        self.embedding_service = embedding_service or EmbeddingService()

        if self.units:
            raw_matrix = np.array([u["embedding"] for u in self.units], dtype=np.float32)
            norms = np.linalg.norm(raw_matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.matrix = raw_matrix / norms
        else:
            self.matrix = np.array([], dtype=np.float32)

    def cosine_similarity(self, vector_a: list[float], vector_b: list[float]) -> float:
        """Calculate cosine similarity between two vectors (for backwards compatibility/tests)."""
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        magnitude_a = math.sqrt(sum(a * a for a in vector_a))
        magnitude_b = math.sqrt(sum(b * b for b in vector_b))
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        return dot_product / (magnitude_a * magnitude_b)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Find the most semantically relevant code units using O(N) numpy vector operations."""
        if len(self.units) == 0:
            return []

        query_embedding = self.embedding_service.embed(query)
        q_vec = np.array(query_embedding, dtype=np.float32)
        
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm
            
        scores = self.matrix @ q_vec
        
        k = min(top_k, len(scores))
        if k == 0:
            return []

        if k == len(scores):
            top_indices = np.argsort(scores)[::-1]
        else:
            partitioned_indices = np.argpartition(scores, -k)[-k:]
            top_indices = partitioned_indices[np.argsort(scores[partitioned_indices])[::-1]]

        results = []
        for idx in top_indices:
            unit = self.units[idx]
            results.append(
                {
                    "score": float(scores[idx]),
                    "path": unit["path"],
                    "type": unit["type"],
                    "name": unit["name"],
                    "source": unit["source"],
                }
            )

        return results