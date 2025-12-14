import json
import types
import pytest
from ai_client import AIClient


class DummyResponse:
    def __init__(self, js):
        self._js = js
        self.status_code = 200
        self.text = json.dumps(js)

    def raise_for_status(self):
        pass

    def json(self):
        return self._js


def test_gemini_chat(monkeypatch):
    called = {}

    def fake_post(url, params=None, json=None, timeout=0):
        called['url'] = url
        called['params'] = params
        called['json'] = json
        return DummyResponse({'candidates': [{'output': 'Gemini says hi'}]})

    monkeypatch.setattr('ai_client.requests.post', fake_post)

    client = AIClient(api_key='TESTKEY', provider='gemini', model='test-model')
    messages = [{'role': 'user', 'content': 'Hello'}]
    resp = client.chat(messages)
    assert resp == 'Gemini says hi'
    assert 'test-model' in called['url']
    assert called['params']['key'] == 'TESTKEY'


def test_openai_missing_package(monkeypatch):
    # If openai isn't available, AIClient should raise when provider=openai
    monkeypatch.setitem(__import__('os').environ, 'OPENAI_API_KEY', 'x')
    # Temporarily simulate missing openai module in ai_client
    import ai_client
    monkeypatch.setattr(ai_client, 'openai', None)
    with pytest.raises(RuntimeError):
        AIClient(api_key='x', provider='openai')
