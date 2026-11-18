"""
ui/overlay.py — VoiceBridge AI
Stealth teleprompter & co-pilot overlay using PyQt6.

Features:
  - Frameless, translucent dark window pinned Always-on-Top at top-center
  - WDA_EXCLUDEFROMCAPTURE via ctypes → invisible in screen-share (Zoom/Teams/Meet)
  - Two modes toggled with Ctrl+Shift+M:
      1. SCRIPT  — fixed teleprompter text with voice-tracked highlight + auto-scroll
      2. INTERVIEW — live co-pilot answers streamed from Groq
  - Global Hotkeys (via pynput daemon thread) + Local Qt Shortcuts:
      Ctrl+Shift+H  hide/show | Ctrl+Shift+M  mode toggle | Ctrl+Shift+Space  pause scroll | Esc  quit
  - Top Control Bar:
      Mode pill, Status indicator, Font size (A- / A+), Clear, Paste Script (from clipboard)
  - Draggable anywhere by clicking and dragging the window body
"""
from __future__ import annotations

import ctypes
import logging
from enum import Enum, auto

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger("voicebridge.overlay")

# Windows constants for SetWindowDisplayAffinity
WDA_EXCLUDEFROMCAPTURE = 0x00000011


class OverlayMode(Enum):
    SCRIPT = auto()      # Teleprompter with voice-tracked scrolling
    INTERVIEW = auto()   # Live co-pilot answer display


