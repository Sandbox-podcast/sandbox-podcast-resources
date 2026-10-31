"""Durable StoryTelling Generator projects in the existing factory store."""
from __future__ import annotations

import math
import uuid
import json
import re
from pathlib import Path

from .contracts import digest, iso, utcnow


DEFAULTS = {"language": "français", "audience": "public curieux non spécialiste",
            "duration_minutes": 20, "format": "16:9", "resolution": "1080p",
            "narration": "une voix narrative"}


def frame(store, brief, *, now=None):
    if not isinstance(brief, dict):
        raise ValueError("Le brief doit être un objet JSON.")
    topic = brief.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Un sujet est requis.")
    story_id = brief.get("story_id") or str(uuid.uuid4())
    if not isinstance(story_id, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}",story_id):
        raise ValueError("Identifiant d'histoire invalide.")
    for key in ("notes", "mandatory", "exclusions", "creative_references"):
        if key in brief and not isinstance(brief[key], str):
            raise ValueError(f"{key} doit être du texte.")
    for key in ("links", "documents", "media"):
        if key in brief and (not isinstance(brief[key], list) or any(not isinstance(v, str) or not v.strip() for v in brief[key])):
            raise ValueError(f"{key} doit être une liste de chaînes non vides.")
    choices = {"mode": {"documentary", "fiction", "mixed"},
               "autonomy": {"autonomous", "editorial_review"}}
    for key, values in choices.items():
        if key in brief and (not isinstance(brief[key], str) or brief[key] not in values):
            raise ValueError(f"Valeur invalide pour {key}.")
    budget = brief.get("budget")
    if budget is not None:
        if (not isinstance(budget, dict) or isinstance(budget.get("limit"), bool)
                or not isinstance(budget.get("limit"), (int, float))
                or not math.isfinite(budget["limit"]) or budget["limit"] < 0
                or not isinstance(budget.get("currency"), str) or not re.fullmatch(r"[A-Z]{3}",budget["currency"])):
            raise ValueError("Budget explicite : limite positive ou nulle et devise requises.")
        credits=budget.get("browser_credit_limit")
        if credits is not None and (type(credits) is not int or credits<0):
            raise ValueError("storytelling_browser_credit_limit_required")
    questions = []
    if "mode" not in brief:
        questions.append({"field": "mode", "question": "Quel type de récit ?", "choices": ["documentary", "fiction", "mixed"], "recommendation": "documentary"})
    if "autonomy" not in brief:
        questions.append({"field": "autonomy", "question": "Quand valider le récit ?", "choices": ["autonomous", "editorial_review"], "recommendation": "editorial_review"})
    if budget is None:
        questions.append({"field": "budget", "question": "Quel plafond de dépense et quelle devise ?", "choices": [], "recommendation": None})
    if brief.get("audio_workflow")=="elevenlabs_browser" and (budget or {}).get("browser_credit_limit") is None:
        questions.append({"field":"browser_credit_limit","question":"Quel plafond de crédits ElevenLabs utiliser dans le navigateur ?","choices":[],"recommendation":None})
    if brief.get("audio_workflow")=="voicestudio" and not any(
            isinstance(s,dict) and isinstance(s.get("voice"),dict) and s["voice"].get("provider")=="voicestudio" for s in (brief.get("speakers") or {}).values()):
        questions.append({"field":"speakers","question":"Quel profil Voice Studio utiliser pour la narration ?","choices":[],"recommendation":None,
                          "action":"python -m youtube_growth.factory voicestudio profiles"})
    data = {**DEFAULTS, **store.setting("storytelling_preferences",{}), **brief, "topic": topic.strip(), "story_id": story_id}
    duration=data.get("duration_minutes")
    if type(duration) not in (int,float) or not math.isfinite(duration) or not .25<=duration<=120:
        raise ValueError("storytelling_duration_invalid")
    if data.get("format") not in {"16:9","9:16"}:
        raise ValueError("storytelling_format_invalid")
    if data.get("audio_workflow","system") not in {"system","voicestudio","elevenlabs_browser","configured"}:
        raise ValueError("storytelling_audio_workflow_invalid")
    if data.get("audio_workflow")=="elevenlabs_browser" and not data.get("speakers"):
        data["speakers"]={"narrator":{"name":"Narrateur","voice":{"provider":"elevenlabs_browser","name":"Voix choisie dans ElevenLabs","authorization":"Voix autorisée de l'espace ElevenLabs connecté."}}}
    revision = digest(data)
    record = {"story_id": story_id, "revision": revision, "brief": data, "questions": questions,
              "status": "needs_framing" if questions else "framed",
              "production_status": "ready" if not questions else "needs_framing", "source_policy": "untrusted_content"}
    from .local_lock import local_lock
    with local_lock(_directory(store,story_id)),store.transaction():
        previous=store.get("storytelling",story_id)
        store.put("storytelling_revision", story_id + ":" + revision, record, now=now)
        store.put("storytelling", story_id, record, now=now)
        project=store.get("storytelling_project",story_id)
        if project and previous and previous["revision"]!=revision:
            project["previous_result"]={k:project[k] for k in ("revision","preview","export","manifest") if k in project}
            for key in ("preview","export","audio","timeline","manifest","approval","estimate","browser_requests"):
                project.pop(key,None)
            project["status"]="brief_changed"
            store.put("storytelling_project",story_id,project,now=now)
        store.event("storytelling_framed", story_id, {"revision": revision, "status": record["status"]}, now=now)
        if data.get("remember_preferences") is True:
            store.set_setting("storytelling_preferences",{k:data[k] for k in ("language","audience","duration_minutes","format","resolution","narration","tone") if k in data})
    return record


