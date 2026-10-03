import json
from app.retriever import CodeRetriever

def test_keyword_retriever(tmp_path):
    idx = tmp_path / "idx.json"
    idx.write_text(json.dumps([
        {"path": "a.py", "type": "function", "name": "foo", "source": "def foo(): pass"},
        {"path": "b.py", "type": "function", "name": "bar", "source": "def bar(): pass"}
    ]))
    
    ret = CodeRetriever(str(idx))
    res = ret.search("foo", top_k=5)
    
    assert len(res) > 0
    assert res[0]["name"] == "foo"

def test_keyword_retriever_empty(tmp_path):
    idx = tmp_path / "idx.json"
    idx.write_text("[]")
    
    ret = CodeRetriever(str(idx))
    res = ret.search("foo", top_k=5)
    
    assert len(res) == 0
