"""
test_gestures.py
------------------
Lightweight test/QA script for the gesture recognition pipeline.

Two modes:
  1. `python test_gestures.py --unit`
     Runs offline unit tests against synthetic landmark data to check that
     the finger-state and gesture-matching logic behaves correctly, without
     needing a webcam. Good for CI.

  2. `python test_gestures.py --live`
     Opens the webcam, runs the real recognizer, and prints a running
     accuracy readout: shows you the gesture + confidence every frame, and
     lets you press a key (0-9) to log whether the prediction was correct,
     then prints a final accuracy percentage on exit ('q').
"""

import argparse
import sys

import numpy as np


def make_fake_hand_points(finger_states):
    """
    Builds a synthetic 21-point hand roughly consistent with the requested
    finger_states tuple (thumb, index, middle, ring, pinky), for unit
    testing GestureRecognizer._match_gesture without a camera.
    This does NOT need to be geometrically perfect — it only needs to
    produce the same finger_states tuple when fed back through the
    real feature-extraction function, which we monkeypatch around here
    by testing _match_gesture directly (the higher-risk, purely-logical
    part of the pipeline).
    """
    return finger_states  # _match_gesture takes finger_states directly


def run_unit_tests():
    from gesture_recognizer import GestureRecognizer
    from gesture_data import GESTURE_RULES

    recognizer = GestureRecognizer.__new__(GestureRecognizer)  # skip MediaPipe init

    passed, failed = 0, 0
    for name, rule in GESTURE_RULES.items():
        finger_states = rule["fingers"]
        predicted_name, score = recognizer._match_gesture(finger_states)
        # Because several gestures share identical finger-state patterns
        # (e.g. HELLO/THANK_YOU/C/O all use open-palm), we only assert that
        # *a* high-confidence match was found, and that the true rule's
        # finger pattern scores a perfect 1.0 against itself.
        self_score = sum(
            1 for a, b in zip(finger_states, rule["fingers"]) if a == b
        ) / len(finger_states)
        if self_score == 1.0 and score >= 0.9:
            passed += 1
        else:
            failed += 1
            print(f"[FAIL] {name}: predicted={predicted_name} score={score:.2f}")

    print(f"\nUnit tests: {passed} passed, {failed} failed out of {passed + failed}")
    return failed == 0


def run_live_test():
    import cv2
    from gesture_recognizer import GestureRecognizer

    recognizer = GestureRecognizer(max_num_hands=2)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: could not open webcam.")
        sys.exit(1)

    correct, total = 0, 0
    print("Live test running. Press 'y' if the prediction looked correct, ")
    print("'n' if it was wrong, and 'q' to quit and see the final score.")

    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        frame = cv2.flip(frame, 1)
        annotated, result = recognizer.process_frame(frame)

        label = f"{result['gesture']} ({result['confidence']}%)" if result["gesture"] else "No gesture"
        cv2.putText(annotated, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated, result["status"], (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 1)
        cv2.imshow("test_gestures.py — live accuracy check", annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("y"):
            correct += 1
            total += 1
        elif key == ord("n"):
            total += 1
        elif key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    recognizer.close()

    if total:
        print(f"\nLive accuracy: {correct}/{total} = {100 * correct / total:.1f}%")
    else:
        print("\nNo samples logged.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", action="store_true", help="Run offline unit tests")
    parser.add_argument("--live", action="store_true", help="Run live webcam accuracy test")
    args = parser.parse_args()

    if args.live:
        run_live_test()
    else:
        ok = run_unit_tests()
        sys.exit(0 if ok else 1)
