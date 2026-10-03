from pathlib import Path

from app.code_parser import parse_python_file
from app.dependency_analyzer import resolve_import
from app.call_analyzer import extract_all_function_calls
from app.constants import get_python_files


class RepositoryAnalyzer:
    def __init__(self, repository_root: str):
        self.root = Path(repository_root).resolve()

    def get_python_files(self) -> list[Path]:
        """Return all relevant Python files in the repository."""

        return get_python_files(self.root)

    def analyze_file(self, path: Path) -> dict:
        """Analyze one Python file."""

        relative_path = path.relative_to(self.root).as_posix()

        parsed = parse_python_file(str(path))

        dependencies = []

        for binding in parsed.get("import_bindings", []):
            resolved = resolve_import(
                str(self.root),
                relative_path,
                binding,
            )

            if resolved is not None:
                dependencies.append(resolved)

        functions = {}
        
        try:
            all_calls = extract_all_function_calls(str(path))
        except (SyntaxError, ValueError):
            all_calls = {}

        for function_name in parsed["functions"]:
            functions[function_name] = {
                "calls": all_calls.get(function_name, []),
            }

        return {
            "path": relative_path,
            "classes": parsed["classes"],
            "imports": parsed["imports"],
            "import_bindings": parsed.get("import_bindings", []),
            "dependencies": sorted(set(dependencies)),
            "functions": functions,
        }

    def analyze(self) -> dict:
        """Build the complete repository map."""

        files = {}

        for path in self.get_python_files():
            relative_path = path.relative_to(self.root).as_posix()

            files[relative_path] = self.analyze_file(path)

        return {
            "repository": self.root.name,
            "python_files": len(files),
            "files": files,
        }
        
    def save_map(self, output_path: str) -> None:
        """Analyze the repository and save the result as JSON."""

        import json

        result = self.analyze()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w", encoding="utf-8") as file:
            json.dump(result, file, indent=2)

        print(f"Codebase map saved to: {output_file}")