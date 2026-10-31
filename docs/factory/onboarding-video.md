# Créer une nouvelle vidéo avec l'onboarding

L'onboarding vidéo t'accompagne de l'idée aux exports. Tu réponds dans le chat ; l'agent pose les questions utiles, choisit les skills adaptés à chaque étape et fait avancer [StoryTelling Generator](storytelling-generator.md). Tes réponses, tes choix et les résultats de chaque étape sont enregistrés dans la factory locale : tu peux t'arrêter et reprendre plus tard, dans une autre session.

## Démarrer

Dans Codex ou Claude Code, ouvert sur ce dépôt, écris simplement :

```text
Je veux créer une nouvelle vidéo.
```

Le skill [`sandbox-video-onboarding`](../../.agents/skills/sandbox-video-onboarding/SKILL.md) se déclenche. Tu peux aussi l'appeler explicitement (`$sandbox-video-onboarding` dans Codex, `/sandbox-video-onboarding` dans Claude Code) et donner d'emblée ce que tu sais déjà :

```text
Je veux créer un documentaire de dix minutes sur la consommation d'eau des data centers,
pour un public curieux, à partir des fichiers joints. Utilise ma voix.
```

L'agent reprend les informations fournies et ne pose que les questions restantes, trois au plus à la fois. Une proposition (durée, public, format) reste une proposition tant que tu ne l'as pas acceptée.

## Les types de vidéos

| Type | Pour quoi | Récit dans StoryTelling |
| --- | --- | --- |
| Documentaire | Raconter des faits sourcés, une enquête ou un parcours | Documentaire |
| Explication | Faire comprendre un mécanisme ou une notion, pas à pas | Documentaire |
| Commentaire | Une chronique argumentée, ou un commentaire dynamique de type sportif | Documentaire |
| Récit de fiction | Une histoire originale avec personnages et dialogues | Fiction |
| Faits et reconstitutions | Un récit factuel avec des scènes reconstituées et annoncées | Mixte |
| Autre format | Un format à décrire ; l'agent compose l'ensemble de skills adapté | Selon ta réponse |

Un format vertical 9:16 ou de trois minutes au plus ajoute les skills d'écriture pour formats courts.

## Les questions de départ

1. **Type de vidéo**, et pour un commentaire, son registre : analyse posée ou commentaire dynamique.
2. **Sujet.** Sans sujet, l'agent cherche des pistes (veille Trend Hunter, angles, idées adaptées au public), te présente leurs angles et leurs sources, puis attend ton choix.
3. **Cadrage** : public, objectif, angle, durée, format 16:9 ou 9:16, sources, médias et leurs droits, éléments obligatoires, exclusions, moyens disponibles, ton, validation du scénario avant production ou non, plafond de dépense. Un plafond de 0 garde la production entièrement locale.
4. **Narrateur** : une voix de Voice Studio, une voix Windows ou ElevenLabs dans le navigateur.

## Le parcours et ses skills

Après ces réponses, l'agent crée l'histoire dans StoryTelling Generator et enchaîne les étapes. À chaque étape, il lit seulement les skills qui lui servent ; les 494 skills installés ne sont pas chargés d'un coup.

| Étape | Exemples de skills utilisés | Ce que tu examines |
| --- | --- | --- |
| Recherche et sources | `research-brief-creator`, `claim-fact-checker`, `source-cross-referencer`, `statistics-verifier` | Les faits retenus, leurs sources et leurs limites |
| Structure narrative | `sw-story-structure`, `hook-generator` (FR), `character-arc-planner`, `sw-character-conflict` en fiction | L'accroche, la progression, la conclusion |
| Texte intégral | `commentary-writer`, `documentary-narration-writer`, `animated-explainer-script-writer`, `full-script-writer`, `sw-scene-craft`, `sw-dialogue` | Le texte complet |
| Adaptation au narrateur | `narrator-voice-adapter`, `dialogue-polisher` en fiction | Le texte te ressemble-t-il ? |
| Révision du français | `humaniseur-fr`, `redundancy-checker`, `tone-consistency-checker` | Les formulations, sans changement des faits |
| Révision pour l'oral | `teleprompter-script-writer`, `voice-over-script-writer` et le diagnostic oral de la factory | Chiffres, sigles, respirations, rythme |
| Storyboard | `b-roll-shot-list`, `archival-footage-brief`, `rights-clearance-checklist`, `subtitles-rewriter` | Les plans, médias, droits et sous-titres |
| Voix et montage | StoryTelling Generator | La prévisualisation |
| Contrôles | `fine-cut-notes`, `picture-lock-checklist`, `claim-fact-checker` | Écoute, visionnage, validation |
| Exports | `chapter-timestamps` si besoin | Le MP4, les sous-titres, le manifeste |

La table complète, par type de vidéo, est dans le code de l'onboarding ; un test vérifie que chaque skill routé existe dans les collections installées. Aucune des collections ne contient de skill « Spoken Script Editor » : la révision orale suit une [procédure SANDBOX](../../.agents/skills/sandbox-video-onboarding/references/revision-orale.md).

## Choisir la voix

L'agent lit les profils réellement présents dans Voice Studio et te les présente avec leur langue, leur consentement et les moteurs compatibles. Il attend ton choix ; un profil ajouté plus tard par un autre membre apparaît sans changement de code. La voix choisie est fixée pour la vidéo : si son enregistrement de référence change, la production s'arrête et l'agent te redemande de choisir.

Voice Studio doit être lancé sur l'ordinateur, avec l'application ou son service local. La factory l'interroge sur `http://127.0.0.1:3900`.

L'interprétation se règle sur trois plans distincts :

- **l'identité vocale** : le profil, le moteur, la langue ;
- **la direction d'interprétation** : surtout le texte lui-même (longueur des phrases, ponctuation, mots), et une consigne seulement si le moteur l'applique ;
- **le traitement audio** : `broadcast`, `podcast`, `cinematic`, `warm`, `bright` ou `raw`, appliqué après la synthèse. Il change le timbre perçu, pas le jeu.

Dans Voice Studio 0.5.7, le moteur VoxCPM2 utilisé pour ta voix ignore le réglage de vitesse. Un commentaire sportif plus dynamique passe donc par l'écriture : phrases courtes au présent, relances, pauses plus brèves entre les phrases. VoxCPM2 accepte une consigne libre, mais elle modifie sa façon de cloner la voix ; l'agent ne l'adopte qu'après un essai comparé sur une phrase, que tu écoutes. OmniVoice applique la vitesse ; sa consigne ne décrit que le timbre. Le détail est dans la [référence voix](../../.agents/skills/sandbox-video-onboarding/references/voix.md).

## Les contrôles

Chaque étape enregistre ses contrôles avec leur nature :

- **automatiques**, calculés par la factory : durée estimée du texte, diagnostic oral, scénario importé, rendu terminé, voix attribuée à chaque réplique, fichiers exportés et empreintes ;
- **faits par l'agent** : sources et causalités, promesse du récit, cohérence, faits préservés après réécriture ;
- **humains** : l'écoute intégrale, le visionnage intégral et ta validation. Ils ne passent qu'avec tes mots, enregistrés tels quels.

Un contrôle échoué renvoie l'étape en reprise. Si tu changes une réponse, les étapes qui en dépendent passent à « À refaire » ; un nouveau rendu annule les contrôles liés à l'ancien fichier. Changer de voix conserve la recherche, la structure et le premier jet, mais pas l'adaptation au narrateur ni la suite.

## Reprendre

Dis par exemple « Reprends ma vidéo sur les data centers ». L'agent retrouve la session et repart de l'étape en cours. La page [StoryTelling Generator](http://127.0.0.1:8765/storytelling) affiche les vidéos guidées, leur étape et l'état de chaque étape, ainsi que les voix disponibles dans Voice Studio (étape « Voix et son »).

## Commandes

Les options globales `--config` et `--state-dir` précèdent la commande. Sous PowerShell, définir d'abord `$env:PYTHONPATH = 'tools/youtube-growth/src'`.

```powershell
python -m youtube_growth.factory video-onboarding list
python -m youtube_growth.factory video-onboarding start --set video_type=documentary --set "topic=Mon sujet"
python -m youtube_growth.factory video-onboarding start --brief .local/trend/storytelling-brief.json
python -m youtube_growth.factory video-onboarding show SESSION
python -m youtube_growth.factory video-onboarding answer SESSION --set duration_minutes=10 --set format=16:9
python -m youtube_growth.factory video-onboarding choose SESSION --proposal 2 --confirmation "La deuxième"
python -m youtube_growth.factory voicestudio profiles
python -m youtube_growth.factory voicestudio plan --video-type commentary --register dynamic
python -m youtube_growth.factory video-onboarding voice SESSION --profile f92d4b17 --confirmation "Ma voix"
python -m youtube_growth.factory video-onboarding frame SESSION
python -m youtube_growth.factory video-onboarding spoken-check texte.md --target-minutes 10
python -m youtube_growth.factory video-onboarding record SESSION --file resultat.json
```

Le format des résultats d'étape et des propositions est décrit dans le [parcours détaillé](../../.agents/skills/sandbox-video-onboarding/references/parcours.md). Les fichiers de travail vont dans `.local/video-onboarding/`, ignoré par Git ; la factory en garde une copie avec son empreinte.

Les contrôles réellement exécutés lors de la mise en place sont dans le [rapport de validation du 31 octobre](validation-onboarding-video-2026-10-31.md).

## Les collections de skills

Les skills externes sont installés dans [`.agents/vendor/`](../../.agents/vendor/README.md), à des révisions épinglées et avec leurs licences : Autopunk Media Skills (408 skills, 50 variantes localisées, 9 agents), Screenwriting Skills (26 skills, rédigés en chinois ; l'agent répond en français) et Humaniseur FR. `python tools/repository/vendor_skills.py check` vérifie leur contenu ; `find` cherche un skill dans le catalogue.

## Limites actuelles

- Les intentions de jeu du scénario (`emotion`, `pace`, `intensity`) guident l'écriture, pas la synthèse : seules la pause entre les phrases et la pause après une réplique (`pause_after_seconds`) entrent dans le rendu.
- Le moteur d'émotions IndexTTS2 n'est pas installé dans Voice Studio ; aucun réglage d'émotion n'est envoyé.
- L'onboarding ne lance pas Voice Studio : il signale le service indisponible et indique comment le démarrer.
- Une transcription ou une mesure automatique ne remplace ni l'écoute ni le visionnage.
- Aucune étape ne publie ni ne programme la vidéo.
