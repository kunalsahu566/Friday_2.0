# Friday 2.0

Friday 2.0 is the next version of the desktop assistant: it keeps the original command capabilities while using a new dark, animated web interface inspired by the Sophia layout.

## Run it

```bash
cd /Users/kunal/Documents/Project/Friday2.0
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3.5:4b
python3 web_server.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Ollama must be installed locally; Friday starts `ollama serve` automatically when needed.

Available commands include opening macOS apps, checking CPU/RAM/battery, web searches, calculations, weather (with `OPENWEATHER_API_KEY` set), and general questions through Ollama. Browser microphone input works in Chrome and Edge.

## Voice, language, and faster replies

Friday automatically responds in the language of the question: English questions receive English replies; Hindi or Hinglish questions receive Hindi/Hinglish replies. The web interface has a persistent Female/Male reply-voice selector beside “Voice replies”; it uses a matching voice installed in the browser/OS, falling back to the closest voice available. The native desktop interface also has a Female/Male voice selector.

For a quick local response, Friday now defaults to `qwen3.5:4b`, a shorter 220-token response limit, reduced context, and keeps the model warm for 30 minutes. Copy `.env.example` to `.env` and choose a larger installed model only when you need it. Greetings such as `Hello` and `How are you?` still answer instantly without waiting for the LLM.

## API keys and models

Copy the example settings, then add future secrets only to `.env` (it is ignored by Git):

```bash
cp .env.example .env
```

`OPENWEATHER_API_KEY` enables weather. Friday uses private local Ollama by default. For OpenAI, add `OPENAI_API_KEY`, set `FRIDAY_LLM_PROVIDER=openai`, and optionally choose `FRIDAY_OPENAI_MODEL`. For AIMLAPI, add `AIMLAPI_KEY`, set `FRIDAY_LLM_PROVIDER=aimlapi`, and select an AIMLAPI catalogue model with `FRIDAY_AIMLAPI_MODEL` (the default is `openai/gpt-5-5`). Restart the server after changing `.env`. Do not paste API keys into source files or commit `.env`.

The web page starts listening for `Hello Friday` automatically. Your browser will still ask for microphone permission once; after you allow it, Friday re-arms listening after every answer. The microphone button is now only a pause/resume control.

To use the original native desktop window and wake-word loop instead, run `python3 app.py`.
