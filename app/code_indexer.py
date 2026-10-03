import ast
from pathlib import Path

from app.constants import get_python_files


class CodeIndexer:
    def __init__(self, repository_root: str):
        self.root = Path(repository_root).resolve()

    def get_python_files(self) -> list[Path]:
        """Find all relevant Python files."""

        return get_python_files(self.root)

    def index_file(self, path: Path) -> list[dict]:
        """Extract classes and functions from one Python file."""

        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        lines = source.splitlines()

        relative_path = path.relative_to(
            self.root
        ).as_posix()

        units = []

        for node in ast.walk(tree):

            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                start = node.lineno - 1
                end = node.end_lineno

                units.append(
                    {
                        "path": relative_path,
                        "type": "function",
                        "name": node.name,
                        "source": "\n".join(
                            lines[start:end]
                        ),
                    }
                )

            elif isinstance(node, ast.ClassDef):
                start = node.lineno - 1
                end = node.end_lineno

                units.append(
                    {
                        "path": relative_path,
                        "type": "class",
                        "name": node.name,
                        "source": "\n".join(
                            lines[start:end]
                        ),
                    }
                )

        return units

    def build_index(self) -> list[dict]:
        """Build code units for the entire repository."""

        units = []

        for path in self.get_python_files():
            units.extend(
                self.index_file(path)
            )

        return units
    
    def save_index(self, output_path: str) -> None:
        """Build the code index and save it as JSON."""

        import json

        units = self.build_index()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w", encoding="utf-8") as file:
            json.dump(units, file, indent=2)

        print(f"Code index saved to: {output_file}")