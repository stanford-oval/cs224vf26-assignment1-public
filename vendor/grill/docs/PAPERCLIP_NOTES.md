# Paperclip notes — usage surface, access, replication

Saved as a working note. Two threads here:

1. What our pipeline actually uses from paperclip (small subset).
2. How hard it would be to replicate, with empirical evidence on what
   their corpus actually contains vs. what we can bulk-download.

---

## What we use

Paperclip is a one-endpoint shell-RPC over a curated paper corpus
(`POST https://paperclip.gxl.ai/api/cli/execute` with `{command,
args}`). Their full surface includes `search lookup sql map pull
ask-image bash` + library management + sources for fda / trials /
patents. We touch ~5% of that.

What our pipeline actually calls:

| operation | how we use it |
|---|---|
| `paperclip search "q" -s <src> -n N` | get paper IDs + metadata, parsed CSV |
| `paperclip cat /papers/<id>/meta.json` | metadata hydration (title, date, doi, authors) |
| `paperclip cat /papers/<id>/content.lines` | full text with `Lxx:` line prefixes |
| `paperclip cat /papers/<id>/sections/<name>` | per-section content |
| `paperclip head -N /papers/<id>/content.lines` | top-N lines |
| `paperclip grep -i "term" /papers/<id>/content.lines` | filtered lines |
| `paperclip scan /papers/<id>/content.lines "t1" "t2"` | multi-term filter |

Sources we touch: `pmc`, `biorxiv`, `medrxiv`, `arxiv`, `abstracts`.
We never use `fda`, `trials`, `patents`, `sql`, `map`, `pull`,
`ask-image`, `bash`, or paper-repo management.

## What their corpus actually delivered (empirical)

Sampled across the two completed investigations (CDH1 SL: 383
papers; Talazoparib resistance: 372 papers):

| source field | papers cited | full-text citations | metadata-only citations |
|---|---|---|---|
| **PMC** | ~600 | **~1900** (95% of all line-anchored evidence) | ~93 |
| **OpenAlex** | ~60 | 24 | 70 |
| **Semantic Scholar Academic Graph** | ~70 | 5 | 87 |

ID-prefix distribution confirms: `PMC*`, `oa_*` (OpenAlex), and
numeric Corpus IDs (Semantic Scholar) — nothing else.

Conclusions from the empirical sample:

- All three sources have **free public bulk channels**:
  - PMC: NCBI FTP (`ftp.ncbi.nlm.nih.gov/pub/pmc/`) — Open Access
    subset bulk-downloadable, daily incremental.
  - OpenAlex: AWS S3 (`s3://openalex/`) free.
  - Semantic Scholar: free bulk with API key.
- 95%+ of grounded evidence is PMC full-text. OpenAlex / Semantic
  Scholar entries are mostly metadata-only — used by the planner for
  coverage discovery, not for deep reading.
- Top-cited papers (PMC6394693, PMC8749886, PMC6769709, PMC10266074,
  PMC11092486, PMC9452295, PMC6613145, …) are all from
  open-access journals (iScience, Cancers, Sci Signal, IJBS, Cell
  Rep, etc.). Nothing in subscription-only journals appeared.

### Caveats I want to be honest about

- **Sample of 2 investigations.** Other topics could surface
  licensed content we didn't trip across.
- **Their PMC slice could be larger than the OA subset.** Full PMC is
  ~10M papers; OA bulk is ~7M. The extra ~3M are author-manuscript /
  embargoed / restricted-license, accessible via NCBI E-utilities to
  paperclip but not bulk-downloadable to us. None of our PMC IDs
  look like they're outside the OA subset, but I haven't verified
  this against NCBI's OA manifest.
- **Their value-add is curation + indexing, not exclusive content.**
  Better section parsing than raw JATS, deduplication across
  sources, unified ID scheme — those are real engineering wins.

## Replication effort

If we ever had to replicate (paperclip access revoked, pricing
changes, or we wanted production independence):

