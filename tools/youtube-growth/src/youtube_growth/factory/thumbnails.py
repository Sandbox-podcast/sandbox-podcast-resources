"""Evidence-led local thumbnail concepts. No uploads or invented performance."""
from __future__ import annotations

from datetime import timedelta
import json
import math
from pathlib import Path
import re
import shutil
import unicodedata

from .contracts import digest, instant, iso, utcnow
from .local_lock import local_lock
from .media import fingerprint
from ..storage import save_json
from ..thumbnails import _font

VERSION = 1
RENDERER_VERSION = "1.1"
CHECKS = frozenset({"content_fidelity", "title_image_complementarity", "mobile_readability", "composition", "brand_rights", "distinct_hypotheses"})
NAVY, CYAN, WHITE = "#071322", "#42e8de", "#f9fbff"


def _normalized(value):
    return " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())


def _portable(value):
    if isinstance(value, dict):
        return {key: _portable(item) for key, item in value.items() if key not in {"path", "directory"} and not key.endswith("_path")}
    if isinstance(value, list):
        return [_portable(item) for item in value]
    return value


def _text(row, fields):
    for name in fields:
        if not isinstance(row.get(name), str) or not row[name].strip():
            raise ValueError(f"Réflexion miniature manquante : {name}.")


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _box(value, *, normalized=False):
    maximum = 1 if normalized else None
    if not isinstance(value, list) or len(value) != 4 or not all(_number(v) for v in value):
        raise ValueError("Cadrage explicite [x,y,largeur,hauteur] requis.")
    x, y, width, height = value
    if x < 0 or y < 0 or width <= 0 or height <= 0 or maximum and (x+width > maximum+1e-8 or y+height > maximum+1e-8):
        raise ValueError("Cadrage hors de l'image.")
    return value


def _contains(outer, inner):
    x, y, w, h = outer
    a, b, c, d = inner
    return x <= a+1e-8 and y <= b+1e-8 and a+c <= x+w+1e-8 and b+d <= y+h+1e-8


def _intersects(a, b):
    return a[0] < b[0]+b[2] and b[0] < a[0]+a[2] and a[1] < b[1]+b[3] and b[1] < a[1]+a[3]


