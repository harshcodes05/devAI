import pytest
from pathlib import Path
from app.code_parser import parse_python_file

def test_parse_python_file(tmp_path):
    # Create a dummy python file
    dummy_code = """
import os
from pathlib import Path

class TestClass:
    def method_one(self):
        pass

def standalone_func():
    pass
"""
    test_file = tmp_path / "dummy.py"
    test_file.write_text(dummy_code, encoding="utf-8")

    result = parse_python_file(str(test_file))

    assert result["error"] is None
    assert "standalone_func" in result["functions"]
    assert "TestClass" in result["classes"]
    assert "os" in result["imports"]
    assert "pathlib" in result["imports"]

def test_parse_invalid_python_file(tmp_path):
    # Syntax error
    test_file = tmp_path / "invalid.py"
    test_file.write_text("def class broken syntax", encoding="utf-8")

    result = parse_python_file(str(test_file))
    
    assert result["error"] is not None
    assert "invalid syntax" in result["error"].lower()
