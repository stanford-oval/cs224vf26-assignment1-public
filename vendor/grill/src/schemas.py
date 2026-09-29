"""Strict JSON schemas for the codex executor tasks (Methodology v2 §3).

These are passed to ``codex exec --output-schema`` so the model's FINAL message is
forced to validated JSON. The docuset Azure provider enforces *strict* structured
output, which means:

  * every object must set ``additionalProperties: false``;
  * every declared property must appear in ``required`` (optionals are made
    nullable via a union type instead of being omitted);
  * no ``format`` / ``minimum`` / ``pattern`` keywords.

Dynamic maps (the ledger's ``numbers: dict[metric, value]``) cannot be expressed as
open objects under those rules, so they are modelled as arrays of ``{metric, value}``
pairs and re-folded into dicts on ingest.
"""
from __future__ import annotations

# ── leaf objects ────────────────────────────────────────────────────────────

SOURCE_REF = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "year": {"type": ["integer", "null"]},
        "journal": {"type": ["string", "null"]},
        "doi": {"type": ["string", "null"]},
        "pmid": {"type": ["string", "null"]},
        "pmc": {"type": ["string", "null"]},
        "url": {"type": ["string", "null"]},
        "quote": {"type": ["string", "null"]},
    },
    "required": ["title", "authors", "year", "journal", "doi", "pmid", "pmc", "url", "quote"],
}

NUMBER_PAIR = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "metric": {"type": "string"},
        "value": {"type": ["number", "string"]},
    },
    "required": ["metric", "value"],
}

EVIDENCE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "text": {"type": "string"},        # what the source actually says
        # stance RELATIVE TO THE HYPOTHESIS being tested — contradicting evidence is as
        # valuable as supporting evidence and must be reported, never suppressed.
        "stance": {"type": "string", "enum": ["supports", "contradicts", "neutral"]},
        "source": SOURCE_REF,              # exactly ONE source per evidence item
        "numbers": {"type": "array", "items": NUMBER_PAIR},
    },
    "required": ["text", "stance", "source", "numbers"],
}

HYPOTHESIS = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "text": {"type": "string"},        # a falsifiable proposition, not a fact
        "rationale": {"type": "string"},   # why it is worth testing
        "aspects": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},  # your prior P(true) before it is tested, 0..1
        "evidence": {"type": "array", "items": EVIDENCE},   # anything already found (may be empty)
    },
    "required": ["text", "rationale", "aspects", "confidence", "evidence"],
}

NEW_DIRECTION = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "question_text": {"type": "string"},
        "rationale": {"type": "string"},
        "promise": {"type": "number"},        # self-reported EIG-ish priority, 0..1
        "est_cost": {"type": "number"},        # self-reported USD to explore
    },
    "required": ["question_text", "rationale", "promise", "est_cost"],
}

# ── executor output schemas ─────────────────────────────────────────────────

PRIOR = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "knowledge": {"type": "string"},
        "prior_hypothesis": {"type": "string"},
        # Each candidate answer carries a self-assessed confidence + aspect. These become HYPOTHESES
        # and go through the full two-stage test during INIT — they came out of parametric memory,
        # so they are the run's highest hallucination risk and nothing may be built on them untested.
        "candidate_answers": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "number"},
                "aspect": {"type": "string"},
            },
            "required": ["answer", "confidence", "aspect"],
        }},
        "key_terms": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        # Premises the model is taking as given to produce this prior — surfaced to the user so the
        # answer's foundations are explicit (an assumption that proves wrong can change everything).
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["knowledge", "prior_hypothesis", "candidate_answers", "key_terms",
                 "open_questions", "assumptions"],
}

REQUIRED_FIELDS = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "required_fields": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["required_fields"],
}

GROUND = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "term": {"type": "string"},
        "definition": {"type": "string"},
        "source": SOURCE_REF,
    },
    "required": ["term", "definition", "source"],
}

# ABLATION baselines: no hypotheses, no verdicts — just an answer with its sources.
ANSWER_SEARCH = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answer_markdown": {"type": "string"},
        "sources": {"type": "array", "items": SOURCE_REF},
        "open_gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer_markdown", "sources", "open_gaps"],
}

EXPLORE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "hypotheses": {"type": "array", "items": HYPOTHESIS},
        "new_directions": {"type": "array", "items": NEW_DIRECTION},
        "dead_end": {"type": "boolean"},
    },
    "required": ["hypotheses", "new_directions", "dead_end"],
}

