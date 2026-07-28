try:
    import speech_recognition as sr
except ImportError:
    sr = None

recognizer = sr.Recognizer() if sr else None


def listen(timeout=5, phrase_time_limit=8, calibrate=False):
    """Listen once and return recognised speech, or None if nothing is understood."""
    if not recognizer or not sr:
        raise RuntimeError("Speech recognition is not installed. Run pip install -r requirements.txt.")
    with sr.Microphone() as source:
        if calibrate:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            return None
    try:
        return recognizer.recognize_google(audio)
    except (sr.UnknownValueError, sr.RequestError):
        return None
