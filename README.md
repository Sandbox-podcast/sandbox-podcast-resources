# Ressources SANDBOX

Ce dépôt rassemble les ressources éditoriales et de production du podcast : médias sources, projets vidéo, kits de diffusion, outils sociaux, documents de suivi datés et archive de l’ancienne plateforme.

Le site web et son code restent dans [`sandbox-podcast-site`](https://github.com/Sandbox-podcast/sandbox-podcast-site). Les ADR, les décisions de conception et les contrôles propres au site y restent également.

## Repères

- `brand/` : sources et déclinaisons de l’identité visuelle.
- `videos/`, `experiments/`, `Episode 2/` : projets vidéo et expériences éditoriales.
- `media/` : médias sources.
- `exports/`, `output/`, `kits-relais/`, `SANDBOX_LinkedIn_Kit/` : livrables et kits de diffusion.
- `tools/` : outils de production, de croissance YouTube et de gestion des réseaux sociaux.
- `docs/site/history/` : rapports datés déplacés depuis le dépôt du site, classés par année et mois.
- `old/` : archive de l’ancienne plateforme de production vidéo, à conserver telle quelle.

## Contrôles

Les workflows GitHub Actions vérifient les pipelines Python et les tests des projets vidéo. Pour le projet Remotion `videos/sandbox-intro`, lancer `npm ci` puis `npm test` depuis ce dossier.

Le premier instantané de séparation vient de `sandbox-podcast-site` à la révision `63385fe20fe04ce2429e027c23d94ba3b089bf4c`. L’historique antérieur reste consultable dans ce dépôt source.

Pour les expériences qui publient un deck dans le site, cloner les deux dépôts côte à côte ou définir `SANDBOX_SITE_ROOT` vers le dossier `apps/site`. Le test de l’épisode 002 bis conserve un instantané des fichiers publics à la date de séparation.
