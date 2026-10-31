"""Durable onboarding for a new video: progressive questions, skill routing, decisions and checks.

The conversation agent asks the questions and does the editorial work with the routed
skills; this module keeps every answer, decision and stage result in the factory store,
links the project to StoryTelling Generator and marks later work stale after a change.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import shutil
import uuid

from .contracts import ROOT, digest, iso, utcnow
from .media import fingerprint

AP, SW = "autopunk-media-skills/", "screenwriting-skills/"
TYPES = {
    "documentary": {"label": "Documentaire", "mode": "documentary"},
    "explainer": {"label": "Explication ou vulgarisation", "mode": "documentary"},
    "commentary": {"label": "Commentaire ou chronique", "mode": "documentary"},
    "fiction": {"label": "Récit de fiction", "mode": "fiction"},
    "docufiction": {"label": "Récit mêlant faits et reconstitutions annoncées", "mode": "mixed"},
    "other": {"label": "Autre format, à décrire", "mode": None},
}
DURATIONS = {"documentary": 12, "explainer": 6, "commentary": 5, "fiction": 8, "docufiction": 12}
STAGES = [
    ("format", "Type de vidéo", "Choisir le type de vidéo ; il oriente toutes les étapes suivantes."),
    ("topic", "Sujet", "Fixer le sujet. Sans sujet, proposer des pistes sourcées puis attendre le choix de Lou."),
    ("framing", "Cadrage", "Définir public, objectif, angle, durée, format, sources, contraintes, moyens et validations."),
    ("voice", "Narrateur", "Choisir une voix réellement disponible et la direction d'interprétation prise en charge."),
    ("research", "Recherche et sources", "Créer l'histoire dans StoryTelling, importer les sources et établir les faits et leurs limites."),
    ("structure", "Structure narrative", "Construire l'accroche, la progression et une conclusion qui répond à la promesse."),
    ("writing", "Texte intégral", "Rédiger tout le texte prononcé selon le format choisi."),
    ("narrator_adaptation", "Adaptation au narrateur", "Adapter registre, rythme et tournures à l'identité du narrateur sans changer les faits."),
    ("french_revision", "Révision du français", "Retirer formulations artificielles, répétitions et passages génériques en préservant faits et sources."),
    ("spoken_revision", "Révision pour l'oral", "Préparer prononciation, respiration, débit, rythme et intentions de jeu."),
    ("storyboard", "Storyboard", "Préparer plans, médias, sons et sous-titres, puis importer le scénario complet dans StoryTelling."),
    ("production", "Voix et montage", "Produire les voix et le montage avec le moteur StoryTelling, sur le même état local."),
    ("controls", "Contrôles", "Séparer contrôles techniques, vérification des faits, écoute, visionnage et validation de Lou."),
    ("exports", "Exports", "Livrer MP4, sous-titres et manifeste avec les réserves restantes."),
]
STAGE_IDS = [s[0] for s in STAGES]
QUESTION_STAGES = {"format", "topic", "framing", "voice"}

FIELDS = {
    "video_type": {"stage": "format", "kind": "choice", "choices": list(TYPES), "question": "Quel type de vidéo veux-tu créer ?"},
    "video_type_note": {"stage": "format", "kind": "text", "question": "Décris le format voulu : exemple, référence, ce qui le distingue.",
                        "when": lambda a: a.get("video_type") == "other"},
    "mode": {"stage": "format", "kind": "choice", "choices": ["documentary", "fiction", "mixed"],
             "question": "Le récit repose-t-il sur des faits, sur une fiction, ou mêle-t-il les deux ?",
             "when": lambda a: a.get("video_type") == "other"},
    "register": {"stage": "format", "kind": "choice", "choices": ["analytic", "dynamic"],
                 "question": "Quel registre : analyse posée, ou commentaire dynamique de type sportif ?",
                 "when": lambda a: a.get("video_type") == "commentary"},
    "topic": {"stage": "topic", "kind": "text", "question": "Quel est le sujet ? Sans sujet, je te propose des pistes sourcées."},
    "audience": {"stage": "framing", "kind": "text", "question": "À qui s'adresse la vidéo ?", "recommend": "public curieux non spécialiste"},
    "objective": {"stage": "framing", "kind": "text", "question": "Que doit comprendre, ressentir ou retenir ce public à la fin ?"},
    "angle": {"stage": "framing", "kind": "text", "question": "Quel angle ou quelle question centrale ?"},
    "duration_minutes": {"stage": "framing", "kind": "number", "range": (.25, 120), "question": "Quelle durée vises-tu, en minutes ?"},
    "format": {"stage": "framing", "kind": "choice", "choices": ["16:9", "9:16"], "question": "Format horizontal 16:9 ou vertical 9:16 ?", "recommend": "16:9"},
    "sources": {"stage": "framing", "kind": "list", "optional": True, "question": "Quelles sources utiliser : fichiers locaux ou liens HTTPS publics ?"},
    "media": {"stage": "framing", "kind": "list", "optional": True, "question": "As-tu des images, vidéos ou sons à intégrer (chemins locaux) ?"},
    "media_rights": {"stage": "framing", "kind": "text", "question": "Quels droits as-tu sur ces médias : créés par toi, licence, autorisation ?",
                     "when": lambda a: bool(a.get("media"))},
    "mandatory": {"stage": "framing", "kind": "text", "optional": True, "question": "Y a-t-il des éléments obligatoires ?"},
    "exclusions": {"stage": "framing", "kind": "text", "optional": True, "question": "Des contraintes ou des sujets à exclure ?"},
    "means": {"stage": "framing", "kind": "text", "optional": True, "question": "Quels moyens as-tu : temps, archives, images, musique, aide ?"},
    "tone": {"stage": "framing", "kind": "text", "optional": True, "question": "Quel ton souhaites-tu ?"},
    "autonomy": {"stage": "framing", "kind": "choice", "choices": ["editorial_review", "autonomous"], "recommend": "editorial_review",
                 "question": "Veux-tu valider scénario et storyboard avant la production, ou laisser la production autonome ?"},
    "budget_limit": {"stage": "framing", "kind": "number", "range": (0, 1e6), "recommend": 0,
                     "question": "Quel plafond de dépense externe ? 0 garde une production entièrement locale."},
    "currency": {"stage": "framing", "kind": "text", "recommend": "EUR", "question": "Dans quelle devise ?"},
    "voice_provider": {"stage": "voice", "kind": "choice", "choices": ["voicestudio", "system", "elevenlabs_browser"], "recommend": "voicestudio",
                       "question": "Quelle source de voix : Voice Studio (voix locales), voix Windows ou ElevenLabs dans le navigateur ?"},
    "system_voice": {"stage": "voice", "kind": "text", "recommend": "Microsoft Hortense Desktop", "question": "Quelle voix Windows utiliser ?",
                     "when": lambda a: a.get("voice_provider") == "system"},
    "browser_credit_limit": {"stage": "voice", "kind": "integer", "range": (0, 10**9), "question": "Quel plafond de crédits ElevenLabs ?",
                             "when": lambda a: a.get("voice_provider") == "elevenlabs_browser"},
}

TREND = ("sandbox-youtube-trend-hunter", "Veille de tendances sourcée quand Lou veut partir de l'actualité ou de YouTube.")
WRITER = ("sandbox-video-scriptwriter", "Agent scénariste : enchaîne les skills d'écriture de cette étape dans l'ordre et applique les règles apprises.")
RESEARCH = ("awesome-claude-skills/content-research-writer", "Fiche préparatoire : faits vérifiés, sources, limites et exemples utilisables.")
YT = "youtube-agent-skill/yt-script"
ROUTES = {
    "format": {"other": [(AP+"template-selector", "Proposer l'ensemble de skills d'un format hybride ou inhabituel.")]},
    "topic": {
        "documentary": [TREND, (AP+"story-angle-finder", "Décliner un thème large en angles distincts."),
                        (AP+"coverage-gap-identifier", "Repérer ce que la couverture existante laisse de côté.")],
        "explainer": [TREND, (AP+"niche-video-idea-generator", "Proposer des idées adaptées au public visé."),
                      (AP+"story-angle-finder", "Décliner un thème large en angles distincts.")],
        "commentary": [TREND, (AP+"trending-topics-brief", "Cartographier les conversations qui montent sur le thème."),
                       (AP+"debate-state-summary", "Résumer l'état du débat avant de prendre position.")],
        "fiction": [(SW+"sw-premise-theme", "Choisir une prémisse et une idée directrice."),
                    (AP+"logline-writer", "Formuler chaque proposition en une phrase.")],
        "docufiction": [(AP+"story-angle-finder", "Décliner un thème large en angles distincts."),
                        (SW+"sw-premise-theme", "Choisir la prémisse des reconstitutions.")],
    },
    "framing": {
        "documentary": [(AP+"logline-creator", "Formuler la promesse du film en une ou deux phrases.")],
        "explainer": [(AP+"story-angle-finder", "Choisir l'angle le plus clair pour le public visé.")],
        "commentary": [(AP+"story-angle-finder", "Choisir la thèse et son angle.")],
        "fiction": [(SW+"sw-premise-theme", "Préciser prémisse, thème et enjeu."), (AP+"logline-writer", "Formuler le récit en une phrase.")],
        "docufiction": [(AP+"logline-creator", "Formuler la promesse du film."), (SW+"sw-premise-theme", "Préciser l'enjeu des reconstitutions.")],
    },
    "research": {
        "explainer": [WRITER, RESEARCH],
        "docufiction": [WRITER, RESEARCH],
        "documentary": [WRITER, RESEARCH, (AP+"research-brief-creator", "Lister questions, sources et documents à obtenir."),
                        (AP+"topic-background-brief", "Organiser les notes en dossier de référence."),
                        (AP+"event-chronology-builder", "Établir la chronologie quand le récit en dépend."),
                        (AP+"claim-fact-checker", "Préparer la vérification des affirmations centrales."),
                        (AP+"source-cross-referencer", "Voir quelles sources soutiennent ou contredisent chaque affirmation."),
                        (AP+"statistics-verifier", "Contrôler chaque chiffre et sa source.")],
        "commentary": [WRITER, RESEARCH, (AP+"topic-background-brief", "Organiser les faits sur lesquels repose l'avis."),
                       (AP+"claim-fact-checker", "Vérifier les affirmations reprises."),
                       (AP+"source-cross-referencer", "Croiser les sources de chaque affirmation."),
                       (AP+"statistics-verifier", "Contrôler chaque chiffre et sa source.")],
        "fiction": [(AP+"cultural-context-brief", "Documenter un contexte réel utilisé par la fiction, si besoin.")],
    },
    "structure": {
        "documentary": [WRITER, (YT, "Cinq accroches d'après ses formules, les deux meilleures montrées à Lou, puis les séquences."),
                        (SW+"sw-story-structure", "Choisir la structure et placer les tournants."),
                        (AP+"character-arc-planner", "Construire l'arc d'un personnage réel, si le récit en suit un."),
                        (AP+"scene-breakdown-writer", "Découper les séquences avec leurs besoins."),
                        (AP+"structure-flow-checker", "Vérifier l'enchaînement et les transitions.")],
        "explainer": [WRITER, (YT, "Cinq accroches d'après ses formules, les deux meilleures montrées à Lou, puis les séquences."),
                      (AP+"structure-flow-checker", "Vérifier que chaque étape prépare la suivante.")],
        "commentary": [WRITER, (SW+"sw-premise-theme", "Fixer l'idée directrice et sa contradiction."),
                       (YT, "Cinq accroches d'après ses formules, les deux meilleures montrées à Lou, puis les séquences."),
                       (AP+"structure-flow-checker", "Vérifier la logique de l'argumentation.")],
        "fiction": [(SW+"sw-story-structure", "Structure, incident déclencheur et tournants."),
                    (SW+"sw-character-conflict", "Personnages, objectifs et conflit."),
                    (SW+"sw-genre-anatomy", "Respecter les attentes du genre choisi."),
                    (AP+"beat-sheet-builder", "Placer les temps forts sur la durée.")],
        "docufiction": [(SW+"sw-story-structure", "Structure générale et tournants."),
                        (AP+"scene-breakdown-writer", "Séparer séquences factuelles et reconstitutions."),
                        (AP+"hook-generator@fr", "Écrire trois accroches d'ouverture.")],
    },
    "writing": {
        "documentary": [WRITER, (YT, "Script séquence par séquence avec ce qui est à l'écran."),
                        (AP+"commentary-writer", "Écrire le commentaire des séquences à partir des images et des notes."),
                        (AP+"documentary-narration-writer", "Construire une narration pensée pour l'écoute."),
                        (AP+"transition-narration-writer", "Écrire les transitions entre séquences.")],
        "explainer": [WRITER, (YT, "Script séquence par séquence avec ce qui est à l'écran."),
                      (AP+"animated-explainer-script", "Passages explicatifs : un concept par phrase, jargon expliqué, un visuel par passage.")],
        "commentary": [WRITER, (YT, "Script séquence par séquence avec ce qui est à l'écran."),
                       (AP+"voice-over-script-writer", "Écrire pour l'oreille, phrases courtes et actives.")],
        "fiction": [(SW+"sw-scene-craft", "Construire chaque scène autour d'un changement."),
                    (AP+"scene-writer", "Rédiger les scènes."), (SW+"sw-dialogue", "Écrire des dialogues avec sous-texte.")],
        "docufiction": [(AP+"commentary-writer", "Écrire la narration factuelle."),
                        (SW+"sw-scene-craft", "Écrire les reconstitutions annoncées."), (SW+"sw-dialogue", "Dialogues des reconstitutions.")],
    },
    "narrator_adaptation": {
        "*": [WRITER, (AP+"narrator-voice-adapter", "Reformuler ce que Lou ne dirait pas ainsi, en gardant faits, réserves et attributions.")],
        "fiction": [(AP+"narrator-voice-adapter", "Adapter la narration au narrateur choisi."),
                    (AP+"dialogue-polisher", "Différencier les voix des personnages.")],
    },
    "french_revision": {
        "*": [WRITER, ("humanizer-fr/humanizer-fr", "Seul correcteur qui réécrit : une passe, profil de voix de Lou en échantillon, guillemets et apostrophes droits."),
              (AP+"redundancy-checker", "Supprimer répétitions et redondances."),
              (AP+"tone-consistency-checker", "Repérer les ruptures de ton."),
              (AP+"unattributed-claims-checker", "Repérer les affirmations sans source après réécriture.")],
        "fiction": [("humanizer-fr/humanizer-fr", "Seul correcteur qui réécrit : une passe, profil de voix de Lou en échantillon, guillemets et apostrophes droits."),
                    (AP+"redundancy-checker", "Supprimer répétitions et redondances."),
                    (AP+"tone-consistency-checker", "Repérer les ruptures de ton.")],
    },
    "spoken_revision": {
        "*": [WRITER, (AP+"teleprompter-script-writer", "Réécrire en phrases parlées avec respirations, à partir du texte existant."),
              (AP+"voice-over-script-writer", "Vérifier que chaque phrase s'entend du premier coup.")],
    },
    "storyboard": {
        "documentary": [(AP+"b-roll-shot-list", "Lister les plans par section avec leur fonction."),
                        (AP+"archival-footage-brief", "Préciser les archives nécessaires et leurs sources."),
                        (AP+"stock-footage-brief", "Préparer la recherche d'images d'illustration."),
                        (AP+"rights-clearance-checklist", "Vérifier les droits des médias, musiques et archives."),
                        (AP+"subtitles-rewriter", "Rendre les sous-titres lisibles à l'écran.")],
        "explainer": [(AP+"animated-explainer-script", "Indications visuelles pour chaque temps de l'explication."),
                      (AP+"b-roll-shot-list", "Lister les plans d'illustration."),
                      (AP+"subtitles-rewriter", "Rendre les sous-titres lisibles à l'écran.")],
        "commentary": [(AP+"b-roll-shot-list", "Lister les plans d'illustration."),
                       (AP+"rights-clearance-checklist", "Vérifier les droits des médias."),
                       (AP+"subtitles-rewriter", "Rendre les sous-titres lisibles à l'écran.")],
        "fiction": [(AP+"cinematic-shot-prompt", "Décrire les plans ; toute génération d'image reste soumise à autorisation."),
                    (AP+"music-rights-request-writer", "Demander les droits d'une musique tierce, si besoin."),
                    (AP+"subtitles-rewriter", "Rendre les sous-titres lisibles à l'écran.")],
    },
    "production": {"*": [("sandbox-storytelling-generator", "Produire voix, timeline et rendu avec le moteur StoryTelling.")]},
    "controls": {
        "*": [(AP+"fine-cut-notes", "Notes sur le rythme, le ton et le mix du montage."),
              (AP+"picture-lock-checklist", "Liste des vérifications avant de figer le montage."),
              (AP+"claim-fact-checker", "Revérifier les affirmations du texte final.")],
        "fiction": [(AP+"fine-cut-notes", "Notes sur le rythme, le ton et le mix du montage."),
                    (AP+"picture-lock-checklist", "Liste des vérifications avant de figer le montage.")],
    },
    "exports": {"*": [(AP+"chapter-timestamps", "Chapitres à partir de la timeline mesurée, si la vidéo en a besoin.")]},
}
SHORT_FORM = [(AP+"shorts-script-adapter", "Adapter le texte au format court vertical."),
              (AP+"short-form-video-brief", "Structurer accroche, corps et fin d'un format court.")]
CHECKS = {
    "research": [("sources_identified", "agent", "Chaque affirmation importante renvoie à une source lisible, datée et importée."),
                 ("causality_checked", "agent", "Les causalités annoncées sont démontrées par les sources, sinon présentées comme hypothèses."),
                 ("gaps_listed", "agent", "Les lacunes, incertitudes et désaccords sont listés.")],
    "structure": [("hook_promise", "agent", "L'introduction pose une question ou une tension que la vidéo résout."),
                  ("progression", "agent", "Chaque partie change ce que le public comprend ou attend."),
                  ("conclusion_answers", "agent", "La conclusion répond à la promesse, sans l'excéder.")],
    "writing": [("full_text", "agent", "Tout le texte prononcé est écrit, sans passage à compléter."),
                ("facts_traceable", "agent", "Chaque fait renvoie à une source du dossier ou est annoncé comme fiction."),
                ("duration_fit", "auto", "Volume de texte compatible avec la durée visée (environ 155 mots par minute).")],
    "narrator_adaptation": [("identity_consistent", "agent", "Registre, personne grammaticale et tournures conformes au narrateur."),
                            ("facts_preserved", "agent", "Aucun fait, chiffre, nom ou source modifié par l'adaptation.")],
    "french_revision": [("single_pass", "agent", "Humaniseur FR appliqué en une seule passe, au registre demandé."),
                        ("facts_preserved", "agent", "Faits, chiffres, citations et sources inchangés."),
                        ("repetitions", "agent", "Répétitions, formules génériques et transitions creuses retirées.")],
    "spoken_revision": [("spoken_report", "auto", "Aucun chiffre, symbole, abréviation, parenthèse ou URL à lire tel quel."),
                        ("pronunciations", "agent", "Noms propres et sigles prononcés comme voulu, dictionnaire de la voix complété."),
                        ("delivery_intentions", "agent", "Intentions de jeu cohérentes d'une scène à l'autre.")],
    "storyboard": [("script_imported", "auto", "Le scénario complet est importé et validé par StoryTelling pour le cadrage courant."),
                   ("shots_readable", "agent", "Chaque plan a une fonction et une source ou un schéma réalisable."),
                   ("media_rights", "agent", "Les droits de chaque média, musique et archive sont renseignés."),
                   ("subtitles_readable", "agent", "Textes à l'écran et sous-titres sont courts et lisibles.")],
    "production": [("story_completed", "auto", "Le rendu StoryTelling de la révision courante est terminé."),
                   ("voice_attribution", "auto", "Chaque réplique utilise la voix choisie pour son locuteur.")],
    "controls": [("technical_exports", "auto", "Les fichiers exportés existent et correspondent à leurs empreintes."),
                 ("fact_check_final", "agent", "Le texte final a été revérifié contre les sources."),
                 ("listening_review", "human", "Écoute intégrale : diction, attribution des voix, intelligibilité du mix."),
                 ("visual_review", "human", "Visionnage intégral : lisibilité des plans et des sous-titres."),
                 ("editorial_validation", "human", "Validation de Lou sur la révision exportée.")],
    "exports": [("export_files", "auto", "MP4, sous-titres SRT et VTT et manifeste sont présents."),
                ("delivery_notes", "agent", "Les liens locaux et les réserves restantes sont communiqués.")],
}
OPTIONAL_STAGES = {"fiction": {"research"}}
GUIDE = ".agents/skills/sandbox-video-onboarding/references/"
REFERENCES = {"voice": [GUIDE + "voix.md"], "narrator_adaptation": [GUIDE + "voix.md"],
              "spoken_revision": [GUIDE + "revision-orale.md", GUIDE + "voix.md"],
              "production": [".agents/skills/sandbox-storytelling-generator/references/production.md"]}
BLOCKING_SPOKEN = {"digits", "symbols", "abbreviation", "brackets", "url"}
ABBREVIATIONS = re.compile(r"\b(?:etc|cf|ex|env|vs|ca|M|Mme|Mmes|Mlle|Dr|Pr|St|Ste|n°|p|pp|vol|chap)\.(?=\s|$)|\bn°", re.I)
STOPWORDS = set("""avoir cette celle celui comme dans donc elle elles encore entre être faire leurs mais même nous notre parce
pendant plus pour quand quel quelle sans selon sont sous toute tous tout très vous votre aussi alors avec autre après avant
bien ceux chez déjà depuis dont leur moins peut plusieurs puis quoi rien seulement surtout toujours trop""".split())


def _load(store, session_id):
    row = store.get("video_onboarding", session_id)
    if not row:
        raise ValueError("video_onboarding_unknown_session")
    return row


def _save(store, session, now, event, data=None):
    session["updated_at"] = iso(now or utcnow())
    with store.transaction():
        store.put("video_onboarding", session["session_id"], session, now=now)
        store.event("video_onboarding_" + event, session["session_id"], data or {}, now=now)
    return session


def _values(session):
    return {key: row["value"] for key, row in session["answers"].items()}


def type_key(answers):
    kind = answers.get("video_type")
    if kind == "other":
        return {"documentary": "documentary", "fiction": "fiction", "mixed": "docufiction"}.get(answers.get("mode"), "documentary")
    return kind or "documentary"


def coerce(field, value):
    spec = FIELDS.get(field)
    if spec is None:
        raise ValueError("video_onboarding_unknown_field")
    kind = spec["kind"]
    if kind == "choice":
        if value not in spec["choices"]:
            raise ValueError("video_onboarding_invalid_choice")
    elif kind == "text":
        if not isinstance(value, str) or not value.strip() or len(value) > 4000:
            raise ValueError("video_onboarding_text_required")
        value = value.strip()
    elif kind in {"number", "integer"}:
        if isinstance(value, str):
            try:
                value = float(value.replace(",", "."))
            except ValueError:
                raise ValueError("video_onboarding_number_required") from None
        low, high = spec["range"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError("video_onboarding_number_out_of_range")
        if kind == "integer":
            if value != int(value):
                raise ValueError("video_onboarding_integer_required")
            value = int(value)
        elif value == int(value):
            value = int(value)
    elif kind == "list":
        value = [value] if isinstance(value, str) else value
        if not isinstance(value, list) or len(value) > 200 or any(not isinstance(v, str) or not v.strip() for v in value):
            raise ValueError("video_onboarding_list_required")
        value = [v.strip() for v in value]
    return value


def _required(field, answers):
    spec = FIELDS[field]
    return not spec.get("optional") and spec.get("when", lambda _: True)(answers)


def start(store, *, answers=None, brief=None, session_id=None, now=None):
    session_id = session_id or "video-" + uuid.uuid4().hex[:12]
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", session_id):
        raise ValueError("video_onboarding_invalid_session_id")
    if store.get("video_onboarding", session_id):
        raise ValueError("video_onboarding_session_exists")
    session = {"version": 1, "session_id": session_id, "status": "active", "created_at": iso(now or utcnow()),
               "answers": {}, "topic_proposals": [], "topic_decision": None, "voice": None, "story_id": None,
               "brief_revision": None, "stages": {}, "imported_brief": None}
    if brief is not None:
        if not isinstance(brief, dict) or not isinstance(brief.get("topic"), str):
            raise ValueError("video_onboarding_brief_invalid")
        session["imported_brief"] = {k: brief[k] for k in ("notes", "documents", "links", "source_metadata", "story_id", "creative_references") if k in brief}
        imported = {k: brief[k] for k in ("topic", "audience", "duration_minutes", "format", "tone", "mandatory", "exclusions", "autonomy") if k in brief}
        for field, value in imported.items():
            session["answers"][field] = {"value": coerce(field, value), "origin": "imported_brief", "at": session["created_at"]}
        budget = brief.get("budget")
        if budget:
            if not isinstance(budget, dict):
                raise ValueError("video_onboarding_brief_invalid")
            session["answers"]["budget_limit"] = {"value": coerce("budget_limit", budget.get("limit")), "origin": "imported_brief", "at": session["created_at"]}
            session["answers"]["currency"] = {"value": coerce("currency", budget.get("currency")), "origin": "imported_brief", "at": session["created_at"]}
    for field, value in (answers or {}).items():
        session["answers"][field] = {"value": coerce(field, value), "origin": "user", "at": session["created_at"]}
    _save(store, session, now, "started", {"fields": sorted(session["answers"])})
    return next_step(store, session_id)


def answer(store, session_id, values, *, origin="user", now=None):
    if origin not in {"user", "accepted_recommendation"}:
        raise ValueError("video_onboarding_invalid_origin")
    session = _load(store, session_id)
    for field, value in values.items():
        session["answers"][field] = {"value": coerce(field, value), "origin": origin, "at": iso(now or utcnow())}
    _save(store, session, now, "answered", {"fields": sorted(values), "origin": origin})
    return next_step(store, session_id)


def propose_topics(store, session_id, proposals, *, now=None):
    session = _load(store, session_id)
    if not isinstance(proposals, list) or not 1 <= len(proposals) <= 12:
        raise ValueError("video_onboarding_proposals_required")
    rows = []
    for index, item in enumerate(proposals, 1):
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in ("title", "angle", "why")):
            raise ValueError("video_onboarding_proposal_incomplete")
        rows.append({"rank": index, "title": item["title"].strip(), "angle": item["angle"].strip(), "why": item["why"].strip(),
                     "sources": [s for s in item.get("sources", []) if isinstance(s, str)], "skills_used": _skills(item.get("skills_used", []))})
    session["topic_proposals"] = rows
    _save(store, session, now, "topics_proposed", {"count": len(rows)})
    return next_step(store, session_id)


def choose_topic(store, session_id, *, rank=None, topic=None, confirmation, now=None):
    """Record Lou's own choice; a proposal is never selected on his behalf."""
    session = _load(store, session_id)
    if not isinstance(confirmation, str) or not confirmation.strip():
        raise ValueError("video_onboarding_user_confirmation_required")
    if rank is not None:
        chosen = next((p for p in session["topic_proposals"] if p["rank"] == rank), None)
        if chosen is None:
            raise ValueError("video_onboarding_unknown_proposal")
        topic = chosen["title"]
        if "angle" not in session["answers"]:
            session["answers"]["angle"] = {"value": chosen["angle"], "origin": "topic_choice", "at": iso(now or utcnow())}
    session["answers"]["topic"] = {"value": coerce("topic", topic), "origin": "topic_choice", "at": iso(now or utcnow())}
    session["topic_decision"] = {"rank": rank, "topic": session["answers"]["topic"]["value"], "confirmation": confirmation.strip(), "at": iso(now or utcnow())}
    _save(store, session, now, "topic_chosen", {"rank": rank})
    return next_step(store, session_id)


