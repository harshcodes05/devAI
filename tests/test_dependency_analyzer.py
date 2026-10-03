import pytest
from pathlib import Path
from app.dependency_analyzer import analyze_dependencies

def test_analyze_dependencies_imports(tmp_path):
    # Setup fixture repo
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text("")
    (tmp_path / "app" / "foo.py").write_text("def foo(): pass")
    
    (tmp_path / "app" / "sub").mkdir()
    (tmp_path / "app" / "sub" / "__init__.py").write_text("")
    (tmp_path / "app" / "sub" / "bar.py").write_text("def bar(): pass")
    
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "pkg").mkdir()
    (tmp_path / "src" / "pkg" / "__init__.py").write_text("")
    (tmp_path / "src" / "pkg" / "helper.py").write_text("def h(): pass")
    
    # File doing the importing
    test_file = tmp_path / "app" / "sub" / "importer.py"
    test_file.write_text("""
import sys # unresolved third-party
from app import foo # absolute, submodule
from app import sub # package __init__
from . import bar # relative level 1
from .. import foo as f2 # relative level 2
from pkg import helper # src layout
    """)
    
    res = analyze_dependencies(str(tmp_path), "app/sub/importer.py")
    files = {d["file"] for d in res["internal_dependencies"]}
    
    assert "app/foo.py" in files
    assert "app/sub/bar.py" in files
    assert "src/pkg/helper.py" in files
    assert "app/sub/__init__.py" in files
    
    # third-party should not be captured since it's not in repo
    assert not any("sys" in f for f in files)
