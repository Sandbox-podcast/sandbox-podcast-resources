# Issue 68 : mise en service du 16 octobre 2026

Lou a autorisé dans le chat la sauvegarde Neon, les migrations, la configuration du cron, la fusion des PR 66 et 69, le déploiement et les réglages GA4 après tests. Ce compte rendu complète le [rapport de corrections](issue-68-2026-10-16.md). L'issue reste ouverte : l'authentification du cron fonctionne, mais les collectes, les nouvelles éditions et les validations éditoriales restent à terminer.

## Code et déploiement

- [PR 66](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/66) fusionnée à 13:42 UTC, commit `46c70e36e28c4feb6c77f4c9f8fb9f1b832942ab`.
- [PR 69](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/69) fusionnée à 13:44 UTC, commit `61955556ba3b05f9c4c61f66ef4a44e4561909a4`.
- [CI de la fusion](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/38910252828) réussie. Le workflow YouTube de ce commit réussit également ; cela ne constitue pas une publication YouTube.
- Production Vercel `GcgV3t7k8Uj8fSmYGL9sKfgdQZgG`, état Ready à 13:53 UTC, confirmée comme déploiement courant de `www.sandboxpodcast.fr`. Source : le commit de fusion ci-dessus.
- Preview de validation `BoVyKgY3fFurnJNtfMbnERHdo3r8`, source `c6855e2729c741267ad7b7c631d83fd7a5948a11`.

## Neon

Projet `fragrant-lab-14685793` (`neon-yellow-planet`). Des branches avec données et schéma, sans suppression automatique, ont été créées avant les migrations :

| Cible      | Branche cible               | Sauvegarde                                                         |
| ---------- | --------------------------- | ------------------------------------------------------------------ |
| Principale | `br-ancient-union-b1zb56o3` | `restore-2026-10-16-issue68-main` (`br-withered-glitter-b15ba1lq`) |
| Preview    | `br-late-cake-b1uwmp4p`     | `restore-2026-10-16-issue68-preview` (`br-sweet-moon-b1a1zlxi`)    |

La principale avait les migrations `0000` à `0011` ; la Preview n'avait que `0000` à `0004`. Les migrations restantes ont été appliquées dans l'ordre jusqu'à `0015` sur chaque branche. Le SQL vient du commit de la PR 69. Les empreintes historiques ont été comparées en tenant compte des fins de ligne LF/CRLF, sans réécrire l'historique existant.

Chaque lot utilisait une transaction, un verrou sur le journal et une garde exigeant l'état initial exact. Un essai local PGlite a vérifié chaque lot complet, la conservation d'un contenu éditorial témoin et le refus d'une seconde application. Après exécution distante, les deux journaux contiennent 16 migrations ; `badge_awards` et `admin_login_attempts` existent sur les deux branches.

Les deux tentatives HTTP volontairement invalides sur la production ont répondu 401, sans cookie de session. La branche principale contient ensuite un compteur avec deux tentatives : la protection déployée écrit bien dans cette base. Les valeurs des connexions Vercel n'ont pas été affichées. Le raccordement exact de la Preview n'a pas été démontré par un marqueur écrit depuis son application.

## GA4

Propriété `558931246`, flux `16126152490`, identifiant `G-45XWR4KJ1M`, domaine `www.sandboxpodcast.fr`.

- Mesure améliorée désactivée, état confirmé après rechargement de la console.
- Conservation des événements passée de 2 à 14 mois, valeur confirmée après rechargement. Celle des utilisateurs était déjà de 14 mois. La console annonce jusqu'à 24 heures pour l'application du changement.
- `NEXT_PUBLIC_GA4_READY=true` ajouté comme Config dans Preview, puis dans Production après validation de la Preview ; chaque environnement a été reconstruit.
- Preview : aucun script Google avant accord ni après refus ; un script après acceptation ; aucun après retrait et rechargement.
- La recherche d'essai est reçue sous `/search`, sans terme ni paramètres dans `page_location`, avec le titre fixe `Sandbox · Recherche`. La console temps réel permet de vérifier ces valeurs reçues.
- Les cinq événements `page_view`, `episode_play_requested`, `episode_source_open`, `episode_project_open` et `project_episode_open` ont été constatés dans Temps réel après les actions correspondantes en production. `discovery_open` est également reçu depuis la Preview.
- Après retrait en production, le tag est absent au rechargement. Aucun événement `view_search_results` n'est apparu pendant cette recette. Les contrôles locaux antérieurs couvrent les envois après retrait avec des services simulés ; l'interface GA4 seule ne constitue pas une capture exhaustive du réseau.

