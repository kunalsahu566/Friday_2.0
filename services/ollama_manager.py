"""Start and verify the local Ollama service used by Friday."""

import subprocess
import time
import urllib.error
import urllib.request

OLLAMA_HEALTH_URL = "http://127.0.0.1:11434/api/tags"


def _is_ollama_running():
    try:
        with urllib.request.urlopen(OLLAMA_HEALTH_URL, timeout=1) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def ensure_ollama_running(status_callback=None, wait_seconds=20):
    if _is_ollama_running():
        if status_callback:
            status_callback("Ollama is ready")
        return
    if status_callback:
        status_callback("Starting Ollama…")
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except FileNotFoundError as error:
        raise RuntimeError("Ollama is not installed. Install it from https://ollama.com/download.") from error
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if _is_ollama_running():
            if status_callback:
                status_callback("Ollama is ready")
            return
        time.sleep(0.5)
    raise RuntimeError("Ollama did not start. Run `ollama serve` in Terminal to see its error.")
