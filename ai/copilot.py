"""
ai/copilot.py — VoiceBridge AI
Live Interview Co-Pilot: receives the interviewer's transcribed question,
sends it with Yago's technical profile to a fast LLM (Groq API), and
streams concise spoken-English bullet points for the teleprompter overlay.

Evolved from C:\\CacadorDeVagas\\tools\\cola_entrevista\\cola_entrevista.py
Key adaptations:
  - Reads profile from config/profile_context.md (not hardcoded CEREBRO_YAGO)
  - English output (cola_entrevista was Portuguese)
  - PyQt6 signal-based UI update (not tkinter root.after)
  - Clean separation: this module has zero UI imports
  - Configurable model cascade with per-call .env hot-reload (from cola_entrevista)
"""
from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

logger = logging.getLogger("voicebridge.copilot")

# ---------------------------------------------------------------------------
# Paths — resolved relative to project root
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
_PROFILE_PATH = _PROJECT_ROOT / "config" / "profile_context.md"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class CopilotConfig:
    """All tunables for the LLM co-pilot."""
    # Groq model cascade (try in order; first success wins)
    groq_models: list[str] = field(default_factory=lambda: [
        "llama-3.3-70b-versatile",   # best quality, free tier
        "openai/gpt-oss-120b",       # strong fallback
        "openai/gpt-oss-20b",        # lightweight fallback
    ])
    max_tokens: int = 500
    temperature: float = 0.3
    timeout: int = 6                 # seconds per Groq call
    history_window: int = 3          # keep last N transcript chunks for context
    profile_path: Path = _PROFILE_PATH
    env_path: Path = _ENV_PATH


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------
_SYSTEM_TEMPLATE = """You are VoiceBridge AI — a discreet, real-time interview co-pilot for Yago Santos Silva.

ROLE: You receive the interviewer's transcribed question. You output a SHORT spoken-English script that Yago will read aloud from his teleprompter while maintaining eye contact with his webcam.

FORMAT RULES:
1. First line: a complete opening sentence Yago can say immediately (gives context, sounds natural). Example: "In my accessibility research project at PICTA, I audited 12 government websites using WCAG 2.1 success criteria…"
2. Then 2–3 short bullet points (max 14 words each) in order: what happened → what I did → result/learning.
3. Use "|" between sentences as a breathing/pause marker for the teleprompter.
4. No labels (no "Situation:", "Action:", "Result:"). No headings. No markdown.
5. First person. Natural spoken English. Include real facts and numbers from the PROFILE below.
6. NEVER invent facts, numbers, or percentages not in the PROFILE.
7. If the PROFILE lacks info for a question, give a structure: "Real example: situation → action → result"
8. Keep total response under 80 words for fast reading.

PROFILE:
{profile}"""


def _load_profile(path: Path) -> str:
    """Load Yago's profile context from markdown file."""
    try:
        text = path.read_text(encoding="utf-8").strip()
        if text:
            return text
    except FileNotFoundError:
        logger.warning("Profile not found at %s — using fallback", path)
    except Exception as exc:
        logger.warning("Error reading profile: %s — using fallback", exc)

    # Minimal fallback so the system prompt is never empty
    return (
        "Yago Santos Silva — ADS student at Senac São Paulo.\n"
        "PICTA Accessibility Researcher: WCAG 2.1/2.2, NVDA, Axe, WAVE, Lighthouse audits.\n"
        "2 years at LATAM Airlines (SGSO safety management system).\n"
        "Skills: Python, Flutter, Java, n8n automation, Playwright, AI agents.\n"
        "Project: 'Caçador de Vagas' — automated job application bot (64 applications with evidence).\n"
        "CRM campaign reaching 5,839+ contacts via Meta API.\n"
        "English level: B1+ (improving daily with docs and practice)."
    )


