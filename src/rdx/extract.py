"""Driving and dissecting SLIDERS, the corpus -> table -> answer engine.

SLIDERS lives at ``sliders-plugin``. Its stages are free functions: each takes
its inputs positionally, ``config``/``trace`` keyword-only, mutates nothing and
returns a complete result. So the pipeline can be run one stage at a time in a
notebook, and every stage's output inspected before the next one consumes it.

What this module adds on top:

* a hand-written phenotype schema, so a run can start without paying for
  schema generation, and so a generated schema has something to be compared to
* a fake LLM client, for exercising extraction and provenance at zero cost
* the bridge from an extracted table back to a ``DiseaseProfile``, which is
  what the diagnosis half of the assignment consumes

The bridge is where the interesting failures live. A row says
"microcephaly, 20/39"; a profile needs ``HP:0000252 -> 0.51``. Grounding the
string, pooling counts across papers that overlap in patients, and deciding
what an unquantified mention means are all judgement calls, and each one is a
place the reconstructed profile can drift from the curated truth.
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

def _vendored(name: str, fallback: str) -> Path:
    """The in-repo copy if it is there, else the original checkout."""
    here = Path(__file__).resolve().parents[2] / "vendor" / name
    return here if here.exists() else Path(fallback)


SLIDERS_ROOT = Path(
    os.environ.get("SLIDERS_ROOT", _vendored("sliders", "/mnt/data/oval/sliders-plugin"))
)


def add_sliders_to_path(root: Path | str = SLIDERS_ROOT) -> Path:
    root = Path(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def sliders_available(root: Path | str = SLIDERS_ROOT) -> dict[str, Any]:
    root = Path(root)
    try:
        import sliders  # noqa: PLC0415

        version = sliders.__version__
        importable = True
    except Exception:  # noqa: BLE001
        version, importable = None, False
    return {
        "root_exists": root.exists(),
        "importable": importable,
        "version": version,
        "anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "openai_key": bool(os.environ.get("OPENAI_API_KEY")),
        "openai_base_url": os.environ.get("OPENAI_BASE_URL"),
        "model": DEFAULT_MODEL,
        "can_run_offline": importable,
        "can_run_live": importable
        and bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")),
    }


#: The Stanford LiteLLM proxy. OpenAI-compatible; routes by model name.
DEFAULT_BASE_URL = "https://azureopenai.genie.stanford.edu/v1"

#: Where the pasted keys are written for GRILL, which reads a file rather than
#: the environment. Under ``runs/``, which is gitignored.
CREDENTIALS_FILE = Path(__file__).resolve().parents[2] / "runs" / ".credentials.env"


def setup_credentials(
    openai_api_key: str,
    *,
    openai_base_url: str = DEFAULT_BASE_URL,
    serper_api_key: str = "",
    paperclip_api_key: str = "",
    anthropic_api_key: str = "",
    verbose: bool = True,
) -> dict:
    """Hand the keys pasted into the notebook to both systems.

    SLIDERS reads credentials from ``os.environ``; GRILL reads a file whose
    path is ``config.ENV_FILE``, overridable with ``GSS_ENV_FILE``. Two systems,
    two mechanisms, one set of keys -- so this sets the environment, writes the
    same values to a private file under ``runs/`` (gitignored, mode 0600), and
    points GRILL at that file. Nothing is read from a ``.env``.

    It overrides an already-exported ``OPENAI_API_KEY`` on purpose. A stale key
    in a login profile otherwise silently outranks the one you just pasted, and
    the failure surfaces much later as a budget or auth error attributed to the
    wrong key. The last four characters are printed so you can catch it.
    """
    openai_api_key = (openai_api_key or "").strip().split()[0] if (openai_api_key or "").strip() else ""
    if not openai_api_key or openai_api_key.startswith("PASTE"):
        raise ValueError(
            "OPENAI_API_KEY is empty. Paste your key into the credentials cell "
            "above and run it again."
        )
    if openai_api_key.startswith(("http://", "https://")):
        raise ValueError(
            f"OPENAI_API_KEY looks like a URL ({openai_api_key[:40]}...). The key "
            f"and the base URL are swapped: the key is the long secret string, "
            f"OPENAI_BASE_URL is the https:// address."
        )
    base_url = (openai_base_url or "").strip()
    if not base_url or base_url.upper().startswith("PASTE"):
        base_url = DEFAULT_BASE_URL          # the placeholder was left in; use the proxy
    if not base_url.startswith(("http://", "https://")):
        raise ValueError(
            f"OPENAI_BASE_URL is not a URL ({base_url[:40]!r}). It should be "
            f"{DEFAULT_BASE_URL} for the Stanford proxy."
        )
    base_url = base_url.split("/chat/completions")[0].rstrip("/")

    values = {
        "OPENAI_BASE_URL": base_url,
        "OPENAI_API_KEY": openai_api_key,
        "SERPER_API_KEY": (serper_api_key or "").strip(),
        "PAPERCLIP_API_KEY": (paperclip_api_key or "").strip(),
        "ANTHROPIC_API_KEY": (anthropic_api_key or "").strip(),
    }
    keys = []
    for key, value in values.items():
        if value:
            os.environ[key] = value
            keys.append(key)
        else:
            os.environ.pop(key, None)

    # GRILL re-reads a file itself rather than trusting the environment.
    env_file = CREDENTIALS_FILE
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text("".join(f"{k}={v}\n" for k, v in values.items() if v))
    env_file.chmod(0o600)
    os.environ["GSS_ENV_FILE"] = str(env_file)

    info = {
        "env_file": str(env_file),
        "keys_set": keys,
        "base_url": base_url,
        "api_key_tail": openai_api_key[-4:],
        "model": DEFAULT_MODEL,
    }
    if verbose:
        print(f"credentials : {env_file}  (written for GRILL; gitignored)")
        print(f"base_url    : {info['base_url']}")
        print(f"api key     : ...{info['api_key_tail']}   <- check this is yours")
        print(f"model       : {info['model']}  (SLIDERS and GRILL)")
    return info


# --------------------------------------------------------------------------
# Model routing
# --------------------------------------------------------------------------

#: Every model role SLIDERS defines. `gate` is the cheap per-chunk relevance
#: call; `answer` is the one that actually limits accuracy.
SLIDERS_ROLES = (
    "schema_gen", "gate", "extract", "plan",
    "canonicalize", "reconcile", "answer", "cite",
)

DEFAULT_MODEL = "gemini-3.8-flash"


def gemini_config(
    model: str = DEFAULT_MODEL,
    *,
    base_url: str | None = None,
    cache_dir: str | Path = ".sliders_rdx",
    roles: Sequence[str] = SLIDERS_ROLES,
    **overrides: Any,
):
    """A ``SlidersConfig`` routing every role to ``model`` through the proxy.

    The proxy speaks the OpenAI Chat Completions API and routes by model name,
    so one ``base_url`` reaches the Gemini, Claude and GPT deployments alike.
    Only the transport changes; the model ids stay as they are.

    Three first-party Anthropic features have no equivalent on that wire and
    are dropped rather than errored, so they are set to ``None`` here instead
    of being left to degrade silently: the five-level ``effort`` ladder, the
    ``thinking`` budget, and explicit ``cache_control`` breakpoints. What you
    lose in practice is control over reasoning depth -- Gemini's flash models
    decide that themselves.
    """
    add_sliders_to_path()
    from sliders import SlidersConfig  # noqa: PLC0415
    from sliders.config import Models, ModelSpec  # noqa: PLC0415

    base_url = base_url or os.environ.get("OPENAI_BASE_URL")
    if not base_url:
        raise RuntimeError(
            "OPENAI_BASE_URL is not set. Run the credentials cell "
            "(X.setup_credentials(...)) first."
        )

    def spec(role: str):
        return ModelSpec(
            provider="openai",
            model=model,
            max_tokens=2_048 if role == "gate" else 32_000,
            effort=None,
            thinking=None,
        )

    models = Models(**{r: spec(r) for r in roles})
    return SlidersConfig(models=models, base_url=base_url,
                         cache_dir=Path(cache_dir), **overrides)


# --------------------------------------------------------------------------
# A schema for phenotype frequencies
# --------------------------------------------------------------------------

PHENOTYPE_QUESTION = (
    "For the rare disease under study, which clinical phenotypes have been "
    "reported in affected individuals, and in how many of the individuals "
    "assessed was each one present?"
)


def phenotype_schema():
    """One table, one row per (paper, phenotype) claim.

    Counts are kept as two integers rather than one percentage on purpose. A
    paper reporting 20/39 and a paper reporting 9/9 pool to 29/48, which is not
    the average of 51% and 100%. Storing the percentage throws away the
    denominator and the weighting with it.
    """
    add_sliders_to_path()
    from sliders.models import Field, Schema, TableSpec, TableScope  # noqa: PLC0415

    return Schema(
        reasoning=(
            "Diagnosis needs P(phenotype | disease). The literature states that as "
            "counts over an assessed subgroup, so capture the numerator and the "
            "denominator separately and keep the cohort they came from."
        ),
        tables=[
            TableSpec(
                name="PhenotypeFrequency",
                description=(
                    "One row per clinical phenotype reported for a specific disease "
                    "or gene in this paper's own cohort."
                ),
                primary_key=["disease_or_gene", "phenotype"],
                scope=TableScope(
                    definition=(
                        "Findings observed in the patients this paper reports. "
                        "Count a phenotype once per disease per paper."
                    ),
                    excludes=[
                        "phenotypes attributed to a different disease being compared",
                        "phenotypes mentioned only as absent in the whole cohort",
                        "findings quoted from another paper rather than observed here",
                    ],
                ),
                fields=[
                    Field(
                        name="disease_or_gene",
                        data_type="str",
                        description=(
                            "The disease name or causative gene these patients have, "
                            "exactly as the paper names it (e.g. 'ReNU syndrome', 'RNU4-2')."
                        ),
                        required=True,
                        canonicalize=True,
                    ),
                    Field(
                        name="phenotype",
                        data_type="str",
                        description=(
                            "The clinical finding, as a short noun phrase in the "
                            "paper's own words (e.g. 'microcephaly', 'absent speech')."
                        ),
                        required=True,
                        canonicalize=True,
                    ),
                    Field(
                        name="n_affected",
                        data_type="int",
                        description="How many assessed individuals showed it. Null if not stated.",
                    ),
                    Field(
                        name="n_assessed",
                        data_type="int",
                        description=(
                            "How many individuals were assessed for it -- the denominator. "
                            "Null if not stated."
                        ),
                    ),
                    Field(
                        name="percent",
                        data_type="float",
                        description=(
                            "The percentage, 0-100, only where the paper states one. "
                            "Do not compute it from the counts."
                        ),
                        normalization=None,
                    ),
                    Field(
                        name="cohort_label",
                        data_type="str",
                        description=(
                            "Which cohort or subgroup the counts describe, if the paper "
                            "distinguishes several (e.g. 'T-loop variants')."
                        ),
                    ),
                ],
            )
        ],
    )


# --------------------------------------------------------------------------
# A fake client, for running the stages at zero cost
# --------------------------------------------------------------------------


#: A markdown table row whose first cell is a label and which carries a
#: "NN.N% (a/b)" somewhere to its right. This is the one shape in the corpus a
#: regex can read reliably; everything else is prose.
TABLE_FREQ = re.compile(
    r"^\|\s*([A-Za-z][A-Za-z \-/,'()]{2,60}?)\s*\|.*?(\d{1,3}(?:\.\d)?)%\s*\((\d+)/(\d+)\)"
)
GENE_MENTION = re.compile(r"\bRNU4-2\b|\bReNU syndrome\b", re.I)


class TableExtractClient:
    """A deterministic stand-in for the extraction model.

    It reads what a regex can read -- markdown table rows of the form
    ``| microcephaly | 72.7% (8/11) | ...`` -- and returns them through the
    real extraction stage, with line citations that point at the rows the
    numbers actually came from. Everything downstream (span resolution, quote
    verification, canonicalization, dedup) then runs for real, at zero cost.

    Its ceiling is the point. Roughly a fifth of the phenotype statements in
    this corpus are in tables; the rest are prose -- "present in more than or
    equal to 75% of individuals", "the majority were non-verbal" -- which no
    regex reads. The gap between what this client extracts and what the model
    extracts is the value of the model, measured rather than asserted.

    It also attributes every row to whichever disease the page is mostly
    about, which is wrong on pages comparing several disorders. That error is
    left in deliberately; finding it is part of the assignment.
    """

    def __init__(self, model: Any = None, default_disease: str = "RNU4-2"):
        self.model = model
        self.calls = 0
        self.default_disease = default_disease
        self.rows_emitted = 0

    async def complete(self, *, system, user, spec, response_model=None, **_):
        from sliders.llm.base import Completion  # noqa: PLC0415
        import json as _json  # noqa: PLC0415

        self.calls += 1
        disease = self.default_disease if GENE_MENTION.search(user) else "unspecified"

        rows = []
        for raw in user.split("\n"):
            head, sep, body = raw.partition("→")
            if not sep or not head.strip().isdigit():
                continue
            n = int(head.strip())
            m = TABLE_FREQ.match(body.strip())
            if not m:
                continue
            label, pct, aff, ass = m.groups()
            rows.append(
                {
                    "fields": {
                        "disease_or_gene": {"rationale": "page subject", "value": disease,
                                            "cite_lines": [n, n]},
                        "phenotype": {"rationale": "row label", "value": label.strip(),
                                      "cite_lines": [n, n]},
                        "n_affected": {"rationale": "row count", "value": int(aff),
                                       "cite_lines": [n, n]},
                        "n_assessed": {"rationale": "row denominator", "value": int(ass),
                                       "cite_lines": [n, n]},
                        "percent": {"rationale": "row percentage", "value": float(pct),
                                    "cite_lines": [n, n]},
                        "cohort_label": {"rationale": "not stated", "value": None,
                                         "cite_lines": [n, n]},
                    }
                }
            )
        self.rows_emitted += len(rows)
        text = _json.dumps({"PhenotypeFrequency": rows})
        parsed = response_model.model_validate_json(text) if response_model else None
        return Completion(
            text=text, parsed=parsed, model="rule-based-stand-in",
            input_tokens=0, output_tokens=0, cache_read_tokens=0,
        )


class FakeExtractClient:
    """Stands in for the provider during extraction.

    It cites line ranges that really contain the values it returns, so
    citation resolution and ``quote_verified`` exercise honestly rather than
    passing because nothing was checked. Patterned on the repo's own tests.
    """

    def __init__(self, model: Any = None, rows_per_chunk: int = 2):
        self.model = model
        self.calls = 0
        self.rows_per_chunk = rows_per_chunk
        self.seen_prompts: list[str] = []

    @staticmethod
    def _find_line(user: str, needle: str) -> int:
        for line in user.split("\n"):
            if "→" in line and needle.lower() in line.lower():
                head, _, _ = line.partition("→")
                if head.strip().isdigit():
                    return int(head.strip())
        return 1

    async def complete(self, *, system, user, spec, response_model=None, **_):
        from sliders.llm.base import Completion  # noqa: PLC0415

        self.calls += 1
        self.seen_prompts.append(user)

        rows = []
        for needle, n, d in (("hypotonia", 42, 48), ("microcephaly", 20, 39)):
            ln = self._find_line(user, needle)
            rows.append(
                {
                    "fields": {
                        "disease_or_gene": {
                            "rationale": "stub",
                            "value": "ReNU syndrome",
                            "cite_lines": [ln, ln],
                        },
                        "phenotype": {
                            "rationale": "stub",
                            "value": needle,
                            "cite_lines": [ln, ln],
                        },
                        "n_affected": {
                            "rationale": "stub",
                            "value": n,
                            "cite_lines": [ln, ln],
                        },
                        "n_assessed": {
                            "rationale": "stub",
                            "value": d,
                            "cite_lines": [ln, ln],
                        },
                        "percent": {"rationale": "stub", "value": None, "cite_lines": [ln, ln]},
                        "cohort_label": {
                            "rationale": "stub",
                            "value": None,
                            "cite_lines": [ln, ln],
                        },
                    }
                }
            )
        payload = {"PhenotypeFrequency": rows[: self.rows_per_chunk]}
        import json as _json  # noqa: PLC0415

        text = _json.dumps(payload)
        parsed = response_model.model_validate_json(text) if response_model else None
        return Completion(
            text=text,
            parsed=parsed,
            model="fake-model",
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=90 if self.calls > 1 else 0,
        )


def patch_extract_client(client: Any):
    """Point the extraction stage at ``client``. Returns an undo callable.

    Patch the module under test, not the definition site -- patching
    ``sliders.llm.get_client`` would leave ``sliders.stages.extraction``'s
    already-bound name alone and silently do nothing.
    """
    add_sliders_to_path()
    import sliders.stages.extraction as ex  # noqa: PLC0415

    original = ex.get_client
    ex.get_client = lambda config, spec=None: client

    def undo() -> None:
        ex.get_client = original

    return undo


# --------------------------------------------------------------------------
# Table -> DiseaseProfile
# --------------------------------------------------------------------------


@dataclass
class ProfileEvidence:
    """Why a term ended up in the profile, and at what frequency."""

    hpo_id: str
    label: str
    raw_phrase: str
    match_method: str
    match_score: float
    n_affected: int | None
    n_assessed: int | None
    percent: float | None
    doc_name: str
    locator: str
    quote: str
    quote_verified: bool
    row_id: str

    def as_row(self) -> dict:
        return {
            "hpo_id": self.hpo_id,
            "label": self.label,
            "raw_phrase": self.raw_phrase,
            "match": f"{self.match_method}/{self.match_score:.2f}",
            "n": f"{self.n_affected}/{self.n_assessed}"
            if self.n_assessed
            else (f"{self.percent}%" if self.percent is not None else "-"),
            "doc": self.doc_name,
            "locator": self.locator,
            "verified": self.quote_verified,
            "quote": self.quote[:90],
        }


@dataclass
class ReconstructedProfile:
    """A disease profile assembled from extracted rows, with its receipts."""

    profile: Any  # rdx.hpo.DiseaseProfile
    evidence: list[ProfileEvidence] = field(default_factory=list)
    ungrounded: list[tuple[str, float]] = field(default_factory=list)
    dropped_rows: int = 0

    def evidence_for(self, hpo_id: str) -> list[ProfileEvidence]:
        return [e for e in self.evidence if e.hpo_id == hpo_id]

    def as_rows(self) -> list[dict]:
        return [e.as_row() for e in self.evidence]


def _cell(row, name: str):
    c = row.cells.get(name)
    return c.value_raw if c is not None else None


def _locator(row, name: str) -> str:
    """``data/corpus/PMC13400782.md:71-71`` -- clickable, and short enough to read."""
    c = row.cells.get(name)
    if c is None or c.span is None:
        return ""
    base = row.doc_path or row.doc_name
    try:
        base = str(Path(base).resolve().relative_to(Path.cwd()))
    except (ValueError, OSError):
        base = Path(base).name
    return f"{base}:{c.span.start_line}-{c.span.end_line}"


def _to_int(v) -> int | None:
    if v is None:
        return None
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return None


def _to_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(v)))
    except (TypeError, ValueError):
        return None


def build_profile(
    rows: Sequence[Any],
    matcher: Any,  # rdx.hpo.TermMatcher
    ontology: Any,  # rdx.hpo.Ontology
    *,
    disease_id: str = "RECONSTRUCTED",
    disease_name: str = "reconstructed profile",
    disease_filter: str | None = None,
    min_match_score: float = 0.6,
    default_frequency: float = 0.35,
    pool: str = "counts",
) -> ReconstructedProfile:
    """Turn extracted rows into a ``DiseaseProfile``, keeping the provenance.

    ``pool="counts"`` sums numerators and denominators across papers, which
    weights a 115-patient series above a single case report. It also double
    counts patients reported in more than one paper -- a real limitation, not a
    rounding error, and one of the things students are asked to quantify.

    ``pool="mean"`` averages the per-paper rates instead, which removes the
    double counting and replaces it with treating a case report as equal to a
    cohort. Neither is right; pick one and say which.
    """
    from .hpo import DiseaseProfile  # noqa: PLC0415

    per_term_counts: dict[str, list[tuple[int, int]]] = defaultdict(list)
    per_term_rates: dict[str, list[float]] = defaultdict(list)
    per_term_mentions: dict[str, int] = defaultdict(int)
    evidence: list[ProfileEvidence] = []
    ungrounded: list[tuple[str, float]] = []
    dropped = 0

    dfilter = disease_filter.lower() if disease_filter else None

    for row in rows:
        phrase = _cell(row, "phenotype")
        if not phrase or not str(phrase).strip():
            dropped += 1
            continue

        disease = str(_cell(row, "disease_or_gene") or "")
        if dfilter and dfilter not in disease.lower():
            dropped += 1
            continue

        m = matcher.match(str(phrase), min_score=min_match_score)
        if m.hpo_id is None:
            ungrounded.append((str(phrase), m.score))
            dropped += 1
            continue

        hid = ontology.normalize(m.hpo_id)
        n_aff = _to_int(_cell(row, "n_affected"))
        n_ass = _to_int(_cell(row, "n_assessed"))
        pct = _to_float(_cell(row, "percent"))

        if n_ass and n_ass > 0 and n_aff is not None:
            per_term_counts[hid].append((n_aff, n_ass))
            per_term_rates[hid].append(min(n_aff / n_ass, 1.0))
        elif pct is not None:
            per_term_rates[hid].append(max(0.0, min(pct / 100.0, 1.0)))
        else:
            per_term_mentions[hid] += 1

        cell = row.cells.get("phenotype")
        evidence.append(
            ProfileEvidence(
                hpo_id=hid,
                label=ontology.label(hid),
                raw_phrase=str(phrase),
                match_method=m.method,
                match_score=m.score,
                n_affected=n_aff,
                n_assessed=n_ass,
                percent=pct,
                doc_name=row.doc_name,
                locator=_locator(row, "phenotype"),
                quote=(cell.quote or "") if cell else "",
                quote_verified=bool(cell.quote_verified) if cell else False,
                row_id=row.row_id,
            )
        )

    freqs: dict[str, float] = {}
    for hid in set(per_term_counts) | set(per_term_rates) | set(per_term_mentions):
        if pool == "counts" and per_term_counts.get(hid):
            num = sum(a for a, _ in per_term_counts[hid])
            den = sum(b for _, b in per_term_counts[hid])
            freqs[hid] = min(num / den, 1.0) if den else default_frequency
        elif per_term_rates.get(hid):
            rates = per_term_rates[hid]
            freqs[hid] = sum(rates) / len(rates)
        else:
            # Mentioned, never quantified. Assuming a frequency here is a
            # guess; it is recorded as one so the ablation can remove it.
            freqs[hid] = default_frequency

    return ReconstructedProfile(
        profile=DiseaseProfile(
            disease_id=disease_id,
            disease_name=disease_name,
            frequencies=freqs,
            excluded=set(),
        ),
        evidence=evidence,
        ungrounded=ungrounded,
        dropped_rows=dropped,
    )


# --------------------------------------------------------------------------
# Convenience views over a built table
# --------------------------------------------------------------------------


def rows_to_records(table: Any, include_provenance: bool = True) -> list[dict]:
    """A Table's rows as flat dicts, provenance included."""
    out = []
    for row in table.rows:
        rec: dict[str, Any] = {"row_id": row.row_id, "doc": row.doc_name}
        for name, cell in row.cells.items():
            rec[name] = cell.value_raw
            if include_provenance:
                rec[f"{name}__locator"] = _locator(row, name)
                rec[f"{name}__verified"] = cell.quote_verified
        out.append(rec)
    return out


