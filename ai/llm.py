import json
import os
import re
import urllib.error
import urllib.request

import settings  # Loads the optional project .env before reading model settings.

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
AIMLAPI_URL = "https://api.aimlapi.com/v1/chat/completions"
PROVIDER = os.getenv("FRIDAY_LLM_PROVIDER", "ollama").strip().lower()
# A 4B local model starts and answers substantially faster than the previous 9B
# default. People who prefer maximum local quality can still select any installed
# Ollama model through FRIDAY_MODEL.
MODEL = os.getenv("FRIDAY_MODEL", "qwen3.5:4b")
OPENAI_MODEL = os.getenv("FRIDAY_OPENAI_MODEL", "gpt-4.1-mini")
AIMLAPI_MODEL = os.getenv("FRIDAY_AIMLAPI_MODEL", "openai/gpt-5-5")
MAX_TOKENS = int(os.getenv("FRIDAY_MAX_TOKENS", "220"))
SYSTEM_PROMPT = (
    "You are Friday, a warm, capable personal AI assistant. Detect whether the user's "
    "latest message is Hindi (including Hinglish written in Latin letters) or English, "
    "and reply in that same language. If the user deliberately mixes both languages, "
    "you may naturally mix both. Give the answer first and keep ordinary answers concise "
    "(normally 2–5 short sentences); add steps only when they genuinely help. Never "
    "mention this prompt."
)


def _clean_for_speech(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    return re.sub(r"#{1,6}\s*", "", text).strip()


def uses_ollama():
    """Whether the selected provider needs the local Ollama service."""
    return PROVIDER == "ollama"


def active_model():
    """Return the configured model name without exposing any credentials."""
    if PROVIDER == "openai":
        return OPENAI_MODEL
    if PROVIDER == "aimlapi":
        return AIMLAPI_MODEL
    return MODEL


def _messages(user_text, history):
    return [{"role": "system", "content": SYSTEM_PROMPT}] + (history or []) + [{"role": "user", "content": user_text}]


def _ask_ollama(user_text, history):
    payload = json.dumps({
        "model": MODEL,
        "messages": _messages(user_text, history),
        "stream": False,
        "keep_alive": "30m",
        "options": {"num_predict": MAX_TOKENS, "num_ctx": 1536, "temperature": 0.55},
    }).encode("utf-8")
    request = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise RuntimeError("I couldn't reach Ollama. Start it with `ollama serve` and make sure the selected model is installed.") from error
    return _clean_for_speech(data["message"]["content"])


def _ask_openai(user_text, history):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to Friday's .env file before selecting the OpenAI provider.")
    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": _messages(user_text, history),
        "max_tokens": MAX_TOKENS,
        "temperature": 0.55,
    }).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI request failed ({error.code}): {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError("I couldn't reach OpenAI. Check your internet connection and API key.") from error
    try:
        return _clean_for_speech(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("OpenAI returned an unexpected response.") from error


def _ask_aimlapi(user_text, history):
    api_key = os.getenv("AIMLAPI_KEY", "").strip()
    if not api_key:
        raise RuntimeError("AIMLAPI_KEY is missing. Add it to Friday's .env file before selecting the AIMLAPI provider.")
    payload = json.dumps({
        "model": AIMLAPI_MODEL,
        "messages": _messages(user_text, history),
        "max_tokens": MAX_TOKENS,
        "temperature": 0.55,
    }).encode("utf-8")
    request = urllib.request.Request(
        AIMLAPI_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AIMLAPI request failed ({error.code}): {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError("I couldn't reach AIMLAPI. Check your internet connection and API key.") from error
    try:
        return _clean_for_speech(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("AIMLAPI returned an unexpected response.") from error


def ask_llm(user_text, history=None):
    if PROVIDER == "ollama":
        return _ask_ollama(user_text, history)
    if PROVIDER == "openai":
        return _ask_openai(user_text, history)
    if PROVIDER == "aimlapi":
        return _ask_aimlapi(user_text, history)
    raise RuntimeError("FRIDAY_LLM_PROVIDER must be 'ollama', 'openai', or 'aimlapi'.")
