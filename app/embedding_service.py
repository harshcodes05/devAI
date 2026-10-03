import time
import random
import warnings
import logging

# Suppress annoying SDK warnings
warnings.simplefilter("ignore")
logging.getLogger("google").setLevel(logging.ERROR)

import app.config  # noqa: F401
from google import genai
from google.genai import types, errors

BATCH_SIZE = 100
MAX_CHARS = 10000

class EmbeddingService:
    def __init__(self, client=None):
        self.client = client if client else genai.Client()

    def _call_with_retry(self, **kwargs):
        max_retries = 5
        max_total_wait = 60
        total_wait = 0

        for attempt in range(max_retries):
            try:
                return self.client.models.embed_content(**kwargs)
            except errors.APIError as e:
                code = getattr(e, "code", getattr(e, "status_code", None))
                msg = str(e).lower()

                is_quota = code == 429 and ("quota" in msg or "resource_exhausted" in msg)
                is_transient = (code in (429, 500, 502, 503, 504)) and not is_quota

                if is_transient:
                    wait_time = min((2 ** attempt) + random.uniform(0, 1), max_total_wait - total_wait)
                    if wait_time > 0 and attempt < max_retries - 1:
                        time.sleep(wait_time)
                        total_wait += wait_time
                        continue

                if code in (400, 401, 403, 404):
                    raise Exception(f"Invalid or missing GEMINI_API_KEY (HTTP {code}).")

                if is_quota:
                    raise Exception("Gemini daily quota exhausted. Try again after the quota resets.")

                raise Exception(f"Gemini API Error: {str(e)}")

        raise Exception("Gemini API Error: Max retries exceeded.")

    def embed(self, text: str) -> list[float]:
        """Generate an embedding for one piece of text (Query)."""
        truncated = text[:MAX_CHARS]
        
        config = types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        result = self._call_with_retry(
            model="gemini-embedding-2",
            contents=truncated,
            config=config,
        )
        return result.embeddings[0].values

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate one embedding for each document in batches."""
        all_embeddings = []
        config = types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            contents = [
                types.Content(
                    parts=[types.Part.from_text(text=text[:MAX_CHARS])]
                )
                for text in batch
            ]

            print(f"Embedding batch {i // BATCH_SIZE + 1} of {(len(texts) + BATCH_SIZE - 1) // BATCH_SIZE}...")
            
            result = self._call_with_retry(
                model="gemini-embedding-2",
                contents=contents,
                config=config,
            )
            
            for embedding in result.embeddings:
                all_embeddings.append(embedding.values)
                
        return all_embeddings