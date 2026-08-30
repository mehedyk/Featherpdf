"""
core/tts.py
Thin wrapper around pyttsx3 (calls the OS's own speech engine -- SAPI5 on
Windows, NSSpeechSynthesizer on macOS, espeak on Linux -- so no voice
model gets bundled with the app). Runs on a background thread so speaking
never freezes the GUI, with a stop() that can be called from the main thread.
"""
import threading

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class TextToSpeech:
    def __init__(self, rate=175, volume=1.0):
        self.rate = rate
        self.volume = volume
        self._engine = None
        self._thread = None
        self._lock = threading.Lock()

    def is_speaking(self):
        return self._thread is not None and self._thread.is_alive()

    def speak(self, text, on_done=None):
        """Starts speaking `text` on a background thread. Returns False if
        TTS isn't available on this system or text is empty."""
        if not TTS_AVAILABLE or not text or not text.strip():
            return False

        self.stop()

        def run():
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                with self._lock:
                    self._engine = engine
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass
            finally:
                with self._lock:
                    self._engine = None
                if on_done:
                    on_done()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        with self._lock:
            engine = self._engine
        if engine is not None:
            try:
                engine.stop()
            except Exception:
                pass

    def set_rate(self, rate):
        self.rate = rate
