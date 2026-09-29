# embed.py

Low-level walkthrough of `embed.py`, the semantic-similarity helper. It wraps `text-embedding-3-large` behind a small cached `Embedder` and exposes cosine-similarity utilities used for the methodology's `cos(emb(·), emb(·))` terms (relevance, novelty, reference recall, context selection).

Related: [measure.py](./measure.md) (an external caller of the similarity math; orchestrator.py:494 also calls `rank` directly), [orchestrator.py](./orchestrator.md) (constructs the `Embedder` and meters its spend), [calibration.py](./calibration.md), [Budget, cost, and the FDR brake](../architecture/budget-cost-fdr.md).

## Overview

The module is 108 lines: three module-level constants, one env loader, the `Embedder` class, and a free `cosine` function. There is no async, no persistence, and no retry logic — embeddings are fetched synchronously through the OpenAI SDK and cached in-process for the lifetime of the `Embedder` instance.

| Symbol | Kind | Lines | Wired in? |
|---|---|---|---|
| `EMB_MODEL` | constant | embed.py:14 | yes |
| `EMB_RATE_USD_PER_TOKEN` | constant | embed.py:15 | yes |
| `DEFAULT_ENV` | constant | embed.py:16 | yes (default arg) |
| `_load_env` | function | embed.py:19-29 | yes (called in `__init__`) |
| `Embedder.__init__` | method | embed.py:33-39 | yes |
| `Embedder._client_` | method | embed.py:41-58 | yes (lazy) |
| `Embedder.embed` | method | embed.py:60-75 | yes (core) |
| `Embedder.one` | method | embed.py:77-78 | yes |
| `Embedder.cos` | method | embed.py:80-82 | **no — dead** |
| `Embedder.max_sim` | method | embed.py:84-89 | **no — dead** |
| `Embedder.rank` | method | embed.py:91-99 | yes |
| `cosine` | function | embed.py:102-108 | yes |

## Constants (embed.py:14-16)

| Name | Value | Meaning |
|---|---|---|
| `EMB_MODEL` | `"text-embedding-3-large"` | Model/deployment name passed as `model=` on every request. |
| `EMB_RATE_USD_PER_TOKEN` | `0.13 / 1_000_000` (= 1.3e-7 USD/token) | Metering rate. The inline comment labels it the `text-embedding-3-large` list price. |
| `DEFAULT_ENV` | `/data/oval/report_formation/graph-search-sliders-2/.env` | Absolute path to the `.env` file loaded on construction. |

