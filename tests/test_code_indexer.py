from pathlib import Path

from app.code_indexer import CodeIndexer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_PATH = PROJECT_ROOT.parent / "financial_sentinel_old"
OUTPUT_PATH = PROJECT_ROOT / "data" / "code_index.json"


indexer = CodeIndexer(
    str(REPOSITORY_PATH)
)

indexer.save_index(
    str(OUTPUT_PATH)
)