def _directory(store, story_id):
    return store.directory/"storytelling"/digest(story_id)[:24]


def _write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise ValueError("storytelling_immutable_file_changed")
    else:
        with path.open("x",encoding="utf-8") as stream:
            stream.write(content)
    return path


def _record(store, story_id):
    row=store.get("storytelling",story_id)
    if not row:
        raise ValueError("storytelling_unknown_project")
    return row


def _dependencies(script,scene,sources):
    voice_refs={}
    media_refs={shot["source_id"] for shot in scene["shots"] if shot.get("source_id")}
    for line in scene["utterances"]:
        if line.get("recording",{}).get("source_id"):media_refs.add(line["recording"]["source_id"])
        voice=script["speakers"][line["speaker_id"]]["voice"]
        current={k:v for k,v in voice.items() if k!="recordings"}
        if line["utterance_id"] in voice.get("recordings",{}):
            ref=voice["recordings"][line["utterance_id"]]
            current["recording"]=ref
            if ref.get("source_id"):media_refs.add(ref["source_id"])
        voice_refs[line["utterance_id"]]=current
    facts=[f for f in script["facts"] if f["fact_id"] in scene.get("fact_ids",[])]
    sound=scene.get("sound",{})
    for cue in ([sound["music"]] if sound.get("music") else [])+sound.get("effects",[]):
        if cue.get("source_id"):media_refs.add(cue["source_id"])
    for fact in facts:media_refs.update(fact.get("source_ids",[]))
    return {"voices":voice_refs,"facts":facts,"continuity":script["continuity"],
            "sources":{s["source_id"]:s["sha256"] for s in sources if s["source_id"] in media_refs}}


def _sources(store,row):
    from .storytelling_sources import import_sources
    from .storytelling_render import checked
    project=store.get("storytelling_project",row["story_id"]) or {}
    if project.get("brief_revision")==row["revision"] and project.get("sources"):
        checked(project["sources"].get("artifacts",[]))
        return project["sources"]
    return import_sources(row["brief"],_directory(store,row["story_id"])/"sources"/row["revision"])


