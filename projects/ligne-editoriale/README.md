# Ligne éditoriale YouTube

Guide YouTube de Sandbox Podcast (@SandboxFR) pour Lou, Nicolas et Loïc, établi le 12 novembre 2026. Ouvrir `index.html` dans un navigateur : diagnostic de la chaîne, analyse de 1 729 vidéos de 45 chaînes IA, formats, rythme, règles de titres et de miniatures, pipeline, veille et objectifs.

## Contenu

| Emplacement | Rôle |
| --- | --- |
| `index.html` | La présentation |
| `scripts/veille.py` | Lit les 40 dernières vidéos de chaque chaîne de `watchlist.json` et écrit le rapport des vidéos qui surperforment |
| `scripts/analyse.py` | Agrège la veille du jour en chiffres |
| `scripts/watchlist.json` | Les 46 chaînes suivies : top 20 mondial, talk-shows américains, chaînes françaises, SANDBOX |
| `modeles/` | Modèle de brief d'épisode et backlog de sujets |
| `rapports/` | Rapports de veille datés |
| `data/bilans.csv` | Une ligne par vidéo, à remplir chaque semaine |

Les relevés bruts (`data/veille/`, `data/raw/`) restent locaux et sont ignorés par Git.

## Les skills

Les consignes sont dans `.agents/skills/`. Dans Claude Code, `/nom-du-skill` ; dans Codex, `$nom-du-skill`.

| Skill | Étape |
| --- | --- |
| `sandbox-veille-chaines` | Lance la veille sur 46 chaînes et propose les sujets de la semaine ou une alerte Radar |
| `sandbox-sujet-episode` | Transforme un sujet en brief d'épisode (thèse, positions, accroche, démo, Shorts) |
| `sandbox-titres-youtube` | Titres, texte de miniature, description, chapitres et plan de test A/B |
| `sandbox-miniature-series` | Gabarit de miniature par série (Clash, Build, Radar), s'appuie sur `haxprox-youtube-thumbnail-loop` |
| `sandbox-shorts-youtube` | Choix et titres des Shorts d'un épisode |
| `sandbox-bilan-youtube` | Relevé YouTube Studio à J+2 et J+7, comparaison aux objectifs, décision |

Ils complètent les skills existants (`sandbox-youtube-trend-hunter`, `sandbox-packaging`, `sandbox-thumbnail`, `sandbox-resultats`) sans les remplacer. Pour un pack LinkedIn, utiliser `sandbox-packaging`.

## Lancer la veille

Prérequis : Python 3.10 ou plus et yt-dlp dans le PATH. Depuis la racine du dépôt :

```sh
python -I projects/ligne-editoriale/scripts/veille.py --n 40
python -I projects/ligne-editoriale/scripts/analyse.py
```

Le rapport arrive dans `projects/ligne-editoriale/rapports/veille-AAAA-MM-JJ.md`. La veille ne modifie rien sur YouTube et n'utilise aucune clé.