# The planner both RANKS the frontier and ALLOCATES the round's budget across it — the agent,
# not the harness, decides which topics deserve the money. The harness only clamps each
# allocation to a ceiling (a share of what's left) and enforces it with the task watchdog.
PLAN = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "allocations": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "id": {"type": "string"},
                "score": {"type": "number"},       # 0..1 value of pursuing this direction next
                "usd": {"type": "number"},         # USD to spend exploring it this round
                "rationale": {"type": "string"},   # why this much
            },
            "required": ["id", "score", "usd", "rationale"],
        }},
    },
    "required": ["allocations"],
}

# Stage 1 of the two-stage test: a quick web search asking only whether the hypothesis makes
# sense and has any footing in the literature. Cheap; kills nonsense before the deep test pays for it.
SCREEN = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "plausible": {"type": "boolean"},   # worth an in-depth test?
        "note": {"type": "string"},         # one line: what the quick search showed
        "confidence": {"type": "number"},   # P(true) after the quick look, 0..1
        "evidence": {"type": "array", "items": EVIDENCE},   # 0-2 sources found in passing
    },
    "required": ["plausible", "note", "confidence", "evidence"],
}

# Stage 2: an extensive hunt for BOTH corroborating evidence and counter-examples. The verdict
# is three-state because "contested" is a real finding, not a failure to decide.
DEEP_TEST = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "verdict": {"type": "string", "enum": ["supported", "conflicted", "refuted"]},
        "rationale": {"type": "string"},
        "evidence": {"type": "array", "items": EVIDENCE},
        "conflicts": {"type": "array", "items": {"type": "string"}},   # the contradictions found
        "confidence": {"type": "number"},
        "new_directions": {"type": "array", "items": NEW_DIRECTION},
    },
    "required": ["verdict", "rationale", "evidence", "conflicts", "confidence", "new_directions"],
}

_AXIS = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "score": {"type": "number"},     # 0..1 intrinsic, for steering only
        "note": {"type": "string"},
    },
    "required": ["score", "note"],
}

_PATTERN_ROW = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "pattern": {"type": "string"},        # the recurring pattern observed
        "abstraction": {"type": "string"},     # the domain-agnostic generalization
        "instance": {"type": "string"},        # a concrete instance from the findings
        "direction": {"type": "string"},       # a next direction the pattern suggests
        "support": {"type": "string"},         # how strongly the evidence supports it
        "sources": {"type": "array", "items": {"type": "string"}},
        "hypothesis": {"type": "string"},      # a testable hypothesis it raises
        "novelty": {"type": "string"},         # how novel / non-obvious it is
    },
    "required": ["pattern", "abstraction", "instance", "direction", "support",
                 "sources", "hypothesis", "novelty"],
}

PATTERNS = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"patterns": {"type": "array", "items": _PATTERN_ROW}},
    "required": ["patterns"],
}

_OUTLINE_SECTION = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "heading": {"type": "string"},
        "intent": {"type": "string"},         # what this section must deliver
    },
    "required": ["heading", "intent"],
}

FINALIZE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "outline": {"type": "array", "items": _OUTLINE_SECTION},   # step 1: the plan
        "report_markdown": {"type": "string"},                      # step 2: the filled report
    },
    "required": ["outline", "report_markdown"],
}

# The ARTIFACT task builds real files in the run's git workspace. This schema is only the task's
# REPORT of what it built — the harness detects the actual artifacts from the filesystem, so a
# mismatched or missing declaration costs nothing but nicer titles.
ARTIFACT = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "artifacts": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "path": {"type": "string"},        # workspace-relative, e.g. artifacts/auc_by_marker.png
                "title": {"type": "string"},
                "kind": {"type": "string",
                         "enum": ["chart", "table", "data", "doc", "code", "other"]},
                "description": {"type": "string"},  # what it shows and how it was derived
            },
            "required": ["path", "title", "kind", "description"],
        }},
        "summary": {"type": "string"},              # one paragraph: what was built and from what
        "committed": {"type": "boolean"},           # did the task commit its own work?
        "caveats": {"type": "array", "items": {"type": "string"}},   # gaps/limits in the data used
    },
    "required": ["artifacts", "summary", "committed", "caveats"],
}