def choose_voice(store, session_id, discovery, *, profile_id, confirmation, engine=None, authorization=None,
                 settings=None, pronunciations=None, now=None):
    """Pin a Voice Studio profile that the user picked from the live inventory."""
    from .voicestudio import selection
    session = _load(store, session_id)
    if not isinstance(confirmation, str) or not confirmation.strip():
        raise ValueError("video_onboarding_user_confirmation_required")
    values = _values(session)
    if values.get("voice_provider") not in {None, "voicestudio"}:
        raise ValueError("video_onboarding_voice_provider_mismatch")
    previous = (session.get("voice") or {}).get("voice") or {}
    if previous.get("profile_id") == profile_id and pronunciations is None:
        pronunciations = previous.get("pronunciations")
    chosen = selection(discovery, profile_id, engine=engine, video_type=type_key(values), register=values.get("register"),
                       authorization=authorization, settings=settings, pronunciations=pronunciations)
    session["answers"]["voice_provider"] = {"value": "voicestudio", "origin": "user", "at": iso(now or utcnow())}
    session["voice"] = {**chosen, "confirmation": confirmation.strip(), "at": iso(now or utcnow())}
    _save(store, session, now, "voice_chosen", {"profile_id": profile_id, "engine": chosen["voice"]["engine"]})
    return next_step(store, session_id)


def _speaker(session):
    values = _values(session)
    provider = values.get("voice_provider")
    if provider == "voicestudio" and session.get("voice"):
        voice = session["voice"]["voice"]
        return {"narrator": {"name": voice["name"], "voice": voice}}
    if provider == "system":
        return {"narrator": {"name": "Narrateur", "voice": {"provider": "system", "name": values.get("system_voice", "Microsoft Hortense Desktop"),
                                                            "authorization": "Voix standard du système, sans clonage."}}}
    return None


def build_brief(session):
    values = _values(session)
    kind = values.get("video_type")
    mode = TYPES[kind]["mode"] if kind in TYPES and kind != "other" else values.get("mode")
    imported = session.get("imported_brief") or {}
    notes = [f"Type de vidéo : {TYPES[kind]['label']}" + (f" ({values['video_type_note']})" if values.get("video_type_note") else "")]
    if values.get("register"):
        notes.append("Registre : " + {"analytic": "analyse posée", "dynamic": "commentaire dynamique"}[values["register"]])
    for key, label in (("objective", "Objectif"), ("angle", "Angle"), ("means", "Moyens disponibles")):
        if values.get(key):
            notes.append(f"{label} : {values[key]}")
    if imported.get("notes"):
        notes.append(imported["notes"])
    links, documents = list(imported.get("links", [])), list(imported.get("documents", []))
    for item in values.get("sources", []):
        (links if item.startswith("https://") else documents).append(item)
    brief = {"story_id": session.get("story_id") or imported.get("story_id") or session["session_id"], "topic": values["topic"],
             "mode": mode, "autonomy": values["autonomy"], "audience": values["audience"],
             "duration_minutes": values["duration_minutes"], "format": values["format"], "notes": "\n".join(notes),
             "links": sorted(set(links)), "documents": sorted(set(documents)), "media": values.get("media", []),
             "budget": {"limit": values["budget_limit"], "currency": values["currency"]},
             "audio_workflow": values["voice_provider"], "video_onboarding": {"session_id": session["session_id"], "video_type": kind}}
    if values.get("media"):
        brief["media_rights"] = {path: values["media_rights"] for path in values["media"]}
    for key in ("tone", "mandatory", "exclusions"):
        if values.get(key):
            brief[key] = values[key]
    for key in ("source_metadata", "creative_references"):
        if imported.get(key):
            brief[key] = imported[key]
    if values["voice_provider"] == "elevenlabs_browser":
        brief["budget"]["browser_credit_limit"] = values["browser_credit_limit"]
    speakers = _speaker(session)
    if speakers:
        brief["speakers"] = speakers
    return brief


def frame_story(store, session_id, *, now=None):
    from .storytelling import frame
    session = _load(store, session_id)
    view = progress(store, session)
    missing = [s for s in ("format", "topic", "framing", "voice") if view["stages"][s]["status"] != "complete"]
    if missing:
        raise ValueError("video_onboarding_stage_incomplete_" + missing[0])
    brief = build_brief(session)
    record = frame(store, brief, now=now)
    session.update(story_id=record["story_id"], brief_revision=record["revision"], brief_digest=digest(brief))
    _save(store, session, now, "framed", {"story_id": record["story_id"], "revision": record["revision"]})
    return {"story": record, "next": next_step(store, session_id)}


def _skills(values):
    known = {e["id"] for e in catalog()["entries"]}
    local = {p.parent.name for p in (ROOT / ".agents/skills").glob("sandbox-*/SKILL.md")}
    if not isinstance(values, list) or any(not isinstance(v, str) or v not in known | local for v in values):
        raise ValueError("video_onboarding_unknown_skill")
    return sorted(set(values))


_CATALOG = {}


def catalog():
    path = ROOT / ".agents/vendor/catalog.json"
    stamp = path.stat().st_mtime_ns if path.exists() else None
    if _CATALOG.get("stamp") != stamp:
        _CATALOG.update(stamp=stamp, value=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"entries": []})
    return _CATALOG["value"]


def route(stage, answers):
    """Skills to load for this stage only, resolved to their installed file."""
    table = ROUTES.get(stage, {})
    kind = type_key(answers)
    items = list(table.get(kind, table.get("*", [])))
    if stage == "format" and answers.get("video_type") == "other":
        items = list(table["other"])
    if stage == "writing" and (answers.get("format") == "9:16" or answers.get("duration_minutes", 99) <= 3):
        items += SHORT_FORM
    entries = {e["id"]: e for e in catalog()["entries"]}
    result = []
    for skill, purpose in items:
        if "/" in skill:
            entry = entries.get(skill)
            if entry is None:
                raise ValueError("video_onboarding_routed_skill_missing:" + skill)
            result.append({"id": skill, "path": entry["path"], "language": entry["language"], "purpose": purpose})
        else:
            result.append({"id": skill, "path": f".agents/skills/{skill}/SKILL.md", "language": "fr", "purpose": purpose})
    return result


def _words(text):
    return re.findall(r"[\wÀ-ÿ’'-]+", text)


def _texts(path):
    """Spoken units from a StoryTelling script JSON or paragraphs of a text file."""
    content = Path(path).read_text(encoding="utf-8-sig")
    if Path(path).suffix.lower() == ".json":
        script = json.loads(content)
        units = [u for scene in (script.get("scenes", []) if isinstance(script, dict) else []) for u in scene.get("utterances", [])]
        if any(not isinstance(u.get("utterance_id"), str) or not isinstance(u.get("text"), str) for u in units):
            raise ValueError("video_onboarding_script_invalid")
        return [{"id": u["utterance_id"], "text": u["text"]} for u in units]
    content = re.sub(r"(?m)^\s*(?:#.*|[-*_]{3,})\s*$", "", content)
    return [{"id": f"p{index}", "text": part.strip()} for index, part in enumerate(re.split(r"\n\s*\n", content), 1) if part.strip()]


def spoken_report(units, *, target_seconds=None, words_per_minute=155, sentence_words=28):
    """Text diagnostics before synthesis. Listening remains a separate human check."""
    issues, total = [], 0
    def flag(uid, code, excerpt, advice):
        issues.append({"utterance_id": uid, "code": code, "excerpt": excerpt[:120], "advice": advice})
    for unit in units:
        text, uid = unit["text"], unit["id"]
        words = _words(text)
        total += len(words)
        for match in re.finditer(r"https?://\S+|www\.\S+", text):
            flag(uid, "url", match.group(), "Une adresse ne se lit pas : la retirer ou la dire en mots.")
        for match in re.finditer(r"\d[\d\s.,]*\d|\d", text):
            flag(uid, "digits", match.group(), "Écrire le nombre comme il doit être dit (année, montant, ordinal).")
        for match in re.finditer(r"[%€$£&/+=#@*°×~§]", text):
            flag(uid, "symbols", match.group(), "Remplacer le symbole par des mots.")
        for match in ABBREVIATIONS.finditer(text):
            flag(uid, "abbreviation", match.group(), "Écrire l'abréviation en toutes lettres.")
        for match in re.finditer(r"[()\[\]{}]", text):
            flag(uid, "brackets", text[max(0, match.start()-30):match.end()+30], "Une parenthèse ne s'entend pas : intégrer ou supprimer l'incise.")
        for match in re.finditer(r"\b[A-ZÀ-Ý]{2,6}s?\b", text):
            flag(uid, "acronym", match.group(), "Fixer la prononciation du sigle (épelé ou lu) dans le dictionnaire de la voix.")
        if "—" in text or " – " in text or " - " in text:
            flag(uid, "dash", "—", "Un tiret ne garantit pas de pause : préférer une virgule ou un point.")
        sentences = [s for s in re.split(r"(?<=[.!?…])\s+", text) if s.strip()]
        for sentence in sentences:
            if len(_words(sentence)) > sentence_words:
                flag(uid, "long_sentence", sentence, f"Phrase de plus de {sentence_words} mots : la couper pour respirer.")
        starts = [(_words(s) or [""])[0].casefold() for s in sentences]
        for first, second in zip(starts, starts[1:]):
            if first and first == second:
                flag(uid, "same_opening", first, "Deux phrases de suite commencent par le même mot.")
        if not re.search(r"[.!?…»]\s*$", text):
            flag(uid, "final_punctuation", text[-40:], "Terminer par une ponctuation pour marquer la respiration.")
        if len(words) > 160:
            flag(uid, "long_unit", text[:60], "Plus d'une minute d'un seul tenant : découper en répliques.")
        seen = {}
        for index, word in enumerate(w.casefold() for w in words):
            if len(word) >= 6 and word not in STOPWORDS:
                if word in seen and index - seen[word] <= 25:
                    flag(uid, "repetition", word, "Mot répété à moins de vingt-cinq mots d'intervalle.")
                seen[word] = index
    counts = {}
    for issue in issues:
        counts[issue["code"]] = counts.get(issue["code"], 0) + 1
    estimate = round(total / words_per_minute * 60, 1)
    blocking = sorted(code for code in counts if code in BLOCKING_SPOKEN)
    return {"units": len(units), "words": total, "estimated_seconds": estimate, "target_seconds": target_seconds,
            "duration_ratio": round(estimate / target_seconds, 2) if target_seconds else None,
            "counts": counts, "blocking_codes": blocking, "status": "failed" if blocking else "warning" if issues else "passed",
            "issues": issues[:500], "validation": "text_diagnostics_only_listening_pending"}


def _story(store, session):
    from .storytelling import _record
    if not session.get("story_id"):
        return None, None
    try:
        row = _record(store, session["story_id"])
    except ValueError:
        return None, None
    return row, store.get("storytelling_project", session["story_id"]) or {}


def _auto(store, session, stage, artifacts):
    """Checks the engine can establish itself from files and the StoryTelling state."""
    values = _values(session)
    row, project = _story(store, session)
    result = {}
    target = values.get("duration_minutes", 0) * 60 or None
    if stage in {"writing", "spoken_revision"}:
        units = [u for a in artifacts if Path(a["path"]).suffix.lower() in {".json", ".md", ".txt"} for u in _texts(a["path"])]
        report = spoken_report(units, target_seconds=target)
        if stage == "writing":
            ratio = report["duration_ratio"]
            status = "failed" if not units else "passed" if ratio is None or .75 <= ratio <= 1.15 else "warning"
            result["duration_fit"] = {"status": status, "note": f"{report['words']} mots, environ {report['estimated_seconds']} s pour {target} s visées."}
        else:
            result["spoken_report"] = {"status": report["status"] if units else "failed", "report": report,
                                       "note": "Codes bloquants : " + ", ".join(report["blocking_codes"]) if report["blocking_codes"] else "Diagnostic textuel ; l'écoute reste à faire."}
    if stage == "storyboard":
        ok = bool(row and project.get("script_revision") and project.get("brief_revision") == row["revision"])
        result["script_imported"] = {"status": "passed" if ok else "failed", "script_revision": project.get("script_revision") if project else None}
    if stage in {"production", "controls", "exports"}:
        done = bool(project and project.get("status") == "completed" and project.get("export"))
        if stage == "production":
            result["story_completed"] = {"status": "passed" if done else "failed", "project_status": (project or {}).get("status")}
            provider = values.get("voice_provider")
            profile = ((session.get("voice") or {}).get("voice") or {}).get("profile_id")
            rows = [u for s in ((project or {}).get("audio") or {}).get("scenes", []) for u in s.get("utterances", [])]
            # The browser workflow imports files as recordings after its own voice-binding checks.
            allowed = {"recordings"} if provider == "elevenlabs_browser" else {provider}
            mismatch = [u["utterance_id"] for u in rows if u.get("provider") not in allowed
                        or profile and u.get("provider_metadata", {}).get("profile_id") != profile]
            result["voice_attribution"] = {"status": "passed" if rows and not mismatch else "failed", "mismatched": mismatch[:20]}
        if stage == "controls":
            from .storytelling_render import checked
            try:
                checked(((project or {}).get("export") or {}).get("artifacts", []))
                status = "passed" if done else "failed"
            except (ValueError, OSError):
                status = "failed"
            result["technical_exports"] = {"status": status, "export_sha256": ((project or {}).get("export") or {}).get("sha256")}
        if stage == "exports":
            export = (project or {}).get("export") or {}
            present = done and all(export.get(k) and Path(export[k]).is_file() for k in ("path", "srt", "vtt")) and bool(project.get("manifest"))
            result["export_files"] = {"status": "passed" if present else "failed",
                                      "files": {k: export.get(k) for k in ("path", "srt", "vtt")}, "manifest": (project or {}).get("manifest")}
    return result


def _basis(session, stage):
    """Fingerprint of everything a stage result depends on."""
    index = STAGE_IDS.index(stage)
    earlier = {s: session["stages"].get(s, {}).get("revision") for s in STAGE_IDS[:index] if s not in QUESTION_STAGES}
    # Research, structure and the first draft do not depend on the chosen voice.
    narrated = index >= STAGE_IDS.index("narrator_adaptation")
    voice = (session.get("voice") or {}).get("voice") if narrated else None
    answers = {k: v for k, v in _values(session).items() if narrated or not k.startswith(("voice_", "system_voice", "browser_credit"))}
    return digest({"answers": answers, "voice": voice, "earlier": earlier})


def _copy(path, directory):
    source = Path(path).resolve(strict=True)
    if not source.is_file():
        raise ValueError("video_onboarding_artifact_missing")
    sha = fingerprint(source)
    if source.stat().st_size > 20 * 1024 * 1024:
        return {"path": str(source), "sha256": sha, "label": source.name, "copied": False}
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (sha + source.suffix.lower())
    if not target.exists():
        shutil.copyfile(source, target)
    if fingerprint(target) != sha:
        raise ValueError("video_onboarding_artifact_changed")
    return {"path": str(target), "sha256": sha, "label": source.name, "source": str(source), "copied": True}


def evaluate(stage, given, automatic):
    """Merge engine checks with reported ones; a human check needs who confirmed it and how."""
    if not isinstance(given, dict):
        raise ValueError("video_onboarding_checks_invalid")
    evaluated = dict(automatic)
    for check, kind, label in CHECKS.get(stage, []):
        if kind == "auto":
            evaluated[check] = {**evaluated[check], "kind": kind, "label": label}
            continue
        value = given.get(check)
        if not isinstance(value, dict) or value.get("status") not in {"passed", "failed", "not_applicable", "pending", "waived"}:
            raise ValueError("video_onboarding_check_status_required:" + check)
        if kind == "human" and value["status"] in {"passed", "failed", "waived"} and not all(
                isinstance(value.get(k), str) and value[k].strip() for k in ("confirmed_by", "evidence")):
            raise ValueError("video_onboarding_human_check_needs_confirmation:" + check)
        if kind != "human" and value["status"] in {"pending", "waived"}:
            raise ValueError("video_onboarding_agent_check_must_be_done:" + check)
        evaluated[check] = {**{k: value[k] for k in ("status", "note", "confirmed_by", "evidence") if isinstance(value.get(k), str)},
                            "kind": kind, "label": label}
    statuses = {v["status"] for v in evaluated.values()}
    return evaluated, "needs_revision" if "failed" in statuses else "awaiting_user" if "pending" in statuses else "complete"


def record_stage(store, session_id, stage, *, artifacts=(), skills_used=(), checks=None, summary="", status="complete",
                 reason=None, now=None):
    """Store a work stage result. Its later stages become stale when the result changes."""
    session = _load(store, session_id)
    if stage not in STAGE_IDS or stage in QUESTION_STAGES:
        raise ValueError("video_onboarding_not_a_work_stage")
    view = progress(store, session)
    index = STAGE_IDS.index(stage)
    blocked = [s for s in STAGE_IDS[:index] if view["stages"][s]["status"] not in {"complete", "not_applicable"}]
    if blocked:
        raise ValueError("video_onboarding_previous_stage_incomplete_" + blocked[0])
    if not view["story_framed"]:
        raise ValueError("video_onboarding_frame_story_first")
    values = _values(session)
    if status == "not_applicable":
        if stage not in OPTIONAL_STAGES.get(type_key(values), set()) or not isinstance(reason, str) or not reason.strip():
            raise ValueError("video_onboarding_stage_required")
        result = {"status": "not_applicable", "reason": reason.strip()}
    elif status == "complete":
        skills = _skills(list(skills_used))
        directory = store.directory / "video-onboarding" / session_id / stage
        files = [_copy(p, directory) for p in artifacts]
        if not files and stage in {"research", "structure", "writing", "narrator_adaptation", "french_revision", "spoken_revision"}:
            raise ValueError("video_onboarding_artifact_required")
        evaluated, state = evaluate(stage, checks or {}, _auto(store, session, stage, files))
        _, project = _story(store, session)
        result = {"status": state, "artifacts": files, "skills_used": skills, "checks": evaluated,
                  "summary": summary.strip() if isinstance(summary, str) else "",
                  "story_revision": (project or {}).get("revision"), "script_revision": (project or {}).get("script_revision")}
    else:
        raise ValueError("video_onboarding_invalid_stage_status")
    result.update(at=iso(now or utcnow()), basis=_basis(session, stage))
    result["revision"] = digest({k: v for k, v in result.items() if k != "at"})
    session["stages"][stage] = result
    _save(store, session, now, "stage_recorded", {"stage": stage, "status": result["status"]})
    return next_step(store, session_id)