Note the docstring (embed.py:4) describes the backend as "Azure `text-embedding-3-large`", but the metering rate is the OpenAI list price and the client can resolve to either an OpenAI-compatible proxy or an Azure endpoint depending on env (see [Client resolution](#client-resolution-embedpy41-58)).

## `_load_env` (embed.py:19-29)

A minimal dotenv reader. It takes a path, returns silently if the file does not exist (embed.py:21-22), then walks each line:

```
for line in file:
    strip whitespace
    skip if blank, starts with '#', or has no '='
    split on first '=' → k, v
    os.environ[k] = v  (strip surrounding quotes)
```

Key behavior: it **overwrites** any pre-existing environment variable (embed.py:29). The comment explains the intent — the `.env` file is authoritative, so a stale ambient value (e.g. a budget-exhausted `OPENAI_API_KEY` already exported in the shell) is clobbered rather than deferred to. Value cleanup strips a surrounding pair of double quotes then single quotes (embed.py:29).

## `Embedder` class

### `__init__` (embed.py:33-39)

Signature: `Embedder(model=EMB_MODEL, env_file=DEFAULT_ENV)`.

| Step | Line | Effect |
|---|---|---|
| Load env | embed.py:34 | Calls `_load_env(env_file)` immediately, so env is populated before any client is built. |
| `self.model` | embed.py:35 | Stored model name. |
| `self._cache` | embed.py:36 | `dict[str, list[float]]` — text → embedding vector. |
| `self._client` | embed.py:37 | `None` until first use (lazy). |
| `self.spent_usd` | embed.py:38 | Running USD meter, starts at 0.0. |
| `self.tokens` | embed.py:39 | Running token counter, starts at 0. |

Orchestrator constructs exactly one instance: `self.embedder = Embedder(env_file=cfg.env_file)` (orchestrator.py:157).

### Client resolution (`_client_`, embed.py:41-58)

Lazy singleton: builds the OpenAI client on first call and caches it in `self._client`. Import of `openai` is deferred to this method (embed.py:43), so importing `embed` has no hard dependency on the SDK until an embedding is actually requested.

Resolution order:

```
if OPENAI_BASE_URL and OPENAI_API_KEY both set:      # proxy path (embed.py:48-49)
    OpenAI(api_key=OPENAI_API_KEY,
           base_url=OPENAI_BASE_URL.rstrip("/"))       # used verbatim, no suffix
else:                                                  # Azure path (embed.py:50-57)
    key = AZURE_OPENAI_DOCUSET_API_KEY
          or AZURE_OPENAI_API_KEY
    ep  = AZURE_OPENAI_DOCUSET_ENDPOINT
          or AZURE_OPENAI_ENDPOINT
          or "https://docuset.openai.azure.com"
    if ep lacks "http": prepend "https://"
    OpenAI(api_key=key,
           base_url=ep.rstrip("/") + "/openai/v1")
```

| Env var | Role | Line |
|---|---|---|
| `OPENAI_BASE_URL` | Proxy base URL; must be set together with `OPENAI_API_KEY` to take the proxy path. Used verbatim (its `/v1` already carries the embeddings route). | embed.py:46,49 |
| `OPENAI_API_KEY` | Proxy API key. | embed.py:47,49 |
| `AZURE_OPENAI_DOCUSET_API_KEY` → `AZURE_OPENAI_API_KEY` | Azure key, first non-empty wins. | embed.py:51-52 |
| `AZURE_OPENAI_DOCUSET_ENDPOINT` → `AZURE_OPENAI_ENDPOINT` → `https://docuset.openai.azure.com` | Azure endpoint, first non-empty wins; hardcoded fallback last. | embed.py:53-54 |

On the Azure path the endpoint is normalized: a scheme is prepended if missing (embed.py:55-56) and `/openai/v1` is appended (embed.py:57). On the proxy path no suffix is added.

### `embed` (embed.py:60-75) — the core method

Signature: `embed(texts: list[str]) -> list[list[float]]`. Returns one vector per input text (or `None` for empty/whitespace inputs).

Data flow:

```
texts ──> {x.strip() for x in texts}          # dedupe within the call (embed.py:62)
      ──> keep t if t truthy and t not in cache   # only misses hit the API
      ──> `need` (list of unique uncached strings)

for i in range(0, len(need), 256):            # batch of ≤256 (embed.py:63-64)
    chunk = need[i:i+256]
    resp = client.embeddings.create(model, input=chunk)   # one API call (embed.py:65)
    cache[t] = d.embedding  for (t, d) in zip(chunk, resp.data)   # (embed.py:66-67)
    used  = resp.usage.total_tokens  OR  Σ len(t)//4       # metering (embed.py:68)
    self.tokens    += used
    self.spent_usd += used * EMB_RATE_USD_PER_TOKEN        # (embed.py:69-70)

# assemble output preserving input order & duplicates (embed.py:71-75)
out = [cache.get(t) if t else None  for x in texts, t = x.strip()]
return out
```

Points to note:

- **Caching** is by stripped text (embed.py:62, 67, 74). Repeated or duplicated strings — within a call or across calls on the same instance — are embedded once. The cache is unbounded and lives only in memory; there is no eviction and no disk persistence.
- **Empty/whitespace** inputs map to `None`, not a zero vector (embed.py:74). The `embed` docstring says "Empty/whitespace → zero vector" (embed.py:61), but the code returns `None`; `cosine` then treats that `None` as similarity 0.0 (embed.py:103), so the observable effect matches "zero" even though no zero vector is materialized.
- **Batching** is fixed at 256 texts per request (embed.py:63). Batches operate on `need` (misses only), so a fully-cached call makes zero API calls.
- **Token metering** prefers the provider-reported `resp.usage.total_tokens`; if that attribute is absent or zero it falls back to a `len(text)//4` character heuristic per chunk item (embed.py:68). `spent_usd` is incremented by `used * EMB_RATE_USD_PER_TOKEN` (embed.py:70).

### Metering consumers

`spent_usd` is the meter the orchestrator reads; `tokens` is accumulated but never read anywhere in the package.

| Attribute | Written | Read |
|---|---|---|
| `spent_usd` | embed.py:70 | orchestrator.py:192,195 (charges the delta since last check) and orchestrator.py:700 (reports it under an `"embeddings"` cost line) |
| `tokens` | embed.py:69 | **never read** — dead accumulator |

The orchestrator meters by delta: it computes `self.embedder.spent_usd - self._emb_charged` (orchestrator.py:192), bills the difference against the budget, then advances `self._emb_charged` (orchestrator.py:195).

### Convenience methods

| Method | Lines | Definition | Used by |
|---|---|---|---|
| `one(text)` | embed.py:77-78 | `self.embed([text])[0]` — single vector or `None`. | `cos`, `max_sim`, `rank` internally; measure.py:45 (`emb.one(bias)`) externally |
| `cos(a, b)` | embed.py:80-82 | Embeds both, returns `cosine(va, vb)`. | **Nothing** — no caller in the package (dead) |
| `max_sim(query, candidates)` | embed.py:84-89 | Max cosine of `query` against each candidate; `0.0` on empty list. | **Nothing** — no caller in the package (dead) |
| `rank(query, items)` | embed.py:91-99 | `(index, cosine)` per item, sorted descending. | orchestrator.py:494, measure.py:25 |

`rank` (embed.py:91-99): embeds the query with `one` and all items with `embed`, scores each item's cosine to the query, assigns `-1.0` to any item whose vector is `None` (embed.py:97), then sorts by score descending (embed.py:98). Empty `items` returns `[]` (embed.py:93-94).

**Dead code note:** `cos` and `max_sim` are fully implemented but never invoked by the orchestrator, measure module, or anywhere else in the package. Only `embed`, `one`, and `rank` are wired into the running system.

## `cosine` (embed.py:102-108)

Module-level function, `cosine(a, b) -> float`. Not a method — the `Embedder` similarity helpers call it as a free function.

```
if a falsy or b falsy: return 0.0          # None or empty vector (embed.py:103)
dot = Σ a_i * b_i
na  = sqrt(Σ a_i^2)
nb  = sqrt(Σ b_i^2)
return dot / (na * nb)  if na and nb else 0.0   # (embed.py:108)
```

It guards against `None`/empty operands (embed.py:103) and against zero-norm vectors (embed.py:108), returning `0.0` in both degenerate cases. This is where a `None` vector produced by `embed` for empty text becomes an effective similarity of zero. Note there is no length check: if `a` and `b` differ in dimension, `zip` silently truncates to the shorter, but in practice all vectors come from the same model and share dimensionality.

## End-to-end control flow

```
measure.py / orchestrator.py
        │  emb.rank(query, items)  |  emb.one(text)  |  emb.embed(texts)
        ▼
   Embedder.embed(texts)
        │  strip + dedupe → filter cache misses → `need`
        ├── all hit?  ──────────────► assemble from cache, 0 API calls
        └── misses?   ──► _client_()  (lazy build, resolve proxy vs Azure env)
                          │
                          ▼
                    for each 256-batch:
                       client.embeddings.create(...)
                       cache results, add tokens, add USD
        ▼
   list[list[float] | None]  (input order & duplicates preserved)
        ▼
   cosine(vq, v)  per pair  → similarity scores
```

The orchestrator periodically reads `embedder.spent_usd` and charges the delta to the run budget, so embedding cost participates in the same budget accounting as codex executor calls.