def import_script(store,story_id,script,*,now=None,_locked=False,expected_revision=None):
    if not _locked:
        from .local_lock import local_lock
        with local_lock(_directory(store,story_id)):
            return import_script(store,story_id,script,now=now,_locked=True,expected_revision=expected_revision)
    from .storytelling_contracts import validate_script
    from .storytelling_render import artifact, checked
    row=_record(store,story_id)
    sources=_sources(store,row)
    if sources.get("blockers"):
        raise ValueError("storytelling_sources_blocked")
    value=validate_script(script,sources["sources"])
    if value["story_id"]!=story_id or value["mode"]!=row["brief"].get("mode"):
        raise ValueError("storytelling_script_project_mismatch")
    if value.get("budget") != row["brief"].get("budget"):
        raise ValueError("storytelling_script_budget_mismatch")
    previous=store.get("storytelling_project",story_id) or {}
    if expected_revision is not None and previous.get("script_revision")!=expected_revision:
        raise ValueError("storytelling_script_changed_reload")
    if previous.get("script"):
        checked([previous["script"]])
        old=json.loads(Path(previous["script"]["path"]).read_text(encoding="utf-8"))
        locked=previous.get("locked_scenes",[])
        before={s["scene_id"]:s for s in old["scenes"]}
        after={s["scene_id"]:s for s in value["scenes"]}
        if any(before.get(k)!=after.get(k) for k in locked):
            raise ValueError("storytelling_scene_locked")
        old_sources=previous.get("sources",{}).get("sources",[])
        if any(_dependencies(old,before[k],old_sources)!=_dependencies(value,after[k],sources["sources"]) for k in locked):
            raise ValueError("storytelling_scene_dependency_locked")
    revision=digest(value)
    path=_write(_directory(store,story_id)/"scripts"/(revision+".json"),value)
    project={"story_id":story_id,"brief_revision":row["revision"],"script_brief_revision":row["revision"],"sources":sources,
             "script":artifact(path),"script_revision":revision,"status":"script_ready",
             "locked_scenes":previous.get("locked_scenes",[]),"artifacts":sources.get("artifacts",[])+[artifact(path)]}
    with store.transaction():
        store.put("storytelling_project",story_id,project,now=now)
        store.put("storytelling_script",story_id+":"+revision,project,now=now)
        store.event("storytelling_script_imported",story_id,{"revision":revision},now=now)
    return project


def control(store,story_id,action,*,scene_id=None,now=None,_locked=False):
    if action not in {"pause","cancel","resume"} and not _locked:
        from .local_lock import local_lock
        with local_lock(_directory(store,story_id)):
            return control(store,story_id,action,scene_id=scene_id,now=now,_locked=True)
    row=_record(store,story_id)
    project=store.get("storytelling_project",story_id) or {}
    if action in {"pause","cancel","resume"}:
        store.put("storytelling_control",story_id,{"status":{"pause":"paused","cancel":"cancelled","resume":"active"}[action]},now=now)
    elif action=="approve":
        if not project.get("script_revision") or project.get("brief_revision")!=row["revision"]:
            raise ValueError("storytelling_current_script_required")
        project["approval"]={"revision":project["script_revision"],"at":iso(now or utcnow())}
        store.put("storytelling_project",story_id,project,now=now)
    elif action in {"lock","unlock"}:
        if not project.get("script"):
            raise ValueError("storytelling_current_script_required")
        script=json.loads(Path(project["script"]["path"]).read_text(encoding="utf-8"))
        if scene_id not in {s["scene_id"] for s in script["scenes"]}:
            raise ValueError("storytelling_unknown_scene")
        locked=set(project.get("locked_scenes",[]))
        locked.add(scene_id) if action=="lock" else locked.discard(scene_id)
        project["locked_scenes"]=sorted(locked)
        store.put("storytelling_project",story_id,project,now=now)
    else:
        raise ValueError("storytelling_unknown_action")
    store.event("storytelling_"+action,story_id,{"scene_id":scene_id},now=now)
    return {"status":"saved"}


def regenerate(store,story_id,scene_id,utterance_id,*,now=None,_locked=False):
    if not _locked:
        from .local_lock import local_lock
        with local_lock(_directory(store,story_id)):
            return regenerate(store,story_id,scene_id,utterance_id,now=now,_locked=True)
    project=store.get("storytelling_project",story_id) or {}
    if not project.get("script"):
        raise ValueError("storytelling_current_script_required")
    script=json.loads(Path(project["script"]["path"]).read_text(encoding="utf-8"))
    scene=next((s for s in script["scenes"] if s["scene_id"]==scene_id),None)
    if scene is None:
        raise ValueError("storytelling_unknown_scene")
    utterance=next((u for u in scene["utterances"] if u["utterance_id"]==utterance_id),None)
    if utterance is None:
        raise ValueError("storytelling_unknown_utterance")
    utterance["generation_version"]=utterance.get("generation_version",1)+1
    scene["version"]+=1
    return import_script(store,story_id,script,now=now,_locked=True)


