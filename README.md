# DevAI

DevAI is an AI-powered Developer Intelligence System that understands a software repository, retrieves relevant implementation context, analyzes file-level dependencies, and assists developers with codebase understanding.

## Features (V2: Dependency-Aware RAG)
- **Zero-Bloat RAG Engine**: Pure Python, native AST traversal, and direct LLM calls without heavy abstractions.
- **1-Hop Dependency-Aware Context**: Parses Python AST to build a directed graph of file dependencies. When retrieving context, it pulls in 1-hop file dependencies and injects their source code, providing file-level context along with function-call metadata.
- **Semantic + Keyword Retrieval**: Supports both keyword-based and semantic (embedding-based) search strategies.
- **Powered by Gemini**: Uses `gemini-embedding-2` for 3072-dimension vectors and `gemini-3.7-flash` for high-context reasoning.

## Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # On Windows
   source .venv/bin/activate      # On Mac/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup environment variables:
   Create a `.env` file in the project root with your Gemini API key:
   ```env
   GEMINI_API_KEY=your_real_key_here
   ```

## Usage

DevAI provides a CLI via `main.py` with two primary commands: `index` and `ask`.

### 1. Index a Repository
Point DevAI at any local Python repository. It will parse the codebase, extract AST structural units, build a dependency graph, and generate semantic embeddings.

```bash
python main.py index "C:\path\to\your\repository"
```

*Note: This will create `data/code_index.json`, `data/semantic_index.json`, and `data/codebase_map.json`.*

### 2. Ask a Question
Once indexed, you can ask structural or behavioral questions about the codebase.

```bash
python main.py ask "How does fraud prediction work?"
```

**Options:**
- `--mode semantic` (default) or `--mode keyword`
- `--top-k 5` (number of primary code chunks to retrieve before pulling dependencies)

Example:
```bash
python main.py ask "Why would the /predict endpoint return 500?" --mode semantic --top-k 3
```

## Architecture
- **Parse & Index**: Natively walks `.py` files and uses Python's `ast` module to extract classes and functions.
- **Dependency Mapping**: Builds a graph of internal file dependencies and intra-function call chains.
- **Embeddings**: Vectorizes the code using Gemini's embedding model.
- **Retrieve**: Retrieves top vector matches, looks them up in the dependency graph, and pulls in 1-hop dependent source code.
- **Reasoning**: Feeds the augmented file context to Gemini 3.7 Flash for an evidence-backed explanation.
