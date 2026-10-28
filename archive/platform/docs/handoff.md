# Note de passation

Cette note permet à une session relancée ou compactée de reprendre le travail sans contexte. Elle est mise à jour à chaque étape importante.

- Dernière mise à jour : 2026-10-06, 13:00 (heure locale de la session)
- État : en pause volontaire après le noyau serveur ; rapport final écrit (`docs/rapport-final.md`)

## Règles à suivre

1. Lire `AGENTS.md`, `docs/README.md`, `docs/open-questions.md` et `docs/backlog.md`.
2. Le propriétaire (Lou) a délégué les décisions de conception à l'agent : PD-0003. Décider seul, consigner chaque décision dans un ADR/PD/DD avec la mention « décidée par l'agent sur délégation (PD-0003) ». Il a demandé de continuer sans s'arrêter jusqu'à la fin.
3. Ne pas commiter ni pusher (rien n'est commité à ce jour : le dépôt git est initialisé, tout est non suivi). Ne rien dépenser, ne rien publier, ne rien supprimer de réel, ne pas toucher aux réglages système.
4. Écrire en français, sobre, sans style IA. Ne jamais affirmer qu'un test passe sans l'avoir lancé. Aucun résultat de mesure inventé : toujours noter les limites.
5. Méthode qui a bien marché : écrire le code, lancer les tests, puis **vérifier les tests par mutation** (affaiblir un réglage ou une règle, voir un test échouer, rétablir). Plusieurs tests inutiles ont ainsi été corrigés.

## Commandes de travail (Windows, Git Bash)

- `pnpm` n'est pas installé globalement. Créer des shims dans un dossier temporaire : `corepack enable --install-directory <dossier> pnpm`, puis `export PATH="<dossier>:$PATH" COREPACK_ENABLE_DOWNLOAD_PROMPT=0`. Vérification complète : `pnpm check` à la racine (format, lint, typecheck, tests de tous les paquets). 645 tests au 2026-10-06 (format, lint, typecheck et tests verts). Les tests de `apps/api` exigent PostgreSQL (`cd apps/api && pnpm env:init && pnpm db:up`), sinon ils sont sautés.
- Éviter les gabarits de chaînes JavaScript et les guillemets imbriqués dans `node -e` ou les heredocs : ils s'échappent mal dans bash. Préférer l'outil d'édition des fichiers.
- Le répertoire courant du shell persiste d'un appel à l'autre : utiliser des chemins absolus ou revenir à la racine avant `prettier`/`pnpm`.
- Chrome 154 est installé (`C:/Program Files/Google/Chrome/Application/chrome.exe`) et sert aux tests de navigateur via `playwright-core` (`channel: 'chrome'`). GPU : RTX 4090.

## Docker

Docker Desktop doit être démarré par le propriétaire : il s'arrête quand je le lance depuis mon shell (le panneau Terminal de l'app est cassé). La pile du POC 3 : `pocs/poc-03-server-recording`, `docker compose --env-file .local/.env up -d` (secrets générés dans `.local/`, ignoré par git, via `pnpm env:init`). Sans Docker, continuer sur la logique pure et les tests unitaires.

## Reprise automatique après limite de quota

Consigne du propriétaire : quand le quota atteint 100 %, attendre 4 h puis relancer automatiquement. Procédure :

1. Lire `mcp__ccd_session_mgmt__get_usage` (outil différé : le charger avec ToolSearch). Si une fenêtre dépasse 95 %, mettre à jour cette note, puis créer une tâche programmée à usage unique (`mcp__scheduled-tasks__create_scheduled_task`, `fireAt` = maintenant + 4 h) dont le prompt dit de lire cette note et de reprendre.
2. Au démarrage d'une reprise : relire le quota. Si une fenêtre est encore au-dessus de 95 %, reprogrammer une reprise à l'heure de réinitialisation (`resetsAt`) plus quelques minutes, et s'arrêter.
3. Si cette note indique une dernière activité de moins de 2 heures, une autre session travaille : ne rien faire.

