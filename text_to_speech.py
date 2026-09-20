"""
text_to_speech.py
------------------
Wraps pyttsx3 (offline TTS engine) to speak the formed sentence out loud,
with voice (male/female) and speed selection. Falls back to gTTS (which
requires internet) if pyttsx3 fails to initialize on the host machine —
this keeps the app usable in more environments (e.g. some Linux servers
lack pyttsx3's native speech driver).
"""

import os
import tempfile
import threading

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except Exception:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except Exception:
    GTTS_AVAILABLE = False


class TextToSpeech:
    def __init__(self):
        self.engine = None
        self.voices = []
        self._lock = threading.Lock()

        if PYTTSX3_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self.voices = self.engine.getProperty("voices")
                self.engine.setProperty("rate", 160)  # default speaking rate
            except Exception:
                self.engine = None

    # ------------------------------------------------------------------
    def list_voices(self):
        """Returns [{"id": ..., "name": ..., "gender_guess": "male"/"female"}]"""
        result = []
        for v in self.voices:
            name_lower = (v.name or "").lower()
            if "female" in name_lower or "zira" in name_lower or "samantha" in name_lower:
                guess = "female"
            elif "male" in name_lower or "david" in name_lower:
                guess = "male"
            else:
                guess = "unknown"
            result.append({"id": v.id, "name": v.name, "gender_guess": guess})
        return result

    def speak(self, text: str, voice_id: str = None, rate: int = 160):
        """Synchronously speaks `text`. Run this in a background thread from
        Flask so it doesn't block the request."""
        if not text:
            return {"ok": False, "error": "Empty sentence"}

        with self._lock:
            if self.engine:
                try:
                    if voice_id:
                        self.engine.setProperty("voice", voice_id)
                    self.engine.setProperty("rate", rate)
                    self.engine.say(text)
                    self.engine.runAndWait()
                    return {"ok": True, "engine": "pyttsx3"}
                except Exception as e:
                    pass  # fall through to gTTS

            if GTTS_AVAILABLE:
                try:
                    tts = gTTS(text=text, lang="en")
                    tmp_path = os.path.join(tempfile.gettempdir(), "sli_speech.mp3")
                    tts.save(tmp_path)
                    return {"ok": True, "engine": "gTTS", "file": tmp_path}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            return {"ok": False, "error": "No TTS engine available"}

    def pause(self):
        """pyttsx3 has no native pause; stop() halts the current utterance."""
        if self.engine:
            try:
                self.engine.stop()
                return True
            except Exception:
                return False
        return False

    def save_to_file(self, text: str, filepath: str):
        """Save spoken sentence audio to an mp3/wav file (uses gTTS for
        portability across OSes)."""
        if GTTS_AVAILABLE:
            gTTS(text=text, lang="en").save(filepath)
            return filepath
        raise RuntimeError("gTTS not available to save audio file")
