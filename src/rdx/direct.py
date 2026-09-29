"""GRILL without codex: one structured call per task, retrieval done by the harness.

Why this exists. GRILL's only model primitive is ``codex exec``: an agentic CLI
with a shell, given a prompt and an output schema. On gpt-5.6-terra that works.
On gemini-3.8-flash it does not, and not for the reason one would guess. The
model does the task correctly, then treats codex as a coding agent: it lists
directories, greps files, builds the JSON with Python, validates it, prints it,
and issues ``bash -lc true`` until the run times out, without ever sending the
final message codex is waiting for. A trivial field-parsing task cost 48 shell
calls and 180,000 tokens. It has nothing to do with web search; the failing
tasks run in a read-only sandbox with no network.

So this module replaces the primitive. Every executor call becomes:

    1. for a research task, ask the model for two search queries, run them
       through Serper (Scholar and web), fetch abstracts from Europe PMC for
       anything with a PMID, and format a SOURCES block with locators;
    2. one chat completion with the task prompt, the SOURCES block, and the
       schema as ``response_format``;
    3. cost from the token counts at Gemini's rates, not codex's estimate.

What is lost is the agent *reading* pages of its own choosing. A DEEP test
gets abstracts and snippets, not full text and supplementary tables. That is a
real limitation and shows up in the ledger as thinner evidence per claim; it
is also exactly the retrieval design of every plain RAG system, so a run built
this way is a fair comparison point rather than a degraded GRILL.

Everything the orchestrator sees is unchanged: the same prompts, the same
schemas, the same ledger, the same provenance gate. Steering, the belief
ledger, the two-stage test and the budget allocator all run as before.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Sequence

from . import serper

DEFAULT_MODEL = "gemini-3.8-flash"

#: USD per million tokens. Estimates for the proxy's Gemini Flash deployment;
#: the proxy returns no cost header for Gemini, so this is the best available.
PRICES = {"gemini-3.8-flash": (0.50, 3.00)}
FALLBACK_PRICE = (1.25, 10.00)

SYSTEM = (
    "You are one executor inside a literature-research system. You have NO tools and cannot "
    "browse: a retrieval step has already run, and the SOURCES block in the message is "
    "everything you may cite. Where the task says to search or read, use that block. Every "
    "SourceRef you emit must copy a locator from the block (PMID, DOI, PMC or URL) and its real "
    "title and authors; never invent one. If the block does not support a claim, say so in the "
    "JSON rather than filling it in. Reply with ONLY a JSON object matching the schema."
)

QUERY_SYSTEM = (
    "Write literature search queries. Return JSON {\"queries\": [q1, q2]}: one for Google "
    "Scholar (precise, quoted key terms) and one for the general web. Each under 12 words, "
    "no boolean operators."
)

_EPMC = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}"
         "&format=json&resultType=core&pageSize=1")
_abstract_cache: dict[str, str] = {}
_lock = threading.Lock()


def _price(model: str) -> tuple[float, float]:
    return PRICES.get(model, FALLBACK_PRICE)


def _client():
    from openai import OpenAI  # noqa: PLC0415

    base, key = os.environ.get("OPENAI_BASE_URL"), os.environ.get("OPENAI_API_KEY")
    if not (base and key):
        raise RuntimeError("OPENAI_BASE_URL / OPENAI_API_KEY not set; run the credentials cell.")
    return OpenAI(base_url=base, api_key=key)


def _chat(messages: list[dict], schema: dict | None, model: str, max_tokens: int) -> tuple[str, int, int]:
    client = _client()
    kwargs: dict[str, Any] = {"model": model, "messages": messages, "max_tokens": max_tokens,
                              "temperature": 0}
    if schema is not None:
        kwargs["response_format"] = {"type": "json_schema",
                                     "json_schema": {"name": "task", "schema": schema}}
    r = client.chat.completions.create(**kwargs)
    u = r.usage
    return ((r.choices[0].message.content or "").strip(),
            (u.prompt_tokens if u else 0), (u.completion_tokens if u else 0))


def _parse(raw: str) -> dict | None:
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return obj if isinstance(obj, dict) else None


# --------------------------------------------------------------------------
# Retrieval
# --------------------------------------------------------------------------


def abstract_for(hit: serper.Hit, timeout: int = 10) -> str:
    """Europe PMC abstract by PMID or DOI. Empty string when there is none."""
    key = (hit.pmid and f"EXT_ID:{hit.pmid} AND SRC:MED") or (hit.doi and f'DOI:"{hit.doi}"') or ""
    if not key and hit.title and len(hit.title) > 25:
        # Scholar hits usually carry neither locator; the title finds the record, and the
        # record then supplies the PMID the provenance gate wants.
        title = re.sub(r"[^\w\s-]", " ", hit.title.split(" - ")[0]).strip()
        key = f'TITLE:"{title[:150]}"'
    if not key:
        return ""
    with _lock:
        if key in _abstract_cache:
            return _abstract_cache[key]
    text = ""
    try:
        with urllib.request.urlopen(_EPMC.format(q=urllib.parse.quote(key)), timeout=timeout) as r:
            res = (json.loads(r.read()).get("resultList") or {}).get("result") or []
        if res:
            text = (res[0].get("abstractText") or "").strip()
            if not hit.pmid and res[0].get("pmid"):
                hit.pmid = str(res[0]["pmid"])
            if not hit.doi and res[0].get("doi"):
                hit.doi = str(res[0]["doi"])
    except Exception:  # noqa: BLE001 - offline is a normal state
        text = ""
    with _lock:
        _abstract_cache[key] = text
    return text


def retrieve(queries: Sequence[str], *, per_query: int = 5, cap: int = 10,
             with_abstracts: bool = True) -> list[serper.Hit]:
    hits: list[serper.Hit] = []
    seen: set[str] = set()
    for q in queries:
        for source in ("scholar", "search"):
            for h in serper.search(q, source, per_query):
                if not h.resolvable() or h.id in seen:
                    continue
                seen.add(h.id)
                hits.append(h)
    hits = hits[:cap]
    if with_abstracts:
        for h in hits:
            h.abstract = abstract_for(h)  # type: ignore[attr-defined]
    return hits


def sources_block(hits: Sequence[serper.Hit]) -> str:
    if not hits:
        return ("SOURCES: retrieval returned nothing usable for this task. You may not cite "
                "anything; report the absence of evidence.")
    lines = ["SOURCES (the only material you may cite; copy locators exactly):"]
    for i, h in enumerate(hits, 1):
        loc = " ".join(x for x in (h.pmid and f"PMID:{h.pmid}", h.doi and f"DOI:{h.doi}",
                                   h.pmc, h.url) if x)
        lines.append(f"\n[{i}] {h.title}\n    {h.authors or '(authors not shown)'}"
                     f"{f' ({h.year})' if h.year else ''}\n    {loc}")
        if h.snippet:
            lines.append(f"    snippet: {h.snippet}")
        ab = getattr(h, "abstract", "")
        if ab:
            lines.append(f"    abstract: {ab[:2500]}")
    return "\n".join(lines)


_FOCUS = re.compile(r"(?:DIRECTION TO EXPLORE|HYPOTHESIS TO TEST|HYPOTHESIS|CLAIM|Define the term)"
                    r"[^:\n]*:?\s*\n?\s*\"?([^\n\"]{15,200})", re.I)


def fallback_query(prompt: str) -> str:
    """When the model gives no query: the direction, hypothesis or term named in the prompt."""
    m = _FOCUS.search(prompt)
    text = m.group(1) if m else prompt[:200]
    words = re.findall(r"[A-Za-z][A-Za-z0-9.'-]{2,}", text)
    return " ".join(words[:12])


def queries_for(prompt: str, model: str) -> tuple[list[str], int, int]:
    """Two search queries for a task. Never returns an empty list.

    The output cap matters: Gemini's completion tokens include its reasoning,
    and a 300-token cap truncated the JSON mid-string on three of four deep
    tests in the first pilot, which then ran with no sources at all.
    """
    raw, i, o = _chat([{"role": "system", "content": QUERY_SYSTEM},
                       {"role": "user", "content": f"TASK PROMPT:\n{prompt[:6000]}"}],
                      {"type": "object", "properties": {"queries": {"type": "array",
                       "items": {"type": "string"}}}, "required": ["queries"]},
                      model, 2000)
    obj = _parse(raw) or {}
    qs = [str(q).strip() for q in (obj.get("queries") or []) if str(q).strip()][:2]
    if not qs:
        qs = [fallback_query(prompt)]
    return qs, i, o


# --------------------------------------------------------------------------
# The executor
# --------------------------------------------------------------------------


def run_task_direct(task_dir, prompt: str, schema: dict, *, mode: str = "research",
                    model: str = DEFAULT_MODEL, retrieval: bool = True,
                    max_tokens: int = 16000, **_ignored) -> tuple[dict | None, float]:
    """Drop-in for ``executors.run_task``: (validated_json, usd_spent)."""
    task_dir = Path(task_dir)
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "prompt.txt").write_text(prompt)
    (task_dir / "schema.json").write_text(json.dumps(schema, indent=2))
    t0 = time.time()
    tin = tout = 0
    meta: dict[str, Any] = {"mode": mode, "model": model, "executor": "direct"}

    block = ""
    if mode == "research" and retrieval:
        qs, i, o = queries_for(prompt, model)
        tin += i; tout += o
        hits = retrieve(qs) if qs else []
        block = sources_block(hits)
        meta.update(queries=qs, n_hits=len(hits),
                    hits=[{"id": h.id, "title": h.title, "pmid": h.pmid, "doi": h.doi,
                           "url": h.url, "abstract_chars": len(getattr(h, "abstract", ""))}
                          for h in hits])
        (task_dir / "sources.txt").write_text(block)

    user = prompt + ("\n\n" + block if block else "") + \
        "\n\nReturn ONLY a JSON object that validates against this schema:\n" + json.dumps(schema)
    data = None
    for attempt in range(2):
        raw, i, o = _chat([{"role": "system", "content": SYSTEM},
                           {"role": "user", "content": user}], schema, model, max_tokens)
        tin += i; tout += o
        (task_dir / f"raw_{attempt}.txt").write_text(raw)
        data = _parse(raw)
        if data is not None:
            break
        user += "\n\nYour previous reply was not valid JSON. Reply with the JSON object only."

    pin, pout = _price(model)
    usd = (tin * pin + tout * pout) / 1e6
    meta.update(input_tokens=tin, output_tokens=tout, usd=round(usd, 5),
                seconds=round(time.time() - t0, 1), ok=data is not None)
    (task_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    if data is not None:
        (task_dir / "out.json").write_text(json.dumps(data, indent=2))
    return data, usd


_install_lock = threading.Lock()
_install_count = 0
_install_original = None


def install(model: str = DEFAULT_MODEL, *, retrieval: bool = True, root=None):
    """Route every GRILL executor through ``run_task_direct``. Returns an undo.

    Reference-counted, because several runs share one interpreter when a batch
    runs them in threads. The first version restored the codex executor when
    *any* run finished, which silently switched the runs still in flight back
    to codex; on Gemini that meant the last run of a batch stalled in exactly
    the tool loop this module exists to avoid. Now the patch stays until the
    last installer has undone it.
    """
    global _install_count, _install_original
    from . import grill as G  # noqa: PLC0415

    G.add_grill_to_path(root or G.GRILL_ROOT)
    import src.executors as executors  # noqa: PLC0415

    def patched(task_dir, prompt, schema, **kw):
        kw.pop("model", None)
        return run_task_direct(task_dir, prompt, schema, model=model, retrieval=retrieval, **kw)

    with _install_lock:
        if _install_count == 0:
            _install_original = executors.run_task
        _install_count += 1
        executors.run_task = patched

    done = {"v": False}

    def undo():
        global _install_count, _install_original
        with _install_lock:
            if done["v"]:
                return
            done["v"] = True
            _install_count -= 1
            if _install_count == 0 and _install_original is not None:
                executors.run_task = _install_original
                _install_original = None

    return undo


def run_grill_direct(question: str, run_dir, *, budget: float = 10.0, k: int = 2,
                     max_rounds: int = 2, concurrency: int = 4, model: str = DEFAULT_MODEL,
                     steer: str | None = None, retrieval: bool = True):
    """An in-process GRILL run on the direct executor. Same ledger, no codex."""
    from . import grill as G  # noqa: PLC0415

    run_dir = Path(run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    warning = G._warn_if_inside_repo(run_dir)
    if warning:
        print(f"WARNING: {warning}")
    G.add_grill_to_path()
    from src.orchestrator import Config, Orchestrator  # noqa: PLC0415

    undo = install(model, retrieval=retrieval)
    try:
        inbox = G.steer_inbox_path(run_dir)
        if steer:
            G.send_steer(steer, run_dir)
        cfg = Config(budget=budget, K=k, max_rounds=max_rounds, concurrency=concurrency,
                     model=model, env_file=os.environ.get("GSS_ENV_FILE", ""),
                     steer_inbox=str(inbox), workspace=False, auto_artifacts=False,
                     ground_task_usd=0.25, screen_task_usd=0.25, deep_task_usd=0.60)
        (run_dir / "question.txt").write_text(question)
        orch = Orchestrator(question, run_dir, cfg)
        orch.run()
    finally:
        undo()
    return G.GrillRun(run_dir)
