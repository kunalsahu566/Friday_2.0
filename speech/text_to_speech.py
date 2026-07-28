import subprocess
import os

import settings  # Loads optional voice settings from .env.

VOICE_PROFILE = os.getenv("FRIDAY_VOICE_PROFILE", "female").strip().lower()
VOICE_BY_PROFILE = {
    "male": os.getenv("FRIDAY_VOICE_MALE", "Alex"),
    "female": os.getenv("FRIDAY_VOICE_FEMALE", "Samantha"),
}
HINDI_VOICE = os.getenv("FRIDAY_VOICE_HINDI", "").strip()


def set_voice_profile(profile):
    """Select the macOS voice profile used by the desktop app."""
    global VOICE_PROFILE
    if profile in VOICE_BY_PROFILE:
        VOICE_PROFILE = profile


def speak(text):
    """Speak through the macOS built-in voice; safely do nothing for blank replies."""
    text = str(text).strip()
    if not text:
        return
    print(f"[Friday]: {text}")
    voice = HINDI_VOICE if HINDI_VOICE and any("\u0900" <= char <= "\u097F" for char in text) else VOICE_BY_PROFILE[VOICE_PROFILE]
    try:
        subprocess.run(["say", "-r", os.getenv("FRIDAY_VOICE_RATE", "185"), "-v", voice, text], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        print(f"Text-to-speech error: {error}")
