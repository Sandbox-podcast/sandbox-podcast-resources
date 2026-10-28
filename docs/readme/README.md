# Visuel du README

La bannière reprend le [logo officiel partagé](../../assets/brand/logo.png), sur le fond `#05090D` de l'identité SANDBOX. Le cyan `#00C8E8`, la grille et les repères accompagnent les étapes de production décrites dans le README.

- `hero.svg` est la source éditable, avec un lien relatif vers le logo existant.
- `hero.png` est l'export 1440 x 560 utilisé par le README pour un affichage autonome sur GitHub.
- `render_hero.py` intègre le logo en mémoire puis rend le SVG avec Chromium, sans modifier le média source.

Depuis la racine du dépôt, pour installer l'outil de rendu dans un environnement dédié puis régénérer le PNG :

```powershell
python -m venv .local/readme-venv
& ./.local/readme-venv/Scripts/python.exe -m pip install playwright
& ./.local/readme-venv/Scripts/python.exe -m playwright install chromium
& ./.local/readme-venv/Scripts/python.exe docs/readme/render_hero.py
```

La génération ne nécessite ni compte ni clé API. Le PNG ne charge aucune police ou image distante. Les guides de la factory et les ressources citées restent accessibles en texte dans le [README principal](../../README.md).