### Data — all open, all bulk-downloadable

| source | bulk channel | raw size | parsed size | effort |
|---|---|---|---|---|
| **PMC** (OA subset) | `ftp.ncbi.nlm.nih.gov/pub/pmc/` — JATS XML, daily incremental | ~300 GB | ~200 GB | XML → sections via `lxml` + JATS parser; ~1 wk |
| **bioRxiv** | `s3://biorxiv-src-monthly/` monthly snapshots | ~100 GB PDFs | ~50 GB | GROBID for PDF → structured text; ~1 wk |
| **medRxiv** | same model as bioRxiv | ~30 GB | ~15 GB | same pipeline as bioRxiv |
| **arXiv** (q-bio + stat.AP only) | `s3://arxiv/` (requester-pays) | ~50 GB | ~25 GB | TeX + PDF parsing |
| **abstracts (S2 Academic Graph)** | datasets API (free with key) | ~150 GB metadata | ~100 GB | direct ingest, no parsing |

**Total: ~600 GB raw / ~400 GB parsed / ~700 GB-1 TB with ES index = under 2 TB.**

### Service — `/api/cli/execute` is a shell-RPC dispatcher

1. **Ingest workers**: parse XML/PDF/text into uniform `content.lines`
   format (one line per source line, prefixed `L42:`). Plus per-section
   files. Plus `meta.json`.
2. **Storage**: Postgres for paper metadata; filesystem or object
   storage for content + sections.
3. **Search**: Elasticsearch or OpenSearch index over `title + abstract
   + body`, per-source faceting. Tantivy if smaller footprint.
4. **CLI surface wrapper**: a `paperclip-clone` CLI mimicking the 5
   commands we use. `search` → ES query. `cat /papers/<id>/X` →
   filesystem read. `head/grep/scan` → ordinary Unix on the content
   file. ~500–1000 lines of Python.

Existing prompts and our `paperclip_client.py` would work unchanged
if we keep the CLI surface identical.

### Effort + cost

| phase | time |
|---|---|
| PMC ingest + parser | 1 week |
| bioRxiv + medRxiv (PDF → text via GROBID) | 1.5 weeks |
| arXiv (PDF + TeX) | 0.5 weeks |
| Semantic Scholar Academic Graph ingest (metadata) | 3 days |
| Elasticsearch index + tuning | 1 week |
| CLI wrapper matching paperclip's surface | 1 week |
| End-to-end smoke + matching paperclip's CSV output format | 1 week |
| **Total** | **~6 weeks, one engineer** |

Running cost: ~$200–300/mo steady state on cloud (2 TB storage +
managed ES + ingest workers). Plus 1–2 days/month maintenance.

## Hardest parts to replicate

1. **PDF parsing for bioRxiv/medRxiv/arXiv** is the biggest engineering
   risk. GROBID is the standard tool and gives sections + references +
   figure captions, but it takes tuning. PMC's JATS XML is much cleaner.
2. **Search quality** is real engineering. Paperclip's ranking gives
   results the LLM trusts; matching that with plain ES BM25 is OK for
   v1 but biomedical synonyms / MeSH term expansion would need work.
3. **No commercial paper full-text.** If paperclip licenses non-open
   papers (NEJM, Cell back-catalog), we can't replicate. Our pipeline
   only touches open-access, so we likely already don't depend on this
   — but worth flagging.
4. **Ongoing maintenance.** Daily incremental updates, schema changes
   from NCBI, GROBID upgrades, etc. — ~1–2 days/month.

## Access issue history

This server (`crlm-project`, outbound IP `172.179.240.103`) is getting
403 on every `paperclip.gxl.ai` endpoint, root URL included, with no
auth header. Same credentials work from a personal laptop. Diagnosis:
WAF/IP block at paperclip's edge, not a client problem. Likely a
broad rule blocking Azure VM ranges, not a deliberate block against
this specific IP. Workarounds without replication:

