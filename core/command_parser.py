def parse_command(text):
    """Classify a command and keep its argument for the selected handler."""
    if not text:
        return "unknown", ""
    original = text.strip()
    normalized = original.lower()
    if "open" in normalized:
        return "open_app", original[normalized.index("open") + len("open"):].strip()
    if any(term in normalized for term in ("cpu", "battery", "system status", "ram")):
        return "system_status", ""
    if "search" in normalized or "google" in normalized:
        for keyword in ("search for", "search", "google"):
            if keyword in normalized:
                return "web_search", original[normalized.index(keyword) + len(keyword):].strip()
    if any(term in normalized for term in ("calculate", "plus", "minus", "times", "divided by")):
        return "calculate", original
    if "weather" in normalized:
        for keyword in ("weather in", "weather for", "weather of", "weather"):
            if keyword in normalized:
                city = original[normalized.index(keyword) + len(keyword):].strip()
                return "weather", city.removeprefix("in ").removeprefix("for ").removeprefix("of ").strip()
    if any(term in normalized for term in ("exit", "quit", "goodbye", "stop listening", "go to sleep")):
        return "exit", ""
    # Preserve the user's writing for language detection and natural LLM replies.
    return "unknown", original
