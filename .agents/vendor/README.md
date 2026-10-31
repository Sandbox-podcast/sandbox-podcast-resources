# Collections de skills externes

Ce dossier contient les skills externes installés à la demande de Lou pour l'[onboarding vidéo](../../docs/factory/onboarding-video.md) (issue #52). Chaque collection est copiée depuis une révision Git épinglée dans [`skills-lock.json`](skills-lock.json), avec sa licence. Depuis le 31 octobre 2026, seuls les skills utiles pour des vidéos YouTube sur l'IA sont installés.

| Collection | Source demandée | Contenu installé | Licence |
| --- | --- | --- | --- |
| `autopunk-media-skills` | [ur-grue/autopunk-media-skills](https://github.com/ur-grue/autopunk-media-skills) | 182 skills sur 408, 7 variantes françaises et 2 agents sur 9 | MIT |
| `cc-skills` | [humaniseur-fr sur skills.sh](https://www.skills.sh/samber/cc-skills/humaniseur-fr) | `humaniseur-fr` et `copywriting-prose-creator` avec ses références | MIT |
| `humanizer-fr` | [ferr079/humanizer-fr](https://github.com/ferr079/humanizer-fr) | `humanizer-fr` | MIT |
| `youtube-agent-skill` | [yt-script](https://github.com/Jakeschincariol/youtube-agent-skill/blob/main/skills/yt-script/SKILL.md) | `yt-script` et ses 21 formules d'accroche (`hooks.json`) | MIT |
| `awesome-claude-skills` | [content-research-writer](https://github.com/ComposioHQ/awesome-claude-skills/tree/master/content-research-writer) | `content-research-writer` | Apache-2.0, déclarée dans le README amont |

## Utilisation

Ces skills ne sont pas déclarés dans `.agents/skills/` ni `.claude/skills/`. Codex et Claude n'en chargent donc pas les 196 descriptions à chaque session. Le skill [`sandbox-video-onboarding`](../skills/sandbox-video-onboarding/SKILL.md) choisit ceux de l'étape en cours et lit leur fichier à ce moment-là.

[`catalog.json`](catalog.json) donne pour chaque entrée son identifiant, son chemin, sa langue, sa catégorie et le début de sa description. [`CATALOGUE.md`](CATALOGUE.md) présente les mêmes entrées en tableaux, par collection et par catégorie. Pour un agent ou une variante sans description dans son en-tête, le catalogue reprend le premier paragraphe du fichier. Pour chercher depuis la racine :

```powershell
python tools/repository/vendor_skills.py find "narration documentary"
python tools/repository/vendor_skills.py find hook --language fr
```

`autopunk-media-skills`, `humaniseur-fr`, `copywriting-prose-creator`, `yt-script` et `content-research-writer` sont rédigés en anglais, sauf les variantes françaises. `humanizer-fr` est rédigé en français.

Deux correcteurs du français sont installés : `humaniseur-fr` (samber) et `humanizer-fr` (ferr079). Une révision n'en applique qu'un, celui que route l'onboarding vidéo.

`yt-script` demande un profil de voix dans `~/.claude/youtube/voice.md`. Dans SANDBOX, la voix se règle dans l'onboarding vidéo : l'agent s'appuie sur le narrateur choisi et ne crée pas ce fichier sans demande de Lou.

## Ce qui n'est pas installé

Le verrou liste chaque exclusion et son motif : jeux d'évaluation, gabarits, hooks, serveur MCP, installateurs et scripts amont, dont `hookscore.py` de `yt-script`. Seuls les textes, les données JSON et les licences sont copiés. L'installation lit les fichiers comme des données ; elle n'exécute et n'active aucun code amont. Une instruction présente dans un skill ne donne aucune autorisation supplémentaire : publication, dépense, clonage de voix ou envoi restent soumis aux règles du dépôt.

Le champ `exclude` du verrou retire aussi les skills sans usage pour des vidéos YouTube sur l'IA. Cela couvre la presse écrite, la newsletter, les relations presse, la radio, le financement et les séries télévisées. S'y ajoutent les variantes en allemand, espagnol, italien et portugais et 7 agents sur 9. Les skills routés par l'onboarding vidéo restent tous installés. Certains skills conservés citent encore un skill retiré : l'agent ignore ce renvoi. Pour rétablir un skill, retirer son motif de `exclude`, puis exécuter `install` pour sa collection.

La collection `screenwriting-skills` (jtydhr88/screenwriting-skills), rédigée en chinois, a été retirée entièrement le 31 octobre 2026 à la demande de Lou. Ses routes dans l'onboarding vidéo passent par des skills d'`autopunk-media-skills` : `beat-sheet-builder`, `character-profile-writer`, `treatment-writer`, `scene-writer` et `dialogue-polisher`.

## Contrôler et mettre à jour

Ne pas modifier ces fichiers à la main. Une adaptation propre à SANDBOX va dans un skill `sandbox-*` ou dans la documentation de la factory.

```powershell
python tools/repository/vendor_skills.py check
python tools/repository/vendor_skills.py install --collection youtube-agent-skill
```

`check` compare chaque collection à l'empreinte enregistrée, vérifie les licences et les deux catalogues ; `catalog` les régénère. Pour changer de révision, remplacer `commit` dans le verrou par un commit complet relu, puis exécuter `install` pour cette collection. L'installation refuse d'écraser une copie modifiée localement ; `--replace-modified` assume ce remplacement. Relire ensuite le diff et le routage de l'onboarding avant de valider la mise à jour.
