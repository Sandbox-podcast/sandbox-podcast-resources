---
name: sandbox-storytelling-generator
description: Ouvrir StoryTelling Generator, créer une vidéo narrative à partir d'un brief complet, ou reprendre et corriger une histoire existante dans la factory SANDBOX. Utiliser pour le scénario, le storyboard, les voix Voice Studio ou ElevenLabs et le montage ; pour « je veux créer une nouvelle vidéo » sans brief complet, utiliser sandbox-video-onboarding, et pour chercher des tendances, sandbox-youtube-trend-hunter.
---

# StoryTelling Generator

Piloter le moteur existant depuis le chat et conserver son état dans SQLite. Lire le [tutoriel](../../../docs/factory/storytelling-generator.md) pour le cadrage, les modes et les commandes. Le sujet vient de la demande de Lou ; les prompts et guides narratifs fournis décrivent la méthode. Distinguer leurs instructions des sources documentaires et du sujet à raconter.

## Ouvrir ou reprendre

Si Lou demande seulement de lancer ou d'ouvrir le générateur, ouvrir son interface sans créer d'histoire. Pour une reprise, retrouver le `story_id`, la configuration et le dossier d'état avant de relancer le travail.

Depuis la racine du dépôt, utiliser le Python de l'environnement factory disponible et définir séparément `$env:PYTHONPATH = 'tools/youtube-growth/src'`. Exécuter `doctor` et `status` avec la configuration et l'état choisis. Les options globales `--config` et `--state-dir` précèdent la commande.

Réutiliser un serveur local compatible. Son `/api/state` expose `context.state_directory` et `context.database` : vérifier qu'il sert le projet attendu. Si aucun serveur ne convient, suivre [l'exploitation](../../../docs/factory/exploitation.md) pour les dépendances, puis lancer :

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
& ./.local/factory-venv/Scripts/python.exe -m youtube_growth.factory serve --with-worker
```

Cette commande reste au premier plan. Pour un lancement par l'agent sous Windows, utiliser un processus masqué avec des journaux locaux. Réutiliser un worker existant sur le même état plutôt qu'en lancer un second. Ouvrir `/storytelling` sur le port réellement utilisé, `8765` par défaut. Garder serveur, worker et commandes sur la même base ; une nouvelle base masquerait les histoires existantes.

## Créer une histoire

Pour une nouvelle vidéo dont le type, le sujet ou la voix restent à définir, appliquer [sandbox-video-onboarding](../sandbox-video-onboarding/SKILL.md) : il pose les questions progressivement, conserve les réponses et crée l'histoire ici. Si une session d'onboarding existe pour l'histoire (`brief.video_onboarding`), poursuivre cette session plutôt qu'un parcours parallèle.

Lire les fichiers et les choix déjà fournis avant de demander les précisions qui changent le récit. Recueillir le sujet, les sources, le type de récit, le public, la durée, le format et le mode de validation. Proposer les valeurs initiales du tutoriel seulement lorsque Lou n'a pas donné de préférence.

Si le Trend Hunter a produit `storytelling-brief.json`, utiliser ce brief et son dossier documentaire directement. Le choix d'un sujet ne valide ni le scénario ni une dépense. Conserver les plafonds déjà autorisés pour cette histoire ; si un plafond manque, poursuivre le travail local et le demander avant toute génération payante.

Préparer les fichiers structurés pour Lou et exécuter les commandes ; ne pas lui demander de construire les JSON. Les sources et les sorties restent dans l'espace local de la factory.

```powershell
& ./.local/factory-venv/Scripts/python.exe -m youtube_growth.factory storytelling-frame CHEMIN_BRIEF.json
& ./.local/factory-venv/Scripts/python.exe -m youtube_growth.factory storytelling-run STORY_ID
```

Lire [le parcours de production et de reprise](references/production.md) pour traiter la requête de scénario exportée, importer le texte complet et poursuivre le même `story_id`. Utiliser le schéma courant du moteur, distinct du scénario historique du Trend Hunter. Une attente du modèle local doit conduire à traiter la requête dans Codex, puis à l'importer.

Respecter le mode de validation choisi. Un documentaire autonome exige sa vérification éditoriale distincte ; si elle manque, signaler ce blocage et continuer les étapes indépendantes. Une approbation humaine doit venir de Lou et porter sur la révision courante.

## Produire le son et corriger

Pour une voix Voice Studio, le worker appelle l'API locale avec le profil fixé dans le brief ; lire [la référence voix de l'onboarding](../sandbox-video-onboarding/references/voix.md) pour lancer le service, les réglages réellement appliqués et les erreurs.

Pour ElevenLabs dans le navigateur intégré, lire la section navigateur de la [référence de production](references/production.md) et appliquer le contrat courant de `storytelling_browser.py`. Utiliser la session connectée avec les outils de computer use ; le worker seul n'effectue pas ces manipulations.

Enregistrer chaque tentative avant la génération, puis rattacher le téléchargement exact à sa demande avec la voix et la provenance observées. Respecter le plafond de crédits de cette histoire. Une tentative `submitted` ou `unknown` impose de retrouver son résultat avant une autre soumission pour la même ancre. Conserver l'attribution des voix et les fichiers mesurés.

Pour une correction, modifier la scène ou la ressource dans le projet existant, conserver les verrous et réutiliser les dépendances compatibles. Reprendre la production jusqu'aux exports ou jusqu'à un besoin externe précisément identifié.

Vérifier les fichiers produits et leur manifeste ; distinguer contrôles techniques, examen des sources, écoute et revue visuelle réellement effectués. Livrer les liens locaux du MP4, des sous-titres et de l'interface, avec l'état courant et toute validation encore nécessaire.
