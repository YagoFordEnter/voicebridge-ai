"""
ai/transcriber.py — VoiceBridge AI
Real-time speech-to-text engine using faster-whisper.
Dual-purpose: transcribes Yago's mic (English) for voice-tracking scroll,
and the interviewer's loopback audio (English) for the co-pilot.

Evolved from C:\\CacadorDeVagas\\tools\\cola_entrevista\\cola_entrevista.py
Key adaptations:
  - CUDA int8_float16 on RTX 2050 (was CPU int8 in cola_entrevista)
  - English-only base.en model (was multilingual "base" with lang="pt")
  - Two independent consumer loops (mic vs loopback) with separate queues
  - PyQt6 signal emission instead of tkinter root.after()
"""
from __future__ import annotations

import logging
import os
import queue
import threading
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger("voicebridge.transcriber")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class TranscriberConfig:
    """All tunables live here — no magic constants scattered in code."""
    model_size: str = "base.en"           # tiny.en for lower VRAM; base.en for accuracy
    device: str = "cuda"                  # "cuda" or "cpu"
    compute_type: str = "int8_float16"    # fits <700 MB on RTX 2050
    cpu_threads: int = field(default_factory=lambda: max(2, (os.cpu_count() or 4) // 2))
    beam_size: int = 1                    # greedy — fastest for real-time
    language: str = "en"                  # English interviews
    vad_filter: bool = True               # skip silence segments
    vad_min_silence_ms: int = 500         # VAD silence threshold (ms)
    # Fallback: if CUDA fails (driver mismatch, OOM), retry on CPU
    fallback_device: str = "cpu"
    fallback_compute_type: str = "int8"


# ---------------------------------------------------------------------------
# Whisper Engine (singleton-ish, thread-safe after init)
# ---------------------------------------------------------------------------
class WhisperEngine:
    """
    Wraps faster-whisper model loading with automatic CUDA→CPU fallback.
    Once loaded, .transcribe() is thread-safe (faster-whisper uses internal locks).
    """

    def __init__(self, config: TranscriberConfig | None = None):
        self.cfg = config or TranscriberConfig()
        self._model: WhisperModel | None = None
        self._lock = threading.Lock()

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self._model = self._load()
        return self._model

    def _load(self) -> WhisperModel:
        """Load model: try CUDA first, fall back to CPU on any error."""
        try:
            logger.info(
                "Loading faster-whisper %s on %s (%s)…",
                self.cfg.model_size, self.cfg.device, self.cfg.compute_type,
            )
            m = WhisperModel(
                self.cfg.model_size,
                device=self.cfg.device,
                compute_type=self.cfg.compute_type,
            )
            logger.info("✓ Whisper loaded on %s", self.cfg.device)
            return m
        except Exception as exc:
            logger.warning(
                "CUDA load failed (%s), falling back to CPU int8: %s",
                type(exc).__name__, exc,
            )
            m = WhisperModel(
                self.cfg.model_size,
                device=self.cfg.fallback_device,
                compute_type=self.cfg.fallback_compute_type,
                cpu_threads=self.cfg.cpu_threads,
            )
            logger.info("✓ Whisper loaded on CPU (fallback)")
            return m

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe a float32 numpy array (16 kHz mono) → text string.
        Returns empty string on silence / error.
        """
        try:
            segments, _ = self.model.transcribe(
                audio,
                language=self.cfg.language,
                beam_size=self.cfg.beam_size,
                vad_filter=self.cfg.vad_filter,
                vad_parameters={"min_silence_duration_ms": self.cfg.vad_min_silence_ms},
            )
            text = " ".join(seg.text for seg in segments).strip()
            return text
        except Exception as exc:
            logger.error("Transcription error: %s", exc)
            return ""


# ---------------------------------------------------------------------------
# Transcription Worker — runs in a daemon thread, drains an audio queue
# ---------------------------------------------------------------------------
class TranscriberWorker:
    """
    Continuously pulls audio arrays from `audio_queue`, transcribes them,
    and calls `on_text(source, text)` with the result.

    `source` is a tag string ("mic" or "loopback") so the callback can route
    the text to the right handler (script_matcher vs copilot).
    """

    def __init__(
        self,
        engine: WhisperEngine,
        audio_queue: queue.Queue,
        on_text: Callable[[str, str], None],
        source_tag: str = "mic",
    ):
        self._engine = engine
        self._queue = audio_queue
        self._on_text = on_text
        self._source = source_tag
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name=f"transcriber-{self._source}"
        )
        self._thread.start()
        logger.info("TranscriberWorker [%s] started", self._source)

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        # Force model load on this thread's first iteration
        _ = self._engine.model
        while self._running:
            try:
                audio: np.ndarray = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            text = self._engine.transcribe(audio)
            if text:
                logger.debug("[%s] → %s", self._source, text[:80])
                try:
                    self._on_text(self._source, text)
                except Exception as exc:
                    logger.error("on_text callback error: %s", exc)
