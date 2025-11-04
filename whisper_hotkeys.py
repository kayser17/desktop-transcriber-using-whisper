# --- CUDA/cuDNN paths: keep these FIRST (your same two blocks) ---
import os
os.add_dll_directory(r"C:\Program Files\NVIDIA\CUDNN\v9.14\bin\12.9")
os.environ["PATH"] = r"C:\Program Files\NVIDIA\CUDNN\v9.14\bin\12.9;" + os.environ.get("PATH", "")
os.add_dll_directory(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin")
os.environ["PATH"] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin;" + os.environ.get("PATH", "")

# --- imports ---
import queue, threading, time, sys
import numpy as np
import sounddevice as sd
import pyperclip
import keyboard  # global hotkeys
from faster_whisper import WhisperModel

# --- Indicador visual: mini-ventana "Grabando…" ---
import threading
try:
    import tkinter as _tk
    _rec_win = None

    def show_recording_indicator():
        """Muestra una ventanita pequeña '🎙️  Grabando…' arriba-izquierda."""
        global _rec_win
        if _rec_win is not None:
            return
        _rec_win = _tk.Tk()
        _rec_win.overrideredirect(True)         # sin bordes
        _rec_win.attributes("-topmost", True)   # siempre al frente
        _rec_win.geometry("+20+40")             # posición en pantalla (x,y)
        frame = _tk.Frame(_rec_win, bg="#202020")
        frame.pack()
        label = _tk.Label(frame, text=" Grabando…",
                          bg="#202020", fg="white",
                          padx=12, pady=8, font=("Segoe UI", 11, "bold"))
        label.pack()
        # loop de tkinter en un hilo para no bloquear tu script
        threading.Thread(target=_rec_win.mainloop, daemon=True).start()

    def hide_recording_indicator():
        """Oculta la ventanita si está visible."""
        global _rec_win
        try:
            if _rec_win is not None:
                _rec_win.destroy()
        except Exception:
            pass
        _rec_win = None

except Exception:
    # Fallback silencioso si Tk no está disponible
    def show_recording_indicator(): pass
    def hide_recording_indicator(): pass


# ====== CONFIG ======
LANG = "es"                     
MODEL_SIZE = os.getenv("WHISPER_SIZE", "medium")
SAMPLE_RATE = 16000
CHANNELS    = 1
CHUNK_MS    = 200
INPUT_DEVICE = None             # None = default mic
COMPUTE_TYPE = "float16"        # "float16" on RTX 30 is perfect
HOTKEY_START = "ctrl+alt+h"     # start recording
HOTKEY_STOP  = "ctrl+alt+j"     # stop + transcribe + paste
HOTKEY_CANCEL= "ctrl+alt+c"     # cancel current recording
HOTKEY_QUIT  = "ctrl+alt+q"     # quit app
PASTE_RESULT = True             # send Ctrl+V automatically
# ====== END CONFIG ======

# --- Whisper model (load once) ---
model = WhisperModel(MODEL_SIZE, device="cuda", compute_type=COMPUTE_TYPE)

def _pack_audio(collected):
    """concat -> float32 mono 1D"""
    audio2d = np.concatenate(collected, axis=0).astype(np.float32, copy=False)
    if audio2d.ndim == 2:
        return audio2d.mean(axis=1) if audio2d.shape[1] > 1 else audio2d[:, 0]
    return audio2d

class HotkeyRecorder:
    def __init__(self):
        self.q = queue.Queue()
        self.blocksize = int(SAMPLE_RATE * CHUNK_MS / 1000)
        self.collected = []
        self.stream = None
        self.lock = threading.Lock()
        self.recording = False

    def _callback(self, indata, frames, time_info, status):
        self.q.put(indata.copy())

    def start(self):
        with self.lock:
            if self.recording:
                return
            self.collected = []
            self.q = queue.Queue()
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                blocksize=self.blocksize,
                device=INPUT_DEVICE,
                callback=self._callback,
            )
            self.stream.start()
            self.recording = True
        print(" Grabando… (", HOTKEY_STOP, " para transcribir | ", HOTKEY_CANCEL, " para cancelar)")

        # Drain queue in background while recording
        threading.Thread(target=self._collector_loop, daemon=True).start()

    def _collector_loop(self):
        while True:
            with self.lock:
                rec = self.recording
            if not rec:
                break
            try:
                data = self.q.get(timeout=0.05)
                self.collected.append(data)
            except queue.Empty:
                pass

    def stop_and_get_audio(self):
        with self.lock:
            if not self.recording:
                return None
            self.recording = False
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        if not self.collected:
            return np.zeros(0, dtype=np.float32)
        return _pack_audio(self.collected)

    def cancel(self):
        with self.lock:
            if not self.recording:
                return
            self.recording = False
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.collected = []
        print(" Grabación cancelada.")

rec = HotkeyRecorder()

def transcribe(audio_np):
    if audio_np.size == 0:
        return ""
    segments, _ = model.transcribe(
        audio_np,
        language=LANG,
        vad_filter=False,                 # NO VAD: tú decides cuándo parar
        vad_parameters=dict(min_silence_duration_ms=400),
    )
    return "".join(s.text for s in segments).strip()

def on_start():
    rec.start()
    show_recording_indicator()

def on_stop():
    audio = rec.stop_and_get_audio()
    hide_recording_indicator()
    if audio is None:
        print("No hay grabación activa.")
        return
    print("Transcribiendo…")
    text = transcribe(audio)
    if not text:
        print("…(vacío)")
        return
    pyperclip.copy(text)
    print("Copiado al portapapeles.")
    if PASTE_RESULT:
        # paste to active window
        keyboard.press_and_release("ctrl+v")

def on_cancel():
    rec.cancel()
    hide_recording_indicator()

def on_quit():
    print("Saliendo…")
    hide_recording_indicator()
    try:
        rec.cancel()
    except Exception:
        pass
    os._exit(0)

def main():
    print("Whisper Hotkeys listo.")
    print(f"  {HOTKEY_START}  = Empezar a grabar")
    print(f"  {HOTKEY_STOP}   = Parar + transcribir + pegar")
    print(f"  {HOTKEY_CANCEL} = Cancelar grabación")
    print(f"  {HOTKEY_QUIT}   = Salir")
    print("Mantén el foco en el app donde quieras pegar el texto.")

    keyboard.add_hotkey(HOTKEY_START, on_start, suppress=False)
    keyboard.add_hotkey(HOTKEY_STOP,  on_stop,  suppress=False)
    keyboard.add_hotkey(HOTKEY_CANCEL,on_cancel, suppress=False)
    keyboard.add_hotkey(HOTKEY_QUIT,  on_quit,  suppress=False)

    # Keep process alive
    keyboard.wait()

if __name__ == "__main__":
    main()