La Preview n'a pas de replay publié : les actions d'épisode ont été vérifiées sur la production après les contrôles de consentement et de recherche en Preview. Les événements de recette font partie des données GA4 de cette période.

## Contrôles de production

Le script local `verify-production.mjs` a vérifié deux réponses admin avec nonces distincts de 128 bits, absence de permission inline/eval dans leur directive de scripts, cache privé sans stockage et remplacement du nonce fourni par le client. La connexion invalide répond 401 sans session. Les pages `/`, `/podcast`, `/charts`, `/charts/awards`, `/es-es` et `/de-de` répondent 200 ; les deux dernières restent `noindex`.

Le premier essai utilisait les mauvais préfixes `/es-ES` et `/de-DE` et a rencontré une 404. Le test a été corrigé d'après `src/i18n/locales.ts`, puis exécuté avec succès. Aucune correction du site n'était nécessaire pour ce point.

La commande `pnpm check` a été exécutée après la mise à jour documentaire : format, lint et types valides, 686 tests site, 7 tests de la vidéo d'introduction, 4 tests des jingles et 24 tests BIS réussis.

## Blocages et suite

Le premier [rafraîchissement manuel 38910871153](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/38910871153) a échoué car `CRON_SECRET` reçu par le workflow était vide. Ce constat est désormais résolu : `SANDBOX_CHARTS_CRON_SECRET` existe dans le dépôt GitHub, avec une date de mise à jour au 16 octobre à 14:36:25 UTC. La console Vercel confirme `CRON_SECRET` comme Secret de Production mis à jour le même jour, avec une entrée Preview distincte.

Lou a ensuite autorisé explicitement la gestion du secret. Au contrôle, il était déjà opérationnel : le [rafraîchissement manuel 38917678851](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/38917678851), lancé à 14:40 UTC, reçoit des réponses métier des routes protégées. Cette preuve confirme l'authentification entre Actions et Vercel sans révéler ni comparer les valeurs des secrets. Aucune rotation supplémentaire n'a été nécessaire. La production courante constatée est `CW2toYLuLEJiTKZbfd7mtr8Tbb2x`, Ready, issue du commit `db224915450cad99541e2b2c90c5fbc1775d025c`, postérieure à la mise à jour du secret.

Le workflow reste en échec pour les résultats suivants : GitHub renvoie trois collectes `partial` puis `insufficient_history` au gel ; Skills renvoie `partial` pour les collectes et le gel ; Models renvoie `failed` pour les collectes puis `skipped` au gel. Les éditions publiques restent au 10 octobre pour GitHub et Skills et au 12 octobre pour Models. Le [contrôle horaire 38919618034](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/38919618034) confirme ce retard à 14:55 UTC. Ces résultats ne constituent pas une panne d'authentification ni une validation des données ou profils.

Les profils de classement n'ont pas été déclarés revus. Les quotas et conditions des sources, les identités contradictoires et les baselines réelles restent à vérifier. Les deux exécutions planifiées réussies, les Awards sur une semaine admissible et les contrôles Camo ne sont pas validés.

YouTube : le diagnostic local constate l'absence du token OAuth pour la chaîne attendue `UCuATIBXo5uvNLVm-gCgMenA`. L'initialisation du journal distant avec son rôle limité et la réconciliation SQLite restent à faire avant les écritures. Les quatre Shorts attendent l'écoute et l'approbation éditoriale ; aucun n'a été publié. Les mesures à 48 h, 7 jours et 3 semaines restent à recueillir après publication.

Décision ultérieure de Lou : indexer les traductions ES/DE complètes sans relecture native et conserver l'email du footer pour les signalements. La procédure proposée ne sera pas publiée. Voir le [lot de traductions et de collecte](issue-68-traductions-et-collectes-2026-10-16.md). Aucun doublon historique de modèle n'a été fusionné ni supprimé.

Les scripts, résultats JSON et captures de cette opération sont conservés localement dans `.local/issue68-release/`, hors Git. Aucun secret n'y a été enregistré. Ce compte rendu est inclus dans le lot de PR autorisé par Lou.
