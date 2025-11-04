# Whisper PTT (Push-to-Transcribe)

Two small utilities to record mic audio and transcribe with Faster-Whisper.

## Versions
- `ptt.py` — press **ENTER** to stop; result goes to clipboard (and optionally prints).
- `whisper_hotkeys.py` — global hotkeys:
  - Ctrl+Alt+H: start
  - Ctrl+Alt+J: stop + transcribe + paste
  - Ctrl+Alt+C: cancel
  - Ctrl+Alt+Q: quit

## Install
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
