from pathlib import Path

from app.code_parser import parse_python_file
from app.constants import get_python_files

def resolve_import(
    repository_root: str,
    importing_file: str,
    binding: dict,
) -> str | None:
    """
    Resolve an import binding to a file inside the repository.
    Handles relative imports, submodule imports (from app import foo -> app/foo.py),
    and src/ layouts. Only returns paths for files that exist in the repo.
    """
    root = Path(repository_root).resolve()
    importer = root / importing_file
    
    level = binding.get("level", 0)
    module_name = binding.get("module", "")
    imported_name = binding.get("name", "")

    # Base path for resolution
    if level > 0:
        base = importer.parent
        for _ in range(level - 1):
            base = base.parent
    else:
        base = root
    
    bases_to_try = [base]
    if level == 0 and (root / "src").is_dir():
        bases_to_try.append(root / "src")

    module_parts = module_name.split(".") if module_name else []
    
    for b in bases_to_try:
        # Try `module.name` as a submodule first
        if imported_name and imported_name != "*":
            parts_with_name = module_parts + [imported_name]
            
            # 1. As a python file
            py_file = b.joinpath(*parts_with_name).with_suffix(".py")
            if py_file.is_file():
                return py_file.relative_to(root).as_posix()
            
            # 2. As a package init
            pkg_init = b.joinpath(*parts_with_name, "__init__.py")
            if pkg_init.is_file():
                return pkg_init.relative_to(root).as_posix()
                
        # Fallback to just the `module`
        if module_parts:
            # 3. As a python file
            py_file = b.joinpath(*module_parts).with_suffix(".py")
            if py_file.is_file():
                return py_file.relative_to(root).as_posix()
            
            # 4. As a package init
            pkg_init = b.joinpath(*module_parts, "__init__.py")
            if pkg_init.is_file():
                return pkg_init.relative_to(root).as_posix()
            
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
    seen = set()
    
    for binding in parsed.get("import_bindings", []):
        resolved = resolve_import(
            repository_root,
            relative_file_path,
            binding,
        )
        
        if resolved is not None and resolved not in seen:
            seen.add(resolved)
            dependencies.append(
                {
                    "module": binding["module"] or "",
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
        analysis = analyze_dependencies(repository_root, relative_path)
        
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