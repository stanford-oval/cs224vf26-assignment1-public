"""Embeddings helper — semantic similarity for the methodology's `cos(emb(·), emb(·))`
terms (relevance, novelty, reference recall, context selection). Methodology §5/§7e.

Uses Azure `text-embedding-3-large` on the same docuset endpoint codex uses (verified
reachable). Vectors are cached by text so repeated comparisons cost nothing. This
replaces every lexical/token-overlap proxy in v1 of this package.
"""
from __future__ import annotations

import math
import os
import time
from pathlib import Path

from . import config

# Model + rates + secrets-file path live in config.py (single source of truth); aliased for compat.
EMB_MODEL = config.EMBED_MODEL
EMB_RATE_USD_PER_TOKEN = config.EMBED_RATE_USD_PER_TOKEN
DEFAULT_ENV = config.ENV_FILE


def _load_env(path: str) -> None:
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            # .env is the authoritative config here — override any (possibly stale) ambient value,
            # e.g. a budget-exhausted OPENAI_API_KEY already exported in the shell.
            os.environ[k.strip()] = v.strip().strip('"').strip("'")


class Embedder:
    def __init__(self, model: str = EMB_MODEL, env_file: str = DEFAULT_ENV):
        _load_env(env_file)
        self.model = model
        self._cache: dict[str, list[float]] = {}
        self._client = None
        self.spent_usd = 0.0
        self.tokens = 0

    def _client_(self):
        if self._client is None:
            from openai import OpenAI
            # Prefer an OpenAI-compatible proxy (Stanford LiteLLM) when configured — its /v1 base
            # already carries the embeddings route, so it is used verbatim (no /openai/v1 suffix).
            base = config.openai_base(os.environ.get("OPENAI_BASE_URL"))
            okey = os.environ.get("OPENAI_API_KEY")
            if base and okey:
                self._client = OpenAI(api_key=okey, base_url=base)
            else:
                key = (os.environ.get("AZURE_OPENAI_DOCUSET_API_KEY")
                       or os.environ.get("AZURE_OPENAI_API_KEY"))
                ep = (os.environ.get("AZURE_OPENAI_DOCUSET_ENDPOINT")
                      or os.environ.get("AZURE_OPENAI_ENDPOINT") or "https://docuset.openai.azure.com")
                if not ep.startswith("http"):
                    ep = "https://" + ep
                self._client = OpenAI(api_key=key, base_url=ep.rstrip("/") + "/openai/v1")
        return self._client

    def _create(self, chunk: list[str]):
        """One embeddings call, retried through transient proxy failures. The shared LiteLLM proxy
        intermittently returns 429/502/503 (rate limits, nginx restarts); without this a single blip
        kills a multi-hour run mid-round and loses everything since the last checkpoint."""
        last = None
        for attempt in range(6):
            try:
                return self._client_().embeddings.create(model=self.model, input=chunk)
            except Exception as e:                       # noqa: BLE001 - retry on anything transient
                last = e
                msg = str(e)
                transient = any(c in msg for c in ("429", "500", "502", "503", "504",
                                                   "Timeout", "timeout", "Connection", "temporarily"))
                if not transient or attempt == 5:
                    raise
                delay = min(60.0, 2.0 * (2 ** attempt))  # 2, 4, 8, 16, 32, capped
                print(f"[embed] transient error ({msg[:90]}) — retry {attempt + 1}/5 in {delay:.0f}s",
                      flush=True)
                time.sleep(delay)
        raise last                                       # unreachable, but keeps the contract explicit

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts (cached). Empty/whitespace → zero vector."""
        need = [t for t in {x.strip() for x in texts} if t and t not in self._cache]
        for i in range(0, len(need), 256):
            chunk = need[i:i + 256]
            resp = self._create(chunk)
            for t, d in zip(chunk, resp.data):
                self._cache[t] = d.embedding
            used = getattr(getattr(resp, "usage", None), "total_tokens", 0) or sum(len(t) // 4 for t in chunk)
            self.tokens += used
            self.spent_usd += used * EMB_RATE_USD_PER_TOKEN
        out = []
        for x in texts:
            t = x.strip()
            out.append(self._cache.get(t) if t else None)
        return out

    def one(self, text: str) -> list[float] | None:
        return self.embed([text])[0]

    def cos(self, a: str, b: str) -> float:
        va, vb = self.embed([a, b])
        return cosine(va, vb)

    def max_sim(self, query: str, candidates: list[str]) -> float:
        if not candidates:
            return 0.0
        vq = self.one(query)
        vs = self.embed(candidates)
        return max((cosine(vq, v) for v in vs if v is not None), default=0.0)

    def rank(self, query: str, items: list[str]) -> list[tuple[int, float]]:
        """Return (index, cosine) for each item, sorted by similarity desc."""
        if not items:
            return []
        vq = self.one(query)
        vs = self.embed(items)
        scored = [(i, cosine(vq, v) if v is not None else -1.0) for i, v in enumerate(vs)]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored


def cosine(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
