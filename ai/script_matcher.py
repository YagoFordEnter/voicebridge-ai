"""
ai/script_matcher.py — VoiceBridge AI
Fuzzy voice-tracking engine: compares Yago's spoken words (from mic transcription)
against the loaded teleprompter script and calculates the current reading position
so the overlay can auto-scroll smoothly.

Uses rapidfuzz for fast Levenshtein / partial-ratio matching at ~µs per comparison.

Design:
  - The script is split into a flat word list with per-word character offsets.
  - Each incoming mic transcription is a "spoken window" of ~5-20 words.
  - We slide the spoken window across a search region in the script
    (around the last known position ± look_ahead/look_back) and find the
    best-matching anchor using token_set_ratio.
  - The resulting word-index is emitted as a scroll position (0.0–1.0 fraction).
"""
from __future__ import annotations

import logging
import re
import threading
import unicodedata
from dataclasses import dataclass, field
from typing import Callable

from rapidfuzz import fuzz

logger = logging.getLogger("voicebridge.script_matcher")


def _normalize(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text: str) -> list[str]:
    """Split normalized text into word tokens."""
    return _normalize(text).split()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class MatcherConfig:
    look_back: int = 10        # words behind cursor to include in search window
    look_ahead: int = 60       # words ahead of cursor to scan
    min_spoken_words: int = 3  # ignore very short fragments (noise / filler)
    min_score: float = 55.0    # minimum rapidfuzz score to accept a match
    window_size: int = 8       # words to extract from script per sliding step
    step: int = 2              # sliding step size (words)


# ---------------------------------------------------------------------------
# Script Matcher
# ---------------------------------------------------------------------------
class ScriptMatcher:
    """
    Stateful matcher that tracks position in a teleprompter script.

    Usage:
        matcher = ScriptMatcher(on_position=lambda frac, idx: overlay.scroll_to(frac))
        matcher.load_script("Hello, my name is Yago ...")
        # called every time mic transcription arrives:
        matcher.feed("hello my name is")
    """

    def __init__(
        self,
        on_position: Callable[[float, int], None] | None = None,
        config: MatcherConfig | None = None,
    ):
        """
        Args:
            on_position: callback(fraction: float, word_index: int) — called on
                         each successful match with the scroll fraction [0.0, 1.0]
                         and the absolute word index in the script.
            config: tuning parameters.
        """
        self.cfg = config or MatcherConfig()
        self._on_position = on_position

        self._words: list[str] = []          # normalized word list of the full script
        self._raw_words: list[str] = []      # original-case word list (for display)
        self._cursor: int = 0                # current best-match word index
        self._lock = threading.Lock()
        self._script_loaded = False

    # --- Public API ---------------------------------------------------------

    def load_script(self, text: str) -> None:
        """Load (or replace) the teleprompter script text."""
        with self._lock:
            self._raw_words = text.split()
            self._words = _tokenize(text)
            self._cursor = 0
            self._script_loaded = bool(self._words)
            logger.info("Script loaded: %d words", len(self._words))

    @property
    def total_words(self) -> int:
        return len(self._words)

    @property
    def cursor(self) -> int:
        return self._cursor

    @property
    def fraction(self) -> float:
        if not self._words:
            return 0.0
        return self._cursor / max(1, len(self._words) - 1)

    def feed(self, spoken_text: str) -> None:
        """
        Receive a chunk of transcribed speech from the mic.
        Finds the best matching position in the script and updates the cursor.
        """
        if not self._script_loaded:
            return

        spoken_tokens = _tokenize(spoken_text)
        if len(spoken_tokens) < self.cfg.min_spoken_words:
            return

        spoken_joined = " ".join(spoken_tokens)

        with self._lock:
            best_score = 0.0
            best_idx = self._cursor

            # Define search boundaries around current cursor
            search_start = max(0, self._cursor - self.cfg.look_back)
            search_end = min(len(self._words), self._cursor + self.cfg.look_ahead)

            # Slide a window through the search region
            for i in range(search_start, search_end - self.cfg.window_size + 1, self.cfg.step):
                candidate = " ".join(self._words[i : i + self.cfg.window_size])
                score = fuzz.token_set_ratio(spoken_joined, candidate)
                if score > best_score:
                    best_score = score
                    best_idx = i

            if best_score >= self.cfg.min_score:
                # Only advance forward (or stay), never jump far backward
                # Allow small backward jumps (re-reads) but not wild ones
                if best_idx >= self._cursor - self.cfg.look_back:
                    self._cursor = best_idx
                    frac = self._cursor / max(1, len(self._words) - 1)
                    logger.debug(
                        "Match score=%.0f idx=%d frac=%.2f spoken='%s'",
                        best_score, best_idx, frac, spoken_joined[:60],
                    )
                    if self._on_position:
                        try:
                            self._on_position(frac, self._cursor)
                        except Exception as exc:
                            logger.error("on_position callback error: %s", exc)
            else:
                logger.debug(
                    "No match (best=%.0f < %.0f) for '%s'",
                    best_score, self.cfg.min_score, spoken_joined[:60],
                )

    def get_highlight_range(self, context_words: int = 3) -> tuple[int, int]:
        """
        Returns (start_idx, end_idx) of the word range to highlight
        in the teleprompter, centered around the cursor.
        """
        start = max(0, self._cursor)
        end = min(len(self._raw_words), self._cursor + context_words)
        return start, end

    def get_visible_text(
        self, before: int = 5, after: int = 40
    ) -> tuple[str, str, str]:
        """
        Returns (text_before_cursor, highlighted_words, text_after)
        for rendering in the overlay.
        """
        if not self._raw_words:
            return ("", "", "")
        s = max(0, self._cursor - before)
        e = min(len(self._raw_words), self._cursor + after)
        cur_end = min(len(self._raw_words), self._cursor + 3)

        before_text = " ".join(self._raw_words[s : self._cursor])
        highlight = " ".join(self._raw_words[self._cursor : cur_end])
        after_text = " ".join(self._raw_words[cur_end : e])
        return before_text, highlight, after_text

    def reset(self) -> None:
        """Reset cursor to the beginning."""
        with self._lock:
            self._cursor = 0
