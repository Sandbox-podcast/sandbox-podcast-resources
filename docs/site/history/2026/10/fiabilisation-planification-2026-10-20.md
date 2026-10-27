# Fiabilisation de la planification News et Charts

Relevé du 20 octobre 2026. Lou demande de corriger les retards récurrents et choisit un service externe gratuit. Ce document rassemble les preuves du diagnostic, la conception retenue et la première mise en service Cloudflare. Le Worker est déployé en observation : il inspecte les données et les runs, sans déclencher GitHub. Les nouveaux workflows restent à livrer sur `main` après autorisation Git.

## Diagnostic démontré

Les retards observés apparaissent avant la création des runs GitHub Actions. Une fois un run créé, les jobs examinés obtiennent un runner en quelques secondes. Les traitements News réussissent en treize à quinze minutes. Leur durée n'explique donc pas les intervalles de plusieurs heures sans run.

Les horaires du tableau sont en UTC. Paris a deux heures d'avance le 20 octobre 2026.

| Traitement et preuve                                                                                               | Création du run      | Début du job | Résultat                                           |
| ------------------------------------------------------------------------------------------------------------------ | -------------------- | ------------ | -------------------------------------------------- |
| [News planifié, 39356595304](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39356595304)     | 20 octobre, 02:00:56 | —            | Réussi, fin à 02:14:43                             |
| [News planifié, 39389494674](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39389494674)     | 20 octobre, 07:53:06 | 07:53:08     | Réussi, fin du run à 08:06:37                      |
| [News manuel, 39266494010](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39266494010)       | 19 octobre, 14:10:02 | 14:10:05     | Réussi, fin à 14:25:22                             |
| [News manuel, 39308199122](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39308199122)       | 19 octobre, 19:06:36 | 19:06:40     | Réussi, fin à 19:21:30                             |
| [Découverte Charts, 39377815371](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39377815371) | 20 octobre, 05:59:12 | 05:59:14     | Annulé après dix minutes et plusieurs réponses 503 |
| [Contrôle Charts, 39378523156](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39378523156)   | 20 octobre, 06:06:39 | 06:06:42     | Échec de fraîcheur, sans collecte                  |

Les deux passages News du 20 octobre sont espacés de 5 h 52 min 10 s, malgré le cron horaire à la minute 37. Le job de découverte Charts ne s'exécute que pour le cron `17 1 * * *` : sa création à 05:59:12 démontre un retard d'au moins 4 h 42 par rapport à 01:17. Une attente du runner après création du run n'explique pas cet écart.

La consultation des API GitHub confirme les éléments suivants :

- Le dépôt `Sandbox-podcast/sandbox-podcast-site` est public ; sa branche par défaut est `main`.
- Les workflows `news-refresh.yml` et `charts-refresh.yml` sont `active`, présents sur cette branche. GitHub Actions est activé pour le dépôt.
- La variable `SANDBOX_NEWS_PUBLIC` vaut `true`, avec une dernière modification le 19 octobre à 03:36:40 UTC. Les passages News ignorés auparavant ne décrivent donc pas l'état du service le 20 octobre.
- Le dernier commit de `main` lors du contrôle est `208320cedefda854d5de3d63183bbe71d939dc72`, daté du 19 octobre à 20:13:07 UTC. L'arrêt automatique après soixante jours d'inactivité ne correspond pas à ce dépôt.

Ces observations écartent un workflow désactivé, une mauvaise branche par défaut et la désactivation actuelle de News. Elles ne révèlent pas le traitement interne de chaque événement planifié par GitHub.

## Fraîcheur et fonctionnement des traitements

Le dernier run News examine 105 sources, dont 77 sont disponibles, détecte 414 fiches et ajoute 18 candidats nouveaux. Il traite quinze candidats en trois lots et publie six fiches ; neuf candidats sont écartés pour ce passage. La file annonce 487 candidats au premier lot et 482 avant le dernier, avec une première entrée datant du 19 octobre à 14:12:23 UTC. Le traitement se termine avec `drained: false`.

