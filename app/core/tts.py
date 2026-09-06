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
    SPEED_STEPS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    BASE_RATE = 175

    def __init__(self, rate=175, volume=1.0):
        self.rate = rate
        self.speed_multiplier = 1.0
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

    def set_speed_multiplier(self, mult):
        self.speed_multiplier = round(mult, 2)
        self.rate = int(self.BASE_RATE * self.speed_multiplier)
        return self.speed_multiplier

    def slower(self):
        """Decreases TTS speed to the previous step, returning the new multiplier."""
        curr = self.speed_multiplier
        smaller = [s for s in self.SPEED_STEPS if s < curr - 0.01]
        new_mult = smaller[-1] if smaller else self.SPEED_STEPS[0]
        return self.set_speed_multiplier(new_mult)

    def faster(self):
        """Increases TTS speed to the next step, returning the new multiplier."""
        curr = self.speed_multiplier
        larger = [s for s in self.SPEED_STEPS if s > curr + 0.01]
        new_mult = larger[0] if larger else self.SPEED_STEPS[-1]
        return self.set_speed_multiplier(new_mult)
