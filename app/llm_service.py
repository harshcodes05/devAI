import time

import app.config  # noqa: F401 — ensures .env is loaded
from google import genai
from google.genai import errors


class LLMService:
    def __init__(self):
        self.client = genai.Client()

    def answer(self, question: str, context: str) -> str:
        """
        Answer a developer question using retrieved code context.
        """

        prompt = f"""
You are a software-engineering codebase assistant.

Answer the developer's question using ONLY the provided repository context.

Rules:
- Do not invent code or behavior that is not present in the context.
- Explain the reasoning clearly.
- Mention relevant file paths and function/class names.
- If the provided context is insufficient, say so.

Developer question:
{question}

Repository context:
{context}
"""

        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.7-flash",
                    contents=prompt,
                )
                return response.text

            except errors.ServerError:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"API busy, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise