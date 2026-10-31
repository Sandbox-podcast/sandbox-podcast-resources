# Parcours d'une nouvelle vidéo

La sortie de `video-onboarding show SESSION` donne l'étape courante, les skills routés selon le type de vidéo et les contrôles attendus. Cette référence explique ce que chaque étape doit produire. La table de routage complète se trouve dans `ROUTES` de [video_onboarding.py](../../../../tools/youtube-growth/src/youtube_growth/factory/video_onboarding.py).

## Enregistrer une étape de travail

```json
{
  "stage": "structure",
  "artifacts": [".local/video-onboarding/SESSION/structure.md"],
  "skills_used": ["screenwriting-skills/sw-story-structure", "autopunk-media-skills/hook-generator@fr"],
  "checks": {
    "hook_promise": {"status": "passed", "note": "L'ouverture pose la question du basculement."},
    "progression": {"status": "passed"},
    "conclusion_answers": {"status": "passed"}
  },
  "summary": "Trois actes, accroche retenue : option 2."
}
```

```powershell
& $py -m youtube_growth.factory video-onboarding record SESSION --file resultat.json
```

Statuts d'un contrôle : `passed`, `failed`, `not_applicable` ; pour un contrôle humain, aussi `pending` et `waived`. Un contrôle humain `passed`, `failed` ou `waived` exige `confirmed_by` et `evidence`, c'est-à-dire qui l'a fait et les mots par lesquels Lou l'a confirmé. Un contrôle `failed` met l'étape en `needs_revision`. La factory copie les fichiers enregistrés et garde leur empreinte ; modifier ensuite le fichier d'origine n'altère pas la version enregistrée.

<a id="format"></a>
## Type de vidéo

Types : `documentary`, `explainer`, `commentary`, `fiction`, `docufiction`, `other`. Pour `commentary`, demander le registre : `analytic` ou `dynamic` (commentaire sportif ou de direct). Pour `other`, faire décrire le format et choisir le moteur du récit (`documentary`, `fiction` ou `mixed`) ; le skill `template-selector` aide à composer un ensemble de skills.

<a id="topic"></a>
## Sujet

Si Lou donne un sujet, l'enregistrer tel quel. Sinon, utiliser les skills routés (Trend Hunter pour une tendance, `story-angle-finder`, `niche-video-idea-generator`, `trending-topics-brief`, `sw-premise-theme` pour une fiction). Présenter trois à six propositions avec leur angle, leur intérêt et leurs sources, les enregistrer avec `propose`, puis attendre. Le choix s'enregistre avec `choose --proposal RANG --confirmation "..."` ou `choose --topic "..." --confirmation "..."`.

```json
{"proposals": [{"title": "...", "angle": "...", "why": "...", "sources": ["https://..."], "skills_used": ["autopunk-media-skills/story-angle-finder"]}]}
```

<a id="framing"></a>
## Cadrage

Questions : public, objectif, angle, durée, format 16:9 ou 9:16, sources, médias et leurs droits, éléments obligatoires, exclusions, moyens disponibles, ton, mode de validation, plafond de dépense et devise. La durée proposée dépend du type de vidéo ou des préférences enregistrées. Un plafond de 0 garde la production locale ; Voice Studio ne consomme aucun crédit externe.

<a id="voice"></a>
## Narrateur

Choisir la source de voix, puis, pour Voice Studio, suivre [voix.md](voix.md) : lister les profils réellement présents, montrer leur consentement et les moteurs utilisables, attendre le choix de Lou, puis `voice SESSION --profile ID --confirmation "..."`. La factory fixe le profil, sa révision, le moteur et les réglages vérifiés. La voix est choisie avant la rédaction parce qu'elle entre dans le brief de StoryTelling ; l'adaptation du texte à cette voix vient après le premier jet.

<a id="research"></a>
## Recherche et sources

Exécuter `frame SESSION` : la factory crée l'histoire StoryTelling avec les réponses et la voix, puis importe les sources. Lancer ensuite `storytelling-run STORY_ID` : sans modèle local, la factory exporte la requête de scénario (`request_path`) qui contient les `source_id`, les textes importés et le schéma. Établir avec les skills routés un dossier de faits : affirmation, source, citation exacte, statut, limites. Une source ajoutée en cours de route passe par `answer --set sources=[...]`, puis un nouveau `frame`. Pour une fiction sans contexte réel, enregistrer `"status": "not_applicable"` avec un motif.

<a id="structure"></a>
## Structure narrative

Définir la question centrale, la raison de s'y intéresser, la réponse visée et la progression scène par scène : ce que le public sait avant et après chaque scène. L'introduction donne une raison de rester, chaque partie prépare la suivante, la conclusion répond à la promesse sans l'excéder. Comparer les accroches de `hook-generator@fr` et retenir celle que les faits soutiennent.

<a id="writing"></a>
## Texte intégral

Rédiger tout le texte prononcé avec les skills du type : commentaire et narration documentaire, script d'explication minuté, chronique, scènes et dialogues de fiction. Pour un format vertical ou de trois minutes au plus, la factory ajoute les skills de format court. Garder les faits reliés au dossier de recherche. Le contrôle `duration_fit` compare le volume de texte à la durée visée, à environ 155 mots par minute.

<a id="narrator-adaptation"></a>
## Adaptation au narrateur

Appliquer `narrator-voice-adapter` avec la description de la voix choisie : registre, personne grammaticale, longueur des phrases, tournures habituelles. Pour la voix de Lou, s'appuyer sur sa façon de parler dans les épisodes ou sur ses textes, pas sur une imitation. Ne modifier aucun fait, chiffre, nom ni citation.

<a id="french-revision"></a>
## Révision du français

Appliquer `humaniseur-fr` en une seule passe, au registre demandé, puis `redundancy-checker` et `tone-consistency-checker`. Pour un texte factuel, `unattributed-claims-checker` repère les affirmations devenues orphelines. Relire ensuite les faits contre le dossier : une reformulation ne doit ni durcir ni affaiblir une affirmation.

<a id="spoken-revision"></a>
## Révision pour l'oral

Suivre [revision-orale.md](revision-orale.md). Aucun des trois dépôts ne contient de skill « Spoken Script Editor » ; cette étape combine `teleprompter-script-writer`, `voice-over-script-writer`, le diagnostic `spoken-check` de la factory et la procédure SANDBOX. Le contrôle `spoken_report` échoue tant qu'il reste des chiffres, symboles, abréviations, parenthèses ou adresses à lire tels quels.

<a id="storyboard"></a>
## Storyboard

Écrire le scénario complet au schéma de la requête exportée : scènes, répliques, faits, plans reliés aux répliques, direction sonore. Chaque plan a une fonction et une source importée avec ses droits, ou un schéma explicatif réalisable. Préparer avec les skills routés les listes de plans, archives, images d'illustration, droits et sous-titres. Importer avec `storytelling-script STORY_ID scenario.json` : StoryTelling valide la structure et les citations. Le contrôle `script_imported` vérifie que ce scénario correspond au cadrage courant.

<a id="production"></a>
## Voix et montage

Si le mode de validation est `editorial_review`, montrer à Lou le scénario et le storyboard et attendre sa décision avant `storytelling-control STORY_ID approve`. Lancer ensuite `storytelling-run STORY_ID --queue` sur l'état du worker, ou sans `--queue` au premier plan. Avec Voice Studio, le service doit être lancé (voir [voix.md](voix.md)). Les contrôles automatiques vérifient le rendu terminé et l'attribution de chaque réplique à la voix choisie.

<a id="controls"></a>
## Contrôles

Garder séparés : `technical_exports` (fichiers et empreintes, automatique), `fact_check_final` (agent, texte final contre les sources), `listening_review` et `visual_review` (Lou ou une personne désignée, écoute et visionnage intégraux) et `editorial_validation` (Lou, sur la révision exportée). Les skills `fine-cut-notes` et `picture-lock-checklist` aident à préparer ces revues. Un nouveau rendu rend ces contrôles caducs.

<a id="exports"></a>
## Exports

Le contrôle `export_files` vérifie le MP4, les sous-titres SRT et VTT et le manifeste. Livrer les liens locaux, l'interface `/storytelling`, l'état des contrôles et les réserves. Les chapitres YouTube (`chapter-timestamps`) et le packaging (`sandbox-packaging`) restent facultatifs. Aucune publication ne fait partie de ce parcours.
