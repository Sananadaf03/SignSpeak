"""
sentence_builder.py
--------------------
Turns a stream of *committed* gestures (from gesture_recognizer.py) into
words and full sentences.

Rules:
  - Whole-word gestures (HELLO, YES, NO, THANK_YOU, HELP, I_LOVE_YOU) are
    inserted directly as words, followed by a space.
  - Letter gestures (A, B, C, ...) are appended to an in-progress "current
    word" buffer. When a pause is detected (no committed gesture for
    WORD_GAP_SECONDS) the current word is flushed into the sentence.
  - Number gestures are appended similarly, treated as their own "word".
  - Auto-space is inserted between words; the sentence is auto-cleared
    after being spoken & saved, or on demand.
"""

import time


WORD_GAP_SECONDS = 2.5   # pause length that signals "end of word"
SENTENCE_GESTURES = {
    "HELLO": "Hello",
    "YES": "Yes",
    "NO": "No",
    "THANK_YOU": "Thank you",
    "HELP": "Help",
    "I_LOVE_YOU": "I love you",
}


class SentenceBuilder:
    def __init__(self):
        self.sentence = ""
        self._current_word = ""
        self._last_gesture_time = None

    def _flush_word(self):
        if self._current_word:
            self.sentence = (self.sentence + self._current_word + " ").lstrip()
            self._current_word = ""

    def add_gesture(self, gesture_name: str):
        """Feed one committed gesture into the builder. Call this only when
        gesture_recognizer.py reports `committed = True`."""
        now = time.time()

        # If enough time has passed since the last gesture, flush any
        # in-progress word first (handles the "pause = word boundary" rule).
        if self._last_gesture_time and (now - self._last_gesture_time) > WORD_GAP_SECONDS:
            self._flush_word()

        self._last_gesture_time = now

        if gesture_name in SENTENCE_GESTURES:
            # Whole-word / phrase gesture — flush any pending letters first,
            # then insert the phrase as its own word.
            self._flush_word()
            self.sentence = (self.sentence + SENTENCE_GESTURES[gesture_name] + " ").lstrip()
        else:
            # Letter or number — append to the word currently being spelled.
            self._current_word += gesture_name

        return self.get_display_sentence()

    def maybe_flush_on_timeout(self):
        """Call periodically (e.g. once per video frame) so a word gets
        flushed into the sentence even if no new gesture arrives."""
        if (
            self._current_word
            and self._last_gesture_time
            and (time.time() - self._last_gesture_time) > WORD_GAP_SECONDS
        ):
            self._flush_word()
        return self.get_display_sentence()

    def get_display_sentence(self):
        """Sentence so far, including the word currently being spelled."""
        return (self.sentence + self._current_word).strip()

    def clear(self):
        self.sentence = ""
        self._current_word = ""
        self._last_gesture_time = None

    def backspace_word(self):
        """Remove the last completed word (undo)."""
        if self._current_word:
            self._current_word = ""
            return self.get_display_sentence()
        words = self.sentence.strip().split(" ")
        if words:
            words = words[:-1]
        self.sentence = (" ".join(words) + " ") if words else ""
        return self.get_display_sentence()
