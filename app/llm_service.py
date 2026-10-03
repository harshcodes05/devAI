import logging
import time
import warnings

# Suppress annoying SDK warnings about AFC globally
warnings.simplefilter("ignore")
logging.getLogger("google").setLevel(logging.ERROR)

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

        max_retries = 5

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.7-flash",
                    contents=prompt,
                )
                return response.text

            except errors.APIError as e:
                # Check for quota exhaustion
                if e.code == 429 or "RESOURCE_EXHAUSTED" in str(e):
                    raise Exception("Gemini daily quota exhausted. Try again after the quota resets.")
                
                # For other API errors (like 503), retry
                if attempt < max_retries - 1:
                    wait = 3 ** (attempt + 1)
                    time.sleep(wait)
                else:
                    raise Exception(f"Gemini API Error after {max_retries} retries: {str(e)}")
                    
            except errors.ServerError as e:
                if attempt < max_retries - 1:
                    wait = 3 ** (attempt + 1)
                    time.sleep(wait)
                else:
                    raise Exception(f"Gemini API is currently overloaded after {max_retries} retries. Please try again later. (Error: {str(e)})")