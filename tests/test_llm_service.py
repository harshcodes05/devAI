from pathlib import Path

from app.context_builder import ContextBuilder
from app.llm_service import LLMService
from app.semantic_retriever import SemanticRetriever


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INDEX_PATH = (
    PROJECT_ROOT
    / "data"
    / "semantic_index.json"
)


question = "How does fraud prediction work?"

retriever = SemanticRetriever(
    str(INDEX_PATH)
)

results = retriever.search(
    question,
    top_k=5,
)

builder = ContextBuilder()

context = builder.build(
    question,
    results,
)

llm = LLMService()

answer = llm.answer(
    question,
    context,
)

print("\nANSWER:\n")
print(answer)