# Organisation et stockage local

`check_repository.py` contrôle les fichiers suivis par Git, y compris les ajouts forcés. Il refuse les médias d'épisode, les exports, les bases et les anciens emplacements de livrables. Le logo commun et la bannière du README sont les deux images autorisées ; les gabarits SVG et le code restent partageables.

Depuis la racine :

```powershell
python tools/repository/check_repository.py
python tools/repository/sync_skills.py
python -m unittest discover -s tools/repository -v
```

La [structure du dépôt et la migration locale](../../docs/organisation.md) précisent où ranger les fichiers sur chaque ordinateur.

## Skills SANDBOX et collections externes

`sync_skills.py` vérifie les skills `sandbox-*` de `.agents/skills/` et génère leurs petites entrées Claude dans `.claude/skills/` (`--write`). Les collections externes restent dans `.agents/vendor/`, sous leurs noms amont, sans entrée découverte automatiquement ; l'onboarding vidéo les charge par leur chemin.

`vendor_skills.py` gère ces collections à partir de `.agents/vendor/skills-lock.json` :

```powershell
python tools/repository/vendor_skills.py check
python tools/repository/vendor_skills.py find "documentary narration"
python tools/repository/vendor_skills.py install --collection autopunk-media-skills
```

`install` récupère le commit épinglé avec Git sans extraire l'arbre amont, copie seulement les fichiers texte et JSON demandés et leurs licences, puis régénère `catalog.json` et sa version lisible `CATALOGUE.md`. Il refuse d'écraser une copie modifiée localement. `catalog` régénère ces deux fichiers sans rien récupérer. `check` compare chaque collection à son empreinte, vérifie les licences et les deux catalogues ; la CI l'exécute. Le [README des collections](../../.agents/vendor/README.md) liste les sources, les exclusions et la procédure de mise à jour.

## Compte GitHub SANDBOX

Les comptes autorisés sont `loukan42` et `azerothl`, ce dernier ajouté à la demande du propriétaire le 29 octobre 2026. Le script sélectionne explicitement le compte, vérifie son identité et restaure l'environnement de la session après la commande. Le défaut reste `loukan42` :

```powershell
& ./tools/repository/github.ps1 api user --jq .login
& ./tools/repository/github.ps1 pr list
& ./tools/repository/github.ps1 pr view 19 --json 'author,state'
& ./tools/repository/github.ps1 -Account azerothl api user --jq .login
& ./tools/repository/github.ps1 -Account azerothl -Git push -u origin codex/ma-branche
```

L'identité Git locale doit correspondre au compte choisi. Avec `-Git`, le credential helper est limité à la commande ; les réglages globaux et les autres projets restent inchangés. Les jetons restent dans le gestionnaire de credentials ; aucun fichier versionné ne les contient. Un compte absent, une identité différente ou un refus d'accès interrompt la commande sans repli automatique.
