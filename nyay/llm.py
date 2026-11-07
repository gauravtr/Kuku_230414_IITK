"""Model layer. Swapping the model = changing two env vars:

    NYAY_PROVIDER = gemini | groq | openai | openrouter | anthropic | ollama | manual
    NYAY_MODEL    = any model name that provider serves

Only `requests` is used (no SDKs), so a new OpenAI-compatible provider is one line
in OPENAI_COMPATIBLE. Every call can be cached to disk (used by run_tests.py), which
makes test runs reproducible and lets the `manual` provider replay responses.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import re
import time

import requests

OPENAI_COMPATIBLE = {
    # provider: (base_url, api-key env var, default model)
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.3-70b-versatile"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "meta-llama/llama-3.3-70b-instruct:free"),
    "ollama": ("http://localhost:11434/v1", None, "llama3.1"),
}
DEFAULTS = {"gemini": "gemini-flash-latest", "anthropic": "claude-sonnet-5-5", "manual": "manual"}
# Google retires model names often; on a 404 we try these in order (first one that answers wins).
GEMINI_FALLBACKS = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class ModelError(RuntimeError):
    """Error safe to show to users: never contains URLs or API keys."""


def _safe(e: Exception) -> str:
    msg = re.sub(r"https?://\S+", "[url]", str(e))
    return re.sub(r"(key=|Bearer\s+)[\w\-.]+", r"\1[hidden]", msg)[:300]


class PendingResponse(Exception):
    """Raised by the `manual` provider when a prompt has no cached response yet."""


class LLM:
    def __init__(self, provider: str | None = None, model: str | None = None,
                 cache_dir: str | None = None, timeout: int = 50):
        self.provider = (provider or os.getenv("NYAY_PROVIDER") or "gemini").lower()
        default = OPENAI_COMPATIBLE.get(self.provider, (None, None, DEFAULTS.get(self.provider)))[2]
        self.model = model or os.getenv("NYAY_MODEL") or default
        self.cache_dir = pathlib.Path(cache_dir) if cache_dir else None
        self.timeout = timeout
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return f"{self.provider}:{self.model}"

    # ------------------------------------------------------------------ public
    def chat(self, system: str, messages: list[dict], json_mode: bool = False,
             temperature: float = 0.2, max_tokens: int = 8192) -> str:
        """messages: [{'role': 'user'|'assistant', 'content': str}, ...]"""
        key = self._key(system, messages, json_mode)
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        if self.provider == "manual":
            self._write_pending(key, system, messages, json_mode)
            raise PendingResponse(key)
        for attempt in range(3):
            try:
                out = self._call(system, messages, json_mode, temperature, max_tokens)
                break
            except requests.HTTPError as e:  # rate limits on free tiers -> back off
                code = e.response.status_code if e.response is not None else None
                if code in (429, 500, 503) and attempt < 1:
                    time.sleep(3 * (attempt + 1))
                    continue
                raise ModelError(f"model call failed ({code}): {_safe(e)}") from None
            except requests.RequestException as e:
                raise ModelError(f"could not reach the model: {_safe(e)}") from None
        self._cache_put(key, out, system, messages)
        return out

    def transcribe(self, audio: bytes, mime: str = "audio/wav") -> str:
        """Voice input. Free options: Gemini (audio understanding) or Groq Whisper."""
        if self.provider == "gemini" or os.getenv("GEMINI_API_KEY"):
            body = {"contents": [{"role": "user", "parts": [
                {"inline_data": {"mime_type": mime, "data": base64.b64encode(audio).decode()}},
                {"text": "Transcribe this audio exactly, in the language and script it is spoken in. Output only the transcript."}]}]}
            try:
                return self._gemini_post(body)
            except requests.RequestException as e:
                raise ModelError(f"voice transcription failed: {_safe(e)}") from None
        if os.getenv("GROQ_API_KEY"):
            r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions",
                              headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
                              files={"file": ("voice.wav", audio, mime)},
                              data={"model": "whisper-large-v3"}, timeout=self.timeout)
            r.raise_for_status()
            return r.json()["text"]
        raise RuntimeError("Voice needs GEMINI_API_KEY or GROQ_API_KEY.")

    # ----------------------------------------------------------------- private
    def _call(self, system, messages, json_mode, temperature, max_tokens) -> str:
        if self.provider == "gemini":
            body = {
                "system_instruction": {"parts": [{"text": system}]},
                "contents": [{"role": "model" if m["role"] == "assistant" else "user",
                              "parts": [{"text": m["content"]}]} for m in messages],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens,
                                     **({"responseMimeType": "application/json"} if json_mode else {})},
            }
            return self._gemini_post(body)

        if self.provider == "anthropic":
            r = requests.post("https://api.anthropic.com/v1/messages", timeout=self.timeout,
                              headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                                       "anthropic-version": "2023-06-01"},
                              json={"model": self.model, "max_tokens": max_tokens, "temperature": temperature,
                                    "system": system, "messages": messages})
            r.raise_for_status()
            return "".join(b.get("text", "") for b in r.json()["content"])

        if self.provider in OPENAI_COMPATIBLE:
            base, key_env, _ = OPENAI_COMPATIBLE[self.provider]
            base = os.getenv("NYAY_BASE_URL", base)
            headers = {"Authorization": f"Bearer {os.environ[key_env]}"} if key_env else {}
            body = {"model": self.model, "temperature": temperature, "max_tokens": max_tokens,
                    "messages": [{"role": "system", "content": system}] + messages}
            if json_mode:
                body["response_format"] = {"type": "json_object"}
            r = requests.post(f"{base}/chat/completions", headers=headers, json=body, timeout=self.timeout)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

        raise ValueError(f"Unknown provider '{self.provider}'")

    def _gemini_post(self, body: dict) -> str:
        """Key goes in a header (never in the URL). On 404 (model retired), walk the fallback list."""
        headers = {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}
        tried, last_err, start = [], None, time.monotonic()
        for m in [self.model] + [f for f in GEMINI_FALLBACKS if f != self.model]:
            if last_err is not None and time.monotonic() - start > 70:
                break                       # keep the user's total wait bounded
            tried.append(m)
            fast = {**body, "generationConfig": {**body.get("generationConfig", {}), "thinkingConfig": {"thinkingLevel": "low"}}}
            try:
                r = requests.post(GEMINI_URL.format(model=m), headers=headers, json=fast, timeout=self.timeout)
                if r.status_code == 400:  # model without thinking levels: retry with the plain request
                    r = requests.post(GEMINI_URL.format(model=m), headers=headers, json=body, timeout=self.timeout)
            except requests.Timeout as e:   # slow model -> try the next (faster) one instead of waiting again
                last_err = e
                continue
            if r.status_code == 404:
                continue
            if r.status_code in (429, 500, 503):
                last_err = requests.HTTPError(f"{r.status_code} from {m}", response=r)
                continue                    # overloaded / quota for this model -> next model
            r.raise_for_status()
            if m != self.model:
                self.model = m          # remember the working model for the rest of the session
            return _gemini_text(r.json())
        if last_err is not None:
            raise last_err
        raise ModelError(f"none of these Gemini models is available to this key: {', '.join(tried)}")

    def _key(self, system, messages, json_mode) -> str:
        blob = json.dumps({"s": system, "m": messages, "j": json_mode}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def _cache_get(self, key):
        if not self.cache_dir:
            return None
        f = self.cache_dir / f"{key}.json"
        return json.loads(f.read_text())["response"] if f.exists() else None

    def _cache_put(self, key, out, system, messages):
        if self.cache_dir:
            (self.cache_dir / f"{key}.json").write_text(json.dumps(
                {"model": self.name, "response": out, "last_user": messages[-1]["content"][:300]},
                ensure_ascii=False, indent=1))

    def _write_pending(self, key, system, messages, json_mode):
        d = (self.cache_dir or pathlib.Path("outputs/cache")) / "_pending"
        d.mkdir(parents=True, exist_ok=True)
        text = f"# SYSTEM\n{system}\n\n" + "\n\n".join(f"# {m['role'].upper()}\n{m['content']}" for m in messages)
        (d / f"{key}.prompt.md").write_text(text + ("\n\n(JSON output required)" if json_mode else ""))


def _gemini_text(data: dict) -> str:
    try:
        return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"] if not p.get("thought"))
    except (KeyError, IndexError):
        raise RuntimeError(f"Gemini returned no text: {json.dumps(data)[:400]}")
