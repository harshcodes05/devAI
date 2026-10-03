import ast
from pathlib import Path

def _get_call_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    elif isinstance(func, ast.Attribute):
        parts = []
        current = func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return None

def extract_all_function_calls(file_path: str) -> dict[str, list[str]]:
    """
    Extract all function and method calls for every function in the file in a single pass.
    Keys are fully qualified function names.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    calls_by_func = {}

    class CallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.scope = []

        def visit_ClassDef(self, node):
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def _visit_func(self, node):
            qual_name = ".".join(self.scope + [node.name])
            self.scope.append(node.name)
            
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    cname = _get_call_name(child)
                    if cname:
                        calls.append(cname)
                        
            calls_by_func[qual_name] = sorted(set(calls))
            
            self.generic_visit(node)
            self.scope.pop()

        def visit_FunctionDef(self, node):
            self._visit_func(node)

        def visit_AsyncFunctionDef(self, node):
            self._visit_func(node)

    CallVisitor().visit(tree)
    return calls_by_func

def extract_function_calls(
    file_path: str,
    function_name: str,
) -> list[str]:
    """
    Extract function and method calls made inside one function (Backwards compatible).
    """
    calls = extract_all_function_calls(file_path).get(function_name)
    if calls is None:
        raise ValueError(f"Function '{function_name}' not found.")
    return calls