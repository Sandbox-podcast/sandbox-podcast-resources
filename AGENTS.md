# AGENTS.md — ressources SANDBOX

Ce dépôt rassemble les documents et outils éditoriaux, audiovisuels et de diffusion de SANDBOX. Le code, les contenus publiés et les décisions actuelles du site restent dans [`sandbox-podcast-site`](https://github.com/Sandbox-podcast/sandbox-podcast-site).

## Organisation

- `brand/`, `media/`, `videos/`, `experiments/`, `exports/`, `kits-relais/` et `tools/` contiennent les ressources et outils de production.
- `docs/site/history/` conserve les rapports datés ; les guides à jour et décisions du site restent dans le dépôt du site.
- `old/` archive l’ancienne plateforme de production vidéo. Ne pas la modifier sans demande explicite.

## Travail sur les médias

- Ne jamais écraser un média source ; créer une nouvelle version ou un export séparé.
- Ne pas ajouter de secrets, jetons ou données de comptes. Les configurations locales restent dans `.local/` et sont ignorées par Git.
- Distinguer les sources de travail des exports livrés et documenter les commandes de génération.
- Les outils sociaux et YouTube peuvent agir sur des services externes : ne pas publier, programmer ou supprimer de contenu sans autorisation explicite du propriétaire.
- Avant une modification, consulter le README du dossier concerné et les décisions ou rapports associés.

## Qualité

- Les identifiants de code sont en anglais ; la documentation est en français.
- Adapter les tests avec chaque modification et exécuter les contrôles pertinents indiqués dans les workflows.
- Ne pas déclarer un contrôle réussi sans l’avoir exécuté.
- Attendre une demande explicite avant de créer une PR. Les commits et les pushes restent soumis à l’autorisation du propriétaire.
