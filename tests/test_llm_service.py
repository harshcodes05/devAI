import pytest
from unittest.mock import patch, MagicMock
from google.genai import errors
from app.llm_service import LLMService

class FakeResponse:
    def __init__(self, text):
        self.text = text

class FakeModels:
    def __init__(self):
        self.generate_content_calls = 0
        self.error_to_raise = None
        self.return_val = FakeResponse("Success")

    def generate_content(self, model, contents):
        self.generate_content_calls += 1
        if self.error_to_raise:
            if isinstance(self.error_to_raise, list):
                if self.generate_content_calls <= len(self.error_to_raise):
                    err = self.error_to_raise[self.generate_content_calls - 1]
                    if err:
                        raise err
            else:
                raise self.error_to_raise
        return self.return_val

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

def create_mock_api_error(message, code):
    return MockAPIError(message, code)

def test_llm_service_success():
    client = FakeClient()
    service = LLMService(client=client)
    res = service.answer("Q", "Ctx")
    assert res == "Success"

def test_llm_service_auth_error():
    client = FakeClient()
    # Create an APIError with code 401
    err = create_mock_api_error("Auth error", 401)
    client.models.error_to_raise = err
    service = LLMService(client=client)
    with pytest.raises(Exception) as excinfo:
        service.answer("Q", "Ctx")
    assert "Invalid or missing GEMINI_API_KEY" in str(excinfo.value)

def test_llm_service_quota_error():
    client = FakeClient()
    err = create_mock_api_error("RESOURCE_EXHAUSTED", 429)
    client.models.error_to_raise = err
    service = LLMService(client=client)
    with pytest.raises(Exception) as excinfo:
        service.answer("Q", "Ctx")
    assert "quota exhausted" in str(excinfo.value)

@patch("app.llm_service.time.sleep")
def test_llm_service_transient_retry(mock_sleep):
    client = FakeClient()
    err = create_mock_api_error("Rate Limit", 429)
    client.models.error_to_raise = [err, None]
    service = LLMService(client=client)
    res = service.answer("Q", "Ctx")
    assert res == "Success"
    assert client.models.generate_content_calls == 2
    assert mock_sleep.called

@patch("app.llm_service.time.sleep")
def test_llm_service_transient_max_retries(mock_sleep):
    client = FakeClient()
    err = create_mock_api_error("Server Down", 503)
    client.models.error_to_raise = err
    service = LLMService(client=client)
    with pytest.raises(Exception) as excinfo:
        service.answer("Q", "Ctx")
    assert "API Error" in str(excinfo.value)
    assert client.models.generate_content_calls == 5
    assert mock_sleep.call_count == 4
