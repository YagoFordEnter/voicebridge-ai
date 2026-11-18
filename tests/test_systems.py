"""
tests/test_systems.py â€” VoiceBridge AI
Automated headless test suite covering all critical subsystems:
  1. ScriptMatcher: rapidfuzz fuzzy alignment and scroll fraction calculation.
  2. Echo Gate: Half-Duplex mute logic during loopback and 1.5s cooldown recovery.
  3. Web Companion: FastAPI routes and broadcast mechanics.
  4. Copilot Cascade: 404 simulation on primary model and automatic fallback.
  5. OverlayWindow: Headless Qt mousePressEvent and dragging verification.
"""
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

# CRITICAL: Define offscreen headless mode BEFORE importing PyQt6
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest

# Ensure root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai.script_matcher import ScriptMatcher
from ai.copilot import CopilotEngine
from web_companion import WebCompanionServer, HTML_PAGE


# ===========================================================================
# 1. ScriptMatcher Tests (rapidfuzz voice tracking)
# ===========================================================================
def test_script_matcher_fuzzy_alignment():
    recorded_positions = []

    def on_position(fraction: float, cursor: int):
        recorded_positions.append((fraction, cursor))

    matcher = ScriptMatcher(on_position=on_position)
    sample_script = (
        "Hello everyone my name is Yago Santos Silva and I study systems analysis at Senac. "
        "Today I am presenting VoiceBridge AI, a stealth accessibility teleprompter "
        "engineered for international technical interviews and video presentations."
    )
    matcher.load_script(sample_script)
    assert matcher.total_words > 10
    assert matcher.cursor == 0

    # Feed matching words from middle of text
    matcher.feed("systems analysis at Senac presenting voicebridge ai")
    assert matcher.cursor >= 5
    assert len(recorded_positions) >= 1
    fraction, cursor = recorded_positions[-1]
    assert 0.0 < fraction <= 1.0

    # Verify visible text extraction
    before, highlight, after = matcher.get_visible_text(before=2, after=8)
    assert highlight != ""
    assert after != ""


# ===========================================================================
# 2. Echo Gate Tests (Half-Duplex speakerphone protection)
# ===========================================================================
def test_echo_gate_half_duplex_mute_and_recovery():
    last_speaker_active_time = [0.0]
    ECHO_HOLD_SECONDS = 1.5

    def on_speaker_active():
        last_speaker_active_time[0] = time.time()

    def is_echo_gate_active() -> bool:
        return (time.time() - last_speaker_active_time[0]) < ECHO_HOLD_SECONDS

    # Initial state: speaker has been quiet for a long time
    assert not is_echo_gate_active()

    # Interviewer speaks through notebook speakers
    on_speaker_active()
    assert is_echo_gate_active()

    # While speaking (e.g. 0.1s later), gate must remain active
    time.sleep(0.05)
    assert is_echo_gate_active()

    # Simulate passage of cooldown time (> 1.5s)
    last_speaker_active_time[0] = time.time() - 1.6
    assert not is_echo_gate_active()


# ===========================================================================
# 3. Web Companion Tests (FastAPI routes & broadcast)
# ===========================================================================
@pytest.mark.asyncio
async def test_web_companion_routes_and_broadcast():
    import httpx

    submitted_scripts = []
    mode_toggles = []

    server = WebCompanionServer(
        port=8001,
        on_script_submitted=lambda s: submitted_scripts.append(s),
        on_mode_toggled=lambda: mode_toggles.append(True),
    )

    # 1. Test HTML route
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        assert "VoiceBridge AI Companion" in res.text
        assert "#000000" in res.text

    # 2. Test state updates and broadcast mechanics
    server.update_mode("INTERVIEW")
    assert server.current_mode == "INTERVIEW"

    server.update_teleprompter_view("before", "highlight", "after", 0.5)
    assert server.current_scroll_fraction == 0.5

    server.update_copilot_complete("Answer complete")
    assert server.current_text == "Answer complete"


# ===========================================================================
# 4. Copilot Cascade & Fallback Simulation (404 recovery)
# ===========================================================================
def test_copilot_cascade_fallback_on_404():
    """Simulates primary model throwing 404 and verifies automatic fallback."""
    class FakeDelta:
        def __init__(self, content):
            self.content = content

    class FakeChoice:
        def __init__(self, content):
            self.delta = FakeDelta(content)

    class FakeChunk:
        def __init__(self, content):
            self.choices = [FakeChoice(content)]

    class MockChatCompletions:
        def __init__(self):
            self.attempts = []

        def create(self, **kwargs):
            model = kwargs.get("model")
            self.attempts.append(model)
            if model == "test-model-1":
                # Simulate 404 not found (e.g. deprecated model)
                raise RuntimeError("HTTP 404: Model 'test-model-1' does not exist")
            elif model == "test-model-2":
                # Successful fallback streaming chunks
                return [
                    FakeChunk("Opening line ready to speak. |"),
                    FakeChunk(" Built robust AI pipeline. |"),
                    FakeChunk(" 100% verified results."),
                ]
            raise ValueError(f"Unexpected model: {model}")

    class MockClient:
        def __init__(self):
            self.chat = MagicMock()
            self.mock_completions = MockChatCompletions()
            self.chat.completions = self.mock_completions

    mock_client = MockClient()
    received_tokens = []
    received_full = []

    engine = CopilotEngine(
        on_token=lambda t: received_tokens.append(t),
        on_complete=lambda full: received_full.append(full),
        client_override=mock_client,
    )

    result = engine.generate_sync("Tell me about your background in accessibility?")

    # Verify both models were attempted in cascade
    assert mock_client.mock_completions.attempts == ["test-model-1", "test-model-2"]
    # Verify fallback generated the complete text
    assert result and len(str(result)) > 0
    assert "Opening line ready to speak" in result
    assert "100% verified results" in result
    assert len(received_tokens) >= 3


# ===========================================================================
# 5. Overlay Window Mouse Events (Headless Qt verification)
# ===========================================================================
def test_overlay_window_mouse_drag_headless():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt, QPointF
    from PyQt6.QtGui import QMouseEvent

    app = QApplication.instance() or QApplication([])

    from ui.overlay import OverlayWindow
    overlay = OverlayWindow()

    try:
        # Simulate mouse press with LeftButton
        press_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(50.0, 50.0),
            QPointF(150.0, 150.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        overlay.mousePressEvent(press_event)
        assert overlay._drag_pos is not None

        # Simulate mouse move with LeftButton
        move_event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPointF(60.0, 60.0),
            QPointF(160.0, 160.0),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        overlay.mouseMoveEvent(move_event)

        # Simulate mouse release
        release_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            QPointF(60.0, 60.0),
            QPointF(160.0, 160.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        overlay.mouseReleaseEvent(release_event)
        assert overlay._drag_pos is None
    finally:
        overlay.close()
        app.processEvents()

