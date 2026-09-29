"""Natural-language steering → structured steer event (DESIGN_interactive.md).

The user types free text ("focus on X; only clinical studies since 2020; assume Y"); this classifies it
into the SteerEvent fields (directions / scope / assumptions / verdicts / budget / control) with a single
gpt-5.4-mini chat call against the Stanford proxy. It runs in the AGENT (which has working proxy creds) —
the portal only forwards the raw text — so no credential ever leaves the agent's environment.
"""
from __future__ import annotations

import json
import re

from . import config
from .codex_exec import load_env

_SYS = (
    "You translate a researcher's free-text steering message for a live literature-research agent into a "
    "structured steer event (JSON only, no prose). The agent maintains DIRECTIONS (open questions it "
    "investigates) and HYPOTHESES (propositions it tests against the literature; tested ones are either "
    "POOLED or deprioritised into a BIN that is kept, not deleted). Map the message into any of these "
    "keys (include ONLY the ones that apply):\n"
    "- directions_add: NEW topics/questions to investigate — [{question_text, rationale, promise 0-1}].\n"
    "- constraints: SCOPE filters on what to search (e.g. 'only clinical trials', 'since 2020', 'human "
    "studies only', 'exclude preclinical') — short strings.\n"
    "- assumptions: premises to TAKE AS GIVEN without verifying (e.g. 'assume average-risk population') — "
    "short strings.\n"
    "- directions_drop: ids of existing OPEN directions to stop (match by meaning to the list provided).\n"
    "- directions_boost: {id: new_promise} to reprioritize existing directions.\n"
    "- hypotheses_verdict: [{hypothesis_id, verdict('supported'|'conflicted'|'refuted'), note}] only if the "
    "user explicitly rules on a specific listed hypothesis.\n"
    "- hypotheses_unbin: [id] to pull a deprioritised hypothesis back out of the bin for another test.\n"
    "- artifacts_request: [{spec, kind}] — the user wants a DELIVERABLE FILE built from what the run "
    "has already found: a CSV/spreadsheet of results, a table, a chart/plot/figure, a comparison "
    "graphic, or a written summary document ('give me a csv of all the benchmarks', 'plot the AUCs', "
    "'chart these side by side', 'export the sources'). `spec` = the request in the user's own words; "
    "`kind` = one of 'chart'|'table'|'data'|'doc'|'other'. This is for BUILDING something out of "
    "existing findings — a request to go FIND OUT more is directions_add, not an artifact.\n"
    "- budget_delta: number (USD) if they ask to add/reduce budget.\n"
    "- control: 'stop_after_round' or 'finalize_now' — ONLY when the user EXPLICITLY asks to stop or wrap "
    "up (e.g. 'stop', 'that's enough', 'finalize now', 'wrap it up'). A request to look for / investigate "
    "/ check / add something is NOT a stop — never set control for it.\n"
    "Guidance: a new subject to explore => directions_add; narrowing what to look at => constraints; a "
    "stated fact to assume => assumptions; a file/figure they want handed to them => artifacts_request. "
    "Most messages ask the agent to DO more work — that's "
    "directions_add (+ maybe constraints), NOT control. One message may produce several keys. When a "
    "message mixes a topic AND a filter AND a premise, SPLIT it across the right keys (don't dump the "
    "whole sentence into directions_add). Output ONLY the JSON object."
)


_INTENT_SYS = (
    "A researcher is watching a live literature-research agent and has typed a message. Decide what "
    "they WANT, and return JSON only.\n\n"
    "- \"steer\": they want the agent to DO something differently — investigate a topic, narrow the "
    "scope, take a premise as given, drop or reprioritise a direction, rule on a hypothesis, build a "
    "deliverable, change the budget, or stop. Anything that changes what the run does next.\n"
    "- \"qa\": they are ASKING SOMETHING and want an answer back — about what the run has found so "
    "far, what the report says, why something was deprioritised, what a source actually showed, what "
    "the current state is. They want information, not a change of course.\n\n"
    "The distinction is who acts. \"Look into whether X causes Y\" is steer — the agent goes and "
    "works. \"Did you find that X causes Y?\" is qa — the agent answers from what it already has. "
    "Imperatives about future work are steer; questions about existing work are qa.\n"
    "A message can look like a question but be a steer (\"can you also check the 2024 trials?\" wants "
    "work done). Judge the intent, not the punctuation. When genuinely torn, prefer \"steer\" — a "
    "wrongly-answered question costs a cheap reply, but a wrongly-ignored instruction stalls the run.\n\n"
    "Return {\"intent\": \"steer\"|\"qa\", \"rationale\": \"<one short line>\"}."
)


def classify_intent(text: str, env_file: str, model: str = config.CLASSIFY_MODEL) -> dict:
    """Is this message an instruction (steer) or a question (qa)? One cheap chat call.

    Fails OPEN to steer: on any error the caller behaves exactly as it did before this existed, so a
    classifier outage can never swallow a real instruction."""
    env: dict = {}
    load_env(env_file, env)
    base, key = config.openai_base(env.get("OPENAI_BASE_URL")), env.get("OPENAI_API_KEY")
    if not base or not key:
        return {"intent": "steer", "rationale": "classifier unavailable — defaulting to steer"}
    try:
        from openai import OpenAI
        client = OpenAI(base_url=base, api_key=key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": _INTENT_SYS},
                      {"role": "user", "content": f"MESSAGE:\n{text}\n\nReturn the JSON."}],
        )
        raw = (resp.choices[0].message.content or "").strip()
        raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
        obj = json.loads(raw)
        intent = str((obj or {}).get("intent", "")).strip().lower()
        if intent not in ("steer", "qa"):
            return {"intent": "steer", "rationale": "unrecognised intent — defaulting to steer"}
        return {"intent": intent, "rationale": str(obj.get("rationale", ""))[:200]}
    except Exception:
        return {"intent": "steer", "rationale": "classifier error — defaulting to steer"}


def _ctx(dirs: list, hyps: list) -> str:
    d = "\n".join(f"  {i}: {t[:110]}" for i, t in dirs) or "  (none)"
    h = "\n".join(f"  {i}: {t[:110]}" for i, t in hyps) or "  (none)"
    return f"OPEN DIRECTIONS (id: text):\n{d}\n\nRECENT HYPOTHESES (id: text):\n{h}"


def nl_to_steer(text: str, dirs: list, hyps: list, env_file: str,
                model: str = config.CLASSIFY_MODEL) -> dict:
    """Classify `text` into a steer-event dict. Returns {} on any failure (caller falls back)."""
    env: dict = {}
    load_env(env_file, env)
    base, key = config.openai_base(env.get("OPENAI_BASE_URL")), env.get("OPENAI_API_KEY")
    if not base or not key:
        return {}
    try:
        from openai import OpenAI
        client = OpenAI(base_url=base, api_key=key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": _SYS},
                      {"role": "user", "content": f"{_ctx(dirs, hyps)}\n\nMESSAGE:\n{text}\n\n"
                                                   "Return the JSON steer event."}],
        )
        raw = (resp.choices[0].message.content or "").strip()
        raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}