def verification_rate(table: Any) -> dict[str, float]:
    """Share of non-null cells whose value really appears in the lines cited."""
    per_field: dict[str, list[bool]] = defaultdict(list)
    for row in table.rows:
        for name, cell in row.cells.items():
            if cell.value_raw is not None:
                per_field[name].append(bool(cell.quote_verified))
    return {
        name: (sum(v) / len(v) if v else 0.0) for name, v in sorted(per_field.items())
    }


def trace_by_stage(trace: Any) -> list[dict]:
    """``Trace.summary().by_stage`` flattened for display."""
    summary = trace.summary()
    return [
        {
            "stage": stage,
            "calls": usage.llm_calls,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_read": usage.cache_read_tokens,
            "cost_usd": round(usage.cost_usd, 4),
        }
        for stage, usage in sorted(
            summary.by_stage.items(), key=lambda kv: -kv[1].cost_usd
        )
    ]


def load_reference_rows(path: str | Path = "data/reference_extraction.json") -> list[Any]:
    """Rehydrate the shipped reference extraction into real ``Row`` objects.

    This is what ``gemini-3.8-flash`` pulled out of a six-document subset,
    saved so the quality of a model-backed extraction is visible without
    credentials. Compare it against the deterministic stand-in: the stand-in
    reads only tables, this reads prose too, and it attributes rows to the
    right disorder on pages that discuss several.
    """
    import json  # noqa: PLC0415

    add_sliders_to_path()
    from sliders.models import Cell, Row, Span  # noqa: PLC0415

    data = json.loads(Path(path).read_text())
    rows = []
    for r in data["rows"]:
        cells = {}
        for name, c in r["cells"].items():
            span = None
            if c.get("start_line") is not None:
                span = Span(start_char=0, end_char=0,
                            start_line=c["start_line"], end_line=c["end_line"])
            cells[name] = Cell(value_raw=c["value_raw"], quote=c["quote"],
                               quote_verified=c["quote_verified"], span=span)
        rows.append(Row(row_id=r["row_id"], table="PhenotypeFrequency",
                        doc_id="", doc_name=r["doc_name"],
                        doc_path=r.get("doc_path"), chunk_id="", cells=cells))
    return rows
