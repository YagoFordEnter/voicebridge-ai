"""
ai/copilot.py — VoiceBridge AI
Live Interview Co-Pilot: receives the interviewer's transcribed question,
sends it with Yago's technical profile to an LLM, and
streams concise spoken-English bullet points for the teleprompter overlay.

Features:
  - Multi-provider support: Groq, DeepSeek, and local Ollama via OpenAI-compatible SDK
  - Hot-reloads .env on every call (allows dynamic key/provider changes without restart)
  - Resilient model cascading: tries primary model, falls back to lightweight model on failure/404
  - Formatted for spoken English (<80 words, opening line + short bullets + "|" pause markers)
"""
from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Any

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
    provider: str = "groq"           # "groq", "deepseek", or "ollama"
    # Groq cascade: primary high-quality OSS model, followed by fast 20b fallback
    groq_models: list[str] = field(default_factory=lambda: [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ])
    deepseek_models: list[str] = field(default_factory=lambda: [
        "deepseek-chat",
    ])
    ollama_models: list[str] = field(default_factory=lambda: [
        "llama3.2",
        "qwen2.5:7b",
    ])
    max_tokens: int = 500
    temperature: float = 0.3
    timeout: int = 7                 # seconds per request
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
    calls the configured LLM API (Groq, DeepSeek, Ollama) with streaming,
    and delivers tokens to callbacks.

    Thread-safe: each `feed_question()` call kicks off generation in a daemon thread.
    Hot-reloads .env on every call (allows dynamic key/provider changes without restart).
    """

    def __init__(
        self,
        on_token: Callable[[str], None] | None = None,
        on_complete: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        config: CopilotConfig | None = None,
        client_override: Any | None = None,  # for dependency injection in unit tests
    ):
        self.cfg = config or CopilotConfig()
        self._on_token = on_token
        self._on_complete = on_complete
        self._on_error = on_error
        self._client_override = client_override

        self._history: list[str] = []
        self._lock = threading.Lock()
        self._generating = False

        self._profile_text = _load_profile(self.cfg.profile_path)
        self._system_prompt = self._build_system_prompt()
        logger.info("CopilotEngine initialized (profile: %d chars)", len(self._profile_text))

    def _build_system_prompt(self) -> str:
        return _SYSTEM_TEMPLATE.format(profile=self._profile_text)

    def reload_profile(self) -> None:
        """Re-read profile_context.md (e.g. after editing mid-session)."""
        self._profile_text = _load_profile(self.cfg.profile_path)
        self._system_prompt = self._build_system_prompt()
        logger.info("Profile reloaded (%d chars)", len(self._profile_text))

    @property
    def is_generating(self) -> bool:
        return self._generating

    def feed_question(self, transcript_chunk: str) -> None:
        """
        Called when a new transcript arrives (the interviewer's speech).
        Appends to rolling history and kicks off LLM generation in a thread.
        """
        if not transcript_chunk.strip():
            return

        with self._lock:
            self._history.append(transcript_chunk.strip())
            if len(self._history) > self.cfg.history_window:
                self._history = self._history[-self.cfg.history_window:]
            combined = " ".join(self._history)

        threading.Thread(
            target=self._generate, args=(combined,), daemon=True, name="copilot-gen"
        ).start()

    def generate_sync(self, question_text: str) -> str:
        """Synchronous version for automated QA, CLI testing and benchmarks."""
        result: list[str] = []
        error_holder: list[str] = []

        old_token = self._on_token
        old_complete = self._on_complete
        old_error = self._on_error

        self._on_token = lambda t: None
        self._on_complete = lambda full: result.append(full)
        self._on_error = lambda err: error_holder.append(err)

        try:
            self._generate(question_text)
        finally:
            self._on_token = old_token
            self._on_complete = old_complete
            self._on_error = old_error

        if error_holder and not result:
            raise RuntimeError(error_holder[0])
        return result[0] if result else ""

    def _get_provider_setup(self) -> tuple[str, list[str], Any]:
        """Resolves active provider, model list, and initialized client."""
        if self._client_override is not None:
            return "override", ["test-model-1", "test-model-2"], self._client_override

        provider = os.getenv("LLM_PROVIDER", self.cfg.provider).lower().strip()

        if provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY not found in .env for provider 'deepseek'")
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=self.cfg.timeout)
            return "deepseek", [model], client

        elif provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            model = os.getenv("OLLAMA_MODEL", "llama3.2")
            from openai import OpenAI
            client = OpenAI(api_key="ollama", base_url=base_url, timeout=self.cfg.timeout)
            return "ollama", [model] + self.cfg.ollama_models, client

        else:
            # Default: Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in .env for provider 'groq'")
            from groq import Groq
            client = Groq(api_key=api_key, max_retries=0, timeout=self.cfg.timeout)
            return "groq", self.cfg.groq_models, client

    def _generate(self, question_text: str) -> None:
        """Runs streaming LLM generation with cascading model fallback."""
        self._generating = True
        try:
            load_dotenv(str(self.cfg.env_path), override=True)

            try:
                provider_name, models_to_try, client = self._get_provider_setup()
            except Exception as e:
                self._emit_error(str(e))
                return

            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": question_text},
            ]

            full_response = ""
            last_exception: Exception | None = None

            for model_name in models_to_try:
                try:
                    logger.info("Attempting copilot generation via [%s] model: %s", provider_name, model_name)
                    kwargs: dict[str, Any] = {
                        "model": model_name,
                        "max_tokens": self.cfg.max_tokens,
                        "stream": True,
                        "messages": messages,
                    }

                    if provider_name == "groq" and model_name.startswith("openai/"):
                        kwargs["reasoning_effort"] = "low"
                    else:
                        kwargs["temperature"] = self.cfg.temperature

                    stream = client.chat.completions.create(**kwargs)

                    for chunk in stream:
                        delta = chunk.choices[0].delta
                        token = getattr(delta, "content", None) or ""
                        if token:
                            full_response += token
                            if self._on_token:
                                self._on_token(token)

                    if full_response.strip():
                        logger.info("✓ Copilot response completed via %s (%d chars)", model_name, len(full_response))
                        break
                    else:
                        logger.warning("Model %s returned empty text, falling back...", model_name)

                except Exception as model_exc:
                    logger.warning("Model %s failed: %s. Trying fallback if available...", model_name, model_exc)
                    last_exception = model_exc
                    full_response = ""
                    continue
            else:
                err_msg = f"All models failed for provider '{provider_name}': {last_exception}"
                self._emit_error(err_msg)
                return

            if full_response.strip() and self._on_complete:
                self._on_complete(full_response.strip())

        except Exception as exc:
            logger.error("Copilot generation unexpected error: %s", exc)
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
        """Reset question history."""
        with self._lock:
            self._history.clear()
        logger.info("Copilot history cleared")
