"""Export a user-selected trend into the StoryTelling Generator framing contract."""
from __future__ import annotations

from pathlib import Path
import re

from ..factory.contracts import digest
from ..factory.research import verify
from .core import instant, load_json, stamp, write_json
from .production import fingerprint, select

CONTRACT = {"name": "storytelling-frame", "version": 1,
            "reference_pr": "https://github.com/Sandbox-podcast/sandbox-podcast-resources/pull/19",
            "reference_revision": "2e0266f522530174f618641425a8f10b63722c7c"}


def _text(value, field, maximum=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError("Texte requis : "+field)
    return value.strip()


def _research(path, now):
    if not path:
        return None
    path = Path(path).resolve(strict=True)
    dossier = load_json(path)
    result = verify(dossier, base=path.parent, now=now)
    if result["blockers"]:
        raise ValueError("Recherche à compléter avant transfert : "+", ".join(result["blockers"]))
    if not any(s["kind"] == "primary" for s in result["sources"]):
        raise ValueError("Une source primaire lue est requise pour préparer le récit documentaire.")
    return result


def check_handoff(directory):
    directory = Path(directory).resolve()
    manifest = load_json(directory / "handoff.json")
    for artifact in manifest["artifacts"]:
        path = (directory / artifact["path"]).resolve(strict=True)
        if not path.is_relative_to(directory) or fingerprint(path) != artifact["sha256"]:
            raise ValueError("Dossier de transfert modifié ; exporter une nouvelle version.")
    return manifest


def handoff(store, rank, cfg, *, run_id, selected_by, selection_note, research_path=None,
            angle=None, voice_name=None, browser_credit_limit=0, now=None):
    """Prepare files only: selection never approves a script, starts audio or mutates factory state."""
    if not run_id:
        raise ValueError("Le run_id explicite est requis pour retrouver la tendance choisie.")
    actor = _text(selected_by, "selected_by", 150)
    note = _text(selection_note, "selection_note")
    if type(browser_credit_limit) is not int or browser_credit_limit < 0:
        raise ValueError("Plafond de crédits navigateur entier positif ou nul requis.")
    report, topic = select(store, rank, run_id)
    story_id = "trend-"+topic["topic_id"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", story_id) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", report["run_id"]):
        raise ValueError("Identifiant de tendance ou d'analyse invalide.")
    current = stamp(now)
    if instant(report["collected_at"]) > instant(current):
        raise ValueError("Une tendance collectée dans le futur ne peut pas être sélectionnée.")
    angle = _text(angle or topic["concept"], "angle")
    if voice_name is not None:
        voice_name = _text(voice_name, "voice_name", 200)
    research = _research(research_path, current)
    stale = (instant(current)-instant(report["collected_at"])).total_seconds() > cfg["window_days"]*86400
    selection = {"run_id": report["run_id"], "topic_id": topic["topic_id"], "rank": rank,
                 "selected_by": actor, "selection_note": note,
                 "scope": "topic_selection_only", "script_approved": False, "production_started": False}
    # Selection time is recorded on first export; identical input reuses that immutable transfer.
    research_revision = {k: v for k, v in research.items() if k != "verified_at"} if research else None
    revision = digest({"selection": selection, "topic": topic, "research": research_revision,
                       "angle": angle, "voice_name": voice_name, "browser_credit_limit": browser_credit_limit,
                       "max_video_seconds": cfg["max_video_seconds"], "stale": stale, "contract": CONTRACT})[:24]
    directory = store.directory / "storytelling" / report["run_id"] / topic["topic_id"] / revision
    if (directory / "handoff.json").exists():
        return directory, check_handoff(directory)
    if directory.exists():
        raise ValueError("Export incomplet déjà présent : conserver ses fichiers et vérifier l'interruption avant de reprendre.")
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "sources").mkdir()
    selection["selected_at"] = current
    write_json(directory / "selection.json", selection)
    write_json(directory / "trend-evidence.json", {"synthetic": report["synthetic"], "collected_at": report["collected_at"], "opportunity": topic,
                                                 "meaning": "Signaux d'intérêt observés ; aucune vérification automatique des affirmations du sujet."})
    documents = [str(directory / "trend-evidence.json")]
    metadata = {documents[0]: {"title": "Observations de veille YouTube datées", "kind": "user_notes",
                              "rights": "Recherche documentaire ; aucun droit de réutilisation des médias liés.", "generated": False}}
    source_map, facts, source_links = {}, [], []
    if research:
        for source in research["sources"]:
            # Different URLs can share identical text while retaining distinct source metadata.
            target = directory / "sources" / (digest(source["source_id"])[:20]+"-"+source["sha256"]+".txt")
            raw = Path(source["snapshot"]).read_bytes()
            with target.open("xb") as stream:
                stream.write(raw)
            if fingerprint(target) != source["sha256"]:
                raise ValueError("Source modifiée pendant le transfert.")
            ref = str(target)
            documents.append(ref)
            # This is the ID calculated by PR19's import_sources for a local document.
            imported_id = "source-"+digest(str(target.resolve()))[:20]
            source_map[source["source_id"]] = {"source_id": imported_id, "url": source["url"],
                                                "snapshot": "sources/"+target.name, "sha256": source["sha256"],
                                                "retrieved_at": source["retrieved_at"], "kind": source["kind"]}
            metadata[ref] = {"title": source["title"], "kind": source["kind"], "rights": source["rights"], "generated": False}
            source_links.append(source["url"])
        for claim in research["claims"]:
            references = [{"source_id": source_map[r["source_id"]]["source_id"], "quote": r["quote"]} for r in claim.get("references", [])]
            facts.append({"fact_id": "fact-"+digest(claim["claim_id"])[:20], "original_claim_id": claim["claim_id"], "text": claim["text"], "kind": claim["kind"],
                          "status": "source_supported" if references and claim["kind"] == "fact" else "uncertain",
                          "source_ids": list(dict.fromkeys(r["source_id"] for r in references)), "quotes": references,
                          "research_verification": claim.get("verification", {}),
                          "notice": "Conserver la nature du propos ; la revue du scénario StoryTelling reste à réaliser."})
    write_json(directory / "source-map.json", source_map)
    documents.append(str(directory / "source-map.json"))
    metadata[documents[-1]] = {"title": "Provenance des documents : URL, dates et identifiants StoryTelling", "kind": "user_notes",
                              "rights": "Registre de provenance local.", "generated": True}
    write_json(directory / "research-facts.json", {"facts": facts, "status": "documentary_material_not_an_approved_script"})
    documents.append(str(directory / "research-facts.json"))
    metadata[documents[-1]] = {"title": "Faits documentaires et réserves pour le récit", "kind": "user_notes",
                              "rights": "Dossier éditorial local ; citations réservées à la recherche.", "generated": True}
    remaining = []
    if not research:
        remaining.append("Lire et archiver des sources primaires ; fournir le dossier de recherche pour compléter le transfert.")
    if not voice_name:
        remaining.append("Choisir une voix ElevenLabs autorisée avant la production sonore.")
    if browser_credit_limit == 0:
        remaining.append("Plafond de crédits ElevenLabs à zéro : aucune génération sonore autorisée avant choix explicite.")
    remaining.append("Rédiger puis examiner le scénario et le storyboard dans StoryTelling ; la sélection du sujet ne les approuve pas.")
    if stale:
        remaining.insert(0, "Actualiser la veille : la collecte sélectionnée dépasse la fenêtre d'analyse.")
    duration = min(cfg["max_video_seconds"], max(120, topic["duration_seconds_estimate"]))
    notes = ("Tendance choisie par l'utilisateur, pas scénario approuvé.\n"
             "Angle de travail proposé : "+angle+"\n"
             "Lire les documents joints : les observations de veille mesurent l'intérêt, les textes primaires soutiennent le récit.\n"
             "Le dossier research-facts relie les citations aux source_id calculés lors de l'import. Les statuts source_supported ne valent pas confirmation indépendante.\n"
             "Les titres, l'accroche et la miniature du rapport sont des propositions à examiner, pas des faits.\n")
    if report["synthetic"]:
        notes = "DÉMONSTRATION SYNTHÉTIQUE : aucune actualité réelle.\n"+notes
    brief = {"story_id": story_id, "topic": topic["subject"], "notes": notes,
             "mandatory": "Conserver les citations, dates, unités, incertitudes et la distinction entre faits et analyses. Expliquer une idée utile au public français.",
             "exclusions": "Aucune rumeur présentée comme certaine, archive inventée, parole attribuée sans source, tournage ou montage complexe.",
             "creative_references": "Actualité expliquée en voix off, schémas originaux et textes courts. Une illustration ne constitue pas une preuve.",
             "links": [], "documents": documents, "media": [], "source_metadata": metadata, "media_rights": {},
             "mode": "documentary", "autonomy": "editorial_review", "language": "français",
             "audience": "public francophone curieux non spécialiste", "duration_minutes": duration/60,
             "format": "16:9", "resolution": "1080p", "tone": "pédagogique, direct et accessible",
             "narration": "une voix narrative", "audio_workflow": "elevenlabs_browser",
             "budget": {"limit": 0, "currency": "EUR", "browser_credit_limit": browser_credit_limit},
             "trend_origin": {**selection, "contract": CONTRACT, "synthetic": report["synthetic"],
                              "collected_at": report["collected_at"], "score": topic["score"], "confidence": topic["confidence"]}}
    if voice_name:
        brief["speakers"] = {"narrator": {"name": "Narrateur", "voice": {"provider": "elevenlabs_browser", "name": voice_name,
                               "authorization": "Voix désignée par l'utilisateur ; droits à contrôler avant génération."}}}
    write_json(directory / "storytelling-brief.json", brief)
    bundle_note = ["# Tendance sélectionnée pour StoryTelling", "", "DÉMONSTRATION SYNTHÉTIQUE" if report["synthetic"] else "Observations réelles ; aucune prédiction de vues.", "",
                   "Sujet : "+topic["subject"], "", "Angle proposé : "+angle, "",
                   "Choix : "+actor+" ; "+note+" ; "+current, "", f"Analyse : {report['run_id']} ; sujet : {topic['topic_id']} ; rang à la sélection : {rank}.", "",
                   "Fichiers d'entrée : storytelling-brief.json, documents locaux, métadonnées des sources et preuves datées.", "",
                   "URL conservées comme références, sans nouvelle lecture réseau à l'import :", ""]
    bundle_note += ["- "+url for url in dict.fromkeys([*source_links, *(r["url"] for r in topic["evidence"])])]
    bundle_note += ["", "Décisions et vérifications restantes :", "", *["- "+line for line in remaining], "",
                    "Après installation de la PR #19, depuis sa racine avec PYTHONPATH configuré :", "", "```powershell",
                    'python -m youtube_growth.factory storytelling-frame "'+str(directory / "storytelling-brief.json")+'"',
                    "python -m youtube_growth.factory storytelling-run "+story_id, "```", "",
                    "Garder le même --state-dir pour le serveur, le worker et les deux commandes. L'import ne constitue pas une validation du scénario."]
    (directory / "handoff.md").write_text("\n".join(bundle_note)+"\n", encoding="utf-8")
    artifacts = [{"path": p.relative_to(directory).as_posix(), "sha256": fingerprint(p)} for p in sorted(directory.rglob("*")) if p.is_file()]
    result = {"version": 1, "contract": CONTRACT, "story_id": story_id, "selection": selection,
              "status": "ready_for_storytelling_framing" if research and not stale else "research_required",
              "brief_path": str(directory / "storytelling-brief.json"), "remaining_decisions": remaining,
              "synthetic": report["synthetic"], "artifacts": artifacts}
    write_json(directory / "handoff.json", result)
    return directory, result