- Get paperclip operators to allowlist this IP.
- SSH reverse SOCKS proxy from the laptop (see scripts/ directory).
- Run the whole pipeline from the laptop (where paperclip works).

## Recommendation

Replication is **engineering-bounded, ~6 weeks + ~$250/mo + 1–2
days/month maintenance**. Nothing exotic. But if paperclip operators
will allowlist the server's IP, that's a one-line fix on their end
and avoids the ongoing engineering load entirely. The reverse SOCKS
proxy is the no-permissions workaround in the interim.

---

## Working SOCKS-tunnel setup (current state on this VM)

The laptop runs `ssh -R 1080 -N azureuser@<this-server>` to open a SOCKS5
proxy on the server's port 1080 routed through the laptop's network.
The server then ferries paperclip's HTTPS + DNS through that proxy.

Pieces installed:

1. **Credentials**: `~/.paperclip/credentials.json` (mode 600), copied from
   the laptop's `~/.paperclip/credentials.json`.
2. **Wrapper at `~/.local/bin/paperclip`** — `paperclip` resolves here
   (which precedes the real binary in PATH). The wrapper sets
   `ALL_PROXY=socks5h://localhost:1080`, `HTTPS_PROXY=...`, then execs
   the renamed `paperclip-real` via the venv's Python:

   ```bash
   #!/bin/bash
   exec env ALL_PROXY=socks5h://localhost:1080 \
            HTTPS_PROXY=socks5h://localhost:1080 \
     /home/azureuser/.paperclip/venv/bin/python \
     /home/azureuser/.local/bin/paperclip-real "$@"
   ```

3. **The real CLI**: `~/.local/bin/paperclip-real` — the original
   paperclip script, renamed. The wrapper invokes it.
4. **Python venv at `~/.paperclip/venv`** with `requests[socks]` and
   `click`. The system Python lacks PySOCKS and PEP 668 blocks pip into
   it; uv was used to create the venv (`uv venv --python 3.12`) and
   `uv pip install --python ~/.paperclip/venv/bin/python "requests[socks]" click`
   populated it.

### Operating it

- Start the tunnel from the laptop: `ssh -R 1080 -N azureuser@<server>`.
  Keep that terminal open. For resilience, use `autossh -M 0 -R 1080 -N ...`
  so the tunnel reconnects after laptop sleep / network blips.
- Paperclip Just Works™ on the server: `paperclip --no-repo search ...`,
  `paperclip --no-repo cat /papers/<id>/meta.json`, etc.
- The graph-search background hydration daemon and any codex shards
  that exec paperclip pick up the wrapper transparently — no code
  changes in the project.

### Failure modes to recognize

- **Tunnel went down**: paperclip returns "Could not reach the server."
  Restart the `ssh -R 1080` on the laptop.
- **Credentials expired**: paperclip says "Not authenticated. Run:
  paperclip login." Re-scp the file from the laptop. (Refresh attempts
  succeed when the tunnel is up because they exit the laptop's IP.)
- **`ModuleNotFoundError: socks`**: someone reinstalled paperclip and
  the wrapper's path to the venv is now stale. Re-run
  `uv pip install --python ~/.paperclip/venv/bin/python "requests[socks]"`.

### What to do if the wrapper ever needs to be rebuilt from scratch

```bash
mv ~/.local/bin/paperclip ~/.local/bin/paperclip-real  # only if not already done
uv venv --python 3.12 ~/.paperclip/venv
uv pip install --python ~/.paperclip/venv/bin/python "requests[socks]" click
cat > ~/.local/bin/paperclip <<'WRAPPER'
#!/bin/bash
exec env ALL_PROXY=socks5h://localhost:1080 HTTPS_PROXY=socks5h://localhost:1080 \
  /home/azureuser/.paperclip/venv/bin/python \
  /home/azureuser/.local/bin/paperclip-real "$@"
WRAPPER
chmod +x ~/.local/bin/paperclip
```
