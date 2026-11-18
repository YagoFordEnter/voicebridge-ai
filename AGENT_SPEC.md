\# PROJECT: VoiceBridge AI — Real-Time Accessibility \& Interview Co-Pilot



\## 1. Objective \& Context

Build a low-latency, local-first Windows desktop accessibility and communication assistant in Python for \*\*Yago Santos Silva\*\*. The application helps a non-native English speaker participate smoothly in live technical interviews (Teams/Meet/Zoom) and record pitch videos without breaking eye contact or freezing on spoken English phrasing.



\## 2. Target Hardware \& Environment

\- \*\*Device:\*\* Lenovo LOQ 15 (Windows 11)

\- \*\*CPU / RAM:\*\* Intel Core i5 | 16GB DDR5 RAM

\- \*\*GPU:\*\* NVIDIA GeForce RTX 2050 (4GB VRAM — CUDA enabled)

\- \*\*Constraint:\*\* Must fit comfortably within 4GB VRAM alongside browser/video call apps (use quantized `int8`/`float16` models and lightweight inference).



\## 3. Core Functional Modules

1\. \*\*Stealth Top-Center Teleprompter Overlay (`ui/overlay.py`):\*\*

&#x20;  - Frameless, translucent dark overlay (`PyQt6` or `CustomTkinter`) pinned `Always on Top` directly beneath the physical webcam bezel.

&#x20;  - Supports hotkeys (`Ctrl+Shift+Space` to Pause/Resume, `Ctrl+Shift+Up/Down` for scroll speed/font size, `Ctrl+Shift+H` to hide/show).

&#x20;  - \*\*Click-through / Screen-share invisibility option:\*\* Use Windows API (`SetWindowDisplayAffinity` with `WDA\\\_EXCLUDEFROMCAPTURE`) so the teleprompter is visible to Yago on screen, \*\*but completely invisible if Yago shares his screen\*\* during a live coding or accessibility audit test.

2\. \*\*Dual-Channel Audio Capture (`audio/capture.py`):\*\*

&#x20;  - \*\*Mic Channel:\*\* Captures Yago's spoken English (`sounddevice` / `pyaudio`) to drive voice-activated text highlighting and auto-scrolling.

&#x20;  - \*\*System Loopback Channel (WASAPI):\*\* Captures the interviewer's audio from Teams/Meet/Browser using `PyAudioWPatch` (Windows WASAPI loopback) without needing virtual audio cables.

3\. \*\*Real-Time Speech-to-Text \& Voice Tracking (`ai/transcriber.py`):\*\*

&#x20;  - Uses `faster-whisper` (`tiny.en` or `base.en` with `compute\\\_type="int8\\\_float16"` on CUDA, fallback to `int8` on CPU).

&#x20;  - Tracks Yago's spoken words against the loaded script using fuzzy matching (`rapidfuzz`) to highlight the current word and smoothly advance the scroll.

4\. \*\*Live Interview Co-Pilot / Answer Generator (`ai/copilot.py`):\*\*

&#x20;  - Transcribes the interviewer's question from the WASAPI loopback stream.

&#x20;  - Sends context + Yago's technical profile (ADS student at Senac, PICTA Accessibility Researcher WCAG 2.1/2.2 \& NVDA, LATAM Airlines SGSO 2 yrs, Python/Flutter/Java) to a fast LLM API (\*\*Groq API\*\* `llama-3.3-70b-versatile` or \*\*Google Gemini Flash API\*\* for <500ms latency) to stream concise, natural spoken-English bullet points onto the teleprompter overlay.

5\. \*\*Eye-Contact \& Virtual Camera Pipeline (`vision/camera.py`):\*\*

&#x20;  - Optional lightweight OpenCV + MediaPipe Face Mesh gaze-smoothing module outputting to `pyvirtualcam` (OBS Virtual Camera), OR seamless compatibility with \*\*NVIDIA Broadcast Eye Contact\*\* running natively on the RTX 2050.



\## 4. Open-Source Reference Repositories (Atlas for Reuse \& Reverse Engineering)

The agent should inspect, adapt, or benchmark patterns from these proven architectures:

\- \*\*Real-time Whisper + WASAPI Loopback:\*\* `ufal/whisper\\\_streaming` and `collabora/WhisperLive` (chunked VAD + low-latency transcription).

\- \*\*Live Interview / Meeting AI Overlay:\*\* `roy-jingyang/Interview-Copilot` and `Ilan-K/ecoute` (dual mic + system audio transcription + live LLM answer overlay).

\- \*\*Gaze Correction / Eye Contact:\*\* `google-ai-edge/mediapipe` (Iris landmark tracking) and `NVIDIA Broadcast SDK` integration.

\- \*\*Windows Capture Exclusion (`WDA\\\_EXCLUDEFROMCAPTURE`):\*\* `ctypes.windll.user32.SetWindowDisplayAffinity` patterns for stealth accessibility overlays.



\## 5. Architecture \& Coding Standards

\- \*\*Decoupled Async/Threaded Pipeline:\*\* UI main thread must NEVER block. Audio capture, Whisper inference, and LLM streaming must communicate via thread-safe `queue.Queue` or `PyQt6` signals.

\- \*\*Directory Structure:\*\*

&#x20; ```text

&#x20; voicebridge-ai/

&#x20; ├── AGENT\_SPEC.md

&#x20; ├── requirements.txt

&#x20; ├── .env.example          # GROQ\_API\_KEY, GEMINI\_API\_KEY

&#x20; ├── config/

&#x20; │   └── profile\_context.md # Yago's resume, PICTA research \& STAR stories

&#x20; ├── audio/

&#x20; │   ├── mic\_stream.py

&#x20; │   └── loopback\_stream.py

&#x20; ├── ai/

&#x20; │   ├── whisper\_engine.py

&#x20; │   ├── script\_matcher.py

&#x20; │   └── copilot\_llm.py

&#x20; ├── ui/

&#x20; │   └── teleprompter\_overlay.py

&#x20; └── main.py

