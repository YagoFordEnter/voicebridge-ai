"""
main.py — VoiceBridge AI
Orchestrator: connects audio capture → whisper transcription → script matcher / copilot → overlay UI + web companion.

Modes & Capabilities:
  - SCRIPT mode (default): Fixed teleprompter with rapidfuzz voice-tracked auto-scrolling
  - INTERVIEW mode: Live co-pilot answers streamed from Groq
  - --room-mic: Captures speakerphone/room audio via notebook microphone with 1.75s silence gate
  - Echo Gate (Half-Duplex): Blocks notebook mic feed to ScriptMatcher while loopback (speakers) is playing + 1.5s post-silence
  - Web Companion (FastAPI + WebSocket on 0.0.0.0:8000): Serves mobile teleprompter to iPhone 13 via Wi-Fi
"""
from __future__ import annotations

import argparse
import logging
import os
import queue
import sys
import threading
import time
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
from web_companion import WebCompanionServer, get_local_ip


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
    p.add_argument(
        "--room-mic", action="store_true",
        help="Room Mic mode: notebook mic captures speakerphone/room audio with 1.75s silence gate and routes questions to Copilot.",
    )
    p.add_argument(
        "--port", type=int, default=8000,
        help="Port for the iPhone 13 Web Companion server (default: 8000).",
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
    if args.mode == "interview":
        overlay._toggle_mode()
    overlay.show()

    # Start OS-wide Global Hotkeys listener
    start_global_hotkeys(overlay)

    # -- Echo Gate State (Half-Duplex speakerphone protection) --
    # When loopback (speakers) is active, mute mic input to script matcher for +1.5s
    last_speaker_active_time = [0.0]
    ECHO_HOLD_SECONDS = 1.5

    def on_speaker_active():
        last_speaker_active_time[0] = time.time()

    def is_echo_gate_active() -> bool:
        return (time.time() - last_speaker_active_time[0]) < ECHO_HOLD_SECONDS

    # -- Audio Queues --
    mic_audio_q: queue.Queue = queue.Queue()
    loopback_audio_q: queue.Queue = queue.Queue()

    # -- Whisper Engine (shared; model loaded once) --
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
        web_server.update_teleprompter_view(before, highlight, after, fraction)

    script_matcher = ScriptMatcher(on_position=on_position)

    # Sync scripts pasted from Desktop Overlay to matcher and iPhone
    def on_script_pasted(text: str) -> None:
        script_matcher.load_script(text)
        logger.info("Script updated (%d words)", script_matcher.total_words)

    overlay.sig_script_pasted.connect(on_script_pasted)

    # Load initial script from file if provided
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
        web_server.update_copilot_token(token)

    def on_copilot_complete(full_text: str) -> None:
        overlay.sig_copilot_complete.emit(full_text)
        web_server.update_copilot_complete(full_text)

    def on_copilot_error(msg: str) -> None:
        overlay.sig_copilot_error.emit(msg)
        web_server.update_status(f"Error: {msg[:30]}")

    copilot = CopilotEngine(
        on_token=on_copilot_token,
        on_complete=on_copilot_complete,
        on_error=on_copilot_error,
    )

    # -- Transcription dispatch --
    def on_transcription(source: str, text: str) -> None:
        """
        Routes transcribed audio:
        - In --room-mic mode: Mic audio IS the room/speakerphone audio -> goes to Copilot
        - In normal mode:
            - loopback -> Interviewer speech -> Copilot
            - mic -> Yago's speech -> ScriptMatcher (blocked by echo gate if speakers are playing)
        """
        overlay.sig_heard_text.emit(f"[{source}] {text[:100]}")

        if args.room_mic:
            if source == "mic":
                copilot.feed_question(text)
                overlay.sig_status.emit("generating…")
                web_server.update_status("generating…")
        else:
            if source == "mic":
                if is_echo_gate_active():
                    logger.debug("Echo gate active: suppressing speaker bleed from script matcher")
                    return
                script_matcher.feed(text)
            elif source == "loopback":
                on_speaker_active()
                copilot.feed_question(text)
                overlay.sig_status.emit("generating…")
                web_server.update_status("generating…")

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
    mic_capture = MicCapture(
        output_queue=mic_audio_q,
        room_mic=args.room_mic,
    )
    loopback_capture = LoopbackCapture(
        output_queue=loopback_audio_q,
        on_activity=on_speaker_active,
    )

    # -- Web Companion Server (FastAPI + WebSockets for iPhone 13) --
    def on_web_script_submitted(pasted_text: str):
        # Update Qt overlay on main thread
        overlay.load_script_text(pasted_text)
        script_matcher.load_script(pasted_text)
        overlay.sig_status.emit(f"web script ({len(pasted_text.split())}w)")
        logger.info("Mobile script received (%d words)", len(pasted_text.split()))

    def on_web_mode_toggled():
        overlay.sig_action_toggle_mode.emit()

    web_server = WebCompanionServer(
        port=args.port,
        on_script_submitted=on_web_script_submitted,
        on_mode_toggled=on_web_mode_toggled,
    )
    companion_url = web_server.start()

    # Inform mobile client when overlay mode changes
    def on_overlay_mode_changed():
        mode_str = overlay.mode.name
        web_server.update_mode(mode_str)

    overlay.sig_action_toggle_mode.connect(on_overlay_mode_changed)

    # -- Print clear connection Banner for iPhone 13 --
    banner_border = "=" * 65
    print(banner_border)
    print("   🎙️  VOICEBRIDGE AI — REAL-TIME ACCESSIBILITY & CO-PILOT")
    print(banner_border)
    print(f"   ► Desktop Mode:     {'ROOM-MIC (Speakerphone)' if args.room_mic else 'DUAL-CHANNEL + ECHO GATE'}")
    print(f"   ► Whisper Hardware: {'CPU' if args.cpu else 'CUDA (RTX 2050 int8_float16)'}")
    print(f"   ► iPhone 13 URL:    {companion_url}")
    print("   (Open Safari on your iPhone on the same Wi-Fi to sync!)")
    print(banner_border)

    # -- Start everything --
    logger.info("Starting VoiceBridge AI audio & AI workers…")
    overlay.sig_status.emit("loading whisper…")

    mic_capture.start()
    if not args.room_mic:
        loopback_capture.start()
        loopback_transcriber.start()

    mic_transcriber.start()

    overlay.sig_status.emit("live ✓")
    logger.info("All systems live. Mode: %s", args.mode.upper())

    # -- Qt event loop (blocks here until window closes) --
    exit_code = app.exec()

    # -- Cleanup --
    logger.info("Shutting down…")
    mic_capture.stop()
    if not args.room_mic:
        loopback_capture.stop()
        loopback_transcriber.stop()
    mic_transcriber.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
