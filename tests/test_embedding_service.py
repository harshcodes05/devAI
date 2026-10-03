from app.embedding_service import EmbeddingService


service = EmbeddingService()

text = """
PredictorService preprocesses a transaction,
runs XGBoost and Isolation Forest,
and produces a risk consensus.
"""

embedding = service.embed(text)

print("Embedding generated successfully.")
print("Dimensions:", len(embedding))
print("First 5 values:", embedding[:5])