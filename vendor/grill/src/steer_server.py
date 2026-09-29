#!/usr/bin/env python3
"""A tiny, self-contained steering server for a live run (DESIGN_interactive.md, Phase 5).

It is a thin frontend over the same file inbox the orchestrator drains — no framework, no external
deps, stdlib `http.server` only. Point it at a run-dir and an inbox path, open the browser console,
and steer:

    # terminal 1 — the run, draining the inbox each round
    python3 -m src.cli --question-file Q.txt --run-dir OUT --budget 50 \
        --steer-inbox OUT/steer_inbox.json

    # terminal 2 — the steering console
    python3 -m src.steer_server --run-dir OUT --inbox OUT/steer_inbox.json --port 8765
    # → open http://localhost:8765

Routes:
    GET  /                → the console (src/ui/steer.html)
    GET  /ledger          → OUT/ledger.json        (directions, claims, scope, assumptions)
    GET  /digest          → OUT/steer_request.md   (the round digest)
    GET  /run             → OUT/run.json           (budget + snapshots)
    GET  /artifacts       → OUT/artifacts.json     (the deliverables index + git log)
    GET  /qa              → OUT/qa_log.jsonl       (the Q&A thread — answers come back here)
    GET  /file?p=<rel>    → a file from OUT/workspace (charts, CSVs — path-confined)
    POST /steer           → append a SteerEvent (or array) to the inbox (merged, never clobbered)

The orchestrator's FileInbox drains + clears the inbox each round; POST merges into whatever is
pending so a concurrent human append is never lost.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

UI_HTML = Path(__file__).with_name("ui") / "steer.html"


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl(path: Path) -> list:
    """Append-only log → list. A half-written final line (the agent may be appending as we read)
    is skipped rather than failing the whole request."""
    out = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return out


def make_handler(run_dir: Path, inbox: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):        # quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def _file(self, path: Path, ctype: str) -> None:
            if not path.exists():
                self._send(404, b'{"error":"not found yet"}', "application/json")
                return
            self._send(200, path.read_bytes(), ctype)

        def do_OPTIONS(self):
            self._send(204, b"", "text/plain")

        def do_GET(self):
            route = self.path.split("?", 1)[0]
            if route in ("/", "/index.html"):
                if UI_HTML.exists():
                    self._send(200, UI_HTML.read_bytes(), "text/html; charset=utf-8")
                else:
                    self._send(500, b"steer.html missing", "text/plain")
            elif route == "/ledger":
                self._file(run_dir / "ledger.json", "application/json")
            elif route == "/run":
                self._file(run_dir / "run.json", "application/json")
            elif route == "/digest":
                self._file(run_dir / "steer_request.md", "text/markdown; charset=utf-8")
            elif route == "/artifacts":
                self._file(run_dir / "artifacts.json", "application/json")
            elif route == "/qa":
                # The Q&A thread. This is the ONLY return path from the agent to the human: POST
                # /steer is fire-and-forget into a file inbox, and the agent (not this server) holds
                # the proxy credentials, so an answer cannot come back on the POST itself.
                self._send(200, json.dumps({"qa": _read_jsonl(run_dir / "qa_log.jsonl")}).encode(),
                           "application/json")
            elif route == "/file":
                self._workspace_file()
            else:
                self._send(404, b'{"error":"unknown route"}', "application/json")

        def _workspace_file(self) -> None:
            """Serve one file out of the run's workspace. The path is resolved and confined to the
            workspace root, so `?p=../../.env` cannot escape it."""
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            rel = (q.get("p") or [""])[0]
            root = (run_dir / "workspace").resolve()
            try:
                target = (root / rel).resolve()
            except (OSError, ValueError):
                self._send(400, b'{"error":"bad path"}', "application/json")
                return
            if not rel or (target != root and root not in target.parents) or not target.is_file():
                self._send(404, b'{"error":"no such file"}', "application/json")
                return
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            # Workspace files are MODEL-authored. Anything the browser would execute on this
            # origin (HTML, SVG) is served as plain text instead of rendered.
            if ctype in ("text/html", "image/svg+xml", "application/xhtml+xml"):
                ctype = "text/plain"
            if ctype.startswith("text/") or ctype == "application/json":
                ctype += "; charset=utf-8"
            self._send(200, target.read_bytes(), ctype)

        def do_POST(self):
            if self.path.split("?", 1)[0] != "/steer":
                self._send(404, b'{"error":"unknown route"}', "application/json")
                return
            n = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(n) if n else b""
            try:
                event = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                self._send(400, b'{"error":"bad json"}', "application/json")
                return
            new = event if isinstance(event, list) else [event]
            pending = _read_json(inbox)
            if not isinstance(pending, list):
                pending = []
            pending.extend(new)
            inbox.write_text(json.dumps(pending, indent=2), encoding="utf-8")
            body = json.dumps({"ok": True, "queued": len(new), "pending": len(pending)}).encode()
            self._send(200, body, "application/json")

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser(description="Live steering console for a methodology-v2 run")
    ap.add_argument("--run-dir", required=True, help="the run's output dir (holds ledger.json etc)")
    ap.add_argument("--inbox", default="", help="steer inbox path (default: <run-dir>/steer_inbox.json)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()

    run_dir = Path(a.run_dir)
    inbox = Path(a.inbox) if a.inbox else run_dir / "steer_inbox.json"
    if not inbox.exists():
        inbox.write_text("[]", encoding="utf-8")
    httpd = ThreadingHTTPServer((a.host, a.port), make_handler(run_dir, inbox))
    print(f"steering console → http://{a.host}:{a.port}   (run-dir {run_dir}, inbox {inbox})")
    print("start the run with:  --steer-inbox", inbox)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
