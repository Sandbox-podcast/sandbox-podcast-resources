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
STORYTELLING_PAGE = Path(__file__).with_name("storytelling.html").read_text(encoding="utf-8")


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
            if parsed.path in {"/", "/storytelling"}:
                page = PAGE if parsed.path == "/" else STORYTELLING_PAGE
                content = page.replace("__TOKEN__", json.dumps(token)).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(content)
            elif parsed.path == "/api/storytelling":
                with Store(directory) as store:
                    from .storytelling_audio import budget_status
                    projects=store.records("storytelling_project")
                    voice_bindings=store.records("storytelling_browser_voice")
                    for project in projects:
                        project["voice_bindings"]=[v for v in voice_bindings if v["story_id"]==project["story_id"]]
                        if project.get("browser_requests"):
                            project["browser_requests"]=[store.get("storytelling_browser_request",r["request_id"]) or r for r in project["browser_requests"]]
                        script=project.get("script")
                        if script:
                            from .media import fingerprint
                            path=Path(script["path"])
                            if path.is_relative_to(directory.resolve()) and path.is_file() and fingerprint(path)==script["sha256"]:
                                project["script_data"]=json.loads(path.read_text(encoding="utf-8"))
                    stories=store.records("storytelling")
                    budgets={r["story_id"]:budget_status(store,r["story_id"],r["brief"]["budget"]) for r in stories if r["brief"].get("budget")}
                    for story in stories:
                        if story["story_id"] not in budgets:continue
                        rows=[r for r in store.records("storytelling_browser_request") if r["story_id"]==story["story_id"] and r["status"] in {"submitted","unknown","completed"}]
                        budgets[story["story_id"]]["browser"]={"limit":story["brief"]["budget"].get("browser_credit_limit"),
                            "committed":sum(r.get("actual_credits") if r.get("actual_credits") is not None else r.get("estimated_credits",0) for r in rows),
                            "confirmed":sum(r.get("actual_credits") or 0 for r in rows),"unknown_calls":sum(r.get("actual_credits") is None for r in rows)}
                    self.send_json({"stories":stories,"projects":projects,"budgets":budgets,
                                    "jobs":[j for j in store.jobs() if j["kind"]=="storytelling"],
                                    "capabilities":{"editorial_model":bool(config.get("generation",{}).get("local_command")),
                                                    "elevenlabs_enabled":config.get("storytelling",{}).get("elevenlabs",{}).get("enabled",False)}})
            elif parsed.path.startswith("/storytelling-file/"):
                parts=parsed.path.split("/")
                if len(parts)!=4 or not re.fullmatch(r"[a-f0-9]{64}",parts[3]):
                    return self.send_json({"error":"Fichier absent."},404)
                with Store(directory) as store:
                    project=store.get("storytelling_project",unquote(parts[2])) or {}
                files=project.get("artifacts",[])
                if project.get("request_path"):
                    from .media import fingerprint
                    request_path=Path(project["request_path"])
                    if request_path.is_relative_to(directory.resolve()) and request_path.is_file():
                        files=files+[{"path":str(request_path),"sha256":fingerprint(request_path)}]
                item=next((r for r in files if r["sha256"]==parts[3]),None)
                if not item:
                    return self.send_json({"error":"Fichier absent."},404)
                path=Path(item["path"]).resolve()
                if not path.is_relative_to(directory.resolve()) or not path.is_file():
                    return self.send_json({"error":"Fichier hors du stockage."},403)
                from .media import fingerprint
                if fingerprint(path)!=item["sha256"]:
                    return self.send_json({"error":"Fichier modifié."},409)
                return self.send_file(path)
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
                if not 0 < length < (16 * 1024 * 1024 if self.path.startswith("/api/storytelling") else 4096):
                    raise ValueError("Requête invalide.")
                # Drain the bounded body before refusing auth; unread bytes can
                # reset the connection and discard the 403 response on Windows.
                body = self.rfile.read(length)
                hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
                if self.headers.get("Host") not in hosts or (self.headers.get("Origin") and self.headers["Origin"] not in {"http://"+host for host in hosts}):
                    return self.send_json({"error": "Origine refusée."}, 403)
                if self.path not in {"/api/action", "/api/storytelling", "/api/storytelling/action"} or self.headers.get("X-Factory-Token") != token or self.headers.get("Content-Type") != "application/json":
                    return self.send_json({"error": "Action refusée."}, 403)
                def reject_constant(value):
                    raise ValueError("Nombre JSON non fini interdit : "+value)
                data = json.loads(body, parse_constant=reject_constant)
                if self.path == "/api/storytelling":
                    from .storytelling import frame
                    with Store(directory) as store:
                        result = frame(store, data)
                    return self.send_json(result)
                if self.path == "/api/storytelling/action":
                    from .storytelling import enqueue,control,import_script,regenerate,frame
                    if not isinstance(data,dict):
                        raise ValueError("Objet JSON requis.")
                    with Store(directory) as store:
                        action=data.get("action")
                        story_id=data.get("story_id")
                        if not isinstance(story_id,str):
                            raise ValueError("Histoire requise.")
                        if action=="run":
                            result=enqueue(store,story_id)
                        elif action=="upload":
                            import base64
                            import hashlib
                            row=store.get("storytelling",story_id)
                            if not row:
                                raise ValueError("Histoire inconnue.")
                            name=data.get("name","")
                            suffix=Path(name).suffix.lower() if isinstance(name,str) else ""
                            allowed={".txt",".md",".json",".docx",".pdf",".png",".jpg",".jpeg",".webp",".mp4",".mov",".wav",".mp3",".m4a"}
                            if suffix not in allowed or not isinstance(data.get("base64"),str):
                                raise ValueError("Type de fichier refusé.")
                            try:
                                content=base64.b64decode(data["base64"],validate=True)
                            except (ValueError,TypeError):
                                raise ValueError("Contenu du fichier invalide.") from None
                            if not 0<len(content)<=10*1024*1024:
                                raise ValueError("Le fichier doit peser au plus 10 Mio. Pour un média plus lourd, fournis son chemin local.")
                            sha=hashlib.sha256(content).hexdigest()
                            folder=directory.resolve()/"storytelling"/"uploads"
                            folder.mkdir(parents=True,exist_ok=True)
                            path=folder/(sha+suffix)
                            if not path.exists():
                                with path.open("xb") as stream:stream.write(content)
                            from .media import fingerprint
                            if fingerprint(path)!=sha:
                                raise ValueError("Copie du fichier modifiée.")
                            result={"path":str(path),"sha256":sha}
                        elif action=="regenerate":
                            result=regenerate(store,story_id,data.get("scene_id"),data.get("utterance_id"))
                        elif action in {"browser_attempt","browser_complete","browser_unknown"}:
                            from .storytelling_browser import record_attempt,complete_request,mark_unknown
                            request_id=data.get("request_id")
                            browser_row=store.get("storytelling_browser_request",request_id) if isinstance(request_id,str) else None
                            if not browser_row or browser_row["story_id"]!=story_id:
                                raise ValueError("Demande navigateur inconnue pour cette histoire.")
                            if action=="browser_attempt":
                                brief=store.get("storytelling",story_id)["brief"]
                                result=record_attempt(store,request_id,brief.get("budget",{}).get("browser_credit_limit"),data.get("estimated_credits"),data.get("evidence"))
                            elif action=="browser_unknown":
                                result=mark_unknown(store,request_id,data.get("evidence"))
                            else:
                                result=complete_request(store,request_id,data.get("path"),data.get("provenance"),data.get("actual_credits"))
                                project=store.get("storytelling_project",story_id) or {}
                                current=project.get("browser_requests",[])
                                if current and all((store.get("storytelling_browser_request",r["request_id"]) or {}).get("status")=="completed" for r in current):
                                    enqueue(store,story_id)
                        elif action=="refresh_sources":
                            import uuid
                            row=store.get("storytelling",story_id)
                            if not row:raise ValueError("Histoire inconnue.")
                            brief={**row["brief"],"source_revision":str(uuid.uuid4())}
                            result=frame(store,brief)
                        elif action=="script":
                            result=import_script(store,story_id,data.get("script"))
                        elif action=="edit_scene":
                            from .media import fingerprint
                            project=store.get("storytelling_project",story_id) or {}
                            if project.get("script_revision")!=data.get("revision"):
                                raise ValueError("Le scénario a changé ; recharge la page.")
                            script_ref=project["script"]
                            if fingerprint(Path(script_ref["path"]))!=script_ref["sha256"]:
                                raise ValueError("Scénario modifié hors de la factory.")
                            script=json.loads(Path(script_ref["path"]).read_text(encoding="utf-8"))
                            scene=next((s for s in script["scenes"] if s["scene_id"]==data.get("scene_id")),None)
                            edits=data.get("texts",{})
                            if scene is None or not isinstance(edits,dict) or set(edits)!={u["utterance_id"] for u in scene["utterances"]}:
                                raise ValueError("Répliques de la scène requises.")
                            for utterance in scene["utterances"]:
                                utterance["text"]=edits[utterance["utterance_id"]]
                            scene["version"]+=1
                            result=import_script(store,story_id,script,expected_revision=data.get("revision"))
                        else:
                            result=control(store,story_id,action,scene_id=data.get("scene_id"))
                            if action in {"resume","approve"}:
                                result=enqueue(store,story_id)
                    return self.send_json(result)
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
            except (ValueError, KeyError, TypeError, RuntimeError) as error:
                self.send_json({"error": str(error)}, 400)

        def send_file(self,path):
            total=path.stat().st_size
            start,end,partial=0,total-1,False
            requested=self.headers.get("Range")
            if requested:
                match=re.fullmatch(r"bytes=(\d+)-(\d*)",requested)
                if not match:
                    return self.send_json({"error":"Intervalle invalide."},416)
                start=int(match[1]);end=min(int(match[2]) if match[2] else total-1,total-1)
                if start>end or start>=total:
                    return self.send_json({"error":"Intervalle invalide."},416)
                partial=True
            self.send_response(206 if partial else 200)
            self.send_header("Content-Type","text/vtt; charset=utf-8" if path.suffix.lower()==".vtt" else mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Cache-Control","no-store")
            self.send_header("Accept-Ranges","bytes")
            if path.suffix.lower() not in {".mp4",".wav",".mp3",".png",".jpg",".jpeg",".vtt"}:
                self.send_header("Content-Disposition",'attachment; filename="'+path.name+'"')
            self.send_header("Content-Length",str(end-start+1))
            if partial:
                self.send_header("Content-Range",f"bytes {start}-{end}/{total}")
            self.end_headers()
            try:
                with path.open("rb") as stream:
                    stream.seek(start);remaining=end-start+1
                    while remaining:
                        block=stream.read(min(remaining,1024*1024))
                        if not block:break
                        self.wfile.write(block);remaining-=len(block)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):
                pass
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(directory: Path, config: dict, *, port=8765, with_worker=False):
    import threading
    stop=threading.Event()
    def work():
        from .runtime import run_once
        while not stop.is_set():
            try:
                with Store(directory) as store:
                    result=run_once(store,config)
                if result["status"]=="idle":stop.wait(2)
            except Exception:
                stop.wait(2)
    thread=threading.Thread(target=work,daemon=True) if with_worker else None
    if thread:thread.start()
    server = make_server(directory, config, port=port)
    print(f"http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    finally:
        stop.set()
        if thread:thread.join(timeout=3)
        server.server_close()