class OverlayWindow(QWidget):
    """
    Main overlay window. Thread-safe: external background threads trigger
    Qt slots through pyqtSignals.
    """

    # --- Signals (thread-safe bridge from backend / global hotkeys → Qt main thread) ---
    sig_scroll_to = pyqtSignal(float, int)        # (fraction, word_index)
    sig_update_script_view = pyqtSignal(str, str, str)  # (before, highlight, after)
    sig_copilot_token = pyqtSignal(str)            # streaming token
    sig_copilot_complete = pyqtSignal(str)         # full response
    sig_copilot_error = pyqtSignal(str)            # error message
    sig_heard_text = pyqtSignal(str)               # last heard transcript
    sig_status = pyqtSignal(str)                   # status bar text

    # Hotkey trigger signals (emitted from pynput thread)
    sig_action_toggle_mode = pyqtSignal()
    sig_action_toggle_visibility = pyqtSignal()
    sig_action_toggle_pause = pyqtSignal()

    # Callback when new script is pasted directly via UI
    sig_script_pasted = pyqtSignal(str)

    # Window geometry
    WIDTH = 720
    HEIGHT = 270
    TOP_MARGIN = 8  # pixels below top of screen (under webcam bezel)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = OverlayMode.SCRIPT
        self._scroll_paused = False
        self._drag_pos = None
        self._copilot_buffer = ""
        self._font_size = 13  # Default font size for reading text

        self._init_window()
        self._init_ui()
        self._init_local_hotkeys()
        self._connect_signals()
        self._apply_stealth()

    # -----------------------------------------------------------------
    # Window setup
    # -----------------------------------------------------------------
    def _init_window(self) -> None:
        self.setWindowTitle("VoiceBridge AI")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # hides from Windows taskbar & alt-tab
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Center horizontally at the top of the primary screen
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.WIDTH) // 2
            y = geo.y() + self.TOP_MARGIN
        else:
            x, y = 300, self.TOP_MARGIN
        self.setGeometry(x, y, self.WIDTH, self.HEIGHT)
        self.setMinimumSize(420, 140)

    def _init_ui(self) -> None:
        # Root container with rounded corners and translucent background
        self._container = QWidget(self)
        self._container.setObjectName("container")
        self._container.setStyleSheet("""
            #container {
                background-color: rgba(16, 18, 22, 238);
                border-radius: 12px;
                border: 1px solid rgba(79, 195, 247, 80);
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 16);
                color: #bbb;
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 4px;
                padding: 2px 7px;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(79, 195, 247, 45);
                color: #fff;
                border-color: rgba(79, 195, 247, 120);
            }
            QPushButton:pressed {
                background-color: rgba(79, 195, 247, 80);
            }
        """)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self._container)

        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(14, 8, 14, 10)
        layout.setSpacing(4)

        # -- Top bar: mode indicator + quick control buttons + status --
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)

        self._mode_label = QLabel("📜 SCRIPT")
        self._mode_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._mode_label.setStyleSheet("color: #4fc3f7; padding-right: 4px;")
        top_bar.addWidget(self._mode_label)

        # Quick Control Buttons
        self._btn_font_dec = QPushButton("A-")
        self._btn_font_dec.setToolTip("Decrease Font Size")
        self._btn_font_dec.setFixedWidth(28)
        self._btn_font_dec.clicked.connect(self._decrease_font)
        top_bar.addWidget(self._btn_font_dec)

        self._btn_font_inc = QPushButton("A+")
        self._btn_font_inc.setToolTip("Increase Font Size")
        self._btn_font_inc.setFixedWidth(28)
        self._btn_font_inc.clicked.connect(self._increase_font)
        top_bar.addWidget(self._btn_font_inc)

        self._btn_paste = QPushButton("📋 Paste")
        self._btn_paste.setToolTip("Paste Script from Clipboard")
        self._btn_paste.clicked.connect(self._paste_from_clipboard)
        top_bar.addWidget(self._btn_paste)

        self._btn_clear = QPushButton("✕ Clear")
        self._btn_clear.setToolTip("Clear Text / Reset View")
        self._btn_clear.clicked.connect(self._clear_text)
        top_bar.addWidget(self._btn_clear)

        top_bar.addStretch()

        self._status_label = QLabel("starting…")
        self._status_label.setFont(QFont("Segoe UI", 8))
        self._status_label.setStyleSheet("color: #888;")
        top_bar.addWidget(self._status_label)
        layout.addLayout(top_bar)

        # -- Heard text (small, dimmed — last transcript snippet) --
        self._heard_label = QLabel("")
        self._heard_label.setFont(QFont("Segoe UI", 8))
        self._heard_label.setStyleSheet("color: #555;")
        self._heard_label.setWordWrap(True)
        self._heard_label.setMaximumHeight(30)
        layout.addWidget(self._heard_label)

        # -- Main content area (scrollable) --
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QWidget { background: transparent; }
        """)

        self._content_widget = QWidget()
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self._main_text = QLabel("")
        self._main_text.setFont(QFont("Segoe UI", self._font_size))
        self._main_text.setStyleSheet("color: #e0e0e0; line-height: 140%;")
        self._main_text.setWordWrap(True)
        self._main_text.setTextFormat(Qt.TextFormat.RichText)
        content_layout.addWidget(self._main_text)
        content_layout.addStretch()

        self._scroll_area.setWidget(self._content_widget)
        layout.addWidget(self._scroll_area, stretch=1)

    def _init_local_hotkeys(self) -> None:
        """Local Qt shortcuts (fallback when the window has focus)."""
        sc_mode = QShortcut(QKeySequence("Ctrl+Shift+M"), self)
        sc_mode.activated.connect(self._toggle_mode)

        sc_hide = QShortcut(QKeySequence("Ctrl+Shift+H"), self)
        sc_hide.activated.connect(self._toggle_visibility)

        sc_pause = QShortcut(QKeySequence("Ctrl+Shift+Space"), self)
        sc_pause.activated.connect(self._toggle_pause)

        sc_esc = QShortcut(QKeySequence("Escape"), self)
        sc_esc.activated.connect(self.close)

    def _connect_signals(self) -> None:
        self.sig_scroll_to.connect(self._on_scroll_to)
        self.sig_update_script_view.connect(self._on_update_script_view)
        self.sig_copilot_token.connect(self._on_copilot_token)
        self.sig_copilot_complete.connect(self._on_copilot_complete)
        self.sig_copilot_error.connect(self._on_copilot_error)
        self.sig_heard_text.connect(self._on_heard_text)
        self.sig_status.connect(self._on_status)

        # Global hotkey triggers routed to main thread
        self.sig_action_toggle_mode.connect(self._toggle_mode)
        self.sig_action_toggle_visibility.connect(self._toggle_visibility)
        self.sig_action_toggle_pause.connect(self._toggle_pause)

    # -----------------------------------------------------------------
    # WDA_EXCLUDEFROMCAPTURE — invisible in screen sharing
    # -----------------------------------------------------------------
    def _apply_stealth(self) -> None:
        """Make window invisible to screen capture (Zoom, Teams, Meet, OBS)."""
        try:
            hwnd = int(self.winId())
            result = ctypes.windll.user32.SetWindowDisplayAffinity(
                hwnd, WDA_EXCLUDEFROMCAPTURE
            )
            if result:
                logger.info("✓ WDA_EXCLUDEFROMCAPTURE applied (hwnd=%s)", hwnd)
                self._status_label.setText("stealth ✓")
            else:
                error = ctypes.GetLastError()
                logger.warning("SetWindowDisplayAffinity returned 0 (error=%d)", error)
                self._status_label.setText("stealth ✗")
        except Exception as exc:
            logger.warning("Could not apply stealth: %s", exc)
            self._status_label.setText("stealth ✗")

    # -----------------------------------------------------------------
    # Dragging (click anywhere on the window body to reposition)
    # -----------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
            self._drag_pos = pos - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos and (event.buttons() & Qt.MouseButton.LeftButton):
            pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
            self.move(pos - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # -----------------------------------------------------------------
    # Actions & Controls
    # -----------------------------------------------------------------
    @pyqtSlot()
    def _increase_font(self) -> None:
        if self._font_size < 28:
            self._font_size += 1
            font = self._main_text.font()
            font.setPointSize(self._font_size)
            self._main_text.setFont(font)
            self._status_label.setText(f"font: {self._font_size}pt")

    @pyqtSlot()
    def _decrease_font(self) -> None:
        if self._font_size > 9:
            self._font_size -= 1
            font = self._main_text.font()
            font.setPointSize(self._font_size)
            self._main_text.setFont(font)
            self._status_label.setText(f"font: {self._font_size}pt")

    @pyqtSlot()
    def _clear_text(self) -> None:
        self._main_text.setText("")
        self._copilot_buffer = ""
        self._heard_label.setText("")
        self._status_label.setText("cleared")

    @pyqtSlot()
    def _paste_from_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            # Switch to script mode if not already
            if self._mode != OverlayMode.SCRIPT:
                self._toggle_mode()
            self.load_script_text(text)
            self.sig_script_pasted.emit(text)
            self._status_label.setText(f"pasted ({len(text.split())} words)")
        else:
            self._status_label.setText("clipboard empty")

    @pyqtSlot()
    def _toggle_mode(self) -> None:
        if self._mode == OverlayMode.SCRIPT:
            self._mode = OverlayMode.INTERVIEW
            self._mode_label.setText("🎙️ INTERVIEW")
            self._mode_label.setStyleSheet("color: #81c784; padding-right: 4px;")
            self._main_text.setText(
                '<span style="color:#777;">Listening for interviewer question…</span>'
            )
            self._copilot_buffer = ""
        else:
            self._mode = OverlayMode.SCRIPT
            self._mode_label.setText("📜 SCRIPT")
            self._mode_label.setStyleSheet("color: #4fc3f7; padding-right: 4px;")
            self._main_text.setText("")
        logger.info("Mode switched to %s", self._mode.name)

    @pyqtSlot()
    def _toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self._apply_stealth()  # re-apply stealth after restore

    @pyqtSlot()
    def _toggle_pause(self) -> None:
        self._scroll_paused = not self._scroll_paused
        state = "PAUSED" if self._scroll_paused else "LIVE"
        self._status_label.setText(state)
        logger.info("Scroll %s", state)

    @property
    def mode(self) -> OverlayMode:
        return self._mode

    # -----------------------------------------------------------------
    # Slots — SCRIPT mode
    # -----------------------------------------------------------------
    @pyqtSlot(float, int)
    def _on_scroll_to(self, fraction: float, word_index: int) -> None:
        if self._scroll_paused or self._mode != OverlayMode.SCRIPT:
            return
        scrollbar = self._scroll_area.verticalScrollBar()
        target = int(fraction * scrollbar.maximum())
        scrollbar.setValue(target)

    @pyqtSlot(str, str, str)
    def _on_update_script_view(self, before: str, highlight: str, after: str) -> None:
        if self._mode != OverlayMode.SCRIPT:
            return
        html = (
            f'<span style="color:#777;">{before} </span>'
            f'<span style="color:#fff; background-color:rgba(79,195,247,90); '
            f'padding:2px 5px; border-radius:4px; font-weight:600;">{highlight}</span>'
            f'<span style="color:#ccc;"> {after}</span>'
        )
        self._main_text.setText(html)

    def load_script_text(self, full_text: str) -> None:
        self._main_text.setText(f'<span style="color:#d8d8d8;">{full_text}</span>')

    # -----------------------------------------------------------------
    # Slots — INTERVIEW mode
    # -----------------------------------------------------------------
    @pyqtSlot(str)
    def _on_copilot_token(self, token: str) -> None:
        if self._mode != OverlayMode.INTERVIEW:
            return
        self._copilot_buffer += token
        display = self._copilot_buffer.replace("|", "<br>• ").replace("**", "")
        self._main_text.setText(f'<span style="color:#e0e0e0;">{display}</span>')

    @pyqtSlot(str)
    def _on_copilot_complete(self, full_text: str) -> None:
        if self._mode != OverlayMode.INTERVIEW:
            return
        display = full_text.replace("|", "<br>• ").replace("**", "")
        self._main_text.setText(f'<span style="color:#e0e0e0;">{display}</span>')
        self._copilot_buffer = ""
        self._status_label.setText("ready")

    @pyqtSlot(str)
    def _on_copilot_error(self, msg: str) -> None:
        self._status_label.setText(f"⚠ {msg[:60]}")

    # -----------------------------------------------------------------
    # Slots — Shared
    # -----------------------------------------------------------------
    @pyqtSlot(str)
    def _on_heard_text(self, text: str) -> None:
        self._heard_label.setText(text[-120:])

    @pyqtSlot(str)
    def _on_status(self, text: str) -> None:
        self._status_label.setText(text)
