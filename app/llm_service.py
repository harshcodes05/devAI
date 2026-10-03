import logging
import time
import random
import warnings

# Suppress annoying SDK warnings about AFC globally
warnings.simplefilter("ignore")
logging.getLogger("google").setLevel(logging.ERROR)

import app.config  # noqa: F401 — ensures .env is loaded
from google import genai
from google.genai import errors

PROMPT_TEMPLATE = """
You are a software-engineering codebase assistant.

Answer the developer's question using ONLY the provided repository context.

Rules:
- Do not invent code or behavior that is not present in the context.
- Explain the reasoning clearly.
- If the provided context is insufficient, say so.
- AT THE END of your answer, you MUST provide an "Evidence" section listing the exact files and functions you used to construct your answer, formatted exactly like this:

Evidence
-------
1. path/to/file.py
   function_name()

2. path/to/other.py
   ClassName.method()

Developer question:
{question}

Repository context:
{context}
"""

class LLMService:
    def __init__(self, client=None):
        self.client = client if client else genai.Client()

    def answer(self, question: str, context: str) -> str:
        """
        Answer a developer question using retrieved code context.
        """
        prompt = PROMPT_TEMPLATE.format(question=question, context=context)

        max_retries = 5
        max_total_wait = 60
        total_wait = 0

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.7-flash",
                    contents=prompt,
                )
                return response.text

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