def progress(store, session):
    values = _values(session)
    stages, story_row, project = {}, *_story(store, session)
    for stage, title, _ in STAGES:
        fields = [f for f, spec in FIELDS.items() if spec["stage"] == stage]
        if stage in QUESTION_STAGES:
            missing = [f for f in fields if _required(f, values) and f not in values]
            status = "complete" if not missing else "pending"
            if stage == "topic" and missing and session["topic_proposals"]:
                status = "awaiting_user"
            if stage == "voice" and not missing and values.get("voice_provider") == "voicestudio" and not session.get("voice"):
                status = "awaiting_user"
            stages[stage] = {"status": status, "missing": missing}
            continue
        saved = session["stages"].get(stage)
        if not saved:
            stages[stage] = {"status": "pending"}
            continue
        status, reason = saved["status"], None
        if saved["basis"] != _basis(session, stage):
            status, reason = "stale", "Une réponse, la voix ou une étape précédente a changé depuis ce résultat."
        elif stage in {"storyboard"} and project is not None and saved.get("script_revision") != project.get("script_revision"):
            status, reason = "stale", "Le scénario importé a changé."
        elif stage in {"production", "controls", "exports"} and project is not None and saved.get("story_revision") != project.get("revision"):
            status, reason = "stale", "Le rendu a changé ; les contrôles liés à l'ancienne empreinte ne valent plus."
        stages[stage] = {"status": status, "stale_reason": reason}
    framed = bool(story_row and session.get("brief_revision") == story_row["revision"])
    ready = all(stages[s]["status"] == "complete" for s in QUESTION_STAGES)
    # Answers changed after framing: StoryTelling must receive the new brief first.
    outdated = framed and ready and digest(build_brief(session)) != session.get("brief_digest")
    current = next((s for s in STAGE_IDS if stages[s]["status"] not in {"complete", "not_applicable"}), None)
    return {"stages": stages, "current_stage": current, "story_framed": framed and not outdated, "story_outdated": outdated}


def _commands(session, stage):
    sid, story = session["session_id"], session.get("story_id") or "STORY_ID"
    base = "python -m youtube_growth.factory "
    table = {
        "topic": [base + f"video-onboarding propose {sid} --file propositions.json",
                  base + f"video-onboarding choose {sid} --proposal RANG --confirmation \"mots de Lou\""],
        "voice": [base + "voicestudio profiles",
                  base + f"video-onboarding voice {sid} --profile PROFIL --confirmation \"mots de Lou\""],
        "research": [base + f"video-onboarding frame {sid}", base + f"storytelling-run {story}"],
        "storyboard": [base + f"storytelling-script {story} scenario.json"],
        "production": [base + f"storytelling-run {story} --queue", base + f"storytelling-control {story} approve"],
    }
    commands = table.get(stage, [])
    if stage not in QUESTION_STAGES:
        commands = commands + [base + f"video-onboarding record {sid} --stage {stage} --file resultat.json"]
    if stage == "spoken_revision":
        commands.insert(0, base + "video-onboarding spoken-check texte.md")
    return commands


def next_step(store, session_id, *, limit=3):
    session = _load(store, session_id)
    values = _values(session)
    view = progress(store, session)
    stage = view["current_stage"]
    result = {"session_id": session_id, "story_id": session.get("story_id"), "video_type": values.get("video_type"),
              "stages": [{"id": s, "title": t, "status": view["stages"][s]["status"]} for s, t, _ in STAGES],
              "answers": values, "voice": (session.get("voice") or {}).get("voice"), "story_framed": view["story_framed"]}
    if stage is None:
        return {**result, "current_stage": None, "message": "Toutes les étapes sont terminées."}
    title, goal = next((t, g) for s, t, g in STAGES if s == stage)
    pending = view["stages"][stage].get("missing", [])
    questions = []
    for field in pending[:limit]:
        spec = FIELDS[field]
        recommendation = spec.get("recommend")
        if field == "duration_minutes":
            recommendation = store.setting("storytelling_preferences", {}).get("duration_minutes") or DURATIONS.get(type_key(values))
        questions.append({"field": field, "question": spec["question"], "choices": spec.get("choices", []),
                          "labels": {k: TYPES[k]["label"] for k in TYPES} if field == "video_type" else {},
                          "recommendation": recommendation})
    optional = [f for f, spec in FIELDS.items() if spec["stage"] == stage and spec.get("optional") and f not in values]
    decisions = []
    if stage == "topic" and session["topic_proposals"]:
        decisions.append({"kind": "topic_choice", "proposals": session["topic_proposals"],
                          "message": "Présenter les propositions et attendre le choix de Lou."})
    if stage == "voice" and values.get("voice_provider") == "voicestudio" and not session.get("voice"):
        decisions.append({"kind": "voice_choice", "message": "Lister les profils Voice Studio disponibles et attendre le choix de Lou."})
    if stage == "research" and not view["story_framed"]:
        decisions.append({"kind": "frame_story", "message": "Créer ou mettre à jour l'histoire StoryTelling à partir des réponses."})
    saved = session["stages"].get(stage, {})
    return {**result, "current_stage": {"id": stage, "title": title, "goal": goal, "status": view["stages"][stage]["status"],
                                        "stale_reason": view["stages"][stage].get("stale_reason"),
                                        "previous_checks": saved.get("checks")},
            "questions": questions, "optional_questions": [{"field": f, "question": FIELDS[f]["question"]} for f in optional],
            "decisions": decisions, "skills": route(stage, values),
            "references": [GUIDE + "parcours.md#" + stage.replace("_", "-")] + REFERENCES.get(stage, []),
            "checks": [{"id": c, "kind": k, "label": l} for c, k, l in CHECKS.get(stage, [])],
            "commands": _commands(session, stage)}


def sessions(store):
    rows = []
    for session in sorted(store.records("video_onboarding"), key=lambda s: s.get("updated_at", ""), reverse=True):
        view = progress(store, session)
        rows.append({"session_id": session["session_id"], "topic": _values(session).get("topic"),
                     "video_type": _values(session).get("video_type"), "story_id": session.get("story_id"),
                     "current_stage": view["current_stage"], "updated_at": session.get("updated_at"),
                     "voice": (session.get("voice") or {}).get("voice", {}).get("name"),
                     "stages": [{"id": s, "title": t, "status": view["stages"][s]["status"]} for s, t, _ in STAGES]})
    return rows
