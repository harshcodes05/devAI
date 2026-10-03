import pytest
from pathlib import Path
from app.call_analyzer import extract_all_function_calls, extract_function_calls
from app.code_parser import parse_python_file

def test_qualified_names(tmp_path):
    test_file = tmp_path / "test_calls.py"
    test_file.write_text("""
@decorator
def outer():
    def inner():
        return foo()
    return inner()

class A:
    def run(self):
        return bar()

class B:
    def run(self):
        return baz()

async def fetch():
    return await req()
    """)
    
    # 1. Test Code Parser captures qualified names
    parsed = parse_python_file(str(test_file))
    funcs = parsed["functions"]
    assert "outer" in funcs
    assert "outer.inner" in funcs
    assert "A.run" in funcs
    assert "B.run" in funcs
    assert "fetch" in funcs
    
    # 2. Test Call Analyzer correctly associates calls with qualified names
    calls = extract_all_function_calls(str(test_file))
    assert "inner" in calls["outer"]
    assert "foo" in calls["outer.inner"]
    assert "bar" in calls["A.run"]
    assert "baz" in calls["B.run"]
    assert "req" in calls["fetch"]
    
    # 3. Test backwards compatibility function
    assert extract_function_calls(str(test_file), "B.run") == ["baz"]
