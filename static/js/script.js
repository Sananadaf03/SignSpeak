// script.js — frontend logic for SignSpeak
// Polls /prediction to update the live gesture/sentence display, and wires
// up all the control buttons to their Flask API routes.

(() => {
  const videoFeed = document.getElementById("videoFeed");
  const cameraOverlayText = document.getElementById("cameraOverlayText");
  const handsBadge = document.getElementById("handsBadge");
  const startBtn = document.getElementById("startBtn");
  const stopBtn = document.getElementById("stopBtn");
  const statusLine = document.getElementById("statusLine");

  const gestureName = document.getElementById("gestureName");
  const confidenceValue = document.getElementById("confidenceValue");
  const confidenceBar = document.getElementById("confidenceBar");
  const sentenceText = document.getElementById("sentenceText");

  const speakBtn = document.getElementById("speakBtn");
  const pauseBtn = document.getElementById("pauseBtn");
  const clearBtn = document.getElementById("clearBtn");
  const backspaceBtn = document.getElementById("backspaceBtn");
  const saveBtn = document.getElementById("saveBtn");

  const voiceSelect = document.getElementById("voiceSelect");
  const rateRange = document.getElementById("rateRange");
  const rateValue = document.getElementById("rateValue");

  const historyList = document.getElementById("historyList");
  const themeToggle = document.getElementById("themeToggle");
  const themeLabel = document.getElementById("themeLabel");

  let pollTimer = null;
  let cameraRunning = false;

  // ---------------- Camera control ----------------
  async function startCamera() {
    const res = await fetch("/camera/start", { method: "POST" });
    const data = await res.json();
    if (data.ok) {
      cameraRunning = true;
      videoFeed.src = "/video_feed?ts=" + Date.now();
      cameraOverlayText.hidden = true;
      handsBadge.hidden = false;
      startBtn.disabled = true;
      stopBtn.disabled = false;
      startPolling();
    }
  }

  async function stopCamera() {
    await fetch("/camera/stop", { method: "POST" });
    cameraRunning = false;
    videoFeed.removeAttribute("src");
    cameraOverlayText.hidden = false;
    handsBadge.hidden = true;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    stopPolling();
    statusLine.textContent = "Camera stopped";
  }

  startBtn.addEventListener("click", startCamera);
  stopBtn.addEventListener("click", stopCamera);

  // ---------------- Polling loop ----------------
  function startPolling() {
    if (pollTimer) return;
    pollTimer = setInterval(pollPrediction, 350);
  }
  function stopPolling() {
    clearInterval(pollTimer);
    pollTimer = null;
  }

  async function pollPrediction() {
    try {
      const res = await fetch("/prediction");
      const data = await res.json();

      gestureName.textContent = data.gesture || "—";
      const conf = data.confidence || 0;
      confidenceValue.textContent = conf + "%";
      confidenceBar.style.width = conf + "%";

      sentenceText.textContent = data.sentence
        ? data.sentence
        : "Start signing to build a sentence…";

      statusLine.textContent = data.status || "";
      handsBadge.textContent =
        (data.hands_detected || 0) + (data.hands_detected === 1 ? " hand detected" : " hands detected");
    } catch (err) {
      statusLine.textContent = "Connection issue — retrying…";
    }
  }

  // ---------------- Sentence controls ----------------
  clearBtn.addEventListener("click", async () => {
    const res = await fetch("/clear", { method: "POST" });
    const data = await res.json();
    sentenceText.textContent = "Start signing to build a sentence…";
  });

  backspaceBtn.addEventListener("click", async () => {
    const res = await fetch("/backspace", { method: "POST" });
    const data = await res.json();
    sentenceText.textContent = data.sentence || "Start signing to build a sentence…";
  });

  speakBtn.addEventListener("click", async () => {
    await fetch("/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        voice_id: voiceSelect.value || null,
        rate: Number(rateRange.value),
      }),
    });
  });

  pauseBtn.addEventListener("click", async () => {
    await fetch("/pause_speech", { method: "POST" });
  });

  saveBtn.addEventListener("click", async () => {
    const res = await fetch("/save_history", { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      renderHistory(data.history);
    }
  });

  rateRange.addEventListener("input", () => {
    rateValue.textContent = rateRange.value;
  });

  // ---------------- Voices ----------------
  async function loadVoices() {
    try {
      const res = await fetch("/voices");
      const voices = await res.json();
      voiceSelect.innerHTML = "";
      if (!voices.length) {
        const opt = document.createElement("option");
        opt.textContent = "Default voice";
        voiceSelect.appendChild(opt);
        return;
      }
      voices.forEach((v) => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = `${v.name} (${v.gender_guess})`;
        voiceSelect.appendChild(opt);
      });
    } catch (err) {
      /* voices are optional; fail silently */
    }
  }

  // ---------------- History ----------------
  function renderHistory(items) {
    historyList.innerHTML = "";
    if (!items || !items.length) {
      const li = document.createElement("li");
      li.className = "history-empty";
      li.textContent = "No saved sentences yet.";
      historyList.appendChild(li);
      return;
    }
    items.forEach((item) => {
      const li = document.createElement("li");
      const text = document.createElement("div");
      text.textContent = item.sentence;
      const time = document.createElement("time");
      time.textContent = item.timestamp;
      li.appendChild(text);
      li.appendChild(time);
      historyList.appendChild(li);
    });
  }

  async function loadHistory() {
    try {
      const res = await fetch("/history");
      const items = await res.json();
      renderHistory(items);
    } catch (err) {
      /* ignore */
    }
  }

  // ---------------- Theme ----------------
  themeToggle.addEventListener("click", () => {
    const body = document.body;
    const isDark = body.getAttribute("data-theme") === "dark";
    body.setAttribute("data-theme", isDark ? "light" : "dark");
    themeLabel.textContent = isDark ? "Light" : "Dark";
  });

  // ---------------- Init ----------------
  loadVoices();
  loadHistory();
})();
