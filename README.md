# 🤟 SignSpeak — Sign Language Interpreter

## 📌 Project Overview

**SignSpeak** is a real-time sign language interpretation application that uses a webcam to recognize hand gestures and convert them into meaningful text and speech.

The application uses **MediaPipe Hands** for hand landmark detection, **OpenCV** for webcam processing, and a geometry-based gesture recognition system to identify supported sign language gestures.

Recognized gestures can be combined into sentences and converted into speech using text-to-speech functionality.

## 🎯 Objectives

* Recognize hand gestures in real time using a webcam.
* Detect hand landmarks using MediaPipe.
* Classify supported sign language gestures.
* Convert recognized gestures into text.
* Build sentences from individual gestures.
* Convert generated sentences into speech.
* Provide an interactive and accessible web interface.

## ✨ Features

### 🤚 Real-Time Hand Detection

The application uses **MediaPipe Hands** to detect hand landmarks from the webcam.

It supports detection of up to **two hands** simultaneously.

### 🔤 Gesture Recognition

The system recognizes predefined hand gestures using:

* Finger states
* Distances between landmarks
* Joint angles
* Hand orientation
* Gesture-specific rules

The recognized gesture is displayed in real time.

### 📝 Sentence Builder

Recognized gestures can be combined to form sentences.

Users can:

* Add words
* Undo the last word
* Clear the sentence
* Save sentences
* View previous sentences

### 🔊 Text-to-Speech

The generated sentence can be converted into spoken audio.

The interface provides controls for:

* Voice selection
* Speech speed
* Speak
* Pause

### 📊 Confidence Display

The application displays a confidence value for the detected gesture along with a visual confidence bar.

### 🌓 Light and Dark Mode

The web interface supports both:

* Dark mode
* Light mode

### 📜 History

Previously saved sentences can be viewed through the history section.

## 🧠 Gesture Recognition Approach

Unlike a black-box machine learning classifier, the gesture recognition system uses **explicit geometric rules**.

MediaPipe extracts **21 hand landmarks**, which are then processed to determine the state of each finger.

The system evaluates:

* Finger extension
* Finger bending
* Landmark distances
* Joint angles
* Thumb orientation
* Handedness

The resulting finger-state pattern is compared against predefined gesture rules.

```text
Webcam
   ↓
OpenCV Frame Capture
   ↓
MediaPipe Hands
   ↓
21 Hand Landmarks
   ↓
Finger-State Extraction
   ↓
Distance & Angle Analysis
   ↓
Gesture Rule Matching
   ↓
Recognized Gesture
   ↓
Sentence Builder
   ↓
Text-to-Speech
```

## 🛠️ Technologies Used

* **Python**
* **Flask**
* **OpenCV**
* **MediaPipe**
* **NumPy**
* **HTML5**
* **CSS3**
* **JavaScript**
* **Text-to-Speech**
* **Computer Vision**
* **Hand Gesture Recognition**

## 📁 Project Structure

```text
SignSpeak/
│
├── app.py
├── gesture_data.py
├── gesture_recognizer.py
├── sentence_builder.py
├── text_to_speech.py
├── test_gestures.py
├── requirements.txt
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
└── README.md
```

## 📄 File Description

| File                    | Purpose                                          |
| ----------------------- | ------------------------------------------------ |
| `app.py`                | Main Flask application and API routes            |
| `gesture_data.py`       | Gesture definitions and recognition rules        |
| `gesture_recognizer.py` | MediaPipe hand detection and gesture recognition |
| `sentence_builder.py`   | Builds and manages recognized sentences          |
| `text_to_speech.py`     | Converts text into speech                        |
| `test_gestures.py`      | Unit and live gesture testing                    |
| `templates/index.html`  | Main web interface                               |
| `static/css/style.css`  | Application styling                              |
| `static/js/script.js`   | Frontend interaction and API communication       |
| `requirements.txt`      | Python dependencies                              |

## ✋ Supported Gestures

The application contains predefined gesture rules for supported signs such as:

* Hello
* Yes
* No
* Thank You
* Alphabet gestures
* Other configured gestures

The exact supported gesture set is defined in `gesture_data.py`.

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Sananadaf03/SignSpeak.git
```

### 2. Open the Project

```bash
cd SignSpeak
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Application

```bash
python app.py
```

Open the local URL displayed in the terminal in your web browser.

## 🧪 Testing

### Run Unit Tests

```bash
python test_gestures.py --unit
```

The unit tests check the gesture matching logic without requiring a webcam.

### Run Live Testing

```bash
python test_gestures.py --live
```

This opens the webcam and allows gesture predictions to be manually evaluated.

## 💡 Applications

SignSpeak demonstrates potential applications in:

* Accessibility technology
* Human-computer interaction
* Assistive communication
* Educational tools
* Sign language learning
* Real-time gesture interfaces

## 🔮 Future Improvements

* Expand the gesture vocabulary.
* Support continuous sign-language sentence recognition.
* Add more regional sign languages.
* Improve gesture disambiguation.
* Add a trained deep-learning gesture classifier.
* Support mobile and browser-based camera access.
* Add multilingual text-to-speech.
* Improve recognition under different lighting conditions.
* Add user-customizable gestures.

## 📌 Project Type

**Computer Vision | Artificial Intelligence | Assistive Technology | Hand Gesture Recognition | Flask | MediaPipe**

## 👩‍💻 Author

**Sana L. Nadaf**

B.E. Computer Science & Engineering

GitHub: `Sananadaf03`
