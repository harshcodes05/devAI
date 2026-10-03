import pytest
from google.genai import errors
from app.embedding_service import EmbeddingService, MAX_CHARS

class FakeEmbedding:
    def __init__(self, values):
        self.values = values

class FakeResult:
    def __init__(self, values_list):
        self.embeddings = [FakeEmbedding(v) for v in values_list]

class FakeModels:
    def __init__(self):
        self.calls = []
        self.error_to_raise = None
    
    def embed_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error_to_raise:
            raise self.error_to_raise
        
        contents = kwargs.get("contents")
        if isinstance(contents, str):
            return FakeResult([[0.1, 0.2]])
        elif isinstance(contents, list):
            return FakeResult([[0.1, 0.2] for _ in contents])

class FakeClient:
    def __init__(self):
        self.models = FakeModels()

class MockAPIError(errors.APIError):
    def __init__(self, message, code):
        Exception.__init__(self, message)
        self.code = code
        self.status_code = code
        self._message = message
        
    def __str__(self):
        return self._message

def test_embed_query_task_type():
    client = FakeClient()
    service = EmbeddingService(client=client)
    res = service.embed("Test")
    assert res == [0.1, 0.2]
    
    call_args = client.models.calls[0]
    assert call_args["config"].task_type == "RETRIEVAL_QUERY"
    assert call_args["contents"] == "Test"

def test_embed_documents_batching():
    client = FakeClient()
    service = EmbeddingService(client=client)
    
    texts = ["Test"] * 250
    res = service.embed_documents(texts)
    
    assert len(res) == 250
    assert len(client.models.calls) == 3
    assert client.models.calls[0]["config"].task_type == "RETRIEVAL_DOCUMENT"

def test_embed_truncation():
    client = FakeClient()
    service = EmbeddingService(client=client)
    
    long_text = "A" * (MAX_CHARS + 500)
    service.embed(long_text)
    
    call_args = client.models.calls[0]
    assert len(call_args["contents"]) == MAX_CHARS

def test_embed_auth_error():
    client = FakeClient()
    client.models.error_to_raise = MockAPIError("Auth error", 401)
    service = EmbeddingService(client=client)
    with pytest.raises(Exception) as excinfo:
        service.embed("test")
    assert "GEMINI_API_KEY" in str(excinfo.value)
