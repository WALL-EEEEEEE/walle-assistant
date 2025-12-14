import os
import json
import requests
try:
    import openai
except Exception:
    openai = None


class AIClient:
    """Unified AI client supporting multiple providers: 'openai' and 'gemini'.

    Use `provider` to select which LLM backend to call. For 'openai', the
    `api_key` should be an OpenAI API key. For 'gemini', the `api_key` should
    be a Google API key or bearer token that can access the Generative API.
    """

    def __init__(self, api_key=None, provider="openai", model=None):
        self.provider = provider
        self.api_key = api_key
        self.model = model

        if self.provider == "openai":
            self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key not set. Set OPENAI_API_KEY or pass api_key.")
            if openai is None:
                raise RuntimeError("openai package is required for provider 'openai'")
            openai.api_key = self.api_key
            self.model = self.model or "gpt-3.5-turbo"

        elif self.provider == "gemini":
            # Accept either explicit key or GOOGLE_API_KEY/GEMINI_API_KEY env var
            self.api_key = self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                raise ValueError("Gemini API key not set. Set GEMINI_API_KEY/GOOGLE_API_KEY or pass api_key.")
            self.model = self.model or "text-bison-001"

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def chat(self, messages, max_tokens=1024, temperature=0.7):
        if self.provider == "openai":
            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp["choices"][0]["message"]["content"]

        if self.provider == "gemini":
            # Build a simple prompt by concatenating messages.
            prompt = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in messages])
            url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateText"
            params = {"key": self.api_key}
            payload = {
                "prompt": {"text": prompt},
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
            r = requests.post(url, params=params, json=payload, timeout=30)
            r.raise_for_status()
            j = r.json()
            # Try common response shapes
            if "candidates" in j and isinstance(j["candidates"], list) and j["candidates"]:
                # candidate may contain 'output' or 'content' or 'text'
                cand = j["candidates"][0]
                return cand.get("output") or cand.get("content") or cand.get("text") or json.dumps(cand)
            if "output" in j:
                return j["output"]
            # Fallback to raw text
            return r.text

        raise RuntimeError("Unsupported provider")

    def summarize(self, text):
        if self.provider == "openai":
            messages = [
                {"role": "system", "content": "You are a helpful assistant that summarizes text concisely."},
                {"role": "user", "content": f"Summarize the following text:\n\n{text}"},
            ]
            return self.chat(messages, max_tokens=300, temperature=0.3)

        if self.provider == "gemini":
            prompt = f"Summarize the following text concisely:\n\n{text}"
            url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateText"
            params = {"key": self.api_key}
            payload = {
                "prompt": {"text": prompt},
                "temperature": 0.3,
                "maxOutputTokens": 300,
            }
            r = requests.post(url, params=params, json=payload, timeout=30)
            r.raise_for_status()
            j = r.json()
            if "candidates" in j and j["candidates"]:
                cand = j["candidates"][0]
                return cand.get("output") or cand.get("content") or cand.get("text") or json.dumps(cand)
            if "output" in j:
                return j["output"]
            return r.text
