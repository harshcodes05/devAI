import app.config  # noqa: F401 — ensures .env is loaded
from google import genai
from google.genai import types
class EmbeddingService:
    def __init__(self):
        self.client = genai.Client()

    def embed(self, text: str) -> list[float]:
        """Generate an embedding for one piece of text."""

        result = self.client.models.embed_content(
            model="gemini-embedding-2",
            contents=text,
        )

        return result.embeddings[0].values

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate one embedding for each document."""

        contents = [
            types.Content(
                parts=[types.Part.from_text(text=text)]
            )
            for text in texts
        ]

        result = self.client.models.embed_content(
            model="gemini-embedding-2",
            contents=contents,
        )

        return [
            embedding.values
            for embedding in result.embeddings
        ]