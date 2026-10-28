"""Loopback operational view backed by the same persistent SQLite database."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
import re
import secrets
from urllib.parse import parse_qs, unquote, urlparse

from .store import Store
from .runtime import status
from .contracts import iso, utcnow

PAGE = Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")


def make_server(directory: Path, config: dict, *, port=8765):
    token = secrets.token_hex(24)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send_json(self, data, code=200, *, download=False):
            content = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if download:
                self.send_header("Content-Disposition", 'attachment; filename="factory-diagnostic.json"')
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            parsed = urlparse(self.path)
            if self.headers.get("Host") not in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}:
                return self.send_json({"error": "Hôte refusé."}, 403)
            if parsed.path == "/":
                content = PAGE.replace("__TOKEN__", json.dumps(token)).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(content)
            elif parsed.path in {"/api/state", "/api/export"}:
                query = parse_qs(parsed.query)
                with Store(directory) as store:
                    from .monitoring import enrich
                    store.db.execute("BEGIN")
                    try:
                        state = enrich(store, status(store, episode_id=query.get("episode_id", [None])[0], platform=query.get("platform", [None])[0]), config)
                        state["episode_catalog"] = [{"episode_id": ep["episode_id"], "title": ep["title"]} for ep in store.records("episode")]
                    finally:
                        store.db.rollback()
                self.send_json(state, download=parsed.path == "/api/export")
            elif parsed.path.startswith("/thumbnail/"):
                parts = parsed.path.split("/")
                if len(parts) != 5 or parts[4] not in {"320", "160"}:
                    return self.send_json({"error": "Aperçu absent."}, 404)
                with Store(directory) as store:
                    bundle = store.get("thumbnail_bundle", unquote(parts[2]))
                variant = next((v for v in (bundle or {}).get("variants", []) if v["concept_id"] == unquote(parts[3])), None)
                preview = next((p for p in (variant or {}).get("previews", []) if p["kind"] == "preview_"+parts[4]), None)
                if not preview or not Path(preview["path"]).is_file():
                    return self.send_json({"error": "Aperçu absent."}, 404)
                path = Path(preview["path"]).resolve()
                if not path.is_relative_to(directory.resolve()):
                    return self.send_json({"error": "Aperçu hors stockage factory."}, 403)
                from .media import fingerprint
                if fingerprint(path) != preview["sha256"]:
                    return self.send_json({"error": "Aperçu modifié, revue à refaire."}, 409)
                content = path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(content)
            elif parsed.path.startswith("/media/"):
                with Store(directory) as store:
                    asset = store.get("asset", unquote(parsed.path[len("/media/"):]))
                if not asset or not Path(asset["path"]).is_file():
                    return self.send_json({"error": "Média absent."}, 404)
                path = Path(asset["path"]).resolve()
                if not path.is_relative_to(directory.resolve()):
                    return self.send_json({"error": "Média hors stockage factory."}, 403)
                total = path.stat().st_size
                start, end, partial = 0, total-1, False
                requested = self.headers.get("Range")
                if requested:
                    match = re.fullmatch(r"bytes=(\d+)-(\d*)", requested)
                    if not match:
                        return self.send_json({"error": "Intervalle invalide."}, 416)
                    start, end = int(match[1]), min(int(match[2]) if match[2] else total-1, total-1)
                    if start > end or start >= total:
                        return self.send_json({"error": "Intervalle invalide."}, 416)
                    partial = True
                self.send_response(206 if partial else 200)
                self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "video/mp4")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(end-start+1))
                if partial:
                    self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
                self.end_headers()
                try:
                    with path.open("rb") as media:
                        media.seek(start)
                        remaining = end-start+1
                        while remaining:
                            data = media.read(min(remaining, 1024*1024))
                            if not data:
                                break
                            self.wfile.write(data)
                            remaining -= len(data)
                except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self.send_json({"error": "Page absente."}, 404)

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length < 4096:
                    raise ValueError("Requête invalide.")
                # Drain the bounded body before refusing auth; unread bytes can
                # reset the connection and discard the 403 response on Windows.
                body = self.rfile.read(length)
                hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
                if self.headers.get("Host") not in hosts or (self.headers.get("Origin") and self.headers["Origin"] not in {"http://"+host for host in hosts}):
                    return self.send_json({"error": "Origine refusée."}, 403)
                if self.path != "/api/action" or self.headers.get("X-Factory-Token") != token or self.headers.get("Content-Type") != "application/json":
                    return self.send_json({"error": "Action refusée."}, 403)
                def reject_constant(value):
                    raise ValueError("Nombre JSON non fini interdit : "+value)
                data = json.loads(body, parse_constant=reject_constant)
                if not isinstance(data, dict) or not isinstance(data.get("action"), str):
                    raise ValueError("Objet JSON avec une action requis.")
                with Store(directory) as store:
                    if data.get("action") in {"pause", "resume"}:
                        store.set_setting("paused", data["action"] == "pause")
                        store.event("ui_queue_"+data["action"], None, {}, now=utcnow())
                    elif data.get("action") == "retry":
                        if not isinstance(data.get("job_id"), str) or not data["job_id"].strip():
                            raise ValueError("Identifiant de traitement requis.")
                        store.retry(data["job_id"])
                    else:
                        raise ValueError("Action inconnue.")
                self.send_json({"status": "saved"})
            except (ValueError, KeyError, TypeError) as error:
                self.send_json({"error": str(error)}, 400)
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(directory: Path, config: dict, *, port=8765):
    server = make_server(directory, config, port=port)
    print(f"http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
