# VoiceBridge AI 🎙️👓
**Real-Time Stealth Teleprompter & Live Interview Co-Pilot**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![CUDA Enabled](https://img.shields.io/badge/CUDA-RTX_2050_4GB-green.svg)](https://developer.nvidia.com/cuda-zone)
[![Groq API](https://img.shields.io/badge/LLM-Groq_Llama_3.3_70B-orange.svg)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

VoiceBridge AI is a lightweight, local-first Windows desktop accessibility assistant and live interview co-pilot. It is engineered to help non-native English speakers and developers participate smoothly in international technical interviews (Google Meet, Microsoft Teams, Zoom) and record pitch videos without freezing on complex English phrasing or losing direct eye contact with the camera.

---

## ⚡ Key Highlights

- **Stealth Top-Center Teleprompter (`PyQt6` + Windows API):**
  - Translucent, frameless, `Always on Top` overlay pinned directly beneath the physical webcam bezel to maintain natural gaze alignment.
  - Hardened with Windows Desktop Duplication / Capture Exclusion via `ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)`. **The overlay is fully visible to you on screen, yet 100% invisible to others during full screen-sharing in Zoom, Teams, Meet, or OBS.**
- **Voice-Tracked Auto-Scrolling (`faster-whisper` + `rapidfuzz`):**
  - Captures your microphone and runs local STT using `faster-whisper` (`base.en` in `int8_float16` on NVIDIA RTX 2050 CUDA, consuming <700 MB VRAM).
  - Matches spoken words against the loaded script in real time via rapid Levenshtein distance, dynamically highlighting the active sentence and scrolling automatically at your exact speaking pace.
- **Dual-Channel Audio Architecture:**
  - **Interviewer Channel:** Captures system audio via Windows WASAPI Loopback (`soundcard`) running in an isolated subprocess with calibrated 1.75s silence thresholds.
  - **Speaker Channel:** Continuous microphone capture (`sounddevice`) into high-throughput daemon worker queues.
- **Low-Latency LLM Co-Pilot (<400ms):**
  - Streams concise spoken-English bullet points directly onto the overlay using Groq API (`llama-3.3-70b-versatile` with automatic fallbacks to `gpt-oss-120b` and `gpt-oss-20b`).
  - Grounded in personal technical profile notes (`config/profile_context.md`) including Web Accessibility (WCAG 2.1/2.2, NVDA, Axe), aviation-grade compliance (2 years LATAM SGSO), and validated STAR interview stories.
- **Global System-Wide Hotkeys (`pynput`):**
  - Controllable even when Google Meet, Teams, or browser windows hold full desktop focus.

---

## ⌨️ Controls & Shortcuts

| Hotkey | Action | Description |
|---|---|---|
| `Ctrl + Shift + M` | **Toggle Mode** | Switch between 📜 **SCRIPT** (Teleprompter) and 🎙️ **INTERVIEW** (Live Co-Pilot) |
| `Ctrl + Shift + H` | **Stealth Toggle** | Instantly show / hide overlay |
| `Ctrl + Shift + Space` | **Pause / Resume** | Freeze or resume automatic teleprompter scrolling |
| `Esc` | **Exit** | Close application cleanly |

### Quick Action Bar
- `A+` / `A-`: Dynamically increase or decrease reading font size.
- `📋 Paste`: Instantly load text from your Windows clipboard into the active teleprompter.
- `✕ Clear`: Clear live text buffer and reset state.

---

## 🏗️ Architecture Overview

```
                      ┌──────────────────────────────────────────────┐
                      │              VoiceBridge AI                  │
                      └──────────────────────────────────────────────┘
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                   ▼
┌─────────────────────────┐                         ┌─────────────────────────┐
│     Microphone In       │                         │    System Audio (WASAPI)│
│    (sounddevice mic)    │                         │  (soundcard subprocess) │
└───────────┬─────────────┘                         └───────────┬─────────────┘
            │                                                   │
            ▼                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       WhisperEngine (faster-whisper)                        │
│                   CUDA int8_float16 (RTX 2050 4GB VRAM)                     │
└───────────┬───────────────────────────────────────────────────┬─────────────┘
            │ [Yago's Speech]                                   │ [Interviewer Q]
            ▼                                                   ▼
┌─────────────────────────┐                         ┌─────────────────────────┐
│      ScriptMatcher      │                         │      CopilotEngine      │
│  (rapidfuzz alignment)  │                         │  (Groq API streaming)   │
└───────────┬─────────────┘                         └───────────┬─────────────┘
            │ sig_scroll_to / highlight                         │ sig_copilot_token
            └─────────────────────────┬─────────────────────────┘
                                      ▼
                      ┌──────────────────────────────┐
                      │    OverlayWindow (PyQt6)     │
                      │  - WDA_EXCLUDEFROMCAPTURE    │
                      │  - Pinned beneath webcam     │
                      │  - Global Hotkeys (pynput)   │
                      └──────────────────────────────┘
```

---

## 🚀 Quickstart

### Prerequisites
- Windows 10/11 64-bit
- Python 3.10+ (tested on Python 3.12)
- NVIDIA GPU with CUDA drivers (e.g., RTX 2050/3050/4060) or modern multi-core CPU

### 1. Clone & Set Up Environment
```powershell
git clone https://github.com/yago-silva-ads/VoiceBridgeAI.git
cd VoiceBridgeAI

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy the example environment file and add your free [Groq API Key](https://console.groq.com/):
```powershell
copy .env.example .env
```
Edit `.env`:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 3. Launch
```powershell
# Run in Teleprompter mode (Default)
python main.py --mode script

# Run directly in Live Interview Co-Pilot mode
python main.py --mode interview

# Load a custom script file
python main.py --mode script --script path\to\script.txt

# Force CPU inference (if running without dedicated NVIDIA GPU)
python main.py --cpu
```

---

## 🛡️ Screen-Share Invisibility Test
1. Launch `python main.py`.
2. Start a Google Meet, Zoom, or Microsoft Teams call.
3. Share your **Entire Screen** (Desktop).
4. Notice that while VoiceBridge AI is prominently visible to you right below your webcam, **it does not appear at all in the shared stream or meeting recording**.

---

## 👨‍💻 Author
**Yago Santos Silva**
- GitHub: [@yago-silva-ads](https://github.com/yago-silva-ads)
- Focus: Fullstack Systems & Autonomous AI Workflows | Web Accessibility Researcher (WCAG 2.1/2.2, NVDA) | Aviation Compliance (LATAM Airlines SGSO)
