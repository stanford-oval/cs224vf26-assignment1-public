#!/usr/bin/env python3
"""Build a single self-contained HTML showing every EXPLORE agent's trajectory.

For each EXPLORE task in a v2 run it parses the codex transcript into an ordered
action list (web searches, source fetches/reads, shell/compute steps) and pairs it
with the agent's schema output (claims + new directions + dead_end) and its cost.

    python3 -m methodology_v2.build_explore_html <run_dir> <out.html>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RATE = 10.0 / 1_000_000


def parse_prompt(p: str) -> dict:
    d = {"direction": "", "rationale": ""}
    m = re.search(r"DIRECTION TO EXPLORE:\n(.*?)\n\(why this matters: (.*?)\)", p, re.S)
    if m:
        d["direction"] = m.group(1).strip()
        d["rationale"] = m.group(2).strip()
    else:
        m = re.search(r"DIRECTION TO EXPLORE:\n(.*?)\n\n", p, re.S)
        if m:
            d["direction"] = m.group(1).strip()
    return d


def parse_transcript(text: str) -> dict:
    lines = text.splitlines()
    plan, actions = [], []
    tokens = 0
    in_prompt = True
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        s = ln.strip()
        # plan bullets appear right after the prompt, before the first exec
        if in_prompt and re.match(r"^(→|•|\*)\s+", s) and len(actions) == 0:
            plan.append(re.sub(r"^(→|•|\*)\s+", "", s))
        if s == "exec":
            in_prompt = False
            cmd = lines[i + 1].strip() if i + 1 < n else ""
            kind, label = classify_exec(cmd)
            if kind:
                actions.append({"k": kind, "t": label})
            i += 1
        else:
            m = re.match(r"^web search:\s*(.+)$", s)
            if m:
                in_prompt = False
                q = m.group(1).strip()
                if q.startswith("http"):
                    actions.append({"k": "read", "t": q})
                else:
                    actions.append({"k": "search", "t": q})
        mt = re.match(r"^tokens used$", s)
        if mt and i + 1 < n:
            try:
                tokens = int(lines[i + 1].strip().replace(",", ""))
            except ValueError:
                pass
        i += 1
    return {"plan": plan, "actions": actions, "tokens": tokens, "usd": round(tokens * RATE, 3)}


def classify_exec(cmd: str):
    c = cmd.lower()
    url = re.search(r"https?://[^\s\"']+", cmd)
    if "curl" in c or "wget" in c:
        return "read", (url.group(0) if url else cmd[:90])
    if "printf" in c or "echo" in c:
        return "", ""          # the agent narrating — skip
    if "python" in c or "<<'py'" in c or "<<py" in c:
        return "compute", "python: extract/check numbers"
    if url:
        return "read", url.group(0)
    return "shell", cmd[:90]


def main() -> int:
    run_dir = Path(sys.argv[1])
    out = Path(sys.argv[2])
    tasks = sorted((run_dir / "tasks").glob("*explore_r*"),
                   key=lambda p: tuple(int(x) for x in re.findall(r"r(\d+)_(\d+)", p.name)[0]))
    agents = []
    for td in tasks:
        m = re.search(r"explore_r(\d+)_(\d+)", td.name)
        rnd, idx = int(m.group(1)), int(m.group(2))
        prm = parse_prompt((td / "prompt.txt").read_text(encoding="utf-8")) if (td / "prompt.txt").exists() else {}
        tr = parse_transcript((td / "transcript.log").read_text(encoding="utf-8", errors="replace")) \
            if (td / "transcript.log").exists() else {"plan": [], "actions": [], "usd": 0, "tokens": 0}
        out_json = {}
        if (td / "out.json").exists():
            try:
                out_json = json.loads((td / "out.json").read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                out_json = {}
        claims = []
        for c in (out_json.get("claims") or []):
            s = (c.get("evidence") or [{}])[0]
            claims.append({
                "text": c.get("text", ""), "stance": c.get("stance", ""),
                "aspects": c.get("aspects", []),
                "numbers": {x["metric"]: x["value"] for x in (c.get("numbers") or []) if "metric" in x},
                "conf": c.get("confidence", 0),
                "src": {"a": (s.get("authors") or [""])[0], "y": s.get("year"),
                        "t": s.get("title", ""), "loc": s.get("doi") or s.get("pmid") or s.get("pmc") or s.get("url")},
            })
        nd = [{"q": d.get("question_text", ""), "p": d.get("promise"), "c": d.get("est_cost")}
              for d in (out_json.get("new_directions") or [])]
        agents.append({
            "round": rnd, "idx": idx, "name": td.name,
            "direction": prm.get("direction", ""), "rationale": prm.get("rationale", ""),
            "plan": tr["plan"], "actions": tr["actions"][:120], "n_actions": len(tr["actions"]),
            "usd": tr["usd"], "claims": claims, "new_dirs": nd,
            "dead_end": bool(out_json.get("dead_end")),
            "killed": not bool(out_json),
        })

    payload = json.dumps(agents, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    html = TEMPLATE.replace("/*__DATA__*/", payload)
    out.write_text(html, encoding="utf-8")
    n_search = sum(sum(1 for a in ag["actions"] if a["k"] == "search") for ag in agents)
    n_read = sum(sum(1 for a in ag["actions"] if a["k"] == "read") for ag in agents)
    n_claims = sum(len(ag["claims"]) for ag in agents)
    print(f"wrote {out} ({len(html)//1024} KB) · {len(agents)} explore agents · "
          f"{n_search} searches · {n_read} reads · {n_claims} claims")
    return 0


TEMPLATE = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>EXPLORE agents — trajectory</title>
<style>
:root{--bg:#0e1116;--panel:#161b22;--panel2:#1c232c;--line:#2a323d;--ink:#e6edf3;--mut:#8b97a6;
--blue:#4aa3ff;--teal:#3fc7c0;--green:#56d364;--amber:#e3b341;--red:#f85149;--violet:#bc8cff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,Segoe UI,Inter,sans-serif}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace}
header{padding:16px 22px;border-bottom:1px solid var(--line)}header h1{margin:0;font-size:17px}
header p{margin:6px 0 0;color:var(--mut);font-size:12.5px;max-width:1000px}
.wrap{display:grid;grid-template-columns:300px 1fr;height:calc(100vh - 72px)}
.side{border-right:1px solid var(--line);overflow:auto;background:var(--panel)}
.rgroup{padding:8px 12px 2px;color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.05em;position:sticky;top:0;background:var(--panel);border-bottom:1px solid var(--line)}
.item{padding:9px 12px;border-bottom:1px solid #1d242d;cursor:pointer}
.item:hover{background:#11161d}.item.on{background:#10202e;border-left:3px solid var(--blue)}
.item .d{font-size:12.5px;line-height:1.35;max-height:54px;overflow:hidden}
.item .m{color:var(--mut);font-size:11px;margin-top:3px}
.main{overflow:auto;padding:18px 22px}
.dir{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:14px}
.dir .lab{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
h3{font-size:12.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em;margin:18px 0 8px}
.pill{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px;border:1px solid var(--line)}
.b-blue{color:var(--blue);border-color:#2b4a6b}.b-teal{color:var(--teal);border-color:#1f5350}.b-green{color:var(--green);border-color:#235c2c}
.b-amber{color:var(--amber);border-color:#5c4a1f}.b-violet{color:var(--violet);border-color:#43356b}.b-mut{color:var(--mut)}.b-red{color:var(--red);border-color:#5c2626}
.tl{position:relative;margin-left:6px;padding-left:20px;border-left:2px solid var(--line)}
.act{position:relative;margin:0 0 7px;font-size:12.5px}
.act:before{content:"";position:absolute;left:-27px;top:5px;width:9px;height:9px;border-radius:50%;border:2px solid var(--bg);background:var(--mut)}
.act.search:before{background:var(--blue)}.act.read:before{background:var(--teal)}.act.compute:before{background:var(--amber)}.act.shell:before{background:var(--violet)}
.act .ico{display:inline-block;width:54px;color:var(--mut);font-size:10.5px;text-transform:uppercase}
.act a{color:var(--teal);text-decoration:none}.act a:hover{text-decoration:underline}
.claim{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--green);border-radius:8px;padding:11px 13px;margin:8px 0}
.claim.refutes{border-left-color:var(--red)}.claim.neutral{border-left-color:var(--mut)}
.num{display:inline-block;background:#11202e;color:var(--teal);border:1px solid #1f3a4d;border-radius:5px;padding:0 6px;margin:2px 4px 0 0;font-size:11px}
.asp{display:inline-block;background:#1a1430;color:var(--violet);border:1px solid #352a5c;border-radius:5px;padding:0 6px;margin:2px 4px 0 0;font-size:11px}
.src{color:var(--blue);font-size:12px}.src a{color:var(--blue)}
.nd{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:9px 12px;margin:6px 0;font-size:12.5px}
.kpi{display:inline-block;margin-right:14px}.kpi b{font-size:16px}
.plan{background:#0b0f14;border:1px dashed var(--line);border-radius:8px;padding:8px 12px;color:var(--mut);font-size:12.5px}
.muted{color:var(--mut)}
</style></head><body>
<header><h1>EXPLORE agents — research trajectory</h1>
<p>Each EXPLORE is one <span class="mono">codex exec</span> in research mode (native web_search + network shell, reasoning effort xhigh), forced to emit schema JSON. It plans → searches/reads real sources → returns <b>claims</b> (with SourceRef + numbers) + <b>new directions</b>. Pick an agent on the left.</p></header>
<div class="wrap"><div class="side" id="side"></div><div class="main" id="main"></div></div>
<script>
const A = /*__DATA__*/;
const $=s=>document.querySelector(s);
const esc=s=>(s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const loc=l=>!l?'':(l.startsWith('http')?l:(/^10\./.test(l)?'https://doi.org/'+l:(/^\d+$/.test(l)?'https://pubmed.ncbi.nlm.nih.gov/'+l:(l.startsWith('PMC')?'https://www.ncbi.nlm.nih.gov/pmc/articles/'+l:l))));
// sidebar grouped by round
const side=$('#side'); let cur=0; const byR={};
A.forEach((a,i)=>{(byR[a.round]=byR[a.round]||[]).push(i)});
Object.keys(byR).sort((x,y)=>x-y).forEach(r=>{
  const h=document.createElement('div');h.className='rgroup';h.textContent='Round '+r+' · '+byR[r].length+' explore agents';side.appendChild(h);
  byR[r].forEach(i=>{const a=A[i];const el=document.createElement('div');el.className='item';el.id='it'+i;
    el.innerHTML=`<div class="d">${esc(a.direction).slice(0,150)}</div>
      <div class="m">${a.killed?'<span class="b-red">killed</span> · ':''}${a.claims.length} claims · ${a.n_actions} actions · $${a.usd.toFixed(2)}</div>`;
    el.onclick=()=>sel(i);side.appendChild(el);});
});
function sel(i){cur=i;document.querySelectorAll('.item').forEach(e=>e.classList.remove('on'));$('#it'+i).classList.add('on');render(A[i]);}
function render(a){
  const acts=a.actions.map(x=>`<div class="act ${x.k}"><span class="ico">${x.k}</span>${x.k==='read'&&x.t.startsWith('http')?`<a href="${esc(x.t)}" target="_blank">${esc(x.t).slice(0,110)}</a>`:esc(x.t).slice(0,140)}</div>`).join('');
  const claims=a.claims.map(c=>{
    const nums=Object.entries(c.numbers).map(([k,v])=>`<span class="num">${esc(k)}=${esc(v)}</span>`).join('');
    const asp=c.aspects.map(x=>`<span class="asp">${esc(x)}</span>`).join('');
    const s=c.src,L=loc(s.loc);
    return `<div class="claim ${c.stance}"><div>${esc(c.text)}</div>
      <div style="margin-top:6px">${asp}${nums}</div>
      <div class="src" style="margin-top:6px">${s.t?`${esc(s.a||'?')} ${s.y?'('+s.y+')':''} — ${esc(s.t).slice(0,90)} ${L?`<a href="${esc(L)}" target="_blank">↗</a>`:''}`:'<span class="b-red">no source</span>'} · <span class="muted">conf ${(+c.conf).toFixed(2)} · ${c.stance}</span></div></div>`;
  }).join('');
  const nds=a.new_dirs.map(d=>`<div class="nd">${esc(d.q)} <span class="muted mono">· promise ${d.p} · est $${d.c}</span></div>`).join('')||'<div class="muted">none</div>';
  $('#main').innerHTML=`
    <div class="dir"><div class="lab">Round ${a.round} · explore agent #${a.idx} · ${a.killed?'<span class="b-red">killed (no output)</span>':'$'+a.usd.toFixed(2)}</div>
      <div style="margin-top:6px"><b>Direction explored:</b> ${esc(a.direction)}</div>
      ${a.rationale?`<div class="muted" style="margin-top:4px">why: ${esc(a.rationale)}</div>`:''}</div>
    <div>
      <span class="kpi"><b>${a.claims.length}</b> <span class="muted">claims</span></span>
      <span class="kpi"><b>${a.actions.filter(x=>x.k==='search').length}</b> <span class="muted">searches</span></span>
      <span class="kpi"><b>${a.actions.filter(x=>x.k==='read').length}</b> <span class="muted">reads/fetches</span></span>
      <span class="kpi"><b>${a.new_dirs.length}</b> <span class="muted">new directions</span></span>
      <span class="kpi"><b>${a.dead_end?'yes':'no'}</b> <span class="muted">dead-end</span></span>
    </div>
    ${a.plan.length?`<h3>Plan</h3><div class="plan">${a.plan.map(esc).join('<br>')}</div>`:''}
    <h3>Research trajectory (${a.n_actions} actions${a.n_actions>a.actions.length?', showing first '+a.actions.length:''})</h3>
    <div class="tl">${acts||'<span class="muted">no actions parsed</span>'}</div>
    <h3>Output → claims (${a.claims.length})</h3>${claims||'<span class="muted">none</span>'}
    <h3>Output → new directions spawned (${a.new_dirs.length})</h3>${nds}`;
}
sel(0);
</script></body></html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
