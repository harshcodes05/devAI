import ast
from pathlib import Path


def extract_function_calls(
    file_path: str,
    function_name: str,
) -> list[str]:
    """
    Extract function and method calls made inside one function.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {file_path}"
        )

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    target_function = None

    for node in ast.walk(tree):
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            if node.name == function_name:
                target_function = node
                break

    if target_function is None:
        raise ValueError(
            f"Function '{function_name}' not found."
        )

    calls = []

    for node in ast.walk(target_function):

        if not isinstance(node, ast.Call):
            continue

        call = node.func

        if isinstance(call, ast.Name):
            calls.append(call.id)

        elif isinstance(call, ast.Attribute):
            parts = []

            current = call

            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value

            if isinstance(current, ast.Name):
                parts.append(current.id)

            calls.append(".".join(reversed(parts)))

    return sorted(set(calls))