# AI Assistant Tools (Windows)

A small Python GUI assistant for Windows using the Flet framework that connects to the OpenAI API. It supports chat, message selection and summarization, and can be packaged with PyInstaller or run as a web/desktop app via Flet.

## Quick start (Windows)

1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app (desktop/web):

```powershell
python main.py
```

4. Enter your OpenAI API key in the app (or set `OPENAI_API_KEY` env var).

### Summarize selection

- Click messages in the conversation to select them (a blue border indicates selection).
- Click **Summarize Selection** to summarize the selected messages, or paste text into the dialog to summarize arbitrary text.

### Providers

- The app supports multiple LLM backends. Open **Settings** (Set API Key) to select the provider (OpenAI or Gemini) and set per-provider API keys.
- The selected provider is used for chat and summarization.


## Packaging (PyInstaller)

```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --add-data "./templates;templates" main.py
```

This will create a `dist\main.exe` executable.

## Files
- `main.py`: app entrypoint delegating to `ui/app.py` (Flet-based GUI)
- `ui/app.py`: Flet UI components and helpers

- `ai_client.py`: minimal OpenAI client wrapper
- `tools.py`: helper tools (summarize)

## Notes
- This is a minimal starter. Add more tools and features as needed.