def validate_brief(brief, episode, candidate, asset, config, *, now=None):
    if not isinstance(brief, dict) or brief.get("version") != VERSION:
        raise ValueError("Brief miniature version 1 requis.")
    for field, expected in (("episode_id", episode["episode_id"]), ("segment_id", candidate["segment_id"]),
                            ("asset_sha256", asset["sha256"]), ("source_sha256", episode["source_sha256"])):
        if brief.get(field) != expected:
            raise ValueError(f"Le brief miniature ne correspond pas à {field}.")
    _text(brief, ("created_by", "audience", "viewer_question", "content_promise", "essential_nuance", "selection_reason"))
    references = brief.get("benchmark", {}).get("references", [])
    if not isinstance(references, list) or len(references) < 6:
        raise ValueError("Comparer au moins six miniatures observées, sur trois chaînes pertinentes.")
    current = instant(now or utcnow())
    seen, channels, comparable, video_urls, image_urls = set(), set(), set(), set(), set()
    for row in references:
        _text(row, ("reference_id", "channel", "video_url", "thumbnail_url", "format", "selection_reason", "visual_observation", "title_image_relation", "takeaway", "limitations"))
        if (row["reference_id"] in seen or row["video_url"] in video_urls or row["thumbnail_url"] in image_urls
                or not row["video_url"].startswith("https://") or not row["thumbnail_url"].startswith("https://")):
            raise ValueError("Référence visuelle dupliquée ou sans URL HTTPS.")
        observed = instant(row["observed_at"])
        if not timedelta(0) <= current-observed <= timedelta(days=config.get("thumbnails", {}).get("reference_max_age_days", 90)):
            raise ValueError("Relevé des miniatures à actualiser avant de préparer un nouvel épisode.")
        if row.get("synthetic") and not episode.get("synthetic"):
            raise ValueError("Des références synthétiques ne peuvent guider une miniature réelle.")
        if row.get("visually_inspected") is not True:
            raise ValueError("Chaque référence doit avoir été examinée visuellement.")
        seen.add(row["reference_id"])
        video_urls.add(row["video_url"])
        image_urls.add(row["thumbnail_url"])
        channels.add(_normalized(row["channel"]))
        if row.get("comparable_format") is True:
            comparable.add(_normalized(row["channel"]))
    if len(channels) < 3 or len(comparable) < 2:
        raise ValueError("Trois chaînes, dont deux avec des formats comparables, sont requises.")
    evidence = brief.get("content_evidence", [])
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("Les promesses doivent citer les paroles et leurs timecodes source.")
    from ..thematic_core import read_transcript
    transcript = Path(episode["transcript"]) if episode.get("transcript") else None
    if not transcript or not transcript.is_file():
        raise ValueError("Transcription horodatée requise pour vérifier les promesses des miniatures.")
    duration = episode.get("source_probe", {}).get("duration_seconds") or max(c["source_end_seconds"] for c in asset["cuts"])
    segments = read_transcript(transcript, duration, source_hash=episode["source_sha256"])
    evidence_ids = set()
    for item in evidence:
        _text(item, ("evidence_id", "quote", "context", "supports"))
        start, end = item.get("start_seconds"), item.get("end_seconds")
        if not _number(start) or not _number(end) or not 0 <= start < end <= duration:
            raise ValueError("Bornes de preuve invalides, en secondes source.")
        if not any(c["source_start_seconds"] <= start and end <= c["source_end_seconds"] for c in asset["cuts"]):
            raise ValueError("La preuve invoquée est hors des coupes du contenu livré.")
        # Segment timestamps cannot locate a word inside a wider cue. Keep the
        # full documented interval rather than manufacture word precision.
        spoken = " ".join(s["text"] for s in segments if start-.001 <= s["start"] and s["end"] <= end+.001)
        if _normalized(item["quote"]) not in _normalized(spoken) or item["evidence_id"] in evidence_ids:
            raise ValueError("Citation absente de la transcription ou preuve dupliquée.")
        evidence_ids.add(item["evidence_id"])
    concepts = brief.get("concepts", [])
    if not isinstance(concepts, list) or len(concepts) != 3:
        raise ValueError("Trois concepts titre/image distincts sont requis.")
    ids, angles, pairs, hypotheses = set(), set(), set(), set()
    for row in concepts:
        _text(row, ("concept_id", "angle", "hypothesis", "video_title", "wording_reason", "title_image_complementarity", "visual_rationale"))
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", row["concept_id"]):
            raise ValueError("Identifiant de concept invalide.")
        phrase = row.get("thumbnail_text")
        if not isinstance(phrase, str) or not phrase.strip() and not row.get("no_text_reason"):
            raise ValueError("Texte de miniature ou justification du choix sans texte requis.")
        if any(ch in phrase+row["video_title"] for ch in "’‘“”«»—–"):
            raise ValueError("Employer apostrophes simples et guillemets droits.")
        if _normalized(phrase).strip(".?! ") == _normalized(row["video_title"]).strip(".?! "):
            raise ValueError("La phrase de la miniature doit compléter le titre.")
        pair = (_normalized(row["video_title"]), _normalized(phrase))
        if row["concept_id"] in ids or _normalized(row["angle"]) in angles or pair in pairs or _normalized(row["hypothesis"]) in hypotheses:
            raise ValueError("Les trois concepts ne peuvent être des copies recolorées.")
        ids.add(row["concept_id"])
        angles.add(_normalized(row["angle"]))
        pairs.add(pair)
        hypotheses.add(_normalized(row["hypothesis"]))
        if not row.get("reference_ids") or set(row["reference_ids"])-seen or not row.get("evidence_ids") or set(row["evidence_ids"])-evidence_ids:
            raise ValueError("Chaque concept doit citer ses références et les preuves du passage.")
        source = row.get("image", {})
        crop = _box(source.get("crop"), normalized=True)
        focus = _box(source.get("focus_box"), normalized=True)
        if not _contains(crop, focus):
            raise ValueError("Le recadrage coupe le sujet déclaré important.")
        if source.get("kind") == "episode_frame":
            at = source.get("source_time_seconds")
            if not _number(at) or not any(c["source_start_seconds"] <= at < c["source_end_seconds"] for c in asset["cuts"]):
                raise ValueError("L'image doit venir du passage réellement monté.")
        elif source.get("kind") == "authorized_photo":
            _text(source, ("path", "sha256", "rights_evidence", "subject_identity"))
            if fingerprint(Path(source["path"])) != source["sha256"]:
                raise ValueError("La photo autorisée a changé.")
        else:
            raise ValueError("Utiliser une vraie image du passage ou une photo autorisée.")
        image_box = _box(row.get("image_box"))
        text_box = _box(row.get("text_box"))
        safe = [40, 80, 1200, 600]
        if not _contains(safe, image_box) or not _contains(safe, text_box):
            raise ValueError("Respecter les marges et l'espace de marque du canevas 1280 x 720.")
        if phrase.strip() and _intersects(image_box, text_box):
            raise ValueError("Placer le texte hors de la zone réservée à la personne ou à la démonstration.")
        if phrase.strip() and _intersects(text_box, [1080, 640, 200, 80]):
            raise ValueError("Conserver le texte hors de la réserve basse droite des interfaces.")
    if brief.get("preferred_concept_id") not in ids:
        raise ValueError("Choix éditorial initial et justification requis ; aucun gagnant statistique inventé.")
    return brief


