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
