import ast
from pathlib import Path


def parse_python_file(file_path: str) -> dict:
    """
    Parse a Python file and extract its structure and imports.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    if path.suffix.lower() != ".py":
        raise ValueError("Only Python files are supported.")

    content = path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(content)
    except SyntaxError as error:
        return {
            "path": str(path),
            "functions": [],
            "classes": [],
            "imports": [],
            "import_bindings": [],
            "error": str(error),
        }

    functions = []
    classes = []
    imports = []
    import_bindings = []

    for node in ast.walk(tree):

        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            functions.append(node.name)

        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

                import_bindings.append(
                    {
                        "module": alias.name,
                        "name": alias.name.split(".")[-1],
                        "alias": alias.asname,
                    }
                )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

                for alias in node.names:
                    import_bindings.append(
                        {
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname,
                        }
                    )

    return {
        "path": str(path),
        "functions": sorted(set(functions)),
        "classes": sorted(set(classes)),
        "imports": sorted(set(imports)),
        "import_bindings": import_bindings,
        "error": None,
    }