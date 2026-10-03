from pathlib import Path
from app.constants import get_python_files

def test_get_python_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("")
    
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "bad.py").write_text("")
    
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "bad.py").write_text("")
    
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "bad.py").write_text("")
    
    files = list(get_python_files(tmp_path))
    paths = [f.name for f in files]
    
    assert "main.py" in paths
    assert "bad.py" not in paths
