
import os
os.add_dll_directory(r"C:\Program Files\NVIDIA\CUDNN\v9.14\bin\12.9")
os.environ["PATH"] = r"C:\Program Files\NVIDIA\CUDNN\v9.14\bin\12.9;" + os.environ.get("PATH", "")
os.add_dll_directory(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin")
os.environ["PATH"] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin;" + os.environ.get("PATH", "")


import subprocess, queue, time, sys, numpy as np
import sounddevice as sd
import pyperclip
import threading
from faster_whisper import WhisperModel


# ===== CONFIG =====
LANG = "es"                 # "es" español | "en" inglés | None = autodetección
MODEL_SIZE = os.getenv("WHISPER_SIZE", "medium")  # tiny/base/small/medium/large-v3
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 200
SILENCE_SECS = 20
VAD_THRESHOLD = 0.012
INPUT_DEVICE = None
# ===== END CONFIG =====

model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")

def _pack_audio(collected):
    audio2d = np.concatenate(collected, axis=0).astype(np.float32, copy=False)
    if audio2d.ndim == 2:
        return audio2d.mean(axis=1) if audio2d.shape[1] > 1 else audio2d[:, 0]
    return audio2d

def record_until_enter():
    """
    Record mic audio and stop exactly when the user presses ENTER.
    Works in VS Code terminal, PowerShell and CMD (no msvcrt needed).
    """
    q = queue.Queue()
    blocksize = int(SAMPLE_RATE * CHUNK_MS / 1000)
    collected = []
    stop_event = threading.Event()

    def keyboard_waiter():
        # Press ENTER to stop. Keep the terminal focused while talking.
        try:
            input()  # waits for '\n'
        finally:
            stop_event.set()

    def callback(indata, frames, time_info, status):
        q.put(indata.copy())

    print("🎙️ Grabando... pulsa ENTER para terminar (mantén el foco en la terminal).")
    t = threading.Thread(target=keyboard_waiter, daemon=True)
    t.start()

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32",
                        blocksize=blocksize, device=INPUT_DEVICE, callback=callback):
        while not stop_event.is_set():
            try:
                data = q.get(timeout=0.05)
                collected.append(data)
            except queue.Empty:
                pass

    if not collected:
        return np.zeros(0, dtype=np.float32)
    return _pack_audio(collected)
def transcribe(audio_np):
    segments, _ = model.transcribe(
        audio_np,
        language=LANG,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400),
    )
    return "".join(s.text for s in segments).strip()

# ---------- main ----------
if __name__ == "__main__":
    # default is ENTER mode; use `python ptt.py echo` to also print text
    mode = (sys.argv[1].lower() if len(sys.argv) > 1 else "enter")  # "enter" | "echo"
    print("Listo. (Pulsa ENTER para detener y transcribir)")
    audio = record_until_enter()
    print("Transcribiendo…")
    text = transcribe(audio)
    if not text:
        sys.exit(0)
    pyperclip.copy(text)
    if mode == "echo":
        print(text)
