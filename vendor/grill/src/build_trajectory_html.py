#!/usr/bin/env python3
"""Build a single self-contained HTML inspector for a Methodology-v2 run.

Embeds the run's ledger.json + run.json + a timeline parsed from orchestrator.log,
and renders (with vanilla JS, no deps, works offline):
  - INIT: required fields, prior hypothesis, candidate answers, grounded glossary
  - Belief ledger: directions (frontier + what the agent allocated each) + hypotheses
    (pool / bin with reasons) + the evidence behind them
  - Trajectory: round-by-round PLAN -> EXPLORE -> SCREEN -> DEEP TEST -> checkpoint
  - Checkpoints: every metric with its formula and the actual numbers plugged in

    python3 -m src.build_trajectory_html <run_dir> <out.html>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def parse_timeline(text: str) -> list[dict]:
    ev, cum = [], 0.0
    for line in text.splitlines():
        m = re.search(r"\[(\d\d:\d\d:\d\d)\]\s*(.*)$", line)
        if not m:
            continue
        ts, body = m.group(1), m.group(2)
        # one pool: every line that reports spend reports the same running total
        mm = re.search(r"spent \$([\d.]+)/", body) or re.search(r"spent=\$([\d.]+)", body)
        if mm:
            cum = float(mm.group(1))
        e = {"ts": ts, "raw": body, "cum": round(cum, 2)}
        if body.startswith("INIT: parse"):
            e["type"] = "init"
        elif body.lstrip().startswith("required_fields="):
            e["type"] = "init_seed"
            for k in ("required_fields", "seed_directions", "prior_hypotheses", "terms"):
                mm = re.search(rf"{k}=(\d+)", body)
                if mm:
                    e[k] = int(mm.group(1))
        elif body.startswith("INIT: GROUND"):
            e["type"] = "ground"
        elif body.startswith("INIT: probing"):
            e["type"] = "probe"
            e["n"] = int(re.search(r"probing (\d+)", body).group(1))
        elif body.lstrip().startswith("INIT probe:"):
            e["type"] = "probe_done"
            for k, pat in (("pooled", r"(\d+) pooled"), ("binned", r"(\d+) binned"),
                           ("seeded", r"\+(\d+) directions")):
                mm = re.search(pat, body)
                if mm:
                    e[k] = int(mm.group(1))
        elif body.lstrip().startswith("INIT spent"):
            e["type"] = "init_done"
            e["cum"] = cum = float(re.search(r"\$([\d.]+)", body).group(1))
        elif body.lstrip().startswith("PLAN:"):
            e["type"] = "plan"
            e["pot"] = float(re.search(r"\$([\d.]+) pot", body).group(1))
            e["ceiling"] = float(re.search(r"\$([\d.]+) ceiling", body).group(1))
            e["allocs"] = [{"id": i, "usd": float(u), "why": w.strip()}
                           for i, u, w in re.findall(r"(d\d+) \$([\d.]+) \(([^)]*)\)", body)]
        elif body.startswith("ROUND"):
            e["type"] = "round"
            e["round"] = int(re.search(r"ROUND (\d+)", body).group(1))
            mm = re.search(r"EXPLORE (\d+) dir", body)
            e["n_explore"] = int(mm.group(1)) if mm else None
        elif body.lstrip().startswith("+") and "hypotheses from" in body:
            e["type"] = "ingest"
            e["added"] = int(re.search(r"\+(\d+) hypotheses", body).group(1))
            e["from_dirs"] = int(re.search(r"from (\d+) directions", body).group(1))
        elif body.lstrip().startswith("SCREEN:"):
            e["type"] = "screen"
            mm = re.search(r"(\d+) passed / (\d+) screened", body)
            if mm:
                e["passed"], e["screened"] = int(mm.group(1)), int(mm.group(2))
            else:
                e["truncated"] = int(re.search(r"with (\d+)", body).group(1))
        elif body.lstrip().startswith("DEEP:"):
            e["type"] = "deep"
            mm = re.search(r"(\d+) → pool, (\d+) → bin", body)
            if mm:
                e["pooled"], e["binned"] = int(mm.group(1)), int(mm.group(2))
            else:
                e["truncated"] = int(re.search(r"with (\d+)", body).group(1))
        elif body.lstrip().startswith("corroboration:"):
            e["type"] = "corroborate"
            e["bumped"] = int(re.search(r"raised (\d+)", body).group(1))
            mm = re.search(r"(\d+) resurfaced", body)
            e["resurfaced"] = int(mm.group(1)) if mm else 0
        elif body.startswith("CHECKPOINT"):
            e["type"] = "checkpoint"
            e["n"] = int(re.search(r"CHECKPOINT (\d+)", body).group(1))
            for k in ("coverage", "quality", "answeredness", "progress"):
                mm = re.search(rf"{k}=([\d.]+)", body)
                if mm:
                    e[k] = float(mm.group(1))
            for k, pat in (("pooled", r"(\d+) pooled"), ("binned", r"(\d+) binned"),
                           ("backlog", r"untested (\d+)")):
                mm = re.search(pat, body)
                if mm:
                    e[k] = int(mm.group(1))
        elif "STALLED" in body or (body.lstrip().startswith("+") and "deeper directions" in body):
            e["type"] = "steer"
            mm = re.search(r"\+(\d+) deeper", body)
            e["corrective"] = int(mm.group(1)) if mm else 0
            e["stall"] = "STALLED" in body
        elif body.lstrip().startswith("STEER["):
            e["type"] = "human"
            e["text"] = body.split("]:", 1)[-1].strip()
        elif body.lstrip().startswith("human verdict"):
            e["type"] = "human"
            e["text"] = body.strip()
        elif body.startswith("FINALIZE"):
            e["type"] = "finalize"
        elif body.startswith("DONE"):
            e["type"] = "done"
        else:
            e["type"] = "log"
        ev.append(e)
    return ev


def main() -> int:
    run_dir = Path(sys.argv[1])
    out = Path(sys.argv[2])
    ledger = json.loads((run_dir / "ledger.json").read_text(encoding="utf-8"))
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    log = (run_dir / "orchestrator.log").read_text(encoding="utf-8", errors="replace")
    timeline = parse_timeline(log)

    payload = json.dumps({"ledger": ledger, "run": run, "timeline": timeline},
                         ensure_ascii=False)
    # safe-embed: prevent any "</script>" or HTML in the data from breaking the page
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    html = HTML_TEMPLATE.replace("/*__DATA__*/", payload)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}  ({len(html)//1024} KB)  "
          f"{len(ledger['directions'])} directions, {len(ledger.get('hypotheses') or {})} hypotheses, "
          f"{len(ledger.get('evidence') or {})} evidence, {len(timeline)} timeline events")
    return 0


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Methodology v2 — run inspector</title>
<style>
:root{--bg:#0e1116;--panel:#161b22;--panel2:#1c232c;--line:#2a323d;--ink:#e6edf3;--mut:#8b97a6;
--blue:#4aa3ff;--teal:#3fc7c0;--green:#56d364;--amber:#e3b341;--red:#f85149;--violet:#bc8cff;--accent:#4aa3ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,Segoe UI,Inter,Roboto,sans-serif}
code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
header{padding:18px 24px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#11161d,#0e1116)}
header h1{margin:0 0 4px;font-size:18px}
header .q{color:var(--mut);font-size:12.5px;max-width:1100px}
nav{display:flex;gap:4px;padding:0 16px;border-bottom:1px solid var(--line);background:var(--panel);position:sticky;top:0;z-index:5;flex-wrap:wrap}
nav button{background:none;border:0;color:var(--mut);padding:12px 14px;cursor:pointer;font-size:13px;border-bottom:2px solid transparent}
nav button:hover{color:var(--ink)}
nav button.on{color:var(--ink);border-bottom-color:var(--accent)}
main{padding:20px 24px;max-width:1280px;margin:0 auto}
.view{display:none}.view.on{display:block}
h2{font-size:15px;margin:22px 0 10px;color:var(--ink);border-left:3px solid var(--accent);padding-left:9px}
h3{font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em;margin:18px 0 8px}
.grid{display:grid;gap:12px}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}.g2{grid-template-columns:repeat(2,1fr)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.kpi .v{font-size:22px;font-weight:700}.kpi .l{color:var(--mut);font-size:11.5px;text-transform:uppercase;letter-spacing:.04em}
.pill{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px;border:1px solid var(--line)}
.b-blue{color:var(--blue);border-color:#2b4a6b}.b-teal{color:var(--teal);border-color:#1f5350}.b-green{color:var(--green);border-color:#235c2c}
.b-amber{color:var(--amber);border-color:#5c4a1f}.b-red{color:var(--red);border-color:#5c2626}.b-violet{color:var(--violet);border-color:#43356b}.b-mut{color:var(--mut)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:600;position:sticky;top:46px;background:var(--panel)}
tr:hover td{background:#11161d}
.src{color:var(--blue);text-decoration:none}.src:hover{text-decoration:underline}
.num{display:inline-block;background:#11202e;color:var(--teal);border:1px solid #1f3a4d;border-radius:5px;padding:0 6px;margin:1px 3px 1px 0;font-size:11px}
.asp{display:inline-block;background:#1a1430;color:var(--violet);border:1px solid #352a5c;border-radius:5px;padding:0 6px;margin:1px 3px 1px 0;font-size:11px}
.muted{color:var(--mut)}.small{font-size:12px}
input,select{background:var(--panel2);border:1px solid var(--line);color:var(--ink);border-radius:7px;padding:6px 9px;font-size:13px}
.tl{position:relative;margin-left:8px;padding-left:22px;border-left:2px solid var(--line)}
.tl .ev{position:relative;margin:0 0 10px}
.tl .ev:before{content:"";position:absolute;left:-29px;top:5px;width:10px;height:10px;border-radius:50%;background:var(--mut);border:2px solid var(--bg)}
.tl .ev.round:before{background:var(--blue)}.tl .ev.verify:before{background:var(--teal)}.tl .ev.checkpoint:before{background:var(--amber)}
.tl .ev.ingest:before{background:var(--green)}.tl .ev.done:before{background:var(--violet)}
.tl .ev .hd{font-weight:600}.tl .ev .meta{color:var(--mut);font-size:12px}
.cum{float:right;color:var(--mut);font-size:11.5px}
.formula{background:#0b0f14;border:1px dashed var(--line);border-radius:8px;padding:10px 12px;margin:8px 0;font-family:ui-monospace,monospace;font-size:12.5px;color:var(--teal);overflow-x:auto}
.calc{color:var(--amber)}
details{border:1px solid var(--line);border-radius:8px;margin:6px 0;background:var(--panel)}
summary{cursor:pointer;padding:9px 12px;font-weight:600}
details > div{padding:0 12px 12px}
.tree{font-size:12.5px}.tree .node{padding:3px 0;border-bottom:1px dotted #1d242d}
.bar{height:7px;background:#11202e;border-radius:4px;overflow:hidden;display:inline-block;width:120px;vertical-align:middle}
.bar > i{display:block;height:100%;background:var(--blue)}
.legend{color:var(--mut);font-size:12px;margin:6px 0}
a.doi{color:var(--blue)}
.scroll{max-height:560px;overflow:auto;border:1px solid var(--line);border-radius:10px}
.scroll table th{top:0}
</style></head>
<body>
<header>
  <h1>Methodology v2 — run inspector <span class="pill b-mut" id="hdrcost"></span></h1>
  <div class="q" id="hdrq"></div>
</header>
<nav id="nav"></nav>
<main>
  <section class="view" id="v-overview"></section>
  <section class="view" id="v-init"></section>
  <section class="view" id="v-ledger"></section>
  <section class="view" id="v-trajectory"></section>
  <section class="view" id="v-checkpoints"></section>
  <section class="view" id="v-how"></section>
</main>
<script>
const DATA = /*__DATA__*/;
const L = DATA.ledger, R = DATA.run, TL = DATA.timeline;
const $ = s => document.querySelector(s);
const esc = s => (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const dirs = Object.values(L.directions);
const hyps = Object.values(L.hypotheses||{});
const evAll = L.evidence||{};
const srcLoc = s => s.doi?('https://doi.org/'+s.doi):(s.pmid?('https://pubmed.ncbi.nlm.nih.gov/'+s.pmid):(s.pmc?('https://www.ncbi.nlm.nih.gov/pmc/articles/'+s.pmc):(s.url||'')));
const evOf = h => (h.evidence_ids||[]).map(i=>evAll[i]).filter(Boolean);
const balance = h => {const s=new Set(),c=new Set();evOf(h).forEach(e=>{const k=(e.source||{}).doi||(e.source||{}).pmid||(e.source||{}).pmc||(e.source||{}).url;if(!k)return;(e.stance==='contradicts'?c:e.stance==='supports'?s:new Set()).add(k)});return [s.size,c.size];};
const numsOf = h => {const n={};evOf(h).forEach(e=>Object.assign(n,e.numbers||{}));return n;};

// ---- header ----
$('#hdrq').textContent = L.question;
$('#hdrcost').textContent = '$'+(R.budget.spent||0).toFixed(2)+' / $'+R.budget.total+'  ·  '+R.round+' rounds';

// ---- nav ----
const TABS = [['overview','Overview'],['init','INIT'],['ledger','Belief ledger'],
  ['trajectory','Trajectory'],['checkpoints','Checkpoints & metrics'],['how','How it works']];
const nav = $('#nav');
TABS.forEach(([id,lab],i)=>{const b=document.createElement('button');b.textContent=lab;b.onclick=()=>show(id);b.id='nav-'+id;nav.appendChild(b);});
function show(id){TABS.forEach(([t])=>{$('#v-'+t).classList.toggle('on',t===id);$('#nav-'+t).classList.toggle('on',t===id);});location.hash=id;}

// ---- counts ----
const byStatus = s => hyps.filter(h=>h.status===s).length;
const byVerdict = v => hyps.filter(h=>h.verdict===v).length;
const grounded = hyps.filter(h=>(h.evidence_ids||[]).length).length;
const uniqSrc = new Set(), verSrc = new Set();
Object.values(evAll).forEach(e=>{const s=e.source||{};const k=s.doi||s.pmid||s.pmc||s.url||s.title;if(k){uniqSrc.add(k);if(s.verified)verSrc.add(k);}});

// ===== OVERVIEW =====
(function(){
  const b=R.budget, S=R.snapshots[R.snapshots.length-1]||{};
  const kpi=(v,l)=>`<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`;
  const allocs=(R.allocations||[]).slice().sort((x,y)=>y.allocated-x.allocated);
  const phases=b.by_phase||{};
  $('#v-overview').innerHTML=`
   <h2>Run at a glance</h2>
   <div class="grid g4">
     ${kpi('$'+b.spent.toFixed(2),'total spent / $'+b.total)}
     ${kpi(R.round,'rounds')}
     ${kpi(hyps.length,'hypotheses')}
     ${kpi(dirs.length,'directions (frontier)')}
   </div>
   <div class="grid g4" style="margin-top:12px">
     ${kpi(byStatus('pooled'),'pooled (survived the deep test)')}
     ${kpi(byStatus('binned'),'binned (kept, not discarded)')}
     ${kpi(Object.keys(evAll).length,'evidence items')}
     ${kpi(uniqSrc.size,'distinct sources')}
   </div>
   <h2>Final belief state (metrics)</h2>
   <div class="grid g4">
     ${kpi(((S.coverage||0)*100).toFixed(0)+'%','coverage (asks answered)')}
     ${kpi((S.quality||0).toFixed(2),'quality (test survival rate)')}
     ${kpi((S.answeredness||0).toFixed(2),'answeredness = cov×qual')}
     ${kpi(S.backlog||0,'untested (budget ran out)')}
   </div>
   <h2>Budget — one pool, allocated by the agent</h2>
   <div class="card">
     ${poolBar('spent',b.spent,b.total,'var(--blue)')}
     <div class="legend">There is no explore/verify split. The agent's planner prices each direction;
       the harness clamps any single allocation to ${((R.config.alloc_ceiling_frac||0)*100).toFixed(0)}% of the
       round's pot (itself ${((R.config.explore_round_frac||0)*100).toFixed(0)}% of what's left, so every
       hypothesis produced can still be screened and deep-tested — testing is never rationed).</div>
     <table style="margin-top:10px"><tbody>${
       Object.entries(phases).filter(([,v])=>v>0).map(([k,v])=>`<tr><td class="mono muted">${esc(k)}</td><td class="mono">$${v.toFixed(2)}</td><td style="width:60%"><span class="bar" style="width:100%"><i style="width:${(v/b.spent*100).toFixed(1)}%"></i></span></td></tr>`).join('')
     }</tbody></table>
   </div>
   <h2>What the agent bought <span class="muted small">— per-direction allocation vs actual spend</span></h2>
   <div class="card"><div class="scroll"><table><thead><tr><th>direction</th><th>allocated</th><th>spent</th><th>the agent's reason for the amount</th></tr></thead><tbody>${
     allocs.map(a=>`<tr><td class="mono">${esc(a.direction)}</td><td class="mono">$${(a.allocated||0).toFixed(2)}</td><td class="mono">$${(a.spent||0).toFixed(2)}</td><td class="small">${esc(a.rationale||'')}<div class="muted small">${esc((a.question||'').slice(0,110))}</div></td></tr>`).join('')||'<tr><td colspan="4" class="muted">no allocations recorded</td></tr>'
   }</tbody></table></div></div>
   <h2>Config knobs</h2>
   <div class="card"><table><tbody>${
     ['budget','K','alloc_ceiling_frac','explore_round_frac','explore_default_usd','explore_min_usd','screen_task_usd','deep_task_usd','unbin_thresh','progress_eps','model'].filter(k=>R.config[k]!==undefined).map(k=>`<tr><td class="mono muted">${k}</td><td class="mono">${esc(R.config[k])}</td></tr>`).join('')
   }</tbody></table></div>
   <h2>The executors (codex as a schema-constrained pure function)</h2>
   <div class="card small">
     <p><b>PRIOR</b> → parametric knowledge + candidate answers + key terms (read-only). Its candidate
     answers are HYPOTHESES and are tested before anything is built on them.<br>
     <b>GROUND</b> → nail one key term + a real SourceRef (web).<br>
     <b>PLAN</b> → rank the open directions AND allocate the round's money across them (read-only).<br>
     <b>EXPLORE</b> → investigate one direction → falsifiable hypotheses + new directions (web).<br>
     <b>SCREEN</b> (stage 1) → quick search: does this hypothesis hold up at all? Cheap (web).<br>
     <b>DEEP TEST</b> (stage 2) → hunt evidence <i>and</i> counter-examples; supported / conflicted / refuted (web).<br>
     <b>EVALUATE</b> → reflect on the draft vs last checkpoint → corrective directions (read-only).</p>
   </div>`;
})();
function poolBar(lab,sp,cap,col){const p=Math.min(100,sp/cap*100);return `<div style="margin:7px 0"><div class="small"><b>${lab}</b> <span class="muted">$${sp.toFixed(2)} / $${cap.toFixed(2)}</span></div><div class="bar" style="width:100%"><i style="width:${p}%;background:${col||'var(--blue)'}"></i></div></div>`;}

// ===== INIT =====
(function(){
  const p=L.prior;
  $('#v-init').innerHTML=`
   <h2>Step 1 — required fields parsed from the question (FIELDS executor)</h2>
   <div class="card"><div class="legend">The explicit asks the answer must deliver — the faithfulness checklist.</div>
     <ol>${L.required_fields.map(f=>`<li>${esc(f)}</li>`).join('')}</ol></div>
   <h2>Step 2 — prior hypothesis (PRIOR executor, from model knowledge only)</h2>
   <div class="card"><p>${esc(p.text)}</p>
     <h3>Candidate answers — taken as HYPOTHESES and tested (screen → deep) before anything builds on them</h3>
     <ul>${(p.candidate_answers||[]).map(c=>{
        const h=hyps.find(x=>x.text===c);
        return `<li>${esc(c)}${h?` <span class="pill ${h.status==='pooled'?'b-green':h.status==='binned'?'b-red':'b-amber'}">${h.status}</span>`:''}</li>`;
      }).join('')||'<li class="muted">none</li>'}</ul>
     <div class="legend">This is the highest hallucination-risk material in the run — it came out of the
       model's memory, not the literature. Whatever survives also seeds research directions.</div></div>
   <h2>Step 3 — grounded glossary (GROUND executor, ${Object.keys(L.glossary).length} terms)</h2>
   <div class="grid g2">${Object.entries(L.glossary).map(([t,g])=>{
      const s=g.source||{};const loc=srcLoc(s);
      return `<div class="card"><b>${esc(t)}</b><div class="small" style="margin:6px 0">${esc(g.definition||'')}</div>
        ${s.title?`<div class="small muted">${esc((s.authors&&s.authors[0])||'')} ${s.year?'('+s.year+')':''} — ${esc(s.title)} ${loc?`<a class="src" href="${esc(loc)}" target="_blank">↗</a>`:''}</div>`:''}</div>`;
    }).join('')}</div>
   <h2>How the frontier was seeded</h2>
   <div class="card small">From PRIOR's open questions + candidate answers, the orchestrator created the initial
     <b>${dirs.filter(d=>!d.parent_id).length}</b> root directions; EXPLORE then spawned the rest as children
     (${dirs.length} total). See <a href="#" onclick="show('ledger');return false">Belief ledger → Directions</a>.</div>`;
})();

// ===== LEDGER =====
(function(){
  const statusPill=s=>({OPEN:'b-mut',EXPLORING:'b-amber',EXPLORED:'b-blue',CLOSED:'b-mut'}[s]||'b-mut');
  const hPill=s=>({pooled:'b-green',binned:'b-red',screened:'b-teal',proposed:'b-amber'}[s]||'b-mut');
  $('#v-ledger').innerHTML=`
   <h2>The typed graph — Direction → Hypothesis → Evidence (Methodology §2)</h2>
   <div class="grid g4">
     <div class="kpi"><div class="v">${dirs.length}</div><div class="l">Directions</div></div>
     <div class="kpi"><div class="v">${hyps.length}</div><div class="l">Hypotheses</div></div>
     <div class="kpi"><div class="v">${Object.keys(evAll).length}</div><div class="l">Evidence items</div></div>
     <div class="kpi"><div class="v">${uniqSrc.size}</div><div class="l">distinct sources</div></div>
   </div>
   <div class="grid g4" style="margin-top:12px">
     <div class="kpi"><div class="v">${byStatus('pooled')}</div><div class="l">pooled</div></div>
     <div class="kpi"><div class="v">${byVerdict('conflicted')}</div><div class="l">binned: contested</div></div>
     <div class="kpi"><div class="v">${byVerdict('refuted')}</div><div class="l">binned: refuted</div></div>
     <div class="kpi"><div class="v">${byStatus('proposed')+byStatus('screened')}</div><div class="l">untested</div></div>
   </div>
   <h2>Hypotheses <span class="muted small">— every one is screened, and everything that passes is deep-tested. Nothing is discarded: the bin keeps its reason.</span></h2>
   <div style="margin:6px 0"><input id="cq" placeholder="filter text/aspect…" style="width:280px">
     <select id="cf"><option value="">all statuses</option><option>pooled</option><option>binned</option><option>screened</option><option>proposed</option></select>
     <span class="muted small" id="ccount"></span></div>
   <div class="scroll"><table><thead><tr><th>id</th><th>hypothesis</th><th>aspects</th><th>numbers</th><th>for / against</th><th>conf</th><th>state</th></tr></thead><tbody id="cbody"></tbody></table></div>
   <h2>Directions <span class="muted small">— the frontier (tree via parent_id); $ = what the agent's planner allocated</span></h2>
   <div style="margin:6px 0"><select id="df"><option value="">all status</option><option>OPEN</option><option>EXPLORED</option><option>CLOSED</option><option>EXPLORING</option></select>
     <span class="muted small" id="dcount"></span></div>
   <div class="scroll"><table><thead><tr><th>id</th><th>question</th><th>parent</th><th>status</th><th>promise</th><th>allocated</th><th>hyps</th></tr></thead><tbody id="dbody"></tbody></table></div>`;
  function renderHyps(){
    const q=($('#cq').value||'').toLowerCase(), f=$('#cf').value;
    const rows=hyps.filter(h=>(!f||h.status===f) && (!q || (h.text+' '+(h.aspects||[]).join(' ')).toLowerCase().includes(q)));
    $('#ccount').textContent=rows.length+' shown';
    $('#cbody').innerHTML=rows.slice(0,400).map(h=>{
      const [sup,con]=balance(h);
      const nums=Object.entries(numsOf(h)).map(([k,v])=>`<span class="num">${esc(k)}=${esc(v)}</span>`).join('');
      const asp=(h.aspects||[]).map(a=>`<span class="asp">${esc(a)}</span>`).join('');
      const srcs=evOf(h).map(e=>{const s=e.source||{};const loc=srcLoc(s);
        return `<a class="src" href="${esc(loc)}" target="_blank" title="${esc(e.stance)}: ${esc(e.text||'').slice(0,120)}">${e.stance==='contradicts'?'✗':'✓'} ${esc((s.authors&&s.authors[0])||(s.title||'').slice(0,20))}${s.year?' '+s.year:''}</a>`;}).join(' ');
      const why=h.status==='binned'?`<div class="muted small">⤷ ${esc(h.bin_reason||'')}</div>`:'';
      return `<tr><td class="mono">${h.id}</td><td>${esc(h.text)}<div class="muted small">${esc(h.rationale||'')}</div>${why}<div class="small">${srcs}</div></td>
        <td>${asp}</td><td>${nums||'<span class="muted">—</span>'}</td>
        <td class="mono">${sup} / ${con}</td>
        <td class="mono">${(h.confidence||0).toFixed(2)}</td>
        <td><span class="pill ${hPill(h.status)}">${h.status}</span>${h.verdict&&h.verdict!=='untested'?`<div class="muted small">${esc(h.verdict)}</div>`:''}</td></tr>`;
    }).join('');
  }
  function renderDirs(){
    const f=$('#df').value;
    const rows=dirs.filter(d=>!f||d.status===f);
    $('#dcount').textContent=rows.length+' shown';
    $('#dbody').innerHTML=rows.slice(0,400).map(d=>`<tr><td class="mono">${d.id}</td><td>${esc(d.question_text)}<div class="muted small">${esc(d.rationale||'')}</div>${d.alloc_rationale?`<div class="muted small">💰 ${esc(d.alloc_rationale)}</div>`:''}</td>
      <td class="mono muted">${d.parent_id||'root'}</td><td><span class="pill ${statusPill(d.status)}">${d.status}</span></td>
      <td><span class="bar"><i style="width:${Math.max(0,Math.min(100,(d.promise||0)*100))}%"></i></span> <span class="mono small">${(d.promise||0).toFixed(2)}</span></td>
      <td class="mono">${d.allocated_usd?('$'+d.allocated_usd.toFixed(2)+(d.spent_usd?` <span class="muted">(spent $${d.spent_usd.toFixed(2)})</span>`:'')):'<span class="muted">—</span>'}</td>
      <td class="mono">${(d.produced_hypotheses||[]).length}</td></tr>`).join('');
  }
  $('#cq').oninput=renderHyps;$('#cf').onchange=renderHyps;$('#df').onchange=renderDirs;
  renderHyps();renderDirs();
})();

// ===== TRAJECTORY =====
(function(){
  const icon={round:'🔎 EXPLORE',plan:'💰 PLAN',ingest:'＋ hypotheses',screen:'⌕ SCREEN',deep:'⚖ DEEP TEST',
    corroborate:'↺ corroborate',checkpoint:'◆ CHECKPOINT',steer:'↻ steer',human:'👤 human',
    init:'⊕ INIT',init_seed:'⊕ seed',ground:'⊕ GROUND',probe:'⊕ probe priors',probe_done:'⊕ priors tested',
    init_done:'⊕ INIT done',finalize:'■ finalize',done:'■ DONE',log:''};
  const rows=TL.map(e=>{
    let body='';
    if(e.type==='plan') body=`Agent allocated <b>$${e.pot.toFixed(2)}</b> (ceiling $${e.ceiling.toFixed(2)}/direction): `
      + (e.allocs||[]).map(a=>`<b>${a.id}</b> $${a.usd.toFixed(2)} <span class="muted small">${esc(a.why)}</span>`).join(' · ');
    else if(e.type==='round') body=`Exploring <b>${e.n_explore}</b> funded directions`;
    else if(e.type==='ingest') body=`<b>+${e.added}</b> hypotheses from ${e.from_dirs} directions`;
    else if(e.type==='screen') body=e.truncated!=null?`<span class="b-amber">budget ran out</span> — ${e.truncated} left unscreened`
      :`<b>${e.passed}</b> passed / ${e.screened} screened`;
    else if(e.type==='deep') body=e.truncated!=null?`<span class="b-amber">budget ran out</span> — ${e.truncated} left untested`
      :`<b>${e.pooled}</b> → pool · <b>${e.binned}</b> → bin`;
    else if(e.type==='corroborate') body=`raised <b>${e.bumped}</b> binned hypotheses on independent evidence${e.resurfaced?` · <b>${e.resurfaced}</b> resurfaced for another test`:''}`;
    else if(e.type==='probe_done') body=`priors: <b>${e.pooled}</b> pooled · ${e.binned} binned · +${e.seeded||0} directions seeded`;
    else if(e.type==='checkpoint') body=`coverage <b>${e.coverage}</b> · quality <b>${e.quality}</b> · answeredness <b>${e.answeredness}</b> · ${e.pooled} pooled / ${e.binned} binned · ${e.backlog} untested`;
    else if(e.type==='steer') body=e.stall?`<span class="b-amber">STALLED</span> → +${e.corrective} deeper directions`:`+${e.corrective} corrective directions`;
    else if(e.type==='human') body=`<span class="muted small">${esc(e.text||'').slice(0,600)}</span>`;
    else if(e.type==='init_seed') body=`required_fields=${e.required_fields} · seed_directions=${e.seed_directions} · prior hypotheses=${e.prior_hypotheses||0} · terms=${e.terms}`;
    else body=esc(e.raw);
    const cls=['round','ingest','deep','checkpoint','done'].includes(e.type)?({deep:'verify'}[e.type]||e.type):'';
    return `<div class="ev ${cls}"><span class="cum">$${(e.cum||0).toFixed(2)}</span>
      <div class="hd">${icon[e.type]||''} <span class="muted small">${e.ts}</span></div><div class="meta">${body}</div></div>`;
  }).join('');
  $('#v-trajectory').innerHTML=`<h2>Orchestration trajectory <span class="muted small">— INIT → (PLAN → EXPLORE → SCREEN → DEEP TEST → checkpoint)* → finalize</span></h2>
    <div class="legend">Right edge = cumulative spend (one pool). Blue=EXPLORE, green=hypotheses ingested,
      teal=deep test, amber=checkpoint. PLAN rows show what the agent chose to spend where, and why.</div>
    <div class="tl">${rows}</div>`;
})();

// ===== CHECKPOINTS =====
(function(){
  const sn=R.snapshots;
  let html=`<h2>How each checkpoint is computed (Methodology §7, simplified)</h2>
   <div class="card small">Two scored dimensions + one progress signal, one LLM judge total.
   <b>Coverage</b> = asks answered by POOLED hypotheses / total asks (judge). <b>Quality</b> = pooled /
   (pooled + binned) = the share of tested hypotheses that survived; a low score means the agent is
   proposing hypotheses the literature doesn't support, which is information rather than failure.
   <b>Backlog</b> = hypotheses the budget never reached. <b>Progress</b> = (Δ covered + Δ pooled) / Δ$.</div>
   <div class="formula">Coverage     = asks_answered / total_asks
Quality      = pooled / (pooled + binned)
Answeredness = Coverage × Quality        (share of the question answered AND tested)
Progress     = (Δ covered + Δ pooled) / Δcost
STALL        = Progress ≈ 0  AND  Coverage &lt; 1   →  dig deeper, do NOT stop</div>`;
  sn.forEach((s,i)=>{
    const prev=i>0?sn[i-1]:null;
    const ans=(s.coverage*s.quality);
    const dcov=prev?(s.n_covered-prev.n_covered):s.n_covered, dpool=prev?(s.n_pooled-prev.n_pooled):s.n_pooled;
    html+=`<details ${i===sn.length-1?'open':''}><summary>${i===sn.length-1?'FINAL':'Checkpoint '+(i+1)} — $${s.cost.toFixed(2)} · coverage ${s.n_covered}/${s.n_asks} · quality ${s.quality.toFixed(2)} · answeredness ${ans.toFixed(2)}${s.stalled?' · <span class="b-amber">STALLED</span>':''}</summary><div>
      <div class="grid g4" style="margin:10px 0">
        <div class="kpi"><div class="v">${(s.coverage*100).toFixed(0)}%</div><div class="l">Coverage (${s.n_covered}/${s.n_asks})</div></div>
        <div class="kpi"><div class="v">${s.quality.toFixed(2)}</div><div class="l">Quality (${s.n_pooled} pooled / ${s.n_binned} binned)</div></div>
        <div class="kpi"><div class="v">${ans.toFixed(2)}</div><div class="l">Answeredness</div></div>
        <div class="kpi"><div class="v">${s.backlog}</div><div class="l">untested (budget)</div></div>
      </div>
      <div class="formula">Coverage     = ${s.n_covered} answered / ${s.n_asks} asks            →  <span class="calc">${s.coverage.toFixed(2)}</span>
Quality      = ${s.n_pooled} pooled / (${s.n_pooled} + ${s.n_binned} binned)          →  <span class="calc">${s.quality.toFixed(2)}</span>   <span class="muted">(${s.n_conflicted||0} contested, ${s.n_refuted||0} refuted, ${s.backlog} untested)</span>
Answeredness = ${s.coverage.toFixed(2)} × ${s.quality.toFixed(2)}                       →  <span class="calc">${ans.toFixed(2)}</span>
${prev?`Progress     = (Δcov ${dcov} + Δpooled ${dpool}) / $${(s.cost-prev.cost).toFixed(2)}         →  <span class="calc">${s.progress.toFixed(4)}</span> per $`:'Progress     = — (first checkpoint)'}</div>
      ${s.stalled?`<div class="small" style="color:var(--amber)">⚠ STALLED — progress ~0 but coverage &lt; 1 (shallow saturation): the loop spawns deeper directions rather than stopping.</div>`:''}
      ${s.uncovered&&s.uncovered.length?`<div class="small muted">uncovered asks: ${s.uncovered.map(esc).join(' · ')}</div>`:''}
      <div class="small muted">open directions=${s.n_open} · evidence items=${s.n_evidence||0} · unsourced rate ${(s.unsourced||0).toFixed(2)}</div>
    </div></details>`;
  });
  html+=`<h2>Convergence test</h2><div class="card small">STOP ⟺ <b>Coverage = 100%</b> AND <b>nothing untested</b> AND <b>Progress ≈ 0</b>.
   Progress ≈ 0 with coverage &lt; 1 is NOT done — it's shallow saturation, and the loop digs deeper instead.
   ${sn.length&&sn[sn.length-1].coverage>=0.999?'This run answered every ask.':'This run ended on <b>budget</b> with the question not fully answered.'}</div>`;
  $('#v-checkpoints').innerHTML=html;
})();

// ===== HOW =====
$('#v-how').innerHTML=`
  <h2>The algorithm (Blackboard architecture)</h2>
  <div class="card mono small" style="white-space:pre-wrap;line-height:1.7">
INIT   required_fields = FIELDS(question)
       prior           = PRIOR(question)            # parametric knowledge + candidate answers + terms
       candidate answers → HYPOTHESES → SCREEN → DEEP TEST   # test what the model thinks it knows
       survivors        → seed research directions
       glossary        = parallel GROUND(term)      # nail terminology

LOOP   (until the budget is exhausted OR converged)
  ├─ PLAN      the AGENT ranks the open directions and allocates $ across them
  │              harness clamps each to a ceiling (share of the round's pot) — ceiling only, no floor
  ├─ EXPLORE   parallel, each direction capped at exactly its allocation → HYPOTHESES + new directions
  ├─ SCREEN    stage 1, EVERY hypothesis: a quick search — does this hold up at all?  (cheap)
  ├─ DEEP TEST stage 2, EVERY hypothesis that passed: hunt evidence AND counter-examples
  │              supported & uncontradicted → POOL
  │              conflicted / refuted       → BIN (kept, with the reason) + re-investigation direction
  ├─ corroborate  independent evidence raises binned hypotheses; past the threshold they RESURFACE
  └─ checkpoint  measure → EVALUATE(draft) → corrective directions; test convergence

FINAL  report built from the POOL, with the BIN reported alongside → answer.md</div>
  <h2>Why the data structures matter</h2>
  <div class="card small">
   <p><b>Direction</b> (the frontier) makes exploration explicit state — nothing is "surfaced but forgotten" —
   and now also carries the money the agent chose to put behind it.
   <b>Hypothesis</b> is the unit of belief: a falsifiable proposition with a status, a verdict, and a
   confidence. <b>Evidence</b> is one sourced statement with a <code>stance</code>, so a hypothesis's
   support balance is a count over independent sources, and contradicting evidence is first-class rather
   than something the model can quietly omit.</p>
   <p><b>Nothing is discarded.</b> A hypothesis that fails the screen, is refuted, or stays contested goes
   to the BIN with its reason — it stays in the ledger, appears in the report, and later corroborating
   evidence can pull it back out for another test.</p>
   <p><b>Testing is never rationed.</b> There is no promotion gate, no beam width, and no error budget
   deciding what gets checked. Every hypothesis is screened; everything that passes is deep-tested. The
   only thing that can stop a test is the total budget running out — and when that happens the untested
   remainder is disclosed rather than silently dropped.</p>
  </div>
  <h2>This run</h2>
  <div class="card small">${R.round} rounds · ${hyps.length} hypotheses (${byStatus('pooled')} pooled,
   ${byVerdict('conflicted')} contested, ${byVerdict('refuted')} refuted, ${byStatus('proposed')+byStatus('screened')} untested) ·
   ${dirs.length} directions · ${Object.keys(evAll).length} evidence items over ${uniqSrc.size} distinct sources ·
   $${R.budget.spent.toFixed(2)} spent.</div>`;

// init
show((location.hash||'#overview').slice(1));
</script></body></html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
