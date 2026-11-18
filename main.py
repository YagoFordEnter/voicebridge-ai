"""
main.py — VoiceBridge AI
Orchestrator: connects audio capture → whisper transcription → script matcher / copilot → overlay UI.

All heavy work runs in daemon threads; the Qt event loop runs on the main thread and is NEVER blocked.
Communication across threads uses queue.Queue (audio) and PyQt6 signals (UI updates).
Global hotkeys run via pynput GlobalHotKeys daemon thread for OS-wide capture (Meet/Teams/OBS in focus).

Usage:
    python main.py                           # default: SCRIPT mode
    python main.py --mode interview          # start in INTERVIEW mode
    python main.py --script path/to/text.txt # load a teleprompter script
"""
from __future__ import annotations

import argparse
import logging
import os
import queue
import sys
import threading
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("voicebridge.main")

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

# Load .env early
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from PyQt6.QtWidgets import QApplication

from ai.copilot import CopilotEngine
from ai.script_matcher import ScriptMatcher
from ai.transcriber import TranscriberConfig, TranscriberWorker, WhisperEngine
from audio.capture import LoopbackCapture, MicCapture
from ui.overlay import OverlayMode, OverlayWindow


# ---------------------------------------------------------------------------
# Global Hotkeys via pynput (OS-wide hooks)
# ---------------------------------------------------------------------------
def start_global_hotkeys(overlay: OverlayWindow) -> None:
    """
    Registers system-wide hotkeys using pynput.
    Emits PyQt signals to safely invoke actions on the Qt main thread.
    Works even when browser, Zoom, Teams, or Meet has full window focus.
    """
    try:
        from pynput import keyboard

        hotkeys = {
            "<ctrl>+<shift>+h": overlay.sig_action_toggle_visibility.emit,
            "<ctrl>+<shift>+m": overlay.sig_action_toggle_mode.emit,
            "<ctrl>+<shift>+<space>": overlay.sig_action_toggle_pause.emit,
        }

        listener = keyboard.GlobalHotKeys(hotkeys)
        listener.daemon = True
        listener.start()
        logger.info("✓ Global hotkeys active (Ctrl+Shift+H, Ctrl+Shift+M, Ctrl+Shift+Space)")
    except Exception as exc:
        logger.warning("Could not register pynput global hotkeys: %s", exc)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="VoiceBridge AI — Accessibility & Interview Co-Pilot")
    p.add_argument(
        "--mode", choices=["script", "interview"], default="script",
        help="Start in SCRIPT (teleprompter) or INTERVIEW (co-pilot) mode.",
    )
    p.add_argument(
        "--script", type=str, default=None,
        help="Path to a .txt file to load as the teleprompter script.",
    )
    p.add_argument(
        "--model", type=str, default="base.en",
        help="Whisper model size: tiny.en, base.en, or base (default: base.en).",
    )
    p.add_argument(
        "--cpu", action="store_true",
        help="Force CPU inference (skip CUDA).",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main wiring
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args()

    # -- Qt Application --
    app = QApplication(sys.argv)
    app.setApplicationName("VoiceBridge AI")

    # -- Overlay Window --
    overlay = OverlayWindow()

    # Set initial mode
    if args.mode == "interview":
        overlay._toggle_mode()
    overlay.show()

    # Start OS-wide Global Hotkeys listener
    start_global_hotkeys(overlay)

    # -- Audio Queues --
    mic_audio_q: queue.Queue = queue.Queue()
    loopback_audio_q: queue.Queue = queue.Queue()

    # -- Whisper Engine (shared; model loaded once, used by both workers) --
    whisper_cfg = TranscriberConfig(
        model_size=args.model,
        device="cpu" if args.cpu else "cuda",
        compute_type="int8" if args.cpu else "int8_float16",
    )
    whisper_engine = WhisperEngine(whisper_cfg)

    # -- Script Matcher (voice-tracked scrolling) --
    def on_position(fraction: float, word_index: int) -> None:
        overlay.sig_scroll_to.emit(fraction, word_index)
        before, highlight, after = script_matcher.get_visible_text()
        overlay.sig_update_script_view.emit(before, highlight, after)

    script_matcher = ScriptMatcher(on_position=on_position)

    # Allow dynamic pasting from clipboard in UI
    def on_script_pasted(text: str) -> None:
        script_matcher.load_script(text)
        logger.info("Script dynamically updated from clipboard (%d words)", script_matcher.total_words)

    overlay.sig_script_pasted.connect(on_script_pasted)

    # Load teleprompter script if provided via CLI
    if args.script:
        script_path = Path(args.script)
        if script_path.is_file():
            text = script_path.read_text(encoding="utf-8")
            script_matcher.load_script(text)
            overlay.load_script_text(text)
            overlay.sig_status.emit(f"script: {script_path.name}")
            logger.info("Loaded script: %s (%d words)", script_path.name, script_matcher.total_words)
        else:
            logger.warning("Script file not found: %s", script_path)

    # -- Co-Pilot Engine --
    def on_copilot_token(token: str) -> None:
        overlay.sig_copilot_token.emit(token)

    def on_copilot_complete(full_text: str) -> None:
        overlay.sig_copilot_complete.emit(full_text)

    def on_copilot_error(msg: str) -> None:
        overlay.sig_copilot_error.emit(msg)

    copilot = CopilotEngine(
        on_token=on_copilot_token,
        on_complete=on_copilot_complete,
        on_error=on_copilot_error,
    )

    # -- Transcription dispatch --
    def on_transcription(source: str, text: str) -> None:
        """
        Routes transcribed text to the right handler based on source channel.
        source="mic"      → voice tracking (script_matcher.feed)
        source="loopback" → co-pilot (copilot.feed_question)
        Both also update the "heard" display.
        """
        overlay.sig_heard_text.emit(f"[{source}] {text[:100]}")

        if source == "mic":
            script_matcher.feed(text)
        elif source == "loopback":
            copilot.feed_question(text)
            overlay.sig_status.emit("generating…")

    # -- Transcriber Workers (one per audio channel) --
    mic_transcriber = TranscriberWorker(
        engine=whisper_engine,
        audio_queue=mic_audio_q,
        on_text=on_transcription,
        source_tag="mic",
    )

    loopback_transcriber = TranscriberWorker(
        engine=whisper_engine,
        audio_queue=loopback_audio_q,
        on_text=on_transcription,
        source_tag="loopback",
    )

    # -- Audio Capture --
    mic_capture = MicCapture(output_queue=mic_audio_q)
    loopback_capture = LoopbackCapture(output_queue=loopback_audio_q)

    # -- Start everything --
    logger.info("Starting VoiceBridge AI…")
    overlay.sig_status.emit("loading whisper…")

    mic_capture.start()
    loopback_capture.start()
    mic_transcriber.start()
    loopback_transcriber.start()

    overlay.sig_status.emit("live ✓")
    logger.info("All systems live. Mode: %s", args.mode.upper())

    # -- Qt event loop (blocks here until window closes) --
    exit_code = app.exec()

    # -- Cleanup --
    logger.info("Shutting down…")
    mic_capture.stop()
    loopback_capture.stop()
    mic_transcriber.stop()
    loopback_transcriber.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
