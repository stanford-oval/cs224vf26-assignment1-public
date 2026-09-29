"""Central configuration for methodology-v2 — the single source of truth for which MODELS the agent
uses (and a few related knobs). Import from here instead of hardcoding model strings in each module.

    from . import config
    model = config.RUN_MODEL

WHAT LIVES HERE: model names, reasoning effort, the codex price table, and the PATH to the secrets
file. Edit this file to change models in one place.

WHAT DOES *NOT* LIVE HERE: secrets. API keys (AZURE_OPENAI_*, PAPERCLIP_API_KEY, OPENAI_API_KEY) stay
in the .env referenced by ENV_FILE — this module is committed to git, so keys must never be added.

Every value may still be overridden by an environment variable of the same name (handy for one-off
experiments); the literals below are the authoritative defaults.
"""
from __future__ import annotations

import os
from pathlib import Path


def _env(name: str, default: str) -> str:
    v = os.environ.get(name)
    return v if v not in (None, "") else default


def openai_base(raw):
    """Normalize an OPENAI_BASE_URL to the /v1 root the OpenAI SDK expects. Users often set the full
    chat endpoint (…/v1/chat/completions) for raw POSTs, but the SDK appends the route itself, so a
    trailing /chat/completions here would double it (and break /embeddings). Strip it defensively."""
    if not raw:
        return raw
    u = raw.strip().rstrip("/")
    for suf in ("/chat/completions", "/chat"):
        if u.endswith(suf):
            u = u[: -len(suf)]
    return u


# ── Models ───────────────────────────────────────────────────────────────────
# Codex executor model for EXPLORE / VERIFY / GROUND / etc. Per-run overridable via the CLI
# (--model) and the portal launch request; this is the default when none is given.
RUN_MODEL = _env("RUN_MODEL", "gpt-5.6-terra")
# Embedding model for dedup / coverage vectors.
EMBED_MODEL = _env("EMBED_MODEL", "text-embedding-3-large")
# Chat model that classifies free-text steer messages into structured steer events.
CLASSIFY_MODEL = _env("CLASSIFY_MODEL", "gpt-5.6-terra")
# Meta-assistant: the read-only codex that answers questions across a user's own files. Cheaper
# than the research model — it reads and synthesises, it doesn't run the search loop.
ASSIST_MODEL = _env("ASSIST_MODEL", "gpt-5.6-luna")
# Codex reasoning effort: minimal | low | medium | high.
REASONING = _env("REASONING", "low")

# ── Secrets file (the PATH, not the secrets) ──────────────────────────────────
# The .env holding API keys, read by the dotenv loaders in embed.py / codex_exec.py. Derived from this
# file's location (graph-search-sliders/.env) so it survives a repo move; override with GSS_ENV_FILE.
ENV_FILE = _env("GSS_ENV_FILE", str(Path(__file__).resolve().parent.parent / ".env"))

# ── Interpreter for spawned runs (steer_launcher) ─────────────────────────────
VENV_PYTHON = _env("STEER_PY", str(Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"))

# ── Interpreter the AGENT uses to build artifacts (charts / tables) in its workspace ──
# The opt-in sci stack from `make analysis-venv` (pandas, numpy, scipy, matplotlib). The artifact
# executor points codex at this if it exists and falls back to plain python3 otherwise.
ANALYSIS_PYTHON = _env("ANALYSIS_PYTHON",
                       str(Path(__file__).resolve().parent.parent / ".analysis-venv" / "bin" / "python"))


def analysis_python() -> str:
    """The interpreter to hand the artifact executor: the sci venv when it's installed, else python3."""
    return ANALYSIS_PYTHON if Path(ANALYSIS_PYTHON).is_file() else "python3"

# ── Codex $/1M-token price table: (input, output) by model ────────────────────
# REAL LiteLLM proxy rates verified via the x-litellm-response-cost header. Output dominates (reasoning
# tokens, ~6x input) so input and output are priced SEPARATELY. Key on the model that ran.
# gpt-5.6 family (terra/sol/luna) measured 2026-08 by solving cost = p*in + c*out over two calls.
MODEL_RATES_M = {
    "gpt-5": (2.50, 15.0), "gpt-5.4": (2.50, 15.0), "gpt-5.5": (2.50, 15.0),
    "gpt-5.2-codex": (2.50, 15.0), "gpt-5.3-codex": (2.50, 15.0),
    "gpt-5.6-terra": (2.50, 15.0), "gpt-5.6-sol": (5.00, 30.0), "gpt-5.6-luna": (1.00, 6.00),
    "gpt-5-mini": (0.75, 4.50), "gpt-5.4-mini": (0.75, 4.50),
    "gpt-5-nano": (0.20, 1.25), "gpt-5.4-nano": (0.20, 1.25),
}
DEFAULT_RATES_M = (2.50, 15.0)   # unknown model → full-model rates

# Embedding list price ($/token) for EMBED_MODEL (text-embedding-3-large).
EMBED_RATE_USD_PER_TOKEN = 0.13 / 1_000_000