# Q&A over the run: the researcher asked a QUESTION rather than giving an instruction. Answered
# from what the run already holds — no new research — and always closed with a concrete steer the
# answer suggests, so an insight can become work in one click instead of a retyped instruction.
ANSWER_QUESTION = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answer": {"type": "string"},           # the answer, in the researcher's terms
        "basis": {"type": "string"},            # what in the run this rests on (ids, sources, sections)
        "confident": {"type": "boolean"},       # false when the run does not really settle it
        # The offer. null when the answer genuinely implies no next step — better to say nothing
        # than to manufacture busywork.
        "suggested_steer": {"type": ["string", "null"]},   # a ready-to-send steer instruction
        "suggest_reason": {"type": ["string", "null"]},    # why that would help, one line
    },
    "required": ["answer", "basis", "confident", "suggested_steer", "suggest_reason"],
}


# ── the data plane (DESIGN_data_plane.md) ───────────────────────────────────

# Which KINDS of claim does this request need? Routing follows from the claim kinds rather than a
# "research vs task" guess, which has no correct answer for a composite request (§3.2).
CLASSIFY_REQUEST = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "kind": {"type": "string", "enum": ["data_only", "research_only", "both"]},
        "data_ask": {"type": "string"},       # what must be computed from the data ("" if none)
        "research_ask": {"type": "string"},   # what must be established from literature ("" if none)
        "rationale": {"type": "string"},
        "ambiguities": {"type": "array", "items": {"type": "string"}},   # what the ask leaves open
    },
    "required": ["kind", "data_ask", "research_ask", "rationale", "ambiguities"],
}

# A DATA QUERY runs a script over the user's files in the workspace. Like ARTIFACT its real output
# is FILES; this is its report. `assumptions` is load-bearing, not decoration: it is the record of
# the interpretive choices the script fixed, and it is what a reviewer/human actually checks (§4.3).
DATA_QUERY = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "claims": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "text": {"type": "string"},        # a specific finding, e.g. "4 genes overlap: ..."
                "aspects": {"type": "array", "items": {"type": "string"}},
                "numbers": {"type": "array", "items": NUMBER_PAIR},
            },
            "required": ["text", "aspects", "numbers"],
        }},
        "dataset_id": {"type": "string"},          # which input it computed over (from the manifest)
        "query": {"type": "string"},               # one line: the operation performed
        "script": {"type": "string"},              # workspace-relative path to the code that ran
        "result_path": {"type": ["string", "null"]},   # artifacts/… holding the full result
        "rows_in": {"type": ["integer", "null"]},
        "rows_out": {"type": ["integer", "null"]},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "caveats": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["claims", "dataset_id", "query", "script", "result_path",
                 "rows_in", "rows_out", "assumptions", "caveats"],
}

# Verification for a data claim: READ the script, don't re-run it (§4.3). Re-running deterministic
# code over an unchanged file proves repeatability, which was never in doubt — it returns the same
# answer by construction, including the same wrong one.
JUDGE_QUERY = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "correct": {"type": "boolean"},         # does the script compute what the claim says?
        "verdict": {"type": "string",
                    "enum": ["correct", "wrong_script", "questionable_assumptions"]},
        "issues": {"type": "array", "items": {"type": "string"}},
        "unstated_assumptions": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "note": {"type": "string"},
    },
    "required": ["correct", "verdict", "issues", "unstated_assumptions", "confidence", "note"],
}

JUDGE_COVERAGE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "field": {"type": "string"},
                    "covered": {"type": "boolean"},        # >=1 grounded claim answers it
                    "contributing_aspects": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["field", "covered", "contributing_aspects"],
            },
        },
    },
    "required": ["fields"],
}

JUDGE_FORWARD = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "directions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "score": {"type": "number"},          # 0..1 testable AND non-obvious
                },
                "required": ["id", "score"],
            },
        },
    },
    "required": ["directions"],
}

EVALUATE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "per_axis_intrinsics": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "correctness": _AXIS,
                "completeness": _AXIS,
                "forward_looking": _AXIS,
                "faithfulness": _AXIS,
            },
            "required": ["correctness", "completeness", "forward_looking", "faithfulness"],
        },
        "weakest_axis": {
            "type": "string",
            "enum": ["correctness", "completeness", "forward_looking", "faithfulness"],
        },
        "corrective_directions": {"type": "array", "items": NEW_DIRECTION},
        "regressions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["per_axis_intrinsics", "weakest_axis", "corrective_directions", "regressions"],
}
