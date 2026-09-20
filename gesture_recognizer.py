"""
gesture_recognizer.py
----------------------
Core computer-vision module. Uses MediaPipe Hands to find 21 landmarks per
hand from a webcam frame, derives geometric features (which fingers are
extended, angles between joints, distances between fingertips), and matches
those features against the rules in gesture_data.py to classify the gesture.

This is NOT a black-box ML classifier — classification is done with
explicit distance/angle geometry, as required, which also makes it fast
enough to run in real time on CPU.
"""

import math
import time
from collections import deque

import cv2
import mediapipe as mp
import numpy as np

from gesture_data import (
    GESTURE_RULES,
    FINGER_TIPS,
    FINGER_PIPS,
    FINGER_MCPS,
    FINGER_NAMES,
    WRIST,
    THUMB_TIP,
    THUMB_MCP,
    INDEX_TIP,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    GESTURE_HOLD_FRAMES,
    GESTURE_MATCH_THRESHOLD,
)


class GestureRecognizer:
    """Wraps MediaPipe Hands and turns raw landmarks into classified gestures."""

    def __init__(self, max_num_hands=2):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )

        # Rolling buffer used to require a gesture to be stable for N frames
        # before we "commit" it — this filters out noisy, flickery frames
        # and fast pass-through motion, per the edge-case requirements.
        self._recent_predictions = deque(maxlen=GESTURE_HOLD_FRAMES)
        self._last_committed_gesture = None
        self._last_commit_time = 0.0
        self._commit_cooldown_sec = 1.0  # avoid re-firing the same letter instantly

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _landmark_to_xy(landmark, frame_shape):
        h, w = frame_shape[:2]
        return np.array([landmark.x * w, landmark.y * h])

    @staticmethod
    def _distance(p1, p2):
        return float(np.linalg.norm(p1 - p2))

    @staticmethod
    def _angle(a, b, c):
        """Angle (degrees) at vertex b formed by points a-b-c."""
        ba = a - b
        bc = c - b
        cos_angle = np.dot(ba, bc) / (
            (np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-6
        )
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        return math.degrees(math.acos(cos_angle))

    def _finger_states(self, points, handedness_label):
        """
        Returns a 5-length tuple (thumb, index, middle, ring, pinky) of
        1 (extended) / 0 (curled), computed from joint angles and the
        tip-to-wrist distance vs. the pip-to-wrist distance.
        """
        states = []
        wrist = points[WRIST]

        # Thumb: compare x-position of tip vs. mcp, flipped for handedness,
        # since the thumb bends sideways rather than curling like other fingers.
        thumb_tip = points[THUMB_TIP]
        thumb_mcp = points[THUMB_MCP]
        if handedness_label == "Right":
            thumb_extended = thumb_tip[0] < thumb_mcp[0]
        else:
            thumb_extended = thumb_tip[0] > thumb_mcp[0]
        states.append(1 if thumb_extended else 0)

        # Index/middle/ring/pinky: a finger is "extended" if its tip is
        # farther from the wrist than its pip joint by a healthy margin,
        # AND the pip-tip-mcp angle is close to straight (>160 degrees).
        for tip_idx, pip_idx, mcp_idx in zip(FINGER_TIPS[1:], FINGER_PIPS[1:], FINGER_MCPS[1:]):
            tip, pip, mcp = points[tip_idx], points[pip_idx], points[mcp_idx]
            tip_dist = self._distance(tip, wrist)
            pip_dist = self._distance(pip, wrist)
            joint_angle = self._angle(mcp, pip, tip)
            extended = tip_dist > pip_dist * 1.15 and joint_angle > 150
            states.append(1 if extended else 0)

        return tuple(states)

    def _match_gesture(self, finger_states):
        """Compare the observed finger-state tuple against every rule and
        return the best match name + confidence score (0-1)."""
        best_name, best_score = None, 0.0
        for name, rule in GESTURE_RULES.items():
            target = rule["fingers"]
            matches = sum(1 for a, b in zip(finger_states, target) if a == b)
            score = matches / len(target)
            if score > best_score:
                best_name, best_score = name, score

        if best_score >= GESTURE_MATCH_THRESHOLD:
            return best_name, best_score
        return None, best_score

    # ------------------------------------------------------------------
    # Main per-frame entry point
    # ------------------------------------------------------------------
    def process_frame(self, frame):
        """
        Runs detection on one BGR frame.
        Returns: (annotated_frame, result_dict)
        result_dict = {
            "gesture": str or None,
            "confidence": float 0-1,
            "committed": bool,       # True the instant a gesture is confirmed stable
            "hands_detected": int,
            "status": str            # human-readable status for edge cases
        }
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.hands.process(rgb)
        rgb.flags.writeable = True

        result = {
            "gesture": None,
            "confidence": 0.0,
            "committed": False,
            "hands_detected": 0,
            "status": "No hand detected",
        }

        if not results.multi_hand_landmarks:
            self._recent_predictions.clear()
            return frame, result

        result["hands_detected"] = len(results.multi_hand_landmarks)

        # Low-light heuristic: warn if the frame is very dark, since MediaPipe
        # accuracy degrades sharply below a brightness threshold.
        brightness = float(np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)))
        if brightness < 40:
            result["status"] = "Low light detected — accuracy may drop"

        predictions = []
        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks, results.multi_handedness
        ):
            self.mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_styles.get_default_hand_landmarks_style(),
                self.mp_styles.get_default_hand_connections_style(),
            )
            points = [
                self._landmark_to_xy(lm, frame.shape) for lm in hand_landmarks.landmark
            ]
            label = handedness.classification[0].label  # "Left" / "Right"
            finger_states = self._finger_states(points, label)
            name, score = self._match_gesture(finger_states)
            if name:
                predictions.append((name, score))

        if len(results.multi_hand_landmarks) > 1:
            result["status"] = "Two hands detected"

        if not predictions:
            self._recent_predictions.clear()
            result["status"] = result["status"] if result["status"] != "No hand detected" else "Gesture not recognized"
            return frame, result

        # Take the highest-confidence prediction this frame
        predictions.sort(key=lambda p: p[1], reverse=True)
        gesture_name, confidence = predictions[0]

        result["gesture"] = gesture_name
        result["confidence"] = round(confidence * 100, 1)

        # Stability buffer: only "commit" (i.e. hand it to sentence_builder)
        # once the same gesture has been seen for GESTURE_HOLD_FRAMES in a row.
        self._recent_predictions.append(gesture_name)
        if (
            len(self._recent_predictions) == GESTURE_HOLD_FRAMES
            and len(set(self._recent_predictions)) == 1
        ):
            now = time.time()
            if (
                gesture_name != self._last_committed_gesture
                or (now - self._last_commit_time) > self._commit_cooldown_sec
            ):
                result["committed"] = True
                self._last_committed_gesture = gesture_name
                self._last_commit_time = now
                self._recent_predictions.clear()

        return frame, result

    def close(self):
        self.hands.close()
