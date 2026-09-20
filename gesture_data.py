"""
gesture_data.py
----------------
Static reference data used by gesture_recognizer.py to classify hand gestures.

MediaPipe Hands gives us 21 landmarks per hand, indexed 0-20:
    0  - WRIST
    1-4   - THUMB (CMC, MCP, IP, TIP)
    5-8   - INDEX_FINGER (MCP, PIP, DIP, TIP)
    9-12  - MIDDLE_FINGER (MCP, PIP, DIP, TIP)
    13-16 - RING_FINGER (MCP, PIP, DIP, TIP)
    17-20 - PINKY (MCP, PIP, DIP, TIP)

Rather than hard-coding raw pixel coordinates (which change with hand size,
camera distance, and position on screen), every gesture below is described
as a *normalized rule*: which fingers are extended/curled, and the relative
angles/distances between key landmarks. gesture_recognizer.py computes these
same features live from the webcam feed and compares them against the rules
here.

Adding a new gesture is a matter of adding one entry to GESTURE_RULES.
"""

# Landmark index constants (matches MediaPipe's HandLandmark enum ordering)
WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

FINGER_TIPS = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
FINGER_PIPS = [THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]
FINGER_MCPS = [THUMB_MCP, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP]
FINGER_NAMES = ["thumb", "index", "middle", "ring", "pinky"]

# -----------------------------------------------------------------------
# GESTURE_RULES
# -----------------------------------------------------------------------
# Each rule is expressed as a "finger state" pattern: a 5-length tuple of
# 1 (extended) / 0 (curled) for [thumb, index, middle, ring, pinky],
# plus optional extra geometric checks (used by gesture_recognizer.py)
# such as thumb direction, or relative tip distances for pinches.
#
# `two_hand` marks gestures that require both hands to be present.
# `sequence` marks letters/numbers that are meant to be chained together
# by sentence_builder.py into words.
# -----------------------------------------------------------------------

GESTURE_RULES = {
    # ---- Common words / phrases ----
    "HELLO": {
        "fingers": (1, 1, 1, 1, 1),          # open palm
        "extra": "palm_facing_camera",
        "two_hand": False,
        "category": "word",
    },
    "YES": {
        "fingers": (0, 0, 0, 0, 0),          # closed fist, nodding motion
        "extra": "fist_vertical_bob",
        "two_hand": False,
        "category": "word",
    },
    "NO": {
        "fingers": (1, 1, 0, 0, 0),          # index + middle pinch open/close vs thumb
        "extra": "index_middle_thumb_tap",
        "two_hand": False,
        "category": "word",
    },
    "THANK_YOU": {
        "fingers": (1, 1, 1, 1, 1),
        "extra": "flat_hand_chin_to_forward",
        "two_hand": False,
        "category": "word",
    },
    "HELP": {
        "fingers": (1, 0, 0, 0, 0),          # thumbs up resting on other flat palm
        "extra": "thumb_on_opposite_palm",
        "two_hand": True,
        "category": "word",
    },
    "I_LOVE_YOU": {
        "fingers": (1, 1, 0, 0, 1),          # thumb, index, pinky extended (ILY sign)
        "extra": None,
        "two_hand": False,
        "category": "word",
    },

    # ---- Alphabet A-Z (subset shown fully implemented; rest follow same pattern) ----
    "A": {"fingers": (1, 0, 0, 0, 0), "extra": "fist_thumb_side", "two_hand": False, "category": "letter"},
    "B": {"fingers": (0, 1, 1, 1, 1), "extra": "thumb_across_palm", "two_hand": False, "category": "letter"},
    "C": {"fingers": (1, 1, 1, 1, 1), "extra": "curved_c_shape", "two_hand": False, "category": "letter"},
    "D": {"fingers": (0, 1, 0, 0, 0), "extra": "thumb_touches_middle", "two_hand": False, "category": "letter"},
    "E": {"fingers": (0, 0, 0, 0, 0), "extra": "fingertips_curl_to_thumb", "two_hand": False, "category": "letter"},
    "F": {"fingers": (0, 0, 1, 1, 1), "extra": "thumb_index_pinch", "two_hand": False, "category": "letter"},
    "I": {"fingers": (0, 0, 0, 0, 1), "extra": None, "two_hand": False, "category": "letter"},
    "L": {"fingers": (1, 1, 0, 0, 0), "extra": "right_angle", "two_hand": False, "category": "letter"},
    "O": {"fingers": (1, 1, 1, 1, 1), "extra": "all_tips_touch_thumb", "two_hand": False, "category": "letter"},
    "V": {"fingers": (0, 1, 1, 0, 0), "extra": "index_middle_spread", "two_hand": False, "category": "letter"},
    "W": {"fingers": (0, 1, 1, 1, 0), "extra": None, "two_hand": False, "category": "letter"},
    "Y": {"fingers": (1, 0, 0, 0, 1), "extra": None, "two_hand": False, "category": "letter"},

    # ---- Numbers 0-9 (standard ASL counting handshapes) ----
    "0": {"fingers": (1, 1, 1, 1, 1), "extra": "all_tips_touch_thumb", "two_hand": False, "category": "number"},
    "1": {"fingers": (0, 1, 0, 0, 0), "extra": None, "two_hand": False, "category": "number"},
    "2": {"fingers": (0, 1, 1, 0, 0), "extra": None, "two_hand": False, "category": "number"},
    "3": {"fingers": (1, 1, 1, 0, 0), "extra": None, "two_hand": False, "category": "number"},
    "4": {"fingers": (0, 1, 1, 1, 1), "extra": None, "two_hand": False, "category": "number"},
    "5": {"fingers": (1, 1, 1, 1, 1), "extra": "spread_fingers", "two_hand": False, "category": "number"},
}

# Gestures that build the "core 10+" required set explicitly classified
# with distance/angle logic in gesture_recognizer.py (kept as a constant
# so tests / docs can reference the guaranteed-supported set).
CORE_SUPPORTED_GESTURES = [
    "HELLO", "YES", "NO", "THANK_YOU", "HELP", "I_LOVE_YOU",
    "A", "B", "C", "D", "L", "O", "V", "Y",
    "0", "1", "2", "3", "4", "5",
]

# Confidence thresholds used by gesture_recognizer.py
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.6
GESTURE_HOLD_FRAMES = 12          # frames a gesture must be stable before it "commits"
GESTURE_MATCH_THRESHOLD = 0.90    # fraction of rule features that must match
