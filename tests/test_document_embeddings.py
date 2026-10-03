from app.embedding_service import EmbeddingService


service = EmbeddingService()

documents = [
    "PredictorService performs fraud prediction using XGBoost.",
    "PreprocessorService scales transaction features before inference.",
]

embeddings = service.embed_documents(documents)

print("Documents:", len(embeddings))
print("Dimensions:", len(embeddings[0]))
print("First vector, first 5 values:", embeddings[0][:5])
print("Second vector, first 5 values:", embeddings[1][:5])