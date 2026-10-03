import json
from pathlib import Path
from app.repository_analyzer import RepositoryAnalyzer

def test_repository_analyzer(tmp_path):
    (tmp_path / "a.py").write_text("def run():\n    return foo()")
    (tmp_path / "b.py").write_text("from a import run")
    
    analyzer = RepositoryAnalyzer(str(tmp_path))
    res = analyzer.analyze()
    
    assert res["repository"] == tmp_path.name
    assert res["python_files"] == 2
    
    files = res["files"]
    assert "a.py" in files
    assert "b.py" in files
    
    assert "run" in files["a.py"]["functions"]
    assert "foo" in files["a.py"]["functions"]["run"]["calls"]
    
    assert "a.py" in files["b.py"]["dependencies"]
