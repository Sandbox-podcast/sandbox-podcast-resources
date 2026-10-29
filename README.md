<div align="center">

<img src="docs/readme/hero.png" alt="SANDBOX. Les coulisses du podcast. Ressources éditoriales, vidéo et outils de production." width="1000">

# Les coulisses de SANDBOX

Les ressources et les outils avec lesquels nous préparons le podcast.<br>
Du master vidéo aux extraits, jusqu'aux kits de diffusion et au suivi des résultats.

[![Contrôles des ressources](https://github.com/Sandbox-podcast/sandbox-podcast-resources/actions/workflows/ci.yml/badge.svg)](https://github.com/Sandbox-podcast/sandbox-podcast-resources/actions/workflows/ci.yml)
[![Contrôles YouTube](https://github.com/Sandbox-podcast/sandbox-podcast-resources/actions/workflows/youtube-growth.yml/badge.svg)](https://github.com/Sandbox-podcast/sandbox-podcast-resources/actions/workflows/youtube-growth.yml)
[![Diffusion simulée](https://img.shields.io/badge/diffusion-simulation-00C8E8?style=flat&labelColor=101923)](docs/factory/README.md)

[Le podcast](https://www.sandboxpodcast.fr/) · [YouTube](https://www.youtube.com/@SandboxFR) · [La factory](#la-factory) · [Démarrer](#démarrer-en-local) · [Contribuer](#contribuer)

</div>

SANDBOX est un talkshow français sur les effets de l'IA sur le développement logiciel, les produits numériques et les équipes tech. Lou, Nicolas et Loïc y testent des outils, construisent des projets et confrontent leurs points de vue.

Ce dépôt rassemble le travail de production : identité visuelle, médias, montages et outils. Le code du site, les contenus publiés et les décisions de conception se trouvent dans [sandbox-podcast-site](https://github.com/Sandbox-podcast/sandbox-podcast-site).

## Par où commencer

<table>
<tr>
<td width="50%" valign="top">

### Préparer une émission

Les fichiers à fournir, le parcours d'un épisode et les revues à réaliser avec l'équipe.

[Ouvrir le guide de la factory](docs/factory/README.md)

</td>
<td width="50%" valign="top">

### Lancer les outils

L'installation, le worker Windows, le tableau de bord et la reprise après interruption.

[Lire le guide d'exploitation](docs/factory/exploitation.md)

</td>
</tr>
<tr>
<td width="50%" valign="top">

### Produire des extraits

Les rendus verticaux pour les réseaux et les vidéos horizontales thématiques.

[Préparer les formats sociaux](tools/social-network-manager/GENERER.md) · [Produire une vidéo thématique](tools/youtube-growth/THEMATIC.md)

</td>
<td width="50%" valign="top">

### Retrouver les visuels

Les déclinaisons de l'identité SANDBOX pour la chaîne, le plateau et les réseaux.

[YouTube](assets/brand/youtube/README.md) · [Plateau OBS](assets/brand/obs/README.md) · [Réseaux sociaux](assets/brand/social/README.md)

</td>
</tr>
</table>

## La factory

La factory prépare les contenus issus d'une émission et conserve leur avancement dans une base locale. L'équipe examine les passages, les montages et leur présentation avant de préparer le calendrier.

1. **Analyser et sélectionner.** Repérer les sujets dans le master, conserver les timecodes et choisir les passages avec leur contexte et leurs réserves.
2. **Monter et contrôler.** Rendre les formats utiles, vérifier le cadrage, écouter les coupes et relire les sous-titres. Chaque revue porte sur une version précise du média.
3. **Préparer la diffusion.** Décliner les titres, miniatures et textes par réseau. Le calendrier commence après disponibilité confirmée de l'épisode et se termine avant le prochain tournage.
4. **Suivre les résultats.** Consigner les observations, les expériences et les décisions pour le cycle suivant. Les mesures absentes restent signalées.

Il n'y a aucun quota d'extraits à atteindre. Le programme exécute les traitements locaux ; l'analyse et la sélection demandent des preuves et un jugement éditorial.

> [!NOTE]
> La diffusion fonctionne en simulation. Aucun contenu ne part vers les comptes sociaux, y compris en privé, en brouillon ou en programmation. LinkedIn reçoit un pack à publier manuellement. Les données de démonstration sont synthétiques.

Les [capacités et leurs limites](docs/factory/capacites.md), la [procédure des miniatures](docs/factory/miniatures.md) et le [prompt maître du 28 octobre 2026](docs/factory/sources/prompt-maitre-2026-10-28.txt) précisent le fonctionnement attendu.

Le tableau local indique la prochaine étape et présente les passages avec leurs horaires, leurs raisons et un lien vers la vidéo. Les décisions de sélection et les demandes de montage se font dans le chat avec Codex. Le [guide pour l'équipe](docs/factory/README.md#lire-le-tableau-de-bord) explique ce parcours.

Le [guide d'optimisation](docs/factory/optimisation.md) décrit les calculs réutilisés, les mesures de ressources et le brief pour le prochain cycle. La commande `python -m youtube_growth.factory brief --episode-id IDENTIFIANT` rassemble les résultats disponibles et les points à réexaminer ; elle n'applique aucun changement automatique de stratégie.

## Démarrer en local

Prérequis : **Python 3.12+**, **FFmpeg** et **ffprobe** accessibles dans le `PATH`. Depuis la racine du dépôt, dans PowerShell :

```powershell
python -m venv .local/factory-venv
& ./.local/factory-venv/Scripts/python.exe -m pip install -r tools/youtube-growth/requirements.txt
$env:PYTHONPATH = 'tools/youtube-growth/src'

& ./.local/factory-venv/Scripts/python.exe -m youtube_growth.factory doctor
& ./.local/factory-venv/Scripts/python.exe -m youtube_growth.factory demo
& ./.local/factory-venv/Scripts/python.exe -m youtube_growth.factory --config .local/factory-demo/simulation-config.json --state-dir .local/factory-demo serve
```

Ouvre le tableau de bord sur [127.0.0.1:8765](http://127.0.0.1:8765). La démonstration crée ses médias et sa base sous `.local/factory-demo`, séparément du travail opérationnel. Aucun compte social ni clé API n'est nécessaire pour cette recette.

Pour traiter un épisode réel, installer le worker Windows ou sauvegarder l'état, suis le [guide d'exploitation](docs/factory/exploitation.md).

## StoryTelling Generator

StoryTelling Generator transforme un sujet et ses sources en scénario, pistes sonores, plans et vidéo montée. Il conserve les versions dans la factory et permet de corriger une scène après l'export. Le parcours principal se pilote dans Codex, avec une interface locale pour retrouver chaque étape.

1. Installe les prérequis indiqués ci-dessus, puis lance le tableau de la factory :

   ```powershell
   $env:PYTHONPATH = 'tools/youtube-growth/src'
   & ./.local/factory-venv/Scripts/python.exe -m youtube_growth.factory serve --with-worker
   ```

2. Dans Codex, donne ton sujet, tes sources et tes contraintes, puis demande : « Crée cette vidéo avec StoryTelling Generator et utilise ElevenLabs dans le navigateur intégré pour le son. » Codex prépare le cadrage et te demande les choix déterminants qui manquent.
3. Ouvre [StoryTelling Generator](http://127.0.0.1:8765/storytelling). Tu peux y ajouter des notes, liens, documents et médias, choisir documentaire ou fiction, régler la durée et définir le plafond de crédits ElevenLabs. Le mode avec validation éditoriale s'arrête après le scénario et le storyboard.
4. Lance la production. Codex traite la requête de scénario et les demandes ElevenLabs depuis sa session active, puis les fichiers reçus sont importés dans le projet. Le worker mesure les voix, construit la timeline et rend la prévisualisation, le MP4 1080p et les sous-titres.
5. Relis et écoute le résultat. Pour corriger une scène, ouvre son texte, remplace une ressource ou régénère sa voix. Les ressources inchangées sont réutilisées ; une scène verrouillée protège aussi ses dépendances.

Le parcours ElevenLabs dans le navigateur nécessite une session Codex active. Un modèle local configuré peut assurer la rédaction dans le worker ; sans modèle, la requête reste à traiter par Codex. Les voix Windows et les médias autorisés permettent aussi un rendu local. L'API ElevenLabs serveur reste une option désactivée par défaut.

Le [tutoriel complet](docs/factory/storytelling-generator.md) détaille les sept étapes, la configuration, les commandes, les corrections et la reprise. Les tests techniques et les générations réellement effectuées sont distingués dans le [suivi de réalisation](docs/factory/storytelling-progress.md).

## Dans le dépôt

GitHub contient le code, les projets éditables et la documentation. Les masters, Shorts, vidéos, miniatures, sous-titres et packs générés restent sur l'ordinateur de la personne qui utilise la factory. Les workflows vérifient les sources et ne publient aucun média de production en artefact GitHub.

| Emplacement | Ce que tu y trouves |
| --- | --- |
| [assets/brand/](assets/brand/) | Logo commun, gabarits SVG et consignes de l'identité SANDBOX. |
| [projects/](projects/) | Sources éditables des vidéos, jingles, expériences et kits. |
| [tools/](tools/) | Outils de production, de croissance YouTube et de gestion des réseaux sociaux. |
| [docs/factory/](docs/factory/) | Guides de la factory, diagnostics et rapports de validation. |
| [.agents/skills/](.agents/skills/) | Skills SANDBOX, de l'analyse au bilan ; `sandbox-factory` sert de point d'entrée. |
| [config/factory.json](config/factory.json) | Configuration versionnée de la factory. |
| [docs/site/history/](docs/site/history/) | Rapports datés du site, classés par année et mois. |
| [archive/platform/](archive/platform/) | Code de l'ancienne plateforme, conservé pour référence. |

La factory écrit sa base, ses analyses et ses rendus dans `.local/factory/`, ignoré par Git. Les anciens livrables de ce poste sont conservés dans `.local/legacy/`. Sur un autre ordinateur, chaque personne fournit ses propres médias. Un nouveau rendu ne remplace jamais le master.

Le [guide d'organisation](docs/organisation.md) décrit le rangement local et la migration des anciens dossiers. Un contrôle de la CI refuse les médias ajoutés à Git, même avec un ajout forcé. Le logo commun et l'illustration de ce README sont les deux images partagées autorisées.

## Contribuer

Chaque nouveau prompt de travail envoyé à un harnais d'agent doit avoir son issue GitHub. L'agent y consigne la demande et l'avancement, puis la relie à chaque PR correspondante. **L'issue reste ouverte jusqu'à la fusion de la PR qui termine le travail.** Une PR en attente, fermée sans fusion ou bloquée laisse donc le sujet visible.

Les règles complètes sont dans [AGENTS.md](AGENTS.md). Les [issues ouvertes](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues) montrent les sujets en cours. Un [modèle de demande](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/new?template=prompt-agent.yml) et un [modèle de PR](.github/pull_request_template.md) reprennent ce suivi.

<details>
<summary><strong>Commandes de contrôle</strong></summary>

Pour les outils Python et la factory, depuis la racine :

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
python -m unittest discover -s tools/youtube-growth/tests -v
```

La recette audiovisuelle explicite utilise `FACTORY_MEDIA_INTEGRATION=1`. Les tests ordinaires ne prouvent ni une revue audiovisuelle ni une validation avec un compte réel.

Pour le projet Remotion `projects/videos/sandbox-intro` :

```powershell
npm ci --prefix projects/videos/sandbox-intro
npm test --prefix projects/videos/sandbox-intro
```

Les workflows [Resource checks](.github/workflows/ci.yml) et [YouTube SANDBOX](.github/workflows/youtube-growth.yml) détaillent les autres contrôles des pipelines et projets vidéo.

</details>

<details>
<summary><strong>Origine du dépôt et lien avec le site</strong></summary>

Le premier instantané de séparation vient de `sandbox-podcast-site` à la révision `63385fe20fe04ce2429e027c23d94ba3b089bf4c`. L'historique antérieur reste consultable dans [ce dépôt source](https://github.com/Sandbox-podcast/sandbox-podcast-site).

L'expérience de l'épisode 002 bis conserve un instantané textuel du lecteur à la date de séparation. Son export écrit désormais dans `.local/decks/episode-002-bis` ; il ne copie plus de médias dans le dépôt du site.

Les [sources du visuel de ce README](docs/readme/README.md) comprennent la commande de génération et la provenance du logo.

</details>
