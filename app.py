"""
app.py
------
Main Flask application.

Routes:
  GET  /                    - Main UI
  GET  /video_feed          - MJPEG live webcam stream with skeleton overlay
  GET  /prediction           - Latest gesture prediction + confidence (polled by JS)
  POST /speak                - Speak the current sentence out loud
  POST /clear                - Clear the current sentence
  POST /backspace             - Remove the last word
  POST /save_history           - Save current sentence + timestamp to history
  GET  /history                - Fetch saved history
  GET  /voices                 - List available TTS voices
  POST /camera/start | /camera/stop - Toggle the webcam capture thread

Run with:  python app.py
"""

import json
import os
import threading
import time
from datetime import datetime

import cv2
from flask import Flask, Response, jsonify, render_template, request

from gesture_recognizer import GestureRecognizer
from sentence_builder import SentenceBuilder
from text_to_speech import TextToSpeech

app = Flask(__name__)

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")

recognizer = GestureRecognizer(max_num_hands=2)
builder = SentenceBuilder()
tts = TextToSpeech()

# ---------------------------------------------------------------------
# Shared mutable state (protected by a lock since Flask's dev server and
# the camera thread both touch it). For a production deployment this
# would move to Redis or a proper session store.
# ---------------------------------------------------------------------
state_lock = threading.Lock()
state = {
    "camera_on": False,
    "gesture": None,
    "confidence": 0.0,
    "status": "Camera stopped",
    "hands_detected": 0,
}

camera = None
camera_thread = None
stop_camera_flag = threading.Event()


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history_entry(sentence):
    history = load_history()
    history.insert(0, {
        "sentence": sentence,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    history = history[:200]  # keep last 200 entries
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    return history


# ---------------------------------------------------------------------
# Camera / gesture loop
# ---------------------------------------------------------------------
latest_frame = None
frame_lock = threading.Lock()


def camera_loop():
    global camera, latest_frame

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        with state_lock:
            state["status"] = "Could not access webcam"
            state["camera_on"] = False
        return

    while not stop_camera_flag.is_set():
        ok, frame = camera.read()
        if not ok:
            with state_lock:
                state["status"] = "Webcam read failed"
            time.sleep(0.1)
            continue

        frame = cv2.flip(frame, 1)  # mirror for a natural "looking in a mirror" feel
        annotated, result = recognizer.process_frame(frame)

        with state_lock:
            state["gesture"] = result["gesture"]
            state["confidence"] = result["confidence"]
            state["status"] = result["status"]
            state["hands_detected"] = result["hands_detected"]

        if result["committed"] and result["gesture"]:
            builder.add_gesture(result["gesture"])
        else:
            builder.maybe_flush_on_timeout()

        ok2, buffer = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if ok2:
            with frame_lock:
                latest_frame = buffer.tobytes()

        time.sleep(0.01)  # yield briefly; keeps CPU usage reasonable

    camera.release()
    camera = None


def gen_frames():
    """Generator used by the /video_feed MJPEG route."""
    blank_notice_sent = False
    while True:
        with frame_lock:
            frame_bytes = latest_frame

        with state_lock:
            camera_on = state["camera_on"]

        if not camera_on or frame_bytes is None:
            if not blank_notice_sent:
                blank_notice_sent = True
            time.sleep(0.1)
            continue

        blank_notice_sent = False
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/camera/start", methods=["POST"])
def camera_start():
    global camera_thread
    with state_lock:
        if state["camera_on"]:
            return jsonify({"ok": True, "already_running": True})
        state["camera_on"] = True
        state["status"] = "Starting camera..."

    stop_camera_flag.clear()
    camera_thread = threading.Thread(target=camera_loop, daemon=True)
    camera_thread.start()
    return jsonify({"ok": True})


@app.route("/camera/stop", methods=["POST"])
def camera_stop():
    stop_camera_flag.set()
    with state_lock:
        state["camera_on"] = False
        state["status"] = "Camera stopped"
        state["gesture"] = None
        state["confidence"] = 0.0
    return jsonify({"ok": True})


@app.route("/prediction")
def prediction():
    with state_lock:
        data = dict(state)
    data["sentence"] = builder.get_display_sentence()
    return jsonify(data)


@app.route("/speak", methods=["POST"])
def speak():
    sentence = builder.get_display_sentence()
    voice_id = request.json.get("voice_id") if request.is_json else None
    rate = request.json.get("rate", 160) if request.is_json else 160

    def _do_speak():
        tts.speak(sentence, voice_id=voice_id, rate=rate)

    threading.Thread(target=_do_speak, daemon=True).start()
    return jsonify({"ok": True, "sentence": sentence})


@app.route("/pause_speech", methods=["POST"])
def pause_speech():
    ok = tts.pause()
    return jsonify({"ok": ok})


@app.route("/clear", methods=["POST"])
def clear():
    builder.clear()
    return jsonify({"ok": True, "sentence": ""})


@app.route("/backspace", methods=["POST"])
def backspace():
    sentence = builder.backspace_word()
    return jsonify({"ok": True, "sentence": sentence})


@app.route("/save_history", methods=["POST"])
def save_history():
    sentence = builder.get_display_sentence()
    if not sentence.strip():
        return jsonify({"ok": False, "error": "Nothing to save"}), 400
    history = save_history_entry(sentence)
    return jsonify({"ok": True, "history": history})


@app.route("/history")
def history():
    return jsonify(load_history())


@app.route("/voices")
def voices():
    return jsonify(tts.list_voices())


if __name__ == "__main__":
    # debug=False avoids the reloader spawning a second camera thread
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