# ---------------------------------------------------------------------------
# Co-Pilot Engine
# ---------------------------------------------------------------------------
class CopilotEngine:
    """
    Receives interviewer transcript chunks, accumulates recent history,
    calls the Groq API with streaming, and delivers tokens to a callback.

    Thread-safe: each `generate()` call runs in its own daemon thread.
    Hot-reloads .env on every call (so pasting a new API key works instantly,
    exactly like cola_entrevista.py does).
    """

    def __init__(
        self,
        on_token: Callable[[str], None] | None = None,
        on_complete: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        config: CopilotConfig | None = None,
    ):
        """
        Args:
            on_token:    called with each streamed token (for live overlay update)
            on_complete: called with the full response text when streaming finishes
            on_error:    called with error message string
        """
        self.cfg = config or CopilotConfig()
        self._on_token = on_token
        self._on_complete = on_complete
        self._on_error = on_error

        self._history: list[str] = []
        self._lock = threading.Lock()
        self._generating = False

        # Build system prompt once; profile is loaded at init and can be refreshed
        self._profile_text = _load_profile(self.cfg.profile_path)
        self._system_prompt = _SYSTEM_TEMPLATE.format(profile=self._profile_text)
        logger.info("CopilotEngine initialized (profile: %d chars)", len(self._profile_text))

    def reload_profile(self) -> None:
        """Re-read profile_context.md (e.g. after the user edits it mid-session)."""
        self._profile_text = _load_profile(self.cfg.profile_path)
        self._system_prompt = _SYSTEM_TEMPLATE.format(profile=self._profile_text)
        logger.info("Profile reloaded (%d chars)", len(self._profile_text))

    @property
    def is_generating(self) -> bool:
        return self._generating

    def feed_question(self, transcript_chunk: str) -> None:
        """
        Called when a new loopback transcript arrives (the interviewer's words).
        Appends to rolling history and kicks off LLM generation in a thread.
        """
        if not transcript_chunk.strip():
            return

        with self._lock:
            self._history.append(transcript_chunk.strip())
            # Keep only last N chunks (questions can arrive in 2-3 pieces,
            # exactly like cola_entrevista.py's HIST pattern)
            if len(self._history) > self.cfg.history_window:
                self._history = self._history[-self.cfg.history_window:]
            combined = " ".join(self._history)

        threading.Thread(
            target=self._generate, args=(combined,), daemon=True, name="copilot-gen"
        ).start()

    def _generate(self, question_text: str) -> None:
        """Run Groq API streaming in a background thread."""
        self._generating = True
        try:
            # Hot-reload .env so a freshly pasted API key works without restart
            # (validated pattern from cola_entrevista.py line 123)
            load_dotenv(str(self.cfg.env_path), override=True)

            groq_key = os.getenv("GROQ_API_KEY")
            if not groq_key:
                self._emit_error("GROQ_API_KEY not found in .env — paste it and retry")
                return

            from groq import Groq

            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": question_text},
            ]

            full_response = ""

            # Try each model in the cascade (validated pattern from cola_entrevista.py)
            for model_name in self.cfg.groq_models:
                try:
                    client = Groq(max_retries=0, timeout=self.cfg.timeout)
                    kwargs = {
                        "model": model_name,
                        "max_tokens": self.cfg.max_tokens,
                        "stream": True,
                        "messages": messages,
                    }
                    # Only some models support temperature; reasoning models
                    # use reasoning_effort instead
                    if model_name.startswith("openai/"):
                        kwargs["reasoning_effort"] = "low"
                    else:
                        kwargs["temperature"] = self.cfg.temperature

                    stream = client.chat.completions.create(**kwargs)

                    for chunk in stream:
                        token = chunk.choices[0].delta.content or ""
                        if token:
                            full_response += token
                            if self._on_token:
                                self._on_token(token)

                    # Success — stop trying other models
                    logger.info("Copilot response via %s (%d chars)", model_name, len(full_response))
                    break

                except Exception as model_exc:
                    logger.warning("Model %s failed: %s", model_name, model_exc)
                    full_response = ""  # reset for next attempt
                    continue
            else:
                # All models failed
                self._emit_error("All Groq models failed — check API key and quota")
                return

            if full_response.strip() and self._on_complete:
                self._on_complete(full_response.strip())

        except Exception as exc:
            logger.error("Copilot generation error: %s", exc)
            self._emit_error(f"Copilot error: {exc}")
        finally:
            self._generating = False

    def _emit_error(self, msg: str) -> None:
        logger.error(msg)
        if self._on_error:
            try:
                self._on_error(msg)
            except Exception:
                pass

    def clear_history(self) -> None:
        """Reset the question history (e.g. when switching interview topics)."""
        with self._lock:
            self._history.clear()
        logger.info("Copilot history cleared")
