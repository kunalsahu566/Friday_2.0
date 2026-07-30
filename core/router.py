import subprocess
import webbrowser
from urllib.parse import quote_plus

from ai.llm import ask_llm
from core.command_parser import parse_command
from core.memory import ConversationMemory
from core.plugin_loader import load_plugins
from services.ollama_manager import ensure_ollama_running
from services.weather import get_weather
from speech.speech_to_text import listen
from speech.text_to_speech import speak

memory = ConversationMemory()
plugin_commands = {}
load_plugins(plugin_commands)

FAST_REPLIES = {
    "hello": "Hello! I'm doing well, thank you. How are you?",
    "hi": "Hi! I'm doing well, thank you. How are you?",
    "hey": "Hey! I'm doing well, thank you. How are you?",
    "hello friday": "Hello! I'm doing well, thank you. How are you?",
    "how are you": "I'm doing well, thank you. How are you?",
    "how are you?": "I'm doing well, thank you. How are you?",
    "what can you do": "I can answer questions, explain topics, calculate, search the web, open apps, check your system status, tell you the weather, and respond to the wake phrase Hello Friday.",
}

HINDI_MARKERS = ("नमस्ते", "हैलो", "कैसे", "क्या", "मुझे", "आप", "हो", "है")


def get_fast_reply(text):
    """Return immediate friendly replies for common conversation starters."""
    normalized = " ".join((text or "").lower().replace(",", " ").replace("!", " ").replace("?", " ").split())
    is_hindi = any(marker in (text or "") for marker in HINDI_MARKERS)
    if normalized in {"नमस्ते", "हैलो", "हेलो", "नमस्ते फ्राइडे", "हेलो फ्राइडे"}:
        return "नमस्ते! मैं आपकी मदद के लिए तैयार हूँ। आप क्या जानना चाहते हैं?"
    if normalized in {"hello how are you", "hi how are you", "hey how are you"}:
        return "नमस्ते! मैं ठीक हूँ, धन्यवाद। आप कैसे हैं?" if is_hindi else "Hello! I'm doing well, thank you. How are you?"
    reply = FAST_REPLIES.get(normalized)
    if is_hindi and reply:
        return "नमस्ते! मैं आपकी मदद के लिए तैयार हूँ। आप क्या जानना चाहते हैं?"
    return reply


def _publish(callback, speaker, text):
    if callback:
        callback(speaker, str(text))


def handle_open_app(app_name):
    if not app_name:
        return "Tell me which app you would like me to open."
    try:
        subprocess.run(["open", "-a", app_name], check=True)
        return f"Opening {app_name}."
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"I couldn't find an app called {app_name}. Please check the name and try again."


def handle_system_status():
    try:
        import psutil
    except ImportError:
        return "System status needs the optional psutil package. Install it with `python3 -m pip install psutil`."

    ram = psutil.virtual_memory()
    response = f"CPU usage is at {psutil.cpu_percent(interval=1)} percent, and RAM usage is at {ram.percent} percent."
    battery = psutil.sensors_battery()
    if battery:
        response += f" Battery is at {round(battery.percent)} percent and {'charging' if battery.power_plugged else 'not charging'}."
    return response


def route_command(command_name, extra_data):
    if command_name == "open_app":
        return handle_open_app(extra_data)
    if command_name == "system_status":
        return handle_system_status()
    if command_name == "web_search":
        if not extra_data:
            return "Tell me what you would like to search for."
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(extra_data)}")
        return f"Searching the web for {extra_data}."
    if command_name == "weather":
        return get_weather(extra_data)
    if command_name == "exit":
        return "__EXIT__"
    if command_name in plugin_commands:
        return plugin_commands[command_name](extra_data)
    quick_reply = get_fast_reply(extra_data)
    if quick_reply:
        return quick_reply
    reply = ask_llm(extra_data, memory.get())
    memory.add("user", extra_data)
    memory.add("assistant", reply)
    return reply


def process_command(command, status_callback=None, message_callback=None):
    """Run one typed command. Typed web commands stay silent in the browser."""
    _publish(message_callback, "You", command)
    command_name, extra_data = parse_command(command)
    # Direct commands and common conversation starters work without Ollama.
    is_fast_reply = command_name == "unknown" and get_fast_reply(extra_data) is not None
    if command_name == "unknown" and not is_fast_reply:
        ensure_ollama_running(status_callback=status_callback)
    reply = route_command(command_name, extra_data)
    if reply == "__EXIT__":
        reply = "Going back to sleep. Say hello Friday when you need me."
    _publish(message_callback, "Friday", reply)
    return reply


def run_assistant(stop_event=None, status_callback=None, message_callback=None):
    """Run the original wake-word voice loop for the desktop application."""
    ensure_ollama_running(status_callback=status_callback)
    speak("Friday is ready. Say hello Friday to wake me.")
    while not (stop_event and stop_event.is_set()):
        heard = listen(timeout=3, phrase_time_limit=5, calibrate=False)
        if not heard or "hello friday" not in heard.lower():
            continue
        speak("Yes? How can I help?")
        while not (stop_event and stop_event.is_set()):
            command = listen(timeout=5, phrase_time_limit=12, calibrate=False)
            if not command:
                continue
            _publish(message_callback, "You", command)
            name, data = parse_command(command)
            reply = route_command(name, data)
            if reply == "__EXIT__":
                speak("Going back to sleep.")
                break
            _publish(message_callback, "Friday", reply)
            speak(reply)
