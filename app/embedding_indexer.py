import json
from pathlib import Path

from app.embedding_service import EmbeddingService


class EmbeddingIndexer:
    def __init__(
        self,
        code_index_path: str,
        output_path: str,
    ):
        self.code_index_path = Path(code_index_path)
        self.output_path = Path(output_path)

        if not self.code_index_path.exists():
            raise FileNotFoundError(
                f"Code index not found: {self.code_index_path}"
            )

        with self.code_index_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            self.units = json.load(file)

        self.embedding_service = EmbeddingService()

    def build_index(self) -> list[dict]:
        """Generate an embedding for each code unit."""

        documents = []

        for unit in self.units:
            text = (
                f"File: {unit['path']}\n"
                f"Type: {unit['type']}\n"
                f"Name: {unit['name']}\n"
                f"Code:\n{unit['source']}"
            )

            documents.append(text)

        embeddings = (
            self.embedding_service.embed_documents(
                documents
            )
        )

        semantic_index = []

        for unit, embedding in zip(
            self.units,
            embeddings,
        ):
            semantic_index.append(
                {
                    **unit,
                    "embedding": embedding,
                }
            )

        return semantic_index

    def save(self) -> None:
        """Build and save the semantic index."""

        semantic_index = self.build_index()

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.output_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                semantic_index,
                file,
            )

        print(
            f"Semantic index saved to: "
            f"{self.output_path}"
        )