from pathlib import Path

from app.code_parser import parse_python_file
from app.constants import get_python_files

def resolve_import(
    repository_root: str,
    module_name: str,
) -> str | None:
    """
    Resolve a Python module name to a file inside the repository.
    """
    
    root = Path(repository_root).resolve()
    
    # Convert Python module notation to a filesystem path.
    module_path = Path(*module_name.split("."))
    
    # First try: normal Python file
    python_file = root / f"{module_path}.py"
    
    if python_file.is_file():
        return python_file.relative_to(root).as_posix()
    
    # Second try: Python package
    package_init = root / module_path / "__init__.py"
    
    if package_init.is_file():
        return package_init.relative_to(root).as_posix()
    
    return None

def analyze_dependencies(
    repository_root: str,
    relative_file_path: str,
) -> dict:
    """
    Analyze a Python file and resolve its internal dependencies.
    """
    
    root = Path(repository_root).resolve()
    file_path = root / relative_file_path
    
    parsed = parse_python_file(str(file_path))
    
    dependencies = []
    
    for module in parsed["imports"]:
        resolved = resolve_import(
            repository_root,
            module,
        )
        
        if resolved is not None:
            dependencies.append(
                {
                    "module": module,
                    "file": resolved
                }
            )
    
    return {
        "file": relative_file_path,
        "functions": parsed["functions"],
        "classes": parsed["classes"],
        "internal_dependencies": dependencies,
    }
    
def build_dependency_graph(repository_root: str) -> dict[str,list[str]]:
    """
    Build a dependency graph for all Python files in the repository.
    """
    
    root = Path(repository_root).resolve()
    graph = {}
    
    for path in get_python_files(root):
        
        relative_path = path.relative_to(root).as_posix()
        
        analysis = analyze_dependencies(
            repository_root,
            relative_path
        )
        
        graph[relative_path] = [
            dependency["file"]
            for dependency in analysis["internal_dependencies"]
        ]
        
    return graph

def trace_dependencies(
    graph: dict[str, list[str]],
    start_file: str,
    max_depth: int = 5,
) -> list[str]:
    """
    Follow internal dependencies starting from one file.
    """

    visited = set()
    result = []

    def visit(file: str, depth: int) -> None:
        if depth > max_depth:
            return

        if file in visited:
            return

        visited.add(file)
        result.append(file)

        for dependency in graph.get(file, []):
            visit(dependency, depth + 1)

    visit(start_file, 0)

    return result