"""What a gene is, in a paragraph, for the disease brief.

Symbols alone (``RNU4-2``, ``AHDC1``) tell a student nothing. NCBI Gene keeps
a curated RefSeq summary for most human genes; ``mygene.info`` serves it
without a key. Results are cached in ``data/genes.json`` so the notebook
never needs the network: ``make_assignments.py`` fills the cache for every
directory it builds.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

CACHE = Path("data/genes.json")
FIELDS = "name,summary,alias,type_of_gene,map_location,entrezgene,genomic_pos"
URL = "https://mygene.info/v3/query?q=symbol:{sym}&species=human&fields=" + FIELDS


@dataclass
class GeneInfo:
    symbol: str
    name: str = ""
    type_of_gene: str = ""
    map_location: str = ""
    entrez_id: str = ""
    aliases: list[str] = field(default_factory=list)
    summary: str = ""
    source: str = ""

    @property
    def found(self) -> bool:
        return bool(self.name)

    def as_dict(self) -> dict:
        return self.__dict__.copy()

    def describe(self, width: int = 78, indent: str = "  ") -> str:
        """A few lines for the brief."""
        import textwrap  # noqa: PLC0415

        if not self.found:
            return f"{indent}gene                 {self.symbol}  (no description on record)"
        loc = f"{self.map_location}" if self.map_location else ""
        kind = (self.type_of_gene or "").replace("-", " ")
        head = f"{indent}gene                 {self.symbol}  {self.name}"
        lines = [head]
        meta = ", ".join(x for x in (kind, loc, f"NCBI Gene {self.entrez_id}" if self.entrez_id else "") if x)
        if meta:
            lines.append(f"{indent}                     {meta}")
        if self.aliases:
            lines.append(f"{indent}                     also called {', '.join(self.aliases[:5])}")
        if self.summary:
            body = textwrap.fill(self.summary, width=width - len(indent) - 21)
            lines.append(f"{indent}                     " +
                         f"\n{indent}                     ".join(body.splitlines()))
        return "\n".join(lines)


def _fetch(symbol: str, timeout: int = 20) -> GeneInfo:
    url = URL.format(sym=urllib.parse.quote(symbol))
    with urllib.request.urlopen(url, timeout=timeout) as r:
        data = json.loads(r.read())
    hits = data.get("hits") or []
    if not hits:
        return GeneInfo(symbol=symbol, source="mygene.info: no hit")
    h = hits[0]
    alias = h.get("alias") or []
    if isinstance(alias, str):
        alias = [alias]
    return GeneInfo(
        symbol=symbol,
        name=h.get("name", ""),
        type_of_gene=h.get("type_of_gene", ""),
        map_location=h.get("map_location", ""),
        entrez_id=str(h.get("entrezgene", "")),
        aliases=list(alias),
        summary=(h.get("summary") or "").strip(),
        source="NCBI Gene via mygene.info",
    )


def _load_cache(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def gene_info(symbol: str | None, *, cache: Path = CACHE,
              fetch: bool = True) -> GeneInfo | None:
    """The cached description, fetching and caching on a miss if ``fetch``."""
    if not symbol:
        return None
    cache = Path(cache)
    cached = _load_cache(cache)
    if symbol in cached:
        return GeneInfo(**cached[symbol])
    if not fetch:
        return GeneInfo(symbol=symbol, source="not cached")
    try:
        info = _fetch(symbol)
    except Exception as e:  # noqa: BLE001 - offline is a normal state
        return GeneInfo(symbol=symbol, source=f"lookup failed: {e}")
    cached[symbol] = info.as_dict()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(dict(sorted(cached.items())), indent=2) + "\n")
    return info
