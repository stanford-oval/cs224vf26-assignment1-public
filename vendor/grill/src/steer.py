"""Human-in-the-loop steering (see DESIGN_interactive.md).

A human steers a live run by emitting SteerEvents — new directions, scope filters, assumptions,
reprioritizations, budget nudges, and (rarely) claim verdicts. Every event is applied to the ledger
through the SAME typed API the orchestrator uses; there is no parallel representation. This module is
pure Python — no codex, no spend, no network — so it is fully exercised by the offline self-test.

The orchestrator polls a `SteerSource` at the loop seams (top-of-round + post-checkpoint), applies each
event, and logs it. `SteerEvent.apply_to(ledger)` performs every ledger-scoped mutation and returns an
`Applied` summary carrying the residual side effects the orchestrator owns (budget, verdict routing,
run control).

The event keys are `hypotheses_*`; the older `claims_*` spellings are still accepted as aliases so an
already-deployed steering UI keeps working.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Protocol

from .ledger import BINNED, CLOSED, Ledger

VERDICTS = {"supported", "conflicted", "refuted"}
# Legacy verdict words from the claim-era API, mapped onto the hypothesis verdicts.
_VERDICT_ALIASES = {"confirmed": "supported", "error": "conflicted"}
CONTROLS = {"continue", "stop_after_round", "finalize_now"}


def _clamp01(x, default: float = 0.5) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return default


ARTIFACT_KINDS = {"chart", "table", "data", "doc", "code", "other"}


@dataclass
class Applied:
    """What an event did, plus the residuals the orchestrator must handle (it owns the budget —
    the ledger does not)."""
    changes: list[str] = field(default_factory=list)   # human-readable, for the log/digest
    budget_delta: float = 0.0
    control: str = "continue"
    verdicts: list[dict] = field(default_factory=list)  # normalized {hypothesis_id, verdict, note, confidence?}
    # Deliverables to BUILD in the run's git workspace ({spec, kind}) — files, not beliefs, so they
    # never touch the ledger; the orchestrator queues them for the ARTIFACT executor.
    artifacts: list[dict] = field(default_factory=list)


@dataclass
class SteerEvent:
    """One human steer. Every field optional; an empty event is a no-op."""
    directions_add: list[dict] = field(default_factory=list)   # [{question_text, rationale, promise}]
    directions_drop: list[str] = field(default_factory=list)   # direction ids -> CLOSED
    directions_boost: dict = field(default_factory=dict)       # id -> new promise
    fields_add: list[str] = field(default_factory=list)        # extend required_fields
    fields_remove: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)       # SCOPE filters
    assumptions: list[str] = field(default_factory=list)       # GIVENS (not tested)
    hypotheses_verdict: list[dict] = field(default_factory=list)  # [{hypothesis_id, verdict, note, confidence?}]
    hypotheses_pin: list[str] = field(default_factory=list)    # accept as-is, never re-test
    hypotheses_unbin: list[str] = field(default_factory=list)  # pull back out of the bin for another test
    artifacts_request: list[dict] = field(default_factory=list)  # [{spec, kind}] — deliverables to BUILD
    data_add: list[str] = field(default_factory=list)           # NEW data files to stage into workspace/inputs/
    budget_delta: float = 0.0                                  # add/remove total USD
    control: str = "continue"                                  # continue | stop_after_round | finalize_now
    note: str = ""                                             # free text, logged
    nl: str = ""                                               # raw natural-language steer (classified by the agent)

    # ── parsing (defensive: unknown/garbage fields are dropped, not fatal) ────
    @classmethod
    def from_dict(cls, d: dict) -> "SteerEvent":
        d = d or {}
        control = str(d.get("control", "continue")).strip().lower()
        if control not in CONTROLS:
            control = "continue"
        verdicts = []
        for v in (d.get("hypotheses_verdict") or d.get("claims_verdict") or []):
            hid = str(v.get("hypothesis_id", "") or v.get("claim_id", "")).strip()
            verdict = str(v.get("verdict", "")).strip().lower()
            verdict = _VERDICT_ALIASES.get(verdict, verdict)
            if hid and verdict in VERDICTS:
                item = {"hypothesis_id": hid, "verdict": verdict, "note": str(v.get("note", "")).strip()}
                if v.get("confidence") is not None:
                    item["confidence"] = _clamp01(v.get("confidence"))
                verdicts.append(item)
        boost = {}
        for k, val in (d.get("directions_boost") or {}).items():
            boost[str(k)] = _clamp01(val)
        # A deliverable request may arrive as a bare string ("a csv of all the benchmarks") or as
        # {spec, kind}; both normalise to {spec, kind}.
        arts = []
        for a in (d.get("artifacts_request") or []):
            spec = (str(a.get("spec", "") or a.get("request", "")) if isinstance(a, dict)
                    else str(a)).strip()
            if not spec:
                continue
            k = (str(a.get("kind", "")).strip().lower() if isinstance(a, dict) else "")
            arts.append({"spec": spec, "kind": k if k in ARTIFACT_KINDS else ""})
        adds = []
        for a in (d.get("directions_add") or []):
            qt = str(a.get("question_text", "")).strip()
            if qt:
                adds.append({"question_text": qt, "rationale": str(a.get("rationale", "")).strip(),
                             "promise": _clamp01(a.get("promise", 0.8), 0.8)})
        return cls(
            directions_add=adds,
            directions_drop=[str(x).strip() for x in (d.get("directions_drop") or []) if str(x).strip()],
            directions_boost=boost,
            fields_add=[str(x).strip() for x in (d.get("fields_add") or []) if str(x).strip()],
            fields_remove=[str(x).strip() for x in (d.get("fields_remove") or []) if str(x).strip()],
            constraints=[str(x).strip() for x in (d.get("constraints") or []) if str(x).strip()],
            assumptions=[str(x).strip() for x in (d.get("assumptions") or []) if str(x).strip()],
            hypotheses_verdict=verdicts,
            hypotheses_pin=[str(x).strip() for x in
                            (d.get("hypotheses_pin") or d.get("claims_pin") or []) if str(x).strip()],
            hypotheses_unbin=[str(x).strip() for x in (d.get("hypotheses_unbin") or []) if str(x).strip()],
            artifacts_request=arts,
            data_add=[str(x).strip() for x in (d.get('data_add') or []) if str(x).strip()],
            budget_delta=float(d.get("budget_delta", 0.0) or 0.0),
            control=control,
            note=str(d.get("note", "")).strip(),
            nl=str(d.get("nl", "")).strip(),
        )

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()
                if v not in ([], {}, "", 0.0) and not (k == "control" and v == "continue")}

    def is_empty(self) -> bool:
        return not any([self.directions_add, self.directions_drop, self.directions_boost,
                        self.fields_add, self.fields_remove, self.constraints, self.assumptions,
                        self.hypotheses_verdict, self.hypotheses_pin, self.hypotheses_unbin,
                        self.artifacts_request, self.data_add, self.budget_delta,
                        self.control != "continue", self.nl])

    # ── application (ledger-scoped; residuals returned for the orchestrator) ──
    def apply_to(self, ledger: Ledger) -> Applied:
        out = Applied(budget_delta=float(self.budget_delta or 0.0), control=self.control)

        for a in self.directions_add:
            d = ledger.add_direction(a["question_text"], rationale=a.get("rationale") or "human: steer",
                                     promise=a.get("promise", 0.8), origin="human")
            out.changes.append(f"+direction {d.id} (human): {a['question_text'][:80]}")
        for did in self.directions_drop:
            d = ledger.directions.get(did)
            if d is not None:
                d.status = CLOSED
                out.changes.append(f"dropped direction {did}")
            else:
                out.changes.append(f"skip drop: no direction {did}")
        for did, p in self.directions_boost.items():
            d = ledger.directions.get(did)
            if d is not None:
                d.promise = p
                out.changes.append(f"boost {did} promise -> {p:.2f}")
            else:
                out.changes.append(f"skip boost: no direction {did}")

        for f in self.fields_add:
            if f not in ledger.required_fields:
                ledger.required_fields.append(f)
                out.changes.append(f"+required_field: {f}")
        if self.fields_remove:
            keep = [f for f in ledger.required_fields if f not in set(self.fields_remove)]
            removed = len(ledger.required_fields) - len(keep)
            ledger.required_fields = keep
            if removed:
                out.changes.append(f"-{removed} required_field(s)")

        for c in ledger.add_constraints(self.constraints):
            out.changes.append(f"+scope: {c}")
        for a in ledger.add_assumptions(self.assumptions):
            out.changes.append(f"+assumption: {a}")

        for hid in self.hypotheses_pin:
            h = ledger.hypotheses.get(hid)
            if h is not None:
                h.pinned = True
                h.origin = "human"
                out.changes.append(f"pinned hypothesis {hid}")
            else:
                out.changes.append(f"skip pin: no hypothesis {hid}")

        # Nothing is discarded, so a human can always pull a deprioritised hypothesis back out.
        for hid in self.hypotheses_unbin:
            h = ledger.hypotheses.get(hid)
            if h is None:
                out.changes.append(f"skip unbin: no hypothesis {hid}")
            elif h.status != BINNED:
                out.changes.append(f"skip unbin: {hid} is not binned ({h.status})")
            else:
                ledger.unbin(h, reason="human asked for another look")
                out.changes.append(f"unbinned {hid} → re-queued for the deep test")

        # Verdicts are routed by the orchestrator (it owns pinning + logging); pass them through.
        for v in self.hypotheses_verdict:
            if v["hypothesis_id"] in ledger.hypotheses:
                out.verdicts.append(v)
            else:
                out.changes.append(f"skip verdict: no hypothesis {v['hypothesis_id']}")

        # Deliverables are files, not beliefs — they never enter the ledger. The orchestrator queues
        # them for the ARTIFACT executor, which builds them in the run's git workspace.
        for a in self.artifacts_request:
            out.artifacts.append(dict(a))
            out.changes.append(f"+artifact requested: {a['spec'][:80]}")

        if self.note:
            out.changes.append(f"note: {self.note}")
        return out


# ── steer sources (pluggable; default = NullSteer = today's behavior) ─────────

class SteerSource(Protocol):
    def poll(self) -> list[SteerEvent]: ...


class NullSteer:
    """No steering — the run behaves exactly as before."""
    def poll(self) -> list[SteerEvent]:
        return []


class FileInbox:
    """An async inbox: a JSON file a human or the steering UI appends to at any time. On each poll we
    ATOMICALLY CLAIM the current contents (rename the inbox aside) and immediately leave a fresh empty
    inbox for concurrent writers, then process the claimed events. The file may hold a single event
    object or a JSON array of them. Malformed content is skipped, not fatal.

    The claim is a directory-level rename, NOT an in-place overwrite of the inbox file — so draining
    works even when the inbox file is owned by a *different user* than the run. That is the real
    deployment case: the portal container writes the inbox as root, while the host run drains as an
    unprivileged user; an in-place `write("[]")` would silently fail (permission denied) and the same
    events would re-drain every round. Renaming only needs write access to the *directory*, which the
    run owns."""

    def __init__(self, path):
        self.path = Path(path)

    def poll(self) -> list[SteerEvent]:
        if not self.path.exists():
            return []
        parent = self.path.parent
        claim = self.path.with_name(self.path.name + ".draining")
        try:
            os.replace(self.path, claim)        # atomically claim the current contents (dir-level rename)
        except OSError:
            return []                           # nothing to claim / cannot claim → treat as empty
        # Immediately restore an empty inbox so concurrent appends land in a fresh file (minimizes the
        # lost-append window to the gap between these two renames).
        try:
            fd, tmp = tempfile.mkstemp(dir=str(parent), prefix=".inbox", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("[]")
            os.replace(tmp, self.path)
        except OSError:
            pass
        try:
            raw = claim.read_text(encoding="utf-8").strip()
        except OSError:
            raw = ""
        try:
            claim.unlink()
        except OSError:
            pass
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        items = data if isinstance(data, list) else [data]
        events = [SteerEvent.from_dict(x) for x in items if isinstance(x, dict)]
        return [e for e in events if not e.is_empty()]


class CallbackSteer:
    """Programmatic source (portal / tests): a callable returning event dicts (or SteerEvents)."""

    def __init__(self, fn: Callable[[], list]):
        self.fn = fn

    def poll(self) -> list[SteerEvent]:
        out = []
        for x in (self.fn() or []):
            ev = x if isinstance(x, SteerEvent) else SteerEvent.from_dict(x)
            if not ev.is_empty():
                out.append(ev)
        return out


class ConsolePrompt:
    """Blocking stdin source for --interactive checkpoints. Reads one line of JSON (an event or a bare
    control word like 'stop'/'go'). Blank line = continue. EOF/non-tty = no events."""

    _CONTROL_WORDS = {"go": "continue", "continue": "continue", "": "continue",
                      "stop": "finalize_now", "finalize": "finalize_now",
                      "halt": "stop_after_round"}

    def __init__(self, prompt: str = "steer> "):
        self.prompt = prompt

    def poll(self) -> list[SteerEvent]:
        try:
            line = input(self.prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return []
        if line in self._CONTROL_WORDS:
            ctl = self._CONTROL_WORDS[line]
            return [] if ctl == "continue" else [SteerEvent(control=ctl)]
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            print("  (could not parse steer JSON — ignored)")
            return []
        items = data if isinstance(data, list) else [data]
        return [SteerEvent.from_dict(x) for x in items if isinstance(x, dict)]