Les lectures publiques qui suivent donnent :

| Vue ou API                   | État observé                                                                                                         |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `/api/news`                  | HTTP 200 ; trente fiches sur la première page ; collecte `2026-10-20T07:55:10.913Z` ; 77 sources disponibles sur 105 |
| `/api/charts/github/current` | HTTP 200 ; édition `2026-10-19T12:00Z` ; publication le 19 octobre à 14:19:32 UTC                                    |
| `/api/charts/skills/current` | HTTP 200 ; édition `2026-10-19T12:00Z` ; publication le 19 octobre à 14:12:08 UTC                                    |
| `/api/charts/models/current` | HTTP 200 ; édition `2026-10-19T12:00Z` ; publication le 19 octobre à 14:11:44 UTC                                    |
| `/api/charts/rising/current` | HTTP 202 ; `pending`, aucune entrée                                                                                  |

Le champ local `lastPublishedAt` n'est pas encore exposé par la version distante consultée. La date `checkedAt` renseigne la collecte ; elle ne prouve ni la publication d'un nouvel article ni la résorption de la file.

Le job de découverte Charts rencontre aussi une panne d'exécution distincte du retard de déclenchement. Ses logs montrent trois réponses 503 de Trending, deux de la découverte, puis l'annulation à la limite de dix minutes. La correction locale retire les répétitions curl. Le budget passe à vingt minutes pour couvrir le précontrôle GitHub, les deux appels bornés à six minutes et l'installation du runner. La reprise locale des classements est décrite dans [ADR-0038](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0038-reprise-horaire-des-classements.md).

## Cause probable et limites du diagnostic

GitHub documente les [retards et abandons possibles des événements planifiés](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows). Les longues absences de runs, suivies de démarrages rapides, correspondent à ce type d'incident. La saturation exacte de GitHub et la distinction entre événements retardés et abandonnés restent des hypothèses. Aucun journal accessible dans cet audit ne les démontre événement par événement.

Le cron News a déjà été déplacé à la minute 37. Les trous persistent avec cette configuration. Une nouvelle modification de minute peut changer les conditions de charge ; elle ne démontre pas le rétablissement de la cadence.

Ces traitements utilisent les runners GitHub `ubuntu-latest` du dépôt public. GitHub indique que les [runners standard sont gratuits et illimités pour les dépôts publics](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job). Le quota de l'abonnement Codex ne déclenche ni n'exécute ces jobs. News résume avec Qwen sur le CPU du runner et traduit avec Argos ; aucune session Codex n'est nécessaire à ce traitement.

## Conception retenue : une horloge Cloudflare indépendante

Lou retient un service externe gratuit. Les choix locaux de conception relèvent de la délégation PD-0003. Le déploiement distant fonctionne désormais en observation ; l'activation des dispatchs reste à effectuer après livraison autorisée des workflows.

Un Worker Cloudflare se réveille toutes les cinq minutes avec un Cron Trigger UTC. Il détermine les tâches dues et déclenche les workflows existants par l'API GitHub `workflow_dispatch` sur `main`. La collecte, la génération CPU, les secrets Vercel et les publications restent exécutés par GitHub Actions. Cloudflare ne reçoit pas les extraits News et n'exécute aucun modèle.

