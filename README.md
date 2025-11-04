# Whisper PTT (Push-to-Transcribe)
Voice-to-text **anywhere** with global hotkeys.  
Press one hotkey to **start recording**, another to **stop + transcribe + paste** the text where your cursor is.

> Uses **[faster-whisper](https://github.com/guillaumekln/faster-whisper)** (CTranslate2): faster/lighter than original Whisper, with GPU/CPU support.  
> Default language: **Spanish** (changeable).

---

## Versions
Two small utilities to record mic audio and transcribe with Faster-Whisper.

- `ptt.py` — press **ENTER** to stop; result goes to clipboard (and optionally prints).
- `whisper_hotkeys.py` — global hotkeys:
  - Ctrl+Alt+H: start
  - Ctrl+Alt+J: stop + transcribe + paste
  - Ctrl+Alt+C: cancel
  - Ctrl+Alt+Q: quit

## Project made with

- **Windows 10 64-bit**
- **Python 3.12.x** 
- **CUDA Toolkit 12.4**
- **cuDNN 9.14** (e.g., folder `bin\12.9` present)

> Note: even if your driver supports CUDA 12.9, CTranslate2 binaries typically look for **CUDA 12.4** runtime DLLs (e.g., `cublas64_12.dll`). That’s why we install **CUDA 12.4** alongside a modern driver.

## Install
# 1) Clone the repo
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>

# 2) Create the virtual environment (Python 3.12 recommended)
py -3.12 -m venv .venv
.\.venv\Scripts\activate

# 3) Install dependencies
pip install -r requirements.txt

## Prepare GPU

Install CUDA Toolkit 12.4 from NVIDIA.

Install cuDNN 9.14 and ensure DLLs exist, e.g.:

C:\Program Files\NVIDIA\CUDNN\v9.14\bin\12.9\cudnn_ops64_9.dll


The script prepends the needed CUDA/cuDNN folders at runtime (no need to edit global PATH).

## Usage
'''powershell
.\.venv\Scripts\activate
python whisper_hotkeys.py


Place the cursor in the target app (VS Code, Word, WhatsApp Web, etc.).

Press Ctrl+Alt+H and speak.

Press Ctrl+Alt+J to stop + transcribe + paste the text.

Ctrl+Alt+C cancels; Ctrl+Alt+Q quits.

To see that the mic is active, Windows shows a microphone access indicator near the system tray.

## Run in background on Windows
# Task Scheduler
Task Scheduler → Create Task…

General: check Run with highest privileges.

Triggers: At log on.

Actions:

Program:

C:\path\to\<your-repo>\.venv\Scripts\pythonw.exe


Arguments:

C:\path\to\<your-repo>\whisper_hotkeys.py


Start in:

C:\path\to\<your-repo>


Save and test with Run.

To ensure hotkeys work in your desktop session, use “Run only when user is logged on”.
If hotkeys don’t fire, run with highest privileges.

## Models & VRAM (rough guide)
Model	VRAM approx	Quality	Latency
tiny	~1 GB	Low	Very low
base	~1.5 GB	Low	Very low
small	~2.5 GB	Medium	Low
medium	~5 GB	High	Medium
large-v3	>10 GB	Very high	High