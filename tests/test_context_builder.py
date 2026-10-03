import pytest
from app.context_builder import ContextBuilder

def test_context_builder():
    builder = ContextBuilder()
    
    query = "How does login work?"
    results = [
        {
            "path": "app/auth.py",
            "type": "function",
            "name": "login",
            "source": "def login(): return True"
        }
    ]
    
    context = builder.build(query, results)
    
    assert "Developer question" in context
    assert "How does login work?" in context
    assert "Code Unit 1" in context
    assert "File: app/auth.py" in context
    assert "def login(): return True" in context

def test_context_builder_with_dependencies(tmp_path):
    import json
    
    # Mock codebase_map.json
    codebase_map = {
        "files": {
            "app/predict.py": {
                "dependencies": ["app/model.py"],
                "functions": {
                    "run_predict": {"calls": ["predict"]}
                }
            }
        }
    }
    map_file = tmp_path / "codebase_map.json"
    map_file.write_text(json.dumps(codebase_map))

    # Mock code_index.json
    code_index = [
        {
            "path": "app/model.py",
            "type": "function",
            "name": "predict",
            "source": "def predict(): return 1"
        }
    ]
    index_file = tmp_path / "code_index.json"
    index_file.write_text(json.dumps(code_index))

    builder = ContextBuilder(str(map_file), str(index_file))
    
    results = [{
        "path": "app/predict.py",
        "type": "function",
        "name": "run_predict",
        "source": "def run_predict(): return predict()"
    }]
    
    context = builder.build("Run predict?", results)
    
    # Assert metadata
    assert "File Dependencies: app/model.py" in context
    assert "Function Calls: predict" in context
    
    # Assert 1-hop source code injection
    assert "--- 1-Hop Dependency Source: app/model.py ---" in context
    assert "def predict(): return 1" in context
