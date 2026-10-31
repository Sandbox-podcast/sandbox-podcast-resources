# Collections de skills externes

Ce dossier contient les skills externes installés à la demande de Lou pour l'[onboarding vidéo](../../docs/factory/onboarding-video.md) (issue #52). Chaque collection est copiée depuis une révision Git épinglée dans [`skills-lock.json`](skills-lock.json), avec sa licence.

| Collection | Source demandée | Contenu installé | Licence |
| --- | --- | --- | --- |
| `autopunk-media-skills` | [ur-grue/autopunk-media-skills](https://github.com/ur-grue/autopunk-media-skills) | 408 skills, 50 variantes localisées (DE, ES, FR, IT, PT) et 9 agents | MIT |
| `screenwriting-skills` | [jtydhr88/screenwriting-skills](https://github.com/jtydhr88/screenwriting-skills) | 26 skills et leurs références | MIT, avec `NOTICE` |
| `cc-skills` | [humaniseur-fr sur skills.sh](https://www.skills.sh/samber/cc-skills/humaniseur-fr) | `humaniseur-fr` | MIT |

## Utilisation

Ces skills ne sont pas déclarés dans `.agents/skills/` ni `.claude/skills/`. Codex et Claude n'en chargent donc pas les 494 descriptions à chaque session. Le skill [`sandbox-video-onboarding`](../skills/sandbox-video-onboarding/SKILL.md) choisit ceux de l'étape en cours et lit leur fichier à ce moment-là.

[`catalog.json`](catalog.json) donne pour chaque entrée son identifiant, son chemin, sa langue, sa catégorie et le début de sa description. [`CATALOGUE.md`](CATALOGUE.md) présente les mêmes entrées en tableaux, par collection et par catégorie. Pour un agent ou une variante sans description dans son en-tête, le catalogue reprend le premier paragraphe du fichier. Pour chercher depuis la racine :

```powershell
python tools/repository/vendor_skills.py find "narration documentary"
python tools/repository/vendor_skills.py find hook --language fr
```

Les instructions de `screenwriting-skills` sont rédigées en chinois. L'agent répond dans la langue de la demande ; la table des termes de `sw-workflow` donne les équivalents d'origine. `autopunk-media-skills` et `humaniseur-fr` sont rédigés en anglais, sauf les variantes localisées.

## Ce qui n'est pas installé

Le verrou liste chaque exclusion et son motif : jeux d'évaluation, gabarits, hooks, serveur MCP, installateurs et scripts amont. L'installation lit les fichiers comme des données ; elle n'exécute et n'active aucun code amont. Une instruction présente dans un skill ne donne aucune autorisation supplémentaire : publication, dépense, clonage de voix ou envoi restent soumis aux règles du dépôt.

Le `NOTICE` de `screenwriting-skills` précise que les extraits d'ouvrages, de scénarios et de livrets cités dans les `reference*.md` restent la propriété de leurs auteurs, traducteurs et éditeurs. La licence MIT ne les couvre pas ; ils servent d'appui à l'étude et ne doivent pas être recopiés dans un livrable. Le propriétaire du dépôt a choisi, le 31 octobre 2026, de garder ces références dans le dépôt public avec le `NOTICE` amont.

## Contrôler et mettre à jour

Ne pas modifier ces fichiers à la main. Une adaptation propre à SANDBOX va dans un skill `sandbox-*` ou dans la documentation de la factory.

```powershell
python tools/repository/vendor_skills.py check
python tools/repository/vendor_skills.py install --collection screenwriting-skills
```

`check` compare chaque collection à l'empreinte enregistrée, vérifie les licences et les deux catalogues ; `catalog` les régénère. Pour changer de révision, remplacer `commit` dans le verrou par un commit complet relu, puis exécuter `install` pour cette collection. L'installation refuse d'écraser une copie modifiée localement ; `--replace-modified` assume ce remplacement. Relire ensuite le diff et le routage de l'onboarding avant de valider la mise à jour.
