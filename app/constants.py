from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
}


def get_python_files(root: Path) -> list[Path]:
    """Find all relevant Python files under a repository root."""

    files = []

    for path in root.rglob("*.py"):
        if any(
            part in IGNORED_DIRECTORIES
            for part in path.parts
        ):
            continue

        files.append(path)

    return sorted(files)