Au 2026-10-06 01:40 : fenêtre de 5 h à **100 %** (réinitialisation vers 01:40), semaine à 53 %. Conformément à la consigne du propriétaire (attendre 4 h), pause jusqu'à la reprise automatique de 04:57 (tâche `reprise-podcast-plateforme`).

## Ce qui est fait

- Fondations : monorepo pnpm, TypeScript strict, ESLint, Prettier, CI GitHub Actions (jamais exécutée), documentation, ADR-0001 à 0009, PD-0001 à 0003.
- Paquets produit : `recording-core` (modèle de chunk local, en attente), `recording-control` (planificateur d'enregistrement serveur), `auto-director`, `studio-control` (régie), `presentation-sandbox`, `collab`, `episode-factory`, `mcp-server`.
- POC 1 (media plane, vrai Chrome) : PARTIAL. POC 3 (enregistrement serveur Egress) : PARTIAL. POC 5 (Auto Director) : PASS. POC 6 (régie) : PASS. POC 8 (bac à sable HTML) : PASS. POC 7 (collaboration Yjs) : PASS. POC 9 (Episode Factory et MCP) : PASS en mémoire.
- Détail et chiffres dans `docs/pocs/` et `docs/adr/`.

## Dernier état

- POC 1 à 10 faits (voir `docs/pocs/README.md`). `packages/cost-model`, `docs/cost-model.md`, `docs/threat-model.md`, `docs/domain-model.md`, ADR-0009 à 0013.
- **Noyau serveur** `apps/api` (Fastify, PostgreSQL, migrations à empreinte, authentification, rôles par podcast, épisodes depuis template, invitations, jetons de salle, régie persistante, audit en ajout seul) : 75 tests sur vrai PostgreSQL, mutations vérifiées. `packages/collab` durci (origine, taille de message).
- **Interface web** `apps/web` (TypeScript sans framework, ADR-0014) : 47 tests sans navigateur, bundle construit (`pnpm --filter @podcast/web build`, 569 Ko avec LiveKit). Pour l'ouvrir : construire, puis lancer l'API avec `WEB_DIR=<apps/web/dist>` et `ALLOWED_ORIGINS=http://127.0.0.1:3001`, créer un compte avec `NEW_USER_PASSWORD=… pnpm create-user <email> "<nom>"`. **Jamais exécutée dans un navigateur.**
- **Règle de charge, à respecter** : le propriétaire a été fortement gêné (planter de son poste) par des commandes lourdes lancées en parallèle (Chrome, Docker, tsc, vitest, enregistrements de 30 minutes). Une seule commande lourde à la fois, pas de Chrome ni d'enregistrement long sans nécessité, arrêter les conteneurs du POC 3 quand ils ne servent pas (`docker stop poc03-livekit-1 poc03-egress-1 poc03-s3-1 poc03-redis-1`). Le PostgreSQL de test est `podcast-api-db-1`.
- Rapport final : `docs/rapport-final.md`. Aucune tâche programmée n'est en attente.

## Prochaines étapes, dans l'ordre

1. (fait) POC 9 : `packages/episode-factory` et `packages/mcp-server`, voir `docs/pocs/poc-09-mcp-episode-factory.md`.
2. (POC 2, 4 et 10 faits : PARTIAL / PASS avec limites / PARTIAL.)
3. (threat model, cost model et domain-model faits) `docs/security.md` reste à écrire ; le modèle de menaces en couvre l'essentiel.
4. Suite du MVP (voir `docs/rapport-final.md`, « Étape suivante ») : vérifier l'interface web dans Chrome, service d'enregistrement issu du superviseur du POC 3, Golden Path E2E. À lancer seulement avec l'accord du propriétaire sur la charge machine (poste souvent à moins de 3 Go de mémoire libre).
