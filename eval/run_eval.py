import json
import sys
import argparse
from pathlib import Path
from app.semantic_retriever import SemanticRetriever

def calculate_mrr(retrieved_paths, expected_paths):
    for idx, path in enumerate(retrieved_paths, start=1):
        if path in expected_paths:
            return 1.0 / idx
    return 0.0

def calculate_precision(retrieved_paths, expected_paths):
    hits = sum(1 for p in retrieved_paths if p in expected_paths)
    if not retrieved_paths:
        return 0.0
    return hits / len(retrieved_paths)

def calculate_recall(retrieved_paths, expected_paths):
    hits = sum(1 for p in expected_paths if p in retrieved_paths)
    if not expected_paths:
        return 1.0
    return hits / len(expected_paths)

def main():
    parser = argparse.ArgumentParser(description="DevAI Retrieval Evaluation")
    parser.add_argument("--index", default="data/semantic_index.json", help="Path to semantic_index.json")
    parser.add_argument("--test-cases", default="eval/test_cases.json", help="Path to test cases JSON")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved results to evaluate")
    args = parser.parse_args()
    
    index_path = Path(args.index)
    if not index_path.exists():
        print(f"Index not found: {index_path}. Please run 'python main.py index .' first.")
        sys.exit(1)
        
    with Path(args.test_cases).open("r", encoding="utf-8") as f:
        test_cases = json.load(f)
        
    print("Loading Semantic Retriever...")
    retriever = SemanticRetriever(str(index_path))
    
    total_mrr = 0.0
    total_precision = 0.0
    total_recall = 0.0
    
    print(f"\nEvaluating {len(test_cases)} questions (Top-{args.top_k}):")
    print("-" * 60)
    
    for i, tc in enumerate(test_cases, start=1):
        q = tc["question"]
        expected = set(tc["expected_files"])
        
        results = retriever.search(q, top_k=args.top_k)
        retrieved_paths = []
        for r in results:
            if r["path"] not in retrieved_paths:
                retrieved_paths.append(r["path"])
                
        mrr = calculate_mrr(retrieved_paths, expected)
        precision = calculate_precision(retrieved_paths, expected)
        recall = calculate_recall(retrieved_paths, expected)
        
        total_mrr += mrr
        total_precision += precision
        total_recall += recall
        
        print(f"Q{i}: {q}")
        print(f"  Expected: {', '.join(expected)}")
        print(f"  Retrieved: {', '.join(retrieved_paths[:args.top_k])}")
        print(f"  MRR: {mrr:.2f} | Precision: {precision:.2f} | Recall: {recall:.2f}\n")
        
    n = len(test_cases)
    print("-" * 60)
    print("OVERALL METRICS:")
    print(f"Mean Reciprocal Rank (MRR): {total_mrr / n:.4f}")
    print(f"Average Context Precision:  {total_precision / n:.4f}")
    print(f"Average Context Recall:     {total_recall / n:.4f}")

if __name__ == "__main__":
    main()
