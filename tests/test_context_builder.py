import json
import pytest
from app.context_builder import ContextBuilder

def setup_files(tmp_path):
    codebase_map = {
        "files": {
            "app/main.py": {
                "dependencies": ["app/model.py", "app/utils.py"],
                "import_bindings": [{"name": "predict"}, {"name": "helper"}],
                "functions": {
                    "run": {"calls": ["predict", "helper"]}
                }
            },
            "app/other.py": {
                "dependencies": ["app/model.py"],
                "import_bindings": [{"name": "predict"}],
                "functions": {}
            }
        }
    }
    map_file = tmp_path / "codebase_map.json"
    map_file.write_text(json.dumps(codebase_map))

    code_index = [
        {"path": "app/model.py", "type": "function", "name": "predict", "source": "def predict(): pass"},
        {"path": "app/model.py", "type": "function", "name": "unused", "source": "def unused(): pass"},
        {"path": "app/utils.py", "type": "function", "name": "helper", "source": "def helper(): pass"},
        {"path": "app/utils.py", "type": "function", "name": "long", "source": "A" * 5000}
    ]
    index_file = tmp_path / "code_index.json"
    index_file.write_text(json.dumps(code_index))

    return str(map_file), str(index_file)

def test_dedup_and_ordering(tmp_path):
    map_file, index_file = setup_files(tmp_path)
    builder = ContextBuilder(map_file, index_file)
    
    results = [
        {"path": "app/main.py", "type": "function", "name": "run", "source": "def run(): pass"},
        {"path": "app/other.py", "type": "function", "name": "run2", "source": "def run2(): pass"}
    ]
    
    ctx = builder.build("Q", results)
    
    # 1. Primary first
    assert ctx.find("app/main.py") < ctx.find("Dependency Context:")
    assert ctx.find("app/other.py") < ctx.find("Dependency Context:")
    
    # 2. Dedup: model.py is depended on by both, but only injected once
    assert ctx.count("Dependency Source: app/model.py") == 1
    
    # 3. Referenced only: predict and helper are injected, unused is NOT injected
    assert "def predict(): pass" in ctx
    assert "def helper(): pass" in ctx
    assert "def unused(): pass" not in ctx

def test_budget_truncation(tmp_path):
    map_file, index_file = setup_files(tmp_path)
    
    # Set a tiny budget so dependencies get truncated
    builder = ContextBuilder(map_file, index_file, max_budget=200)
    
    results = [
        {"path": "app/main.py", "type": "function", "name": "run", "source": "def run(): pass"}
    ]
    
    ctx = builder.build("Q", results)
    assert "omitted for budget" in ctx
    assert "Dependency Source" not in ctx # should have been omitted

def test_context_builder_depth(tmp_path):
    # Setup chain: main -> mid -> leaf
    codebase_map = {
        "files": {
            "app/main.py": {
                "dependencies": ["app/mid.py"],
            },
            "app/mid.py": {
                "dependencies": ["app/leaf.py"],
            }
        }
    }
    map_file = tmp_path / "codebase_map.json"
    map_file.write_text(json.dumps(codebase_map))

    code_index = [
        {"path": "app/mid.py", "type": "function", "name": "mid_func", "source": "mid"},
        {"path": "app/leaf.py", "type": "function", "name": "leaf_func", "source": "leaf"}
    ]
    index_file = tmp_path / "code_index.json"
    index_file.write_text(json.dumps(code_index))

    builder = ContextBuilder(str(map_file), str(index_file))
    
    results = [
        {"path": "app/main.py", "type": "function", "name": "run", "source": "run"}
    ]
    
    # Depth 1: should include mid.py, but NOT leaf.py
    ctx1 = builder.build("Q", results, depth=1)
    assert "Dependency Source: app/mid.py" in ctx1
    assert "Dependency Source: app/leaf.py" not in ctx1
    
    # Depth 2: should include both mid.py and leaf.py
    ctx2 = builder.build("Q", results, depth=2)
    assert "Dependency Source: app/mid.py" in ctx2
    assert "Dependency Source: app/leaf.py" in ctx2
