# Organisation du dépôt et fichiers locaux

Le dépôt partage les outils et les sources réutilisables. Chaque personne exécute la factory sur son ordinateur et fournit ses propres médias. Les sorties de production ne sont ni committées, ni déposées dans Git LFS, les artefacts Actions ou les releases.

## Ce qui reste dans GitHub

```text
.agents/skills/       Consignes des étapes SANDBOX
.github/             Contrôles et modèles d'issue et de PR
archive/platform/    Code de l'ancienne plateforme
assets/brand/        Logo commun, gabarits SVG et consignes graphiques
config/              Configuration de simulation partagée
docs/                Guides et rapports techniques
projects/            Sources des vidéos, jingles, decks et kits
tools/               Moteurs de la factory et contrôles du dépôt
```

Les projets éditables contiennent leur code et leurs paramètres de référence. Leurs images d'épisode, pistes audio, portraits, captures et rendus ne font pas partie du clone. Le logo commun et la bannière du README sont les deux images autorisées comme ressources du dépôt. Les gabarits graphiques restent des sources SVG.

Les rapports de validation et les références éditoriales documentées peuvent rester dans `docs/`. Ils ne remplacent pas les fichiers de travail ni la base d'un poste.

## Où la factory écrit

```text
.local/
  factory/                Base SQLite, inbox, analyses, rendus et packs
  factory-demo/           Démonstration synthétique séparée
  factory-backups/        Sauvegardes locales
  legacy/                 Anciens médias et livrables de ce poste
  relay-kits/             Exports de l'ancien moteur de kits
  youtube-growth/output/  Sorties du moteur YouTube historique
```

Tous ces dossiers sont ignorés par Git. Le master peut aussi rester sur un disque local externe ; le manifeste donne son chemin et son empreinte. Chaque utilisateur configure les chemins et les comptes sur son poste. Copier le dépôt ne copie ni les médias, ni les credentials, ni la base d'exécution.

Les projets historiques peuvent garder leurs fichiers de travail dans leurs sous-dossiers ignorés, par exemple `public/`, `assets/`, `analysis/` ou `renders/`. Ces fichiers restent locaux. Les commandes de la factory utilisent leur espace `.local/` séparé.

## Migration du 28 octobre 2026

Sur ce poste, les dossiers `exports/`, `output/`, `media/`, `kits-relais/`, `Episode 2/` et `SANDBOX_LinkedIn_Kit/`, ainsi que les ZIP et logos isolés à la racine, ont été déplacés sous `.local/legacy/` avec leurs noms d'origine. Les fichiers n'ont pas été supprimés du disque. Le reçu local `.local/readme-update/migration-receipt.json` conserve les chemins avant et après, la taille et le SHA-256 des 1 021 fichiers vérifiés pendant la réorganisation.

Les sources des anciens dossiers `videos/` et `experiments/` sont dans `projects/videos/` et `projects/experiments/`. Les scripts réutilisables des kits sont dans `projects/relay-kits/`. L'identité commune est dans `assets/brand/` ; le code de `old/` est rangé dans `archive/platform/`.

Sur un clone qui possède encore les anciens livrables, les copier dans une sauvegarde locale avant d'appliquer la suppression de leur suivi Git. Le script `tools/repository/archive_local_media.py` peut préparer cette copie et ses empreintes sans supprimer les originaux. Un nouveau clone ne doit pas télécharger ces livrables depuis GitHub : il utilise ses propres fichiers ou une sauvegarde locale autorisée.

Les rapports historiques conservent leurs anciens chemins pour décrire l'état de l'époque. Pour retrouver un média sur ce poste, chercher d'abord le même chemin sous `.local/legacy/`, puis dans le projet déplacé. Les anciennes captures documentaires restent disponibles localement mais ne sont plus suivies par Git.

Cette PR retire les livrables de l'arborescence courante. Les anciennes versions restent dans l'historique Git ; aucune réécriture de l'historique n'est incluse.

## Contrôles

```powershell
python tools/repository/check_repository.py
python -m unittest discover -s tools/repository -v
```

Le contrôle examine l'index Git et refuse les médias, les bases et les anciens emplacements de sortie, même après un ajout forcé. La CI vérifie les sources et peut fabriquer des fixtures synthétiques temporaires pour les tests. Elle n'exécute aucun rendu d'épisode ni traitement de chaîne et ne téléverse aucun média de production.

Les tests de structure des projets passent avec un clone sans médias. Les tests qui demandent les vrais fichiers de travail restent des contrôles locaux et indiquent leur absence.
