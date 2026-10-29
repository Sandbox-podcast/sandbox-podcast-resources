"""Automatic local controls with explicit sampling and file-bound evidence."""
from __future__ import annotations

import math
from pathlib import Path
import subprocess
import tempfile

from .contracts import digest
from .local_models import LocalModelError, Ollama
from .media import _load_stage, _save_stage, fingerprint
from ..shorts import _call, _require_media_tools


def object_schema(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


TEXT = {"type": "string", "minLength": 1, "maxLength": 4000}


def samples(source: Path, output: Path, ranges: list[list[float]], interval: int) -> list[dict]:
    source_hash = fingerprint(source)
    ffmpeg, _ = _require_media_tools()
    result = []
    for start, end in ranges:
        if not 0 <= start < end or not math.isfinite(end):
            raise ValueError("Plage d'images locale invalide.")
        count = max(1, math.ceil((end-start)/interval))
        for index in range(count):
            at = start+(end-start)*(index+.5)/count
            identity = {"source_sha256": source_hash, "time_seconds": round(at, 6), "width": 640}
            path = output / (digest(identity)+".jpg")
            receipt = path.with_suffix(".json")
            previous = _load_stage(receipt, identity)
            if previous:
                if fingerprint(path) != previous["sha256"]:
                    raise LocalModelError("local_visual_sample_changed")
                result.append(previous)
                continue
            output.mkdir(parents=True, exist_ok=True)
            if path.exists():
                raise LocalModelError("local_visual_sample_without_receipt")
            _call([ffmpeg, "-nostdin", "-v", "error", "-n", "-ss", str(at), "-i", str(source),
                   "-frames:v", "1", "-vf", "scale=640:-2", str(path)])
            row = {**identity, "path": str(path), "sha256": fingerprint(path), "scope": "point_sample"}
            _save_stage(receipt, identity, row)
            result.append(row)
    if fingerprint(source) != source_hash:
        raise LocalModelError("local_visual_source_changed")
    return result


def review_images(model: Ollama, role: str, rows: list[dict], data: dict, checks: tuple[str, ...]) -> dict:
    if not rows:
        raise LocalModelError("local_visual_review_missing_images")
    check_schema = object_schema({"passed": {"type": "boolean"}, "reason": TEXT})
    schema = object_schema({name: check_schema for name in checks})
    receipts = []
    limit = model.options["maximum_images_per_call"]
    prompt = ("Tu es le relecteur indépendant de la factory SANDBOX. Examine réellement chaque image jointe et les propos source. "
              "Le contrôle porte uniquement sur les images jointes et le texte fourni. Refuse une promesse non soutenue, "
              "un texte illisible, une image trompeuse ou une réserve supprimée. N'invente aucun fait, droit ou intervenant. "
              "Pour chaque critère demandé, fournis passed et une raison précise. En cas d'incertitude substantielle, passed=false.")
    if "french_language" in checks:
        prompt += (" Pour french_language, le public est francophone : les titres, phrases d'image, questions, promesses et textes de réseau fournis "
                   "doivent être en français naturel. Les noms propres et termes techniques courants comme Claude Code, Vibe Coding, LLM ou embeddings "
                   "peuvent rester dans leur langue. Refuse les phrases anglaises ou le mélange artificiel des deux langues, même si leur sens est fidèle. "
                   "Par exemple 'Simulating System Pannes for Robust Testing' et 'Simulated Server Pannes' sont à refuser.")
    if role == "thumbnail_review":
        prompt += (" Examine uniquement target_concept et SES content_evidence : ne lui attribue ni le titre général du candidat ni une autre citation. "
                   "Pour faithfulness, vérifie toutes les affirmations de target_concept, y compris angle et hypothesis : ces champs sont des textes à contrôler, jamais des preuves. "
                   "Un titre prudent ne rend pas fidèle une explication causale inventée dans hypothesis. "
                   "Un changement observé après une action ne démontre pas sa cause. Préserve les incertitudes exprimées et refuse les conditions techniques ajoutées sans paroles correspondantes. "
                   "Une paraphrase fidèle est permise ; la présence des mêmes mots n'est ni nécessaire ni suffisante. "
                   "Une question peut annoncer un débat ouvert effectivement présent : elle n'a pas à être confirmée, réfutée ou définitivement résolue pour être fidèle. "
                   "La photo d'un participant réel illustre la discussion : elle n'a pas à démontrer visuellement toutes ses paroles. "
                   "Pour title_image_complementarity, le texte ajouté doit compléter le titre au lieu de le répéter. Un portrait n'exige aucun schéma ou démonstration ajoutée. "
                   "Juge la lisibilité du texte ajouté et du sujet choisi pour la photo ; une diapositive non choisie comme sujet n'a pas à rester lisible. "
                   "Chaque promesse titre/image doit être soutenue par sa propre citation dans content_evidence. "
                   "Un titre annonçant des limites, risques ou critiques exige une réserve effectivement exprimée ; une simple description d'audit ou de checklist ne suffit pas. "
                   "Refuse un concept fondé seulement sur une annotation technique de recette dans l'image. "
                   "N'ajoute aucun critère d'écoute humaine ou de visionnage continu : ils sont hors de cette revue d'images.")
    if role == "thumbnail_comparison":
        prompt += (" Compare les TROIS couples titre/image entre eux pour distinct_hypotheses, pas une phrase avec sa propre citation. "
                   "Des mécanismes, conséquences ou réserves différents du même passage peuvent être distincts. "
                   "Deux concepts qui inversent seulement les mêmes idées entre titre et phrase ne le sont pas. "
                   "Pour brief_fidelity, vérifie que viewer_question est une question du public et content_promise décrit le contenu de l'extrait. "
                   "Une invitation au spectateur comme 'Découvrez comment', 'Comprendre' ou 'Vous découvrirez' est acceptable. "
                   "La promesse peut résumer le sujet : elle n'a pas à répéter chaque détail des trois concepts. "
                   "Elle doit parler des propos de l'extrait et ne pas promettre la fabrication d'un fichier ou la réponse JSON du modèle. "
                   "Ne demande pas au portrait de démontrer les mécanismes racontés. Vérifie aussi les textes de réseau à partir des paroles conservées. "
                   "Les champs du rédacteur ne sont pas des preuves : seules les paroles conservées et les images le sont.")
    if role == "selection_review":
        prompt += (" Vérifie concrètement les premières et dernières paroles, pas seulement le sujet général. "
                   "Seules source_units sont conservées ; context_before_not_in_cut et context_after_not_in_cut sont HORS MONTAGE. "
                   "Refuse une réponse sans sa question, un début qui dépend du passage précédent, "
                   "une question laissée sans réponse à la fin ou une réserve coupée. Le découpage en blocs réguliers n'est pas une preuve d'autonomie.")
    for offset in range(0, len(rows), limit):
        batch = rows[offset:offset+limit]
        response, evidence = model.complete(role, prompt, {**data, "criteria": list(checks), "images": batch}, schema,
                                            images=[Path(row["path"]) for row in batch], reviewer=True)
        receipts.append({"checks": response, "evidence": evidence, "images": batch})
    return {"passed": all(check["passed"] for row in receipts for check in row["checks"].values()),
            "batches": receipts, "scope": "sampled_images_and_supplied_text", "continuous_viewing": False,
            "human_listening": False}


def title_support(model: Ollama, title: str, rows: list[dict]) -> dict:
    """Audit the title against retained words without the creator's explanation."""
    eligible = [i for i,row in enumerate(rows) if len(row["text"].split()) >= 5]
    if not eligible:
        raise LocalModelError("local_title_spoken_evidence_missing")
    schema = object_schema({"supported": {"type": "boolean"}, "evidence_index": {"enum": eligible}, "reason": TEXT})
    answer, proof = model.complete("title_support",
        "Vérifie uniquement si la promesse précise du titre est réellement développée dans les paroles CONSERVÉES. "
        "Aucun résumé du rédacteur ni contexte externe n'est une preuve. Ne confonds pas un mot commun et le sujet central. "
        "Une paraphrase fidèle est permise. Un titre de discussion ne promet ni cours exhaustif, ni preuve scientifique, ni réponse définitive. "
        "N'exige pas une description du mécanisme interne pour un titre qui rapporte une expérience de refus. "
        "Une question peut annoncer un débat ouvert ; vérifie qu'il est réellement discuté, sans exiger sa résolution. "
        "Refuse toutefois une date, une causalité, une attribution ou une garantie non soutenue, et distingue opinion et fait établi. "
        "Si supported=true, choisis evidence_index de l'unité qui soutient le plus précisément cette promesse. "
        "Ne réécris pas la citation : le programme reprendra ses mots exacts à cet index. "
        "Ne complète pas un propos avec une connaissance externe.",
        {"title_to_verify": title, "kept_speech": [{"index": i, "text": row["text"]} for i,row in enumerate(rows)]}, schema, reviewer=True)
    return {"passed": answer["supported"], "quote": rows[answer["evidence_index"]]["text"] if answer["supported"] else "", "reason": answer["reason"],
            "evidence": proof, "scope": "title_and_literal_kept_words_only", "human_listening": False}


def cut_boundaries(model: Ollama, segments: list[dict], start: float, end: float) -> dict:
    """Focus the critic on literal edges, without a title or creator rationale."""
    kept = [r for r in segments if start <= r['start'] and r['end'] <= end]
    if not kept:raise LocalModelError('local_boundary_spoken_evidence_missing')
    schema = object_schema({'start_status':{'enum':['intact','truncated']},'end_status':{'enum':['intact','truncated']},'reason':TEXT})
    speech=' '.join(r['text'] for r in kept)
    words=speech.split()
    answer,evidence=model.complete('cut_boundaries',
        "Vérifie uniquement les DEUX BORDS du texte intégral d'un extrait oral français. Aucune parole extérieure au fichier n'est fournie. "
        "start_status=intact si le début introduit son sujet sans manquer de mots indispensables. Les amorces orales 'et', 'moi', 'du coup', "
        "'justement', 'donc' et les annonces de sujet sont acceptables : ce ne sont pas des phrases scolaires. "
        "start_status=truncated si la coupe commence réellement au milieu d'une phrase ou sans le sujet indispensable de la réponse. "
        "end_status=intact si la dernière parole est achevée. Un constat ou une liste close suffit, sans résumé final. "
        "'c'est toujours chiant', 'en fait', 'tu vois' ou 'voilà' peuvent conclure naturellement une explication. "
        "end_status=truncated si la toute dernière parole attend encore ses mots suivants pour achever la phrase, "
        "ou si elle amorce explicitement un nouveau point sans son développement. "
        "Ne confonds pas phrase inachevée et grand débat qui pourrait continuer : une phrase achevée reste intacte. "
        "Nommer la notion déjà illustrée juste avant (comme la factorisation après un exemple de duplication de code) conclut l'explication ; ce n'est pas un nouveau point. "
        "Par exemple 'et l'évolution suivante' ou 'ce qui fait que dans la session' attend encore une suite grammaticale. "
        "Ne juge ni le titre, ni le style, ni l'écoute humaine. Lis tout le texte pour distinguer une amorce et une réponse effectivement absente.",
        {'full_kept_speech':speech,'actual_first_words':' '.join(words[:12]),'actual_last_words':' '.join(words[-12:])},schema,reviewer=True)
    checks={edge:answer[edge+'_status']=='intact' for edge in ('start','end')}
    adjudication=None
    if not all(checks.values()):
        edge_schema=object_schema({'verdict':{'enum':['intact','truncated','uncertain']},'reason':TEXT})
        reviews=[]
        for edge,passed in list(checks.items()):
            if passed:continue
            window=words[:90] if edge=='start' else words[-90:]
            task=("Les mots fournis sont DÉJÀ le début d'un extrait. Vérifie seulement si des mots indispensables manquent AVANT cette ouverture. "
                  if edge=='start' else
                  "Les mots fournis sont DÉJÀ la fin d'un extrait. Vérifie seulement si des mots indispensables manquent APRÈS la dernière parole. ")
            second,proof=model.complete('cut_boundary_blind_check',
                task+"On ne te demande jamais de classer le fragment comme début ou fin : la cible est déjà déterminée. "
                "Juge l'achèvement linguistique du bord ciblé ; l'autre extrémité de la fenêtre est interne au fichier et ne doit pas être jugée. "
                "Si des mots grammaticalement indispensables manquent, verdict=truncated. S'ils sont présents, verdict=intact. "
                "Une amorce orale peut ouvrir l'échange. Une phrase de souhait, une réserve, une objection brève, une liste ou un constat peuvent le clore. "
                "Les marqueurs 'tu vois', 'en fait', 'avec ça' peuvent fermer une phrase. La ponctuation ASR n'est pas un critère : son absence n'impose aucune suite. "
                "Le locuteur peut toujours continuer à parler : l'ignorance de son intention n'est pas une incertitude sur la grammaire. "
                "Il n'y a pas à résoudre le débat ni à obtenir tous les détails d'un exemple. "
                "Une amorce explicite telle que 'et l'évolution suivante' ou 'ce qui fait que dans la session' attend encore des mots. "
                "Réserve uncertain aux seuls cas où les mots eux-mêmes ne permettent pas de juger leur achèvement.",
                {'kept_speech_window':' '.join(window),
                 'actual_boundary_words':' '.join(words[:12] if edge=='start' else words[-12:])},edge_schema)
            checks[edge]=second['verdict']=='intact'
            reviews.append({'edge':edge,**second,'evidence':proof})
        adjudication={'checks':reviews,'scope':'blind_second_model_without_first_opinion',
                      'reason':' / '.join(r['reason'] for r in reviews)}
    return {**answer,'passed':all(checks.values()),'evidence':evidence,'adjudication':adjudication,
            'scope':'literal_edges_with_independent_refusal_check','human_listening':False}


def audio_correspondence(source: Path, asset: dict) -> dict:
    try:
        import numpy as np
    except ImportError as error:
        raise LocalModelError("numpy_dependency_missing") from error
    directory = Path(asset["path"]).parent.parent / "local-audio-cache"
    reference_path = pcm_audio(source, directory)
    observed_path = pcm_audio(Path(asset["path"]), directory)
    reference_audio = np.memmap(reference_path, dtype="<f4", mode="r")
    observed_audio = None
    try:
        observed_audio = np.memmap(observed_path, dtype="<f4", mode="r")
        return _compare_audio_arrays(reference_audio, observed_audio, asset)
    finally:
        reference_audio._mmap.close()
        if observed_audio is not None:
            observed_audio._mmap.close()


def _compare_audio_arrays(reference_audio, observed_audio, asset):
    from ..thematic_qa import correlation
    rows = []
    for cut in asset["cuts"]:
        length = cut["source_end_seconds"]-cut["source_start_seconds"]
        if length < .5:
            raise LocalModelError("audio_cut_too_short_to_verify")
        duration = min(2, length/2)
        for fraction in (.1, .5, .9):
            inside = max(.05, min(length-duration-.05, (length-duration)*fraction))
            source_at = cut["source_start_seconds"]+inside
            output_at = cut["output_start_seconds"]+inside
            reference_start = round(source_at*4000)
            reference = reference_audio[reference_start:reference_start+round(duration*4000)]
            padding = min(.05, output_at)
            output_start = round((output_at-padding)*4000)
            observed = observed_audio[output_start:output_start+round((duration+padding+.05)*4000)]
            scores = []
            if len(reference) == 0 or len(observed) < len(reference):
                rows.append({"source_seconds": source_at, "passed": False, "reason": "audio_window_incomplete"})
                continue
            for offset in range(0, max(0, len(observed)-len(reference))+1):
                score = correlation(reference, observed[offset:offset+len(reference)])
                if score is not None:
                    lag = offset/4-padding*1000
                    scores.append((score, -abs(lag), lag))
            score, _, lag = max(scores) if scores else (None, None, None)
            rows.append({"source_seconds": source_at, "output_seconds": output_at,
                         "correlation": score, "lag_ms": lag,
                         "passed": score is not None and score >= .90 and abs(lag) <= 30})
    result = {"passed": bool(rows) and all(row["passed"] for row in rows), "samples": rows,
              "scope": "three_audio_windows_per_cut_from_complete_pcm_decode", "human_listening": False}
    return result


def pcm_audio(source: Path, directory: Path) -> Path:
    """Decode once from the start: AAC input seeking can change the resampler phase."""
    identity = {"version": 1, "source_sha256": fingerprint(source), "sample_rate": 4000, "format": "f32le"}
    path = directory / (digest(identity)+".pcm")
    receipt = path.with_suffix(".json")
    previous = _load_stage(receipt, identity)
    if previous:
        if fingerprint(path) != previous["sha256"]:
            raise LocalModelError("local_pcm_cache_changed")
        return path
    directory.mkdir(parents=True, exist_ok=True)
    ffmpeg, _ = _require_media_tools()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, suffix=".pcm", delete=False) as output:
            temporary = Path(output.name)
            result = subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-i", str(source), "-vn", "-ac", "1", "-ar", "4000", "-f", "f32le", "-"],
                                    stdout=output, stderr=subprocess.PIPE)
        if result.returncode or temporary.stat().st_size == 0 or temporary.stat().st_size % 4:
            raise LocalModelError("local_pcm_decode_failed")
        expected = fingerprint(temporary)
        if fingerprint(source) != identity["source_sha256"]:
            raise LocalModelError("local_pcm_input_changed")
        if path.exists():
            if fingerprint(path) != expected:
                raise LocalModelError("local_pcm_cache_changed")
        else:
            temporary.replace(path)
        _save_stage(receipt, identity, {"path": str(path), "sha256": expected})
        return path
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def technical_checks(asset: dict) -> dict:
    qa = asset.get("qa", {})
    duration = asset.get("duration_seconds") or sum(c["source_end_seconds"]-c["source_start_seconds"] for c in asset["cuts"])
    scan = qa.get("signals", qa.get("details", {}))
    # The renderer's technical result is already file-bound, but never implies editorial QA.
    boundaries = qa.get("subtitle_boundary_warnings", [])
    subtitle = Path(asset["subtitle_path"])
    return {"decode_and_dimensions": qa.get("technical") == "passed",
            "subtitle_file": subtitle.is_file() and bool(subtitle.read_text(encoding="utf-8").strip()),
            "subtitle_boundaries": not boundaries,
            "duration_positive": duration > 0,
            "technical_decode": scan.get("decode") == "passed"}


def verify_review_files(review: dict) -> None:
    for batch in review.get("batches", []):
        proof = batch["evidence"]
        if fingerprint(Path(proof["path"])) != proof["sha256"]:
            raise LocalModelError("local_review_receipt_changed")
        for image in batch["images"]:
            if fingerprint(Path(image["path"])) != image["sha256"]:
                raise LocalModelError("local_review_image_changed")


def verify_evidence_files(value) -> None:
    """Verify nested generation/plan/alignment receipts, not just their pointers."""
    if isinstance(value, dict):
        if "path" in value and "sha256" in value and fingerprint(Path(value["path"])) != value["sha256"]:
            raise LocalModelError("local_generation_receipt_changed")
        for child in value.values():
            verify_evidence_files(child)
    elif isinstance(value, list):
        for child in value:
            verify_evidence_files(child)