def audio_inputs(script,sources):
    from copy import deepcopy
    result=deepcopy(script)
    source_map={s["source_id"]:s for s in sources}
    def recording(ref):
        source=source_map.get(ref.get("source_id"))
        if not source:
            raise ValueError("storytelling_recording_source_missing")
        return {"path":source["path"],"sha256":source["sha256"]}
    for speaker in result["speakers"].values():
        voice=speaker["voice"]
        if voice["provider"]=="recordings":
            voice["recordings"]={key:recording(value) for key,value in voice.get("recordings",{}).items()}
    for scene in result["scenes"]:
        for utterance in scene["utterances"]:
            if utterance.get("recording"):
                utterance["recording"]=recording(utterance["recording"])
        sound=scene.get("sound",{})
        for cue in ([sound["music"]] if sound.get("music") else [])+sound.get("effects",[]):
            if cue.get("provider")=="recordings":
                cue.update(recording(cue))
    return result


def enqueue(store,story_id,*,now=None):
    row=_record(store,story_id)
    if row["questions"]:
        raise ValueError("storytelling_framing_required")
    project=store.get("storytelling_project",story_id) or {}
    control_row=store.get("storytelling_control",story_id) or {}
    if control_row.get("status") in {"paused","cancelled"}:
        raise ValueError("storytelling_resume_required")
    payload={"story_id":story_id,"revision":row["revision"],"script_revision":project.get("script_revision")}
    # A resumed blocked job retains the same identity and retry limits.
    job_id=store.enqueue("storytelling",None,payload,now=now)
    job=next(j for j in store.jobs() if j["id"]==job_id)
    if job["status"] in {"blocked","failed"}:
        store.retry(job_id,now=now)
    return {"status":"queued" if job["status"]!="completed" else "completed","job_id":job_id}


