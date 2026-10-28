# Archive : plateforme de production de podcasts vidéo

Tout ce qui a été fait à partir du « prompt maître » (`PODCAST_PLATFORM_MASTER_PROMPT.md`), entre le 2026-10-05 et le 2026-10-06. Le propriétaire ne réutilise pas ce travail. Le site média est désormais développé dans le dépôt [`sandbox-podcast-site`](https://github.com/Sandbox-podcast/sandbox-podcast-site). Cette archive conserve les fichiers de la plateforme et leur arborescence d’origine ; elle provient de son dossier `old/` avant la séparation des dépôts.

## Contenu

| Dossier ou fichier                        | Quoi                                                                                                                                                  |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PODCAST_PLATFORM_MASTER_PROMPT.md`       | Le prompt maître fourni par le propriétaire (exigences, critères d'acceptation)                                                                       |
| `apps/api`                                | Noyau serveur (Fastify, PostgreSQL, authentification, rôles, épisodes, invitations, jetons de salle, régie, audit)                                    |
| `apps/web`                                | Interface web sans framework (conducteur, invitations, studio du Producer, rendu « Program » avec détourage)                                          |
| `packages/`                               | 11 paquets de logique testée : enregistrement, régie, Auto Director, collaboration, MCP, Episode Factory, post-production, qualité de scène, coûts… |
| `pocs/`                                   | Les 10 POC (media plane, segmentation, enregistrement serveur, synchronisation, bac à sable HTML, post-production…) et leurs données locales          |
| `docs/`                                   | ADR-0001 à 0014, décisions produit, résultats des POC, modèle de menaces, modèle de coût, modèle de domaine, rapport final, note de passation         |

Pour reprendre le fil : [docs/rapport-final.md](docs/rapport-final.md) (état, limites, étape suivante), [docs/handoff.md](docs/handoff.md) (commandes et règles de travail), [docs/README.md](docs/README.md) (index).

## État au moment de l'archivage

- 645 tests passaient au dernier contrôle complet (format, lint, typecheck, tests), avant la dernière série de modifications de l'interface web (76 tests de l'interface passaient après).
- Le rendu « Program » de l'interface web (décor commun, participants détourés) a été écrit mais **jamais vu à l'écran** : le détourage MediaPipe sous la politique de contenu de la page n'a pas été vérifié.
- Rien n'a été commité dans git.

## Ce que cette archive n'est plus

- **Hors de l'espace de travail pnpm** : `pnpm-workspace.yaml` ne liste plus que `apps/*`. `pnpm install` et `pnpm check` à la racine ignorent `old/` (Prettier et ESLint aussi : voir `.prettierignore` et `eslint.config.js`).
- **Les chemins relatifs vers la racine ne marchent plus** : les paquets de `old/` étendent `../../tsconfig.base.json`, qui est resté à la racine du dépôt. Les liens de jonction de `node_modules` dans `old/` pointent vers les anciens emplacements.
- **Le fichier de verrouillage** (`pnpm-lock.yaml`) a été remis à jour pour ne plus référencer ces projets.

## Pour la ressusciter

1. Remettre les dossiers à leur place d'origine (`old/apps/*` dans `apps/`, `old/packages` et `old/pocs` à la racine, `old/docs/*` dans `docs/`) et rétablir `packages/*` et `pocs/*` dans `pnpm-workspace.yaml`, puis `pnpm install`. Ou, plus simplement, ajouter `old/apps/*`, `old/packages/*` et `old/pocs/*` à `pnpm-workspace.yaml` et corriger le chemin de `tsconfig.base.json` dans les `tsconfig.json` des projets.
2. Retirer `old` de `.prettierignore` et `old/**` de `eslint.config.js` si on veut qu'ils soient contrôlés.
3. L'exception de lint des tests de l'ancienne API (champs JSON lus sans typage) était dans `eslint.config.js` : son explication est dans [docs/testing-notes-api.md](docs/testing-notes-api.md).

## Données locales et services

- Les dossiers `.local/` (secrets générés, enregistrements de test, fixtures média, comptes de test) sont **dans l'archive** et ignorés par git (`old/**/.local/`). Ils peuvent être volumineux (environ 6 Go dans `old/pocs/poc-03-server-recording/.local/`) : on peut les supprimer sans perdre de code, mais on perd les enregistrements et mesures des POC.
- Conteneurs Docker créés pour ces travaux, **arrêtés mais pas supprimés** : `podcast-api-db-1` (PostgreSQL de test, avec son volume), `poc03-livekit-1`, `poc03-redis-1`, `poc03-egress-1`, `poc03-s3-1` (avec leur volume). Pour les supprimer : `docker rm podcast-api-db-1 poc03-livekit-1 poc03-redis-1 poc03-egress-1 poc03-s3-1`, puis supprimer les volumes `podcast-api_dbdata` et `poc03_s3data` si on n'en a plus besoin.
