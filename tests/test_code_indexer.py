import json
from pathlib import Path
from app.code_indexer import CodeIndexer

def test_code_indexer_syntax_error(tmp_path):
    (tmp_path / "good.py").write_text("def run(): pass")
    (tmp_path / "bad.py").write_text("def broken syntax")
    
    idx_path = tmp_path / "idx.json"
    indexer = CodeIndexer(str(tmp_path))
    indexer.save_index(str(idx_path))
    
    data = json.loads(idx_path.read_text())
    
    names = [d.get("name") for d in data]
    assert "run" in names