def _wrap(text, font, width):
    lines = []
    words = []
    for word in text.split():
        if words and all(char in ".?!:;," for char in word):
            words[-1] += " "+word
        else:
            words.append(word)
    for word in words:
        if font.getlength(word) > width:
            return None
        if lines and font.getlength(lines[-1]+" "+word) <= width:
            lines[-1] += " "+word
        else:
            lines.append(word)
    return lines


def _artifact(path, kind):
    return {"path": str(path), "sha256": fingerprint(path), "kind": kind}


def create_bundle(brief, episode, candidate, asset, output: Path, config, *, now=None):
    from PIL import Image, ImageDraw, ImageOps
    from ..shorts import _call, _require_media_tools
    validate_brief(brief, episode, candidate, asset, config, now=now)
    brief = json.loads(json.dumps(brief))
    if fingerprint(Path(asset["path"])) != asset["sha256"] or fingerprint(Path(episode["source"])) != episode["source_sha256"]:
        raise ValueError("Le média ou son master a changé depuis l'analyse.")
    options = config.get("thumbnails", {})
    width, height = options.get("width", 3840), options.get("height", 2160)
    if type(width) is not int or type(height) is not int or width < 1280 or height < 720 or width*9 != height*16:
        raise ValueError("Exporter toutes les variantes en 16:9 et au moins 1280 x 720.")
    brief_sha = digest(_portable(brief))
    key = digest({"renderer": RENDERER_VERSION, "brief": brief_sha, "asset": asset["sha256"], "width": width, "height": height,
                  "max_bytes": options.get("max_bytes", 1_900_000)})
    directory = Path(output).resolve() / key[:24]
    receipt = directory / "bundle.json"
    if receipt.exists():
        previous = json.loads(receipt.read_text(encoding="utf-8"))
        validate_bundle(previous, asset=asset)
        return previous
    directory.mkdir(parents=True, exist_ok=True)
    with local_lock(directory):
        save_json(directory / "brief.json", brief)
        scale = width/1280
        variants, artifacts = [], []
        for concept in brief["concepts"]:
            source = concept["image"]
            source_file = directory / (concept["concept_id"]+"-source.png")
            if source["kind"] == "episode_frame":
                ffmpeg, _ = _require_media_tools()
                stage_path = source_file.with_suffix(".json")
                stage = json.loads(stage_path.read_text(encoding="utf-8")) if stage_path.exists() else None
                if stage:
                    if stage.get("sha256") != fingerprint(source_file) or stage.get("source_sha256") != episode["source_sha256"] or stage.get("source_time_seconds") != source["source_time_seconds"]:
                        raise ValueError("L'image extraite ou sa provenance a changé.")
                else:
                    if source_file.exists():
                        raise ValueError("Image extraite sans reçu ; conserver le dossier pour diagnostic.")
                    temporary_source = source_file.with_name(source_file.stem+".partial.png")
                    _call([ffmpeg, "-nostdin", "-v", "error", "-y", "-ss", str(source["source_time_seconds"]), "-i", episode["source"], "-frames:v", "1", str(temporary_source)])
                    temporary_source.replace(source_file)
                    save_json(stage_path, {"source_sha256": episode["source_sha256"], "source_time_seconds": source["source_time_seconds"], "sha256": fingerprint(source_file)})
                photo = Image.open(source_file).convert("RGB")
                artifacts.append(_artifact(source_file, "episode_frame"))
            else:
                copied_photo = directory / (concept["concept_id"]+"-photo"+Path(source["path"]).suffix.lower())
                if not copied_photo.exists():
                    shutil.copy2(source["path"], copied_photo)
                if fingerprint(copied_photo) != source["sha256"]:
                    raise ValueError("La copie de la photo autorisée a changé.")
                source["path"] = str(copied_photo)
                photo = Image.open(source["path"]).convert("RGB")
                artifacts.append(_artifact(copied_photo, "authorized_photo"))
            original_size = photo.size
            x, y, w, h = source["crop"]
            photo = photo.crop((round(x*photo.width), round(y*photo.height), round((x+w)*photo.width), round((y+h)*photo.height)))
            canvas = Image.new("RGB", (width, height), NAVY)
            draw = ImageDraw.Draw(canvas)
            draw.rectangle((0, 0, round(14*scale), height), fill=CYAN)
            draw.text((round(40*scale), round(23*scale)), "SANDBOX", font=_font(round(29*scale)), fill=CYAN)
            ix, iy, iw, ih = concept["image_box"]
            fitted = ImageOps.contain(photo, (round(iw*scale), round(ih*scale)), method=Image.Resampling.LANCZOS)
            left, top = round(ix*scale)+(round(iw*scale)-fitted.width)//2, round(iy*scale)+(round(ih*scale)-fitted.height)//2
            canvas.paste(fitted, (left, top))
            fx, fy, fw, fh = source["focus_box"]
            focal = [left/scale+(fx-x)/w*fitted.width/scale, top/scale+(fy-y)/h*fitted.height/scale,
                     fw/w*fitted.width/scale, fh/h*fitted.height/scale]
            if _intersects(focal, [1080, 640, 200, 80]):
                raise ValueError("Le sujet important tombe dans la réserve basse droite destinée aux interfaces.")
            tx, ty, tw, th = concept["text_box"]
            phrase = concept["thumbnail_text"].strip()
            lines, font_size = [], None
            if phrase:
                for size in range(112, 47, -2):
                    font = _font(round(size*scale))
                    wrapped = _wrap(phrase, font, tw*scale)
                    if wrapped and len(wrapped) <= 3 and len(wrapped)*size*1.18 <= th:
                        lines, font_size = wrapped, size
                        break
                if font_size is None:
                    raise ValueError("La phrase ne tient pas lisiblement dans la composition ; la réécrire.")
                line_height = round(font_size*1.18*scale)
                for index, line in enumerate(lines):
                    draw.text((round(tx*scale), round(ty*scale)+index*line_height), line, font=font, fill=WHITE, stroke_width=0)
            target = directory / (concept["concept_id"]+".jpg")
            temporary = directory / (concept["concept_id"]+".partial.jpg")
            for quality in (94, 90, 86, 82, 76):
                canvas.save(temporary, quality=quality, optimize=True)
                if temporary.stat().st_size <= options.get("max_bytes", 1_900_000):
                    break
            else:
                raise ValueError("Miniature trop lourde pour le budget d'export configuré.")
            if target.exists() and fingerprint(target) != fingerprint(temporary):
                raise ValueError("Une miniature déjà produite a changé ; conserver sa version.")
            temporary.replace(target)
            previews = []
            for preview_width in (320, 160):
                preview = directory / f"{concept['concept_id']}-{preview_width}.png"
                canvas.resize((preview_width, preview_width*9//16), Image.Resampling.LANCZOS).save(preview)
                previews.append(_artifact(preview, "preview_"+str(preview_width)))
            variant = {"concept_id": concept["concept_id"], "title": concept["video_title"], "thumbnail_text": phrase,
                       "angle": concept["angle"], "hypothesis": concept["hypothesis"], "wording_reason": concept["wording_reason"],
                       "title_image_complementarity": concept["title_image_complementarity"], "visual_rationale": concept["visual_rationale"],
                       "reference_ids": concept["reference_ids"], "evidence_ids": concept["evidence_ids"],
                       "thumbnail": _artifact(target, "thumbnail"), "previews": previews,
                       "technical_qa": {"status": "passed", "width": width, "height": height, "font_size_base": font_size,
                                        "text_lines": lines, "focus_box_output_base": focal, "source_resolution": list(original_size),
                                        "source_upscaled": fitted.width > original_size[0] or fitted.height > original_size[1],
                                        "human_mobile_review": "pending"}}
            artifacts.extend([variant["thumbnail"], *previews])
            variants.append(variant)
        # Compare the actual title/image pair at feed size, rather than isolated full-size canvases.
        sheet = Image.new("RGB", (1040, 470), "#e9eef3")
        draw = ImageDraw.Draw(sheet)
        for index, variant in enumerate(variants):
            left = 20+index*340
            sheet.paste(Image.open(variant["previews"][0]["path"]), (left, 20))
            title = _wrap(variant["title"], _font(18), 320)
            if not title or len(title) > 6:
                raise ValueError("Le titre ne tient pas dans la planche de comparaison.")
            for line_index, line in enumerate(title):
                draw.text((left, 215+line_index*22), line, font=_font(18), fill=NAVY)
            sheet.paste(Image.open(variant["previews"][1]["path"]), (left, 365))
            draw.text((left, 340), variant["concept_id"], font=_font(16), fill=NAVY)
        comparison = directory / "comparaison.png"
        sheet.save(comparison)
        artifacts.append(_artifact(comparison, "comparison"))
        bundle = {"version": VERSION, "bundle_id": "thumbnails-"+key[:24], "brief_sha256": brief_sha,
                  "episode_id": episode["episode_id"], "segment_id": candidate["segment_id"], "asset_sha256": asset["sha256"],
                  "source_sha256": episode["source_sha256"], "created_by": brief["created_by"], "created_at": iso(now or utcnow()),
                  "brief_path": str(directory / "brief.json"), "receipt_path": str(receipt), "variants": variants, "artifacts": artifacts,
                  "selected_concept_id": brief["preferred_concept_id"], "selection_reason": brief["selection_reason"],
                  "performance_winner": None, "review_status": "needs_review", "synthetic": episode.get("synthetic", False)}
        bundle["content_digest"] = bundle_digest(bundle)
        save_json(directory / "brief.json", brief)
        save_json(receipt, bundle)
        return bundle


def bundle_digest(bundle):
    return digest({"version": bundle["version"], "brief": bundle["brief_sha256"], "asset": bundle["asset_sha256"],
                   "created_by": bundle["created_by"], "episode_id": bundle["episode_id"], "segment_id": bundle["segment_id"],
                   "synthetic": bundle["synthetic"], "selection_reason": bundle["selection_reason"],
                   "source": bundle["source_sha256"], "selected": bundle["selected_concept_id"], "variants": _portable(bundle["variants"]),
                   "artifacts": _portable(bundle["artifacts"])})


def validate_bundle(bundle, asset=None, *, require_review=False):
    if bundle.get("version") != VERSION or len(bundle.get("variants", [])) != 3 or bundle.get("content_digest") != bundle_digest(bundle):
        raise ValueError("Les miniatures ou leurs concepts ont changé depuis leur préparation.")
    if bundle.get("performance_winner") is not None:
        raise ValueError("La préparation éditoriale ne permet pas de déclarer un gagnant de performance.")
    if asset and (asset["sha256"] != bundle["asset_sha256"] or asset.get("source_sha256", bundle["source_sha256"]) != bundle["source_sha256"]):
        raise ValueError("La revue des miniatures porte sur un ancien montage.")
    if digest(_portable(json.loads(Path(bundle["brief_path"]).read_text(encoding="utf-8-sig")))) != bundle["brief_sha256"]:
        raise ValueError("Le brief de création a changé.")
    for artifact in bundle["artifacts"]:
        if fingerprint(Path(artifact["path"])) != artifact["sha256"]:
            raise ValueError("Une miniature ou sa prévisualisation a changé.")
    if require_review:
        review = bundle.get("review", {})
        if not isinstance(review, dict):
            raise ValueError("Reçu de revue des miniatures invalide.")
        _text(review, ("reviewer", "evidence", "reviewed_at"))
        instant(review["reviewed_at"])
        if bundle.get("review_status") != "passed" or review.get("content_digest") != bundle["content_digest"] or set(review.get("checks", [])) != CHECKS:
            raise ValueError("Revue croisée du titre, de l'image et des aperçus requise.")
        if _normalized(review.get("reviewer")) == _normalized(bundle["created_by"]):
            raise ValueError("La revue doit être distincte de la conception.")


def review_bundle(bundle, *, reviewer, evidence, checks, now=None):
    validate_bundle(bundle)
    if not reviewer.strip() or _normalized(reviewer) == _normalized(bundle["created_by"]) or not evidence.strip() or set(checks) != CHECKS:
        raise ValueError("Relecture croisée et preuve pour tous les critères de miniature requises.")
    result = {**bundle, "review_status": "passed", "review": {"reviewer": reviewer, "evidence": evidence,
              "checks": sorted(CHECKS), "reviewed_at": iso(now or utcnow()), "content_digest": bundle["content_digest"]}}
    return result


def fixture_brief(episode, candidate, asset, *, now=None):
    """Exercise the pipeline without presenting synthetic art as a real proposal."""
    if episode.get("synthetic") is not True:
        raise ValueError("Ce générateur de brief est réservé à la recette synthétique.")
    at = asset["cuts"][0]["source_start_seconds"]
    end = min(at+12, asset["cuts"][0]["source_end_seconds"])
    references = [{"reference_id": f"fixture-{i}", "channel": f"Fixture de référence {i//2}",
                   "video_url": f"https://example.invalid/video/{i}", "thumbnail_url": f"https://example.invalid/image/{i}.jpg",
                   "observed_at": iso(now or utcnow()), "format": "synthetic_test", "selection_reason": "Tester les contrats, sans recommandation éditoriale réelle.",
                   "visual_observation": "Mire générée pour la recette.", "title_image_relation": "Cas synthétique du validateur.",
                   "takeaway": "Vérifier que le pipeline exige ses preuves.", "limitations": "Aucune chaîne ni performance réelle.",
                   "synthetic": True, "visually_inspected": True, "comparable_format": True} for i in range(6)]
    variants = [
        ("image", "Contrôle de l'image", "Identifier la mire par sa lisibilité.", "Fixture vidéo : examiner la composition", "MIRE DE TEST", [660, 140, 580, 430], [40, 170, 540, 400]),
        ("cuts", "Traçabilité des coupes", "Identifier le scénario de provenance.", "Fixture vidéo : suivre les coupes source", "COUPES TRACÉES", [40, 80, 1200, 300], [40, 430, 990, 240]),
        ("preview", "Aperçus mobiles", "Tester une question qui invite à examiner les petits formats.", "Fixture vidéo : vérifier les aperçus", "LISIBLE EN PETIT ?", [40, 100, 570, 540], [670, 140, 570, 480]),
    ]
    return {"version": 1, "episode_id": episode["episode_id"], "segment_id": candidate["segment_id"],
            "asset_sha256": asset["sha256"], "source_sha256": episode["source_sha256"], "created_by": "synthetic_fixture_generator",
            "audience": "Vérification technique de la factory", "viewer_question": "Le contrat de préparation et de revue est-il respecté ?",
            "content_promise": "Contrôler une mire, un son de test et les fichiers dérivés.", "essential_nuance": "Aucune parole ni miniature commerciale réelle.",
            "benchmark": {"references": references}, "preferred_concept_id": "image", "selection_reason": "Choix de fixture, sans gagnant de performance.",
            "content_evidence": [{"evidence_id": "fixture-cue", "start_seconds": at, "end_seconds": end,
                                  "quote": "Signal de test", "context": "Sous-titre explicitement synthétique, aucune parole réelle.", "supports": "Identifier la fixture et son périmètre technique."}],
            "concepts": [{"concept_id": identity, "angle": angle, "hypothesis": hypothesis, "video_title": title, "thumbnail_text": text,
                          "wording_reason": "Texte décrivant uniquement le scénario de recette.", "title_image_complementarity": "Le titre nomme le contrôle ; l'image nomme son objet.",
                          "visual_rationale": "Conserver la mire entière et séparer sa zone du texte.", "reference_ids": [f"fixture-{i*2}", f"fixture-{i*2+1}"],
                          "evidence_ids": ["fixture-cue"], "image_box": image_box, "text_box": text_box,
                          "image": {"kind": "episode_frame", "source_time_seconds": at+.1, "crop": [0, 0, 1, 1], "focus_box": [.1, .1, .8, .8]}}
                         for i, (identity, angle, hypothesis, title, text, image_box, text_box) in enumerate(variants)]}
