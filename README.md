# Friday 2.0

Friday 2.0 is the next version of the desktop assistant: it keeps the original command capabilities while using a new dark, animated web interface inspired by the Sophia layout.

## Run it

```bash
cd /Users/kunal/Documents/Project/Friday2.0
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3.5:9b
python3 web_server.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Ollama must be installed locally; Friday starts `ollama serve` automatically when needed.

Available commands include opening macOS apps, checking CPU/RAM/battery, web searches, calculations, weather (with `OPENWEATHER_API_KEY` set), and general questions through Ollama. Browser microphone input works in Chrome and Edge.

## Voice, language, and faster replies

Friday automatically responds in the language of the question: English questions receive English replies; Hindi or Hinglish questions receive Hindi/Hinglish replies. The web interface has a persistent Female/Male reply-voice selector beside “Voice replies”; it uses a matching voice installed in the browser/OS, falling back to the closest voice available. The native desktop interface also has a Female/Male voice selector.

Friday uses only the locally installed Ollama model `qwen3.5:9b`. It keeps the model warm for 30 minutes, limits ordinary replies to 220 tokens, and never sends questions to a cloud AI provider. Greetings such as `Hello` and `How are you?` still answer instantly without waiting for the LLM.

## Weather API key

Copy the example settings, then add future secrets only to `.env` (it is ignored by Git):

```bash
cp .env.example .env
```

`OPENWEATHER_API_KEY` is optional and enables weather. All AI questions are handled by your local Ollama installation; no cloud AI key or provider is configured. Restart the server after changing `.env`. Do not paste the weather key into source files or commit `.env`.

The web page starts listening for `Hello Friday` automatically. Your browser will still ask for microphone permission once; after you allow it, Friday re-arms listening after every answer. The microphone button is now only a pause/resume control.

To use the original native desktop window and wake-word loop instead, run `python3 app.py`.
