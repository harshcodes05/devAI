from pathlib import Path

from app.repository_analyzer import RepositoryAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPOSITORY_PATH = PROJECT_ROOT.parent / "financial_sentinel_old"
OUTPUT_PATH = PROJECT_ROOT / "data" / "codebase_map.json"


analyzer = RepositoryAnalyzer(
    str(REPOSITORY_PATH)
)

analyzer.save_map(
    str(OUTPUT_PATH)
)