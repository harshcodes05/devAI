import json
from pathlib import Path

class ContextBuilder:
    def __init__(self, codebase_map_path: str = None, code_index_path: str = None):
        self.codebase_map = {}
        self.code_units_by_path = {}
        
        if codebase_map_path:
            path = Path(codebase_map_path)
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.codebase_map = data.get("files", {})
                    
        if code_index_path:
            path = Path(code_index_path)
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    units = json.load(f)
                    for unit in units:
                        p = unit["path"]
                        if p not in self.code_units_by_path:
                            self.code_units_by_path[p] = []
                        self.code_units_by_path[p].append(unit)

    def build(
        self,
        query: str,
        results: list[dict],
    ) -> str:
        """
        Build a clean context block from retrieved code units,
        augmented with dependency graph metadata.
        """

        sections = [
            f"Developer question:\n{query}",
            "",
            "Relevant code:",
        ]

        for index, result in enumerate(results, start=1):
            sections.extend(
                [
                    "",
                    f"--- Code Unit {index} ---",
                    f"File: {result['path']}",
                    f"Type: {result['type']}",
                    f"Name: {result['name']}",
                ]
            )

            # Inject V2 Dependency Graph Metadata
            file_info = self.codebase_map.get(result['path'])
            if file_info:
                if file_info.get("dependencies"):
                    deps = ", ".join(file_info["dependencies"])
                    sections.append(f"File Dependencies: {deps}")
                
                if result['type'] == 'function':
                    func_info = file_info.get("functions", {}).get(result['name'])
                    if func_info and func_info.get("calls"):
                        calls = ", ".join(func_info["calls"])
                        sections.append(f"Function Calls: {calls}")

                # Follow 1-hop internal dependencies and inject source
                if file_info.get("dependencies"):
                    for dep_path in file_info["dependencies"]:
                        if dep_path in self.code_units_by_path:
                            sections.append(f"\n--- 1-Hop Dependency Source: {dep_path} ---")
                            for dep_unit in self.code_units_by_path[dep_path]:
                                sections.append(f"Type: {dep_unit['type']} | Name: {dep_unit['name']}")
                                sections.append(dep_unit["source"])
                                sections.append("")

            sections.extend(
                [
                    "",
                    result["source"],
                ]
            )

        return "\n".join(sections)