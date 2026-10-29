# Organisation et stockage local

`check_repository.py` contrôle les fichiers suivis par Git, y compris les ajouts forcés. Il refuse les médias d'épisode, les exports, les bases et les anciens emplacements de livrables. Le logo commun et la bannière du README sont les deux images autorisées ; les gabarits SVG et le code restent partageables.

Depuis la racine :

```powershell
python tools/repository/check_repository.py
python tools/repository/sync_skills.py
python -m unittest discover -s tools/repository -v
```

La [structure du dépôt et la migration locale](../../docs/organisation.md) précisent où ranger les fichiers sur chaque ordinateur.

## Compte GitHub SANDBOX

Toutes les opérations de ce dépôt utilisent `loukan42`. Pour GitHub CLI, passer par le script qui sélectionne le compte, vérifie son identité et restaure l'environnement de la session après la commande :

```powershell
& ./tools/repository/github.ps1 api user --jq .login
& ./tools/repository/github.ps1 pr list
& ./tools/repository/github.ps1 pr view 19 --json 'author,state'
```

L'identité Git et le credential helper sont configurés localement dans le dépôt commun à ses worktrees. Les jetons restent dans le gestionnaire de credentials ; aucun fichier versionné ne les contient. Les consignes du dépôt interdisent le repli vers un autre compte si `loukan42` est indisponible.