def run(store,config,story_id,*,now=None,synthetic=False):
    from .local_lock import local_lock
    from .storytelling_editorial import draft,review
    from .storytelling_audio import produce_audio,estimate_audio
    from .storytelling_render import build_timeline,render,artifact,checked
    root=_directory(store,story_id)
    def save(project,status,**extra):
        project.update(status=status,updated_at=iso(now or utcnow()),**extra)
        if project.get("request_path"):
            path=Path(project["request_path"])
            if path.is_file() and path.resolve().is_relative_to(store.directory):
                item=artifact(path)
                project["artifacts"]=[a for a in project.get("artifacts",[]) if a["path"]!=item["path"]]+[item]
        store.put("storytelling_project",story_id,project,now=now)
        return project
    def interrupt():
        status=(store.get("storytelling_control",story_id) or {}).get("status")
        if status in {"paused","cancelled"}:
            raise ValueError("storytelling_"+status)
    with local_lock(root):
        row=_record(store,story_id)
        project=store.get("storytelling_project",story_id) or {"story_id":story_id,"stages":{}}
        try:
            interrupt()
            if row["questions"]:
                return save(project,"needs_framing",questions=row["questions"])
            sources=_sources(store,row)
            save(project,"sources",sources=sources,brief_revision=row["revision"],artifacts=sources.get("artifacts",[]))
            if sources.get("blockers"):
                return save(project,"blocked",blockers=sources["blockers"])
            if not project.get("script") or project.get("script_brief_revision")!=row["revision"]:
                result=draft(store,config,row["brief"],sources["sources"],root/"drafts"/row["revision"])
                if result.get("status")=="blocked":
                    return save(project,"blocked",blockers=[result.get("blocker","editorial_model_missing")],request_path=result.get("request_path"))
                script=result.get("script",result)
                project=import_script(store,story_id,script,now=now,_locked=True)
            checked([project["script"]])
            script=json.loads(Path(project["script"]["path"]).read_text(encoding="utf-8"))
            from .storytelling_contracts import validate_script
            validate_script(script,sources["sources"])
            project["script_brief_revision"]=row["revision"]
            # Editorial approval covers spoken text and the storyboard in the script.
            if row["brief"]["autonomy"]=="editorial_review" and project.get("approval",{}).get("revision")!=project["script_revision"]:
                return save(project,"awaiting_approval")
            if row["brief"]["autonomy"]=="autonomous" and script["mode"]!="fiction":
                verdict=review(store,config,script,sources["sources"],root/"reviews"/project["script_revision"])
                project["editorial_review"]=verdict
                if verdict.get("status")!="ready" or not verdict.get("passed"):
                    return save(project,"editorial_verification_required",blockers=verdict.get("issues") or [verdict.get("blocker","editorial_review_failed")],request_path=verdict.get("request_path"))
            interrupt()
            prepared=audio_inputs(script,sources["sources"])
            if row["brief"].get("audio_workflow")=="elevenlabs_browser":
                from .storytelling_browser import prepare
                browser=prepare(store,script,root/"browser")
                project["browser_requests"]=browser["requests"]
                project["artifacts"]=project.get("artifacts",[])+browser.get("artifacts",[])
                if not browser["ready"]:
                    return save(project,"awaiting_browser_audio",blockers=[])
                prepared=browser["script"]
            estimate=estimate_audio(prepared,config)
            save(project,"audio",blockers=[],estimate=estimate)
            audio=produce_audio(store,config,prepared,root/"audio",synthetic=synthetic)
            interrupt()
            target=row["brief"]["duration_minutes"]*60
            if audio["duration_seconds"]>target*1.15:
                from .generation import generate
                request={"task":"storytelling_duration_revision","instructions":"Révise le scénario intégral pour respecter la durée cible. Réduis répétitions et développements secondaires sans inventer de faits, couper les éléments déterminants ni accélérer la voix. Préserve identifiants des éléments inchangés, budget, locuteurs et sources. Réponds avec le scénario JSON intégral conforme au contrat fourni.",
                         "script":script,"measured_seconds":audio["duration_seconds"],"target_seconds":target,"untrusted_sources":sources["sources"]}
                from .storytelling_contracts import SCRIPT_SCHEMA
                request["response_schema"]=SCRIPT_SCHEMA
                result=generate(request,config,root/"duration-revisions"/project["script_revision"])
                if result.get("status")=="blocked":
                    return save(project,"duration_revision_required",audio=audio,request_path=result.get("request_path"),blockers=["storytelling_duration_exceeded"],duration_target_seconds=target)
                revised=result.get("script",result)
                old_words=sum(len(u["text"].split()) for s in script["scenes"] for u in s["utterances"])
                new_words=sum(len(u.get("text","").split()) for s in revised.get("scenes",[]) for u in s.get("utterances",[]))
                if new_words>=old_words:
                    return save(project,"duration_revision_required",blockers=["storytelling_duration_revision_no_progress"],duration_target_seconds=target)
                project=import_script(store,story_id,revised,now=now,_locked=True)
                enqueue(store,story_id,now=now)
                return save(project,"revised",blockers=[])
            timeline=build_timeline(script,audio,sources["sources"])
            revision=digest({"script":project["script_revision"],"audio":audio,"timeline":timeline})
            directory=root/"runs"/revision
            timeline_path=_write(directory/"timeline.json",timeline)
            save(project,"rendering",audio=audio,timeline=artifact(timeline_path),artifacts=sources.get("artifacts",[])+[project["script"],artifact(timeline_path)]+audio.get("artifacts",[]))
            portrait=row["brief"].get("format")=="9:16"
            preview=render(script,timeline,audio,directory/"preview",draft=True,portrait=portrait)
            interrupt()
            export=render(script,timeline,audio,directory/"export",portrait=portrait)
            interrupt()
            artifacts=sources.get("artifacts",[])+[project["script"],artifact(timeline_path)]+audio.get("artifacts",[])+preview["artifacts"]+export["artifacts"]
            manifest={"version":1,"story_id":story_id,"revision":revision,"brief":row["brief"],"script":project["script"],"timeline":artifact(timeline_path),"sources":sources["sources"],"audio":audio,"preview":preview,"export":export,"artifacts":artifacts,"synthetic":synthetic,"human_review":"pending"}
            manifest_path=_write(directory/"manifest.json",manifest)
            result=save(project,"completed",revision=revision,preview=preview,export=export,manifest=artifact(manifest_path),artifacts=artifacts+[artifact(manifest_path)],blockers=[])
            store.put("storytelling_run",story_id+":"+revision,result,now=now)
            store.event("storytelling_completed",story_id,{"revision":revision,"duration_seconds":timeline["duration_seconds"]},now=now)
            return result
        except Exception as error:
            # Provider details and arbitrary exception messages never enter state.
            safe=str(error) if isinstance(error,ValueError) and re.fullmatch(r"[a-z][a-z0-9_]{1,100}",str(error)) else type(error).__name__
            save(project,"paused" if safe=="storytelling_paused" else "cancelled" if safe=="storytelling_cancelled" else "blocked",blockers=[safe])
            raise