Les cadences métier restent celles du [guide d'automatisation](automatisation-news-charts-2026-10-20.md) : News toutes les heures à la minute 37, découverte GitHub à 01:17, collecte Charts à 03:17 et 15:17, contrôle Charts chaque heure à la minute 23. Le réveil de cinq minutes identifie les échéances dépassées ; il ne multiplie pas chaque traitement par douze. Les crons GitHub existants peuvent servir de secours pendant la mise en service.

Un Durable Object avec stockage SQLite conserve l'état par tâche et créneau. Une réservation persistante précède l'appel GitHub. Le coordinateur empêche deux réveils concurrents d'envoyer le même travail simultanément, mémorise la tentative et autorise une reprise bornée après erreur ou expiration. Une pause du Worker ne doit pas provoquer le rejeu illimité de tous les anciens créneaux.

Le noyau local laisse cinq minutes de grâce à News, dix à la découverte et douze aux collectes Charts. Il borne les envois externes à trois essais par tâche et créneau, avec une attente de quinze minutes pour News et de trente minutes pour Charts et la découverte. Les contrôles exécutés dans GitHub relisent les résultats sous leurs verrous ; ils n'imposent pas cette grâce supplémentaire au cron déjà arrivé à son échéance.

La réponse à un dispatch prouve seulement son acceptation par GitHub. Il faut également observer le run associé et son résultat, puis contrôler les API publiques. Les verrous partagés des workflows et l'idempotence des écritures restent nécessaires : une coupure réseau après acceptation peut rendre le résultat de l'appel incertain. Le dispositif ne prétend pas garantir un seul envoi dans tous les cas de panne distribuée.

Le contrôle de fraîcheur distingue les collectes, les publications et les absences admissibles. Rising sans historique reste signalé mais ne relance pas seul les trois autres collecteurs. Une API publique indisponible ne fournit aucune preuve d'une édition manquante. Les dernières erreurs et tentatives doivent être consultables sans exposer les secrets.

L'accès GitHub se limite au dépôt concerné et aux permissions requises. La [documentation de l'API dispatch](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event) exige `Actions: write` pour un jeton à permissions fines. Le jeton doit rester dans les secrets Cloudflare et être révocable ; aucune valeur n'entre dans le dépôt ni dans les réponses de santé.

## Gratuité et dépendances restantes

