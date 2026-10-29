# Organisation et stockage local

`check_repository.py` contrôle les fichiers suivis par Git, y compris les ajouts forcés. Il refuse les médias d'épisode, les exports, les bases et les anciens emplacements de livrables. Le logo commun et la bannière du README sont les deux images autorisées ; les gabarits SVG et le code restent partageables.

Depuis la racine :

```powershell
python tools/repository/check_repository.py
python tools/repository/sync_skills.py
python -m unittest discover -s tools/repository -v
```

La [structure du dépôt et la migration locale](../../docs/organisation.md) précisent où ranger les fichiers sur chaque ordinateur.
