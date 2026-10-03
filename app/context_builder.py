import json
from pathlib import Path
from collections import defaultdict
from app.dependency_analyzer import trace_dependencies

class ContextBuilder:
    def __init__(
        self,
        codebase_map_path: str = None,
        code_index_path: str = None,
        max_budget: int = 24000
    ):
        self.codebase_map = {}
        self.code_units_by_path = {}
        self.max_budget = max_budget
        
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

    def _get_dependency_graph(self) -> dict[str, list[str]]:
        return {p: info.get("dependencies", []) for p, info in self.codebase_map.items()}

    def build(
        self,
        query: str,
        results: list[dict],
        depth: int = 1,
    ) -> str:
        """
        Build a clean context block from retrieved code units,
        augmented with dependency graph metadata up to a character budget.
        """
        sections = [f"Developer question:\n{query}\n", "Relevant code:\n"]
        current_len = sum(len(s) for s in sections)
        
        primary_paths = set()
        referenced_names = set()
        dep_reference_counts = defaultdict(int)
        
        graph = self._get_dependency_graph()

        # Phase 1: Primary Results
        for index, result in enumerate(results, start=1):
            path = result["path"]
            primary_paths.add(path)
            
            unit_text = [
                f"--- Code Unit {index} ---",
                f"File: {path}",
                f"Type: {result['type']}",
                f"Name: {result['name']}",
            ]
            
            file_info = self.codebase_map.get(path, {})
            
            if result['type'] == 'function':
                func_info = file_info.get("functions", {}).get(result['name'], {})
                if func_info.get("calls"):
                    unit_text.append(f"Function Calls: {', '.join(func_info['calls'])}")
                    for call in func_info["calls"]:
                        referenced_names.add(call.split(".")[0])
                        
            for binding in file_info.get("import_bindings", []):
                name = binding.get("name")
                if name and name != "*":
                    referenced_names.add(name)
                    
            unit_text.extend(["", result["source"], ""])
            text_block = "\n".join(unit_text)
            
            if current_len + len(text_block) > self.max_budget:
                sections.append("[Omitted some primary units for budget]")
                break
                
            sections.append(text_block)
            current_len += len(text_block)
            
            # Trace dependencies
            deps = trace_dependencies(graph, path, max_depth=depth)
            for dep_path in deps:
                if dep_path != path:
                    dep_reference_counts[dep_path] += 1

        # Phase 2: Dependency Context
        if dep_reference_counts:
            sorted_deps = sorted(
                dep_reference_counts.keys(),
                key=lambda d: dep_reference_counts[d],
                reverse=True
            )
            
            sections.append("Dependency Context:\n")
            deps_omitted = 0
            
            for dep_path in sorted_deps:
                if dep_path in primary_paths:
                    continue
                    
                original_units = self.code_units_by_path.get(dep_path, [])
                if not original_units:
                    continue
                    
                units_to_inject = original_units
                if referenced_names:
                    filtered = [
                        u for u in original_units 
                        if u["name"] in referenced_names 
                        or u["name"].split(".")[0] in referenced_names
                    ]
                    if filtered:
                        units_to_inject = filtered
                        
                dep_block = [f"--- Dependency Source: {dep_path} ---"]
                for u in units_to_inject:
                    dep_block.append(f"Type: {u['type']} | Name: {u['name']}")
                    dep_block.append(u["source"])
                dep_block.append("")
                
                text_block = "\n".join(dep_block)
                if current_len + len(text_block) > self.max_budget:
                    deps_omitted += 1
                else:
                    sections.append(text_block)
                    current_len += len(text_block)
                    
            if deps_omitted > 0:
                sections.append(f"[{deps_omitted} dependency units omitted for budget]")

        return "\n".join(sections)