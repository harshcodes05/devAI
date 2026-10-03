import json
import math
from pathlib import Path

from app.embedding_service import EmbeddingService


class SemanticRetriever:
    def __init__(self, index_path: str):
        self.index_path = Path(index_path)

        if not self.index_path.exists():
            raise FileNotFoundError(
                f"Semantic index not found: {self.index_path}"
            )

        with self.index_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            self.units = json.load(file)

        self.embedding_service = EmbeddingService()

    def cosine_similarity(
        self,
        vector_a: list[float],
        vector_b: list[float],
    ) -> float:
        """Calculate cosine similarity between two vectors."""

        dot_product = sum(
            a * b
            for a, b in zip(vector_a, vector_b)
        )

        magnitude_a = math.sqrt(
            sum(a * a for a in vector_a)
        )

        magnitude_b = math.sqrt(
            sum(b * b for b in vector_b)
        )

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (
            magnitude_a * magnitude_b
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Find the most semantically relevant code units."""

        query_embedding = (
            self.embedding_service.embed(query)
        )

        results = []

        for unit in self.units:
            score = self.cosine_similarity(
                query_embedding,
                unit["embedding"],
            )

            results.append(
                {
                    "score": score,
                    "path": unit["path"],
                    "type": unit["type"],
                    "name": unit["name"],
                    "source": unit["source"],
                }
            )

        results.sort(
            key=lambda result: result["score"],
            reverse=True,
        )

        return results[:top_k]