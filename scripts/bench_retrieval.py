import time
import json
import random
from pathlib import Path
from app.semantic_retriever import SemanticRetriever

class FakeEmbeddingService:
    def embed(self, text):
        return [random.random() for _ in range(3072)]

def main():
    print("Generating 5000 synthetic 3072-dim embeddings...")
    units = []
    for i in range(5000):
        units.append({
            "path": f"file_{i}.py",
            "type": "function",
            "name": f"func_{i}",
            "source": "pass",
            "embedding": [random.random() for _ in range(3072)]
        })
        
    tmp_path = Path("bench_index.json")
    with tmp_path.open("w") as f:
        json.dump(units, f)
        
    try:
        print("Loading retriever...")
        t0 = time.perf_counter()
        retriever = SemanticRetriever(str(tmp_path), embedding_service=FakeEmbeddingService())
        t1 = time.perf_counter()
        print(f"Matrix load and normalization time: {(t1 - t0)*1000:.2f}ms")
        
        print("Querying...")
        t0 = time.perf_counter()
        retriever.search("test query", top_k=10)
        t1 = time.perf_counter()
        print(f"Query and argpartition time: {(t1 - t0)*1000:.2f}ms")
    finally:
        tmp_path.unlink()

if __name__ == "__main__":
    main()
