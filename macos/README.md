# Friday for macOS

The native version runs as a background assistant. It stays hidden while it
waits for **Hello Friday** or **Hey Friday**, then shows a dark central Friday
core while listening, thinking, and replying.

## One-time setup

1. Install PortAudio: `brew install portaudio`
2. Create a virtual environment and activate it.
3. Install the macOS dependencies: `python3 -m pip install -r requirements-macos.txt`
4. Build the no-Dock application bundle: `./macos/build_macos_app.sh`
5. Start it automatically at login: `./macos/install_login_agent.sh`

On the first launch, allow **Friday** to access the microphone in macOS
Settings. For development without packaging, run `python3 mac_app.py`.
The installer safely copies an existing project `.env` to
`~/Library/Application Support/Friday2/.env`; edit that file later to change
the weather key, model, or voice preferences used by the packaged app.

## Behaviour

- Say `Hello Friday`, wait for the listening visual, then say the request.
- Or use one phrase, for example: `Hello Friday, what is my system status?`
- Friday hides again after it has replied and continues listening in the
  background.
- The assistant must be running to detect a wake phrase; installing the login
  agent keeps it running after you sign in.

## Stop or remove

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.friday2.assistant.plist
rm ~/Library/LaunchAgents/com.friday2.assistant.plist
```

## Privacy note

The Ollama model runs locally. The current wake/command recognizer uses
SpeechRecognition's Google recognition backend, so spoken audio recognition is
not an offline feature. A dedicated offline wake-word engine would be the next
step for Siri-level wake detection.
