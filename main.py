import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

CODE_INDEX_PATH = DATA_DIR / "code_index.json"
SEMANTIC_INDEX_PATH = DATA_DIR / "semantic_index.json"
CODEBASE_MAP_PATH = DATA_DIR / "codebase_map.json"


def index_repository(repo_path: str) -> None:
    """Index a repository: parse code units, then generate embeddings."""

    from app.code_indexer import CodeIndexer
    from app.embedding_indexer import EmbeddingIndexer

    print(f"Indexing repository: {repo_path}\n")

    # Step 1: Build the code index
    print("[1/3] Building code index...")
    indexer = CodeIndexer(repo_path)
    indexer.save_index(str(CODE_INDEX_PATH))

    # Step 2: Build the semantic index
    print("[2/3] Building semantic index (this calls the Gemini API)...")
    embedding_indexer = EmbeddingIndexer(
        str(CODE_INDEX_PATH),
        str(SEMANTIC_INDEX_PATH),
    )
    embedding_indexer.save()

    # Step 3: Build the codebase map (dependency graph)
    from app.repository_analyzer import RepositoryAnalyzer
    print("[3/3] Building codebase map (dependency graph)...")
    analyzer = RepositoryAnalyzer(repo_path)
    analyzer.save_map(str(CODEBASE_MAP_PATH))

    print("\nDone! Repository indexed successfully.")


def ask_question(
    question: str,
    mode: str = "semantic",
    top_k: int = 5,
) -> None:
    """Retrieve relevant code and answer a question using the LLM."""

    from app.context_builder import ContextBuilder
    from app.llm_service import LLMService

    # Choose retriever based on mode
    if mode == "semantic":
        from app.semantic_retriever import SemanticRetriever

        if not SEMANTIC_INDEX_PATH.exists():
            print("Error: Semantic index not found. Run 'index' first.")
            sys.exit(1)

        retriever = SemanticRetriever(str(SEMANTIC_INDEX_PATH))

    elif mode == "keyword":
        from app.retriever import CodeRetriever

        if not CODE_INDEX_PATH.exists():
            print("Error: Code index not found. Run 'index' first.")
            sys.exit(1)

        retriever = CodeRetriever(str(CODE_INDEX_PATH))

    else:
        print(f"Error: Unknown mode '{mode}'. Use 'semantic' or 'keyword'.")
        sys.exit(1)

    # Retrieve relevant code
    print(f"Searching ({mode} mode)...\n")
    results = retriever.search(question, top_k=top_k)

    if not results:
        print("No relevant code found.")
        return

    # Build context and get LLM answer
    builder = ContextBuilder(
        codebase_map_path=str(CODEBASE_MAP_PATH),
        code_index_path=str(CODE_INDEX_PATH),
    )
    context = builder.build(question, results)

    llm = LLMService()
    answer = llm.answer(question, context)

    print("ANSWER:\n")
    print(answer)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DevAI — AI-powered codebase assistant",
    )

    subparsers = parser.add_subparsers(dest="command")

    # index command
    index_parser = subparsers.add_parser(
        "index",
        help="Index a repository for code search",
    )
    index_parser.add_argument(
        "repo_path",
        help="Path to the repository to index",
    )

    # ask command
    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask a question about the indexed codebase",
    )
    ask_parser.add_argument(
        "question",
        help="Your question about the codebase",
    )
    ask_parser.add_argument(
        "--mode",
        choices=["semantic", "keyword"],
        default="semantic",
        help="Retrieval mode (default: semantic)",
    )
    ask_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of code units to retrieve (default: 5)",
    )

    args = parser.parse_args()

    if args.command == "index":
        index_repository(args.repo_path)

    elif args.command == "ask":
        ask_question(
            args.question,
            mode=args.mode,
            top_k=args.top_k,
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
