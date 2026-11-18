"""
audio/capture.py — VoiceBridge AI
Dual-channel audio capture:
  Channel 1 (Loopback): Interviewer's audio via WASAPI loopback in isolated subprocess.
  Channel 2 (Mic):      Yago's microphone via sounddevice in a daemon thread.

Evolved from C:\\CacadorDeVagas\\tools\\cola_entrevista\\cola_entrevista.py
Key pattern preserved: loopback MUST run in a subprocess (not a thread) —
in a thread, Windows WASAPI drops audio packets under load.
"""
from __future__ import annotations

import atexit
import logging
import os
import queue
import subprocess
import sys
import threading

import numpy as np

logger = logging.getLogger("voicebridge.capture")

SAMPLE_RATE = 16_000  # 16 kHz mono — what faster-whisper expects

# ---------------------------------------------------------------------------
# Loopback subprocess helper (runs as __main__ with --rec-loopback)
# ---------------------------------------------------------------------------

def _record_loopback_forever(out_stream) -> None:
    """
    Capture system audio (interviewer) via WASAPI loopback.
    Runs as the main function of a child process — never in a thread.
    Writes length-prefixed float32 buffers to stdout.

    Silence detection: waits ~1.75s of silence (7 × 0.25s chunks) after
    speech ends before flushing, so the full question is captured.
    Max utterance: 30s (120 chunks) to prevent infinite buffering.
    """
    import soundcard as sc  # imported here so parent process doesn't need it at top-level

    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    buf: list[np.ndarray] = []
    silent_chunks = 0
    rms_threshold = 0.01  # calibrated in cola_entrevista.py

    with mic.recorder(samplerate=SAMPLE_RATE, channels=1) as rec:
        while True:
            chunk = rec.record(numframes=SAMPLE_RATE // 4).flatten()  # 0.25s
            is_loud = float(np.sqrt(np.mean(chunk ** 2))) > rms_threshold

            if is_loud:
                buf.append(chunk)
                silent_chunks = 0
            elif buf:
                silent_chunks += 1

            # Flush when: ≥1.75s silence after speech, or ≥30s continuous
            if buf and (silent_chunks >= 7 or len(buf) >= 120):
                data = np.concatenate(buf).astype(np.float32).tobytes()
                buf.clear()
                silent_chunks = 0
                out_stream.write(len(data).to_bytes(4, "little") + data)
                out_stream.flush()


# ---------------------------------------------------------------------------
# Loopback Reader — spawns subprocess and reads its stdout
# ---------------------------------------------------------------------------
class LoopbackCapture:
    """
    Spawns a child process that records WASAPI loopback audio and pushes
    complete utterance arrays into `output_queue`.
    """

    def __init__(self, output_queue: queue.Queue):
        self._queue = output_queue
        self._process: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        # Launch child process using this same file with --rec-loopback flag
        capture_script = os.path.abspath(__file__)
        self._process = subprocess.Popen(
            [sys.executable, "-W", "ignore", capture_script, "--rec-loopback"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        atexit.register(self._kill)
        self._thread = threading.Thread(target=self._read_loop, daemon=True, name="loopback-reader")
        self._thread.start()
        logger.info("LoopbackCapture started (PID %s)", self._process.pid)

    def _read_loop(self) -> None:
        assert self._process and self._process.stdout
        stdout = self._process.stdout
        while self._running:
            try:
                length_bytes = stdout.read(4)
                if not length_bytes or len(length_bytes) < 4:
                    break
                n = int.from_bytes(length_bytes, "little")
                raw = stdout.read(n)
                if not raw or len(raw) < n:
                    break
                audio = np.frombuffer(raw, dtype=np.float32)
                self._queue.put(audio)
            except Exception as exc:
                logger.error("Loopback read error: %s", exc)
                break
        logger.warning("Loopback reader exited")

    def stop(self) -> None:
        self._running = False
        self._kill()

    def _kill(self) -> None:
        if self._process:
            try:
                self._process.kill()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Microphone Capture — runs in a daemon thread
# ---------------------------------------------------------------------------
class MicCapture:
    """
    Captures audio from the default microphone using sounddevice.
    Pushes short chunks (~0.5s) into `output_queue` for real-time transcription.
    Uses a simple voice-activity gate so the transcriber isn't flooded with silence.
    """

    def __init__(self, output_queue: queue.Queue, chunk_seconds: float = 0.5):
        self._queue = output_queue
        self._chunk_frames = int(SAMPLE_RATE * chunk_seconds)
        self._thread: threading.Thread | None = None
        self._running = False
        # Accumulation buffer: collect spoken chunks, flush after short silence
        self._buf: list[np.ndarray] = []
        self._silent_chunks = 0
        self._rms_threshold = 0.008  # slightly lower than loopback; mic is closer
        self._silence_flush = 4      # 4 × 0.5s = 2s silence → flush

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True, name="mic-capture")
        self._thread.start()
        logger.info("MicCapture started")

    def _record_loop(self) -> None:
        import sounddevice as sd  # lazy import

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                            blocksize=self._chunk_frames) as stream:
            while self._running:
                chunk, _ = stream.read(self._chunk_frames)
                audio = chunk.flatten()
                rms = float(np.sqrt(np.mean(audio ** 2)))

                if rms > self._rms_threshold:
                    self._buf.append(audio)
                    self._silent_chunks = 0
                elif self._buf:
                    self._silent_chunks += 1

                # Flush accumulated speech after silence gap
                if self._buf and (self._silent_chunks >= self._silence_flush or len(self._buf) >= 60):
                    combined = np.concatenate(self._buf).astype(np.float32)
                    self._buf.clear()
                    self._silent_chunks = 0
                    self._queue.put(combined)

    def stop(self) -> None:
        self._running = False


# ---------------------------------------------------------------------------
# Subprocess entry point for loopback recording
# ---------------------------------------------------------------------------
if __name__ == "__main__" or (len(sys.argv) > 1 and sys.argv[-1] == "--rec-loopback"):
    if "--rec-loopback" in sys.argv:
        import warnings
        warnings.filterwarnings("ignore")
        _record_loopback_forever(sys.stdout.buffer)
        sys.exit(0)