Cloudflare propose les Durable Objects sur Workers Free avec le backend SQLite ; les opérations dépassant les quotas gratuits échouent. Le choix du plan doit rester Workers Free et la consommation doit être vérifiée dans le compte utilisé. Voir les [tarifs Durable Objects](https://developers.cloudflare.com/durable-objects/platform/pricing/) et les [tarifs Workers](https://developers.cloudflare.com/workers/platform/pricing/).

Un réveil toutes les cinq minutes représente 288 réveils par jour, avant reprises. Cette fréquence reste un calcul de conception ; la consommation CPU, le nombre de requêtes et les limites réelles doivent être contrôlés lors de la recette.

Cloudflare précise que les [Cron Triggers utilisent UTC et que leurs changements peuvent prendre jusqu'à quinze minutes à se propager](https://developers.cloudflare.com/workers/configuration/cron-triggers/). Une horloge indépendante retire la dépendance au seul événement `schedule` de GitHub, mais aucun résultat de cet audit ne démontre encore sa régularité en production. GitHub Actions, les sources externes et Neon peuvent toujours rencontrer leurs propres pannes.

## Vérification locale indépendante

Quatre suites Vitest ont été exécutées après relecture : `automation-watchdog`, `automation-workflow-preflight`, `charts-recovery` et `charts-refresh-runner`. Résultat : **87 tests réussis**. Elles couvrent les échéances UTC et leurs marges, la réservation avant l'appel, les limites de reprise, les réponses ambiguës, l'absence de fuite du jeton, les filtres dépôt/branche/événement, les précontrôles sous verrou et les modes des blocs Bash Charts.

La relecture a relevé une incompatibilité de date : les API Charts en production renvoient `publishedAt` sous forme de timestamp Postgres, par exemple `2026-10-19 14:19:32.16+00`. Le schéma initial exigeait une date ISO et aurait bloqué toutes les inspections Charts. Le noyau accepte désormais le format réellement servi après validation de la date ; les fixtures le reproduisent.

Ces tests simulent les transports. Ils ne déclenchent aucun workflow distant et ne mesurent ni la ponctualité de Cloudflare ni celle des runs GitHub. Après ajout du mode simulation, les deux suites `automation-watchdog` et `automation-workflow-preflight` totalisent **67 tests réussis** : 24 pour le noyau, dont l'absence de dispatch et de réservation en simulation, et 43 pour les précontrôles.

La recette de l'adaptateur dans le moteur officiel `workerd`, via Miniflare et le stockage SQLite, passe ses **cinq groupes de contrôles**. Elle vérifie l'accès public limité à la santé, la reconnaissance des données fraîches, la réservation unique entre passages concurrents, la conservation du délai de reprise après redémarrage et l'arrêt des appels réseau après désactivation. Les services distants y sont simulés. Le contrôle global du lot est suivi séparément avant livraison.

## Déploiement réel en observation

Le Worker est réellement déployé, version `9783b910-61f5-4b09-a37a-f42fafc6d663`, à [sandbox-automation-watchdog.sandbox-podcast-pro.workers.dev](https://sandbox-automation-watchdog.sandbox-podcast-pro.workers.dev). Son cron UTC est `*/5 * * * *`, avec `ENABLED=true` et `DRY_RUN=true`. Ce mode exécute les inspections et signale les tâches dues, sans POST de dispatch ni consommation des tentatives persistantes. La configuration locale conserve `ENABLED=false` et `DRY_RUN=true` ; un redéploiement doit donc préciser les deux valeurs voulues.

Un jeton GitHub fin de quatre-vingt-dix jours a été créé, limité au seul dépôt `Sandbox-podcast/sandbox-podcast-site` avec Actions en lecture/écriture. Il est stocké chiffré dans le secret Cloudflare `GITHUB_ACTIONS_TOKEN`, sans valeur dans Git ni dans le présent suivi. Son expiration est le **18 janvier 2027** ; prévoir son renouvellement avant cette date.

Le premier tick réel observé porte `checkedAt=2026-10-20T09:05:12.647Z`. La [santé publique](https://sandbox-automation-watchdog.sandbox-podcast-pro.workers.dev/health) renvoie HTTP 202, `schedulerOk=true` et `dataFresh=null`. Le contrôleur a donc effectué un premier passage distant ; la fraîcheur des publications reste non confirmée. Cette observation unique ne prouve pas encore la régularité des échéances.

## Activation des dispatchs et recette restante

Les nouveaux modes `due`, `recover` et `discovery` ne sont pas encore présents sur `main`. Garder `DRY_RUN=true` tant que leur livraison Git n'est pas autorisée et effectuée. Après cette livraison, sa CI et l'autorisation de mise en service, la commande d'activation est :

```powershell
node apps/site/.local/watchdog-tools/node_modules/wrangler/bin/wrangler.js deploy --config tools/automation-watchdog/wrangler.jsonc --var ENABLED:true --var DRY_RUN:false
```

Cette commande publie une nouvelle version ; elle n'est pas exécutée dans la mise à jour documentaire. Pour revenir à l'observation, remplacer `DRY_RUN:false` par `DRY_RUN:true`. Pour arrêter aussi les inspections, utiliser `--var ENABLED:false --var DRY_RUN:true`. Ces opérations conservent l'état SQLite. La procédure complète figure dans [le guide du Worker](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/tools/automation-watchdog/README.md).

Les vérifications suivantes restent à réaliser :

1. Observer plusieurs ticks réels et vérifier la consommation et les quotas Workers Free, sans souscrire de plan payant.
2. Après activation autorisée des dispatchs, suivre plusieurs échéances consécutives : heure due, tentative externe, création et démarrage du run, résultat public.
3. Vérifier la coexistence avec les crons GitHub et le comportement après une interruption, une erreur GitHub ou une API publique indisponible.

Un dispatch manuel réussi validera l'accès et le traitement. Seule l'observation de plusieurs échéances réelles permettra de confirmer la cadence. Le suivi doit aussi mesurer la taille et l'ancienneté de la file News : un ordonnanceur ponctuel ne garantit pas à lui seul sa résorption.

Le rapport d'[audit News et backend](audit-automatisation-2026-10-20.md) décrit les protections locales déjà vérifiées. Aucun SLA n'est annoncé : une horloge externe ne garantit ni le démarrage d'un runner, ni la disponibilité des sources, ni la publication dans un délai fixe. Les résultats des prochaines échéances doivent compléter ce suivi.
