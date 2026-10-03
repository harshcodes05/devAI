import ast
from pathlib import Path

class StructureVisitor(ast.NodeVisitor):
    def __init__(self):
        self.scope = []
        self.functions = []
        self.classes = []
        self.imports = []
        self.import_bindings = []

    def visit_ClassDef(self, node):
        self.classes.append(".".join(self.scope + [node.name]))
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _visit_func(self, node):
        qual_name = ".".join(self.scope + [node.name])
        self.functions.append(qual_name)
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_func(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
            self.import_bindings.append({
                "module": alias.name,
                "name": alias.name.split(".")[-1],
                "alias": alias.asname,
                "level": 0,
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        level = getattr(node, "level", 0)
        module = node.module or ""
        if module:
            self.imports.append(f"{'.' * level}{module}" if level > 0 else module)

        for alias in node.names:
            self.import_bindings.append({
                "module": module,
                "name": alias.name,
                "alias": alias.asname,
                "level": level,
            })
        self.generic_visit(node)

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

    visitor = StructureVisitor()
    visitor.visit(tree)

    return {
        "path": str(path),
        "functions": sorted(set(visitor.functions)),
        "classes": sorted(set(visitor.classes)),
        "imports": sorted(set(visitor.imports)),
        "import_bindings": visitor.import_bindings,
        "error": None,
    }