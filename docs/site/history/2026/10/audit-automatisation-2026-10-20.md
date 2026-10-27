# Automatisation News et classements : contrôle du 20 octobre 2026

Contrôle demandé par Lou lors de la reprise des travaux locaux. Les observations ci-dessous portent sur la production en lecture seule ; les corrections restent locales. Aucun workflow distant n'a été relancé et aucun article n'a été publié pendant cet audit.

## News : fonctionnement existant

Le workflow `.github/workflows/news-refresh.yml` demande un lancement toutes les heures, à la minute 37. GitHub Actions l'exécute sur `main` si la variable `SANDBOX_NEWS_PUBLIC` vaut `true`. Le site Vercel doit aussi avoir son drapeau `SANDBOX_NEWS_PUBLIC=1` et un secret `CRON_SECRET` correspondant au secret du runner. Une visite de `/news` lit le fil en base ; elle ne lance pas la collecte.

Le runner consulte les 105 sources du registre, avec quatre requêtes simultanées et un budget de huit minutes. Il conserve l'état des sources et les articles datés des quatorze derniers jours dans la file Postgres. L'URL canonique évite de traiter deux fois un même article. Les articles déjà publiés restent accessibles dans l'historique au-delà de cette fenêtre.

Le runner produit ensuite les résumés français avec le modèle Qwen3-4B-Instruct-2507 exécuté sur son CPU, puis les traductions anglaises, espagnoles et allemandes avec Argos. Il ne fait pas appel à une API de génération payante. Les modèles restent dans le cache GitHub Actions entre les passages lorsqu'il est disponible. Une fiche doit respecter les contrôles de résumé, de citations et de traduction avant publication.

Chaque réservation porte sur cinq candidats et expire après vingt minutes. Le traitement enchaîne les lots dans un budget de vingt-deux minutes. Un candidat refusé est repris après vingt-quatre heures, au maximum trois fois. La file conserve les éléments restants pour les passages suivants. Le runner appelle les API privées avec le secret cron, ajoute les fiches acceptées à `news_items`, puis invalide les pages News. Le contrôle final relit l'API publique et échoue si la collecte a plus de trois heures, si toutes les sources sont indisponibles ou si le fil est vide.

## News : résultats distants

À 09 h 53, heure de Paris, le 20 octobre, `GET /api/news` répond HTTP 200. Sa première page contient trente articles et un curseur de suite. Le fil annonce 78 sources lisibles sur 105 et une collecte datée du **20 octobre à 04 h 03 Paris** (`2026-10-20T02:03:02.931Z`). L'article en tête porte une date de publication éditeur du 19 octobre à 14 h Paris. Cette date ne renseigne pas l'heure d'insertion sur le site.

Le script `node apps/site/scripts/news-health.ts` échoue à ce contrôle : la collecte a dépassé le seuil de trois heures. Le fil reste lisible avec ses anciens articles.

Les derniers lancements GitHub Actions ont été lus avec `gh run list` et les bilans du dernier run avec `gh run view --log` :

| Déclenchement                                                                                             | Début, heure de Paris        | Résultat                           |
| --------------------------------------------------------------------------------------------------------- | ---------------------------- | ---------------------------------- |
| [Planifié, 39356595304](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39356595304) | 20 octobre, 04 h 00 min 56 s | Réussi, terminé à 04 h 14 min 43 s |
| [Planifié, 39338877846](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39338877846) | 20 octobre, 01 h 01 min 10 s | Réussi                             |
| [Manuel, 39308199122](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39308199122)   | 19 octobre, 21 h 06 min 36 s | Réussi                             |
| [Manuel, 39266494010](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39266494010)   | 19 octobre, 16 h 10 min 02 s | Réussi                             |
| [Planifié, 39260759503](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39260759503) | 19 octobre, 15 h 30 min 34 s | Échec                              |

Les deux derniers passages planifiés sont espacés d'environ trois heures. Aucun passage plus récent n'apparaît lors du contrôle du matin. La programmation horaire existe, mais les événements observés ne suivent pas cette cadence. Ces journaux ne donnent pas la cause des événements absents ; ils ne suffisent pas à attribuer le retard à un quota ou à une configuration particulière.

Le dernier run a détecté 413 articles et ajouté dix candidats nouveaux. La file annonçait 475 candidats en attente au premier lot, avec une première entrée datant du 19 octobre à 16 h 12 Paris. Le runner a traité quinze candidats en trois lots, publié six fiches, dont trois résumés nouvellement générés, et écarté neuf candidats. Il a terminé sans vider la file. Le contrôle de santé était réussi à la fin de ce run, puisque la collecte venait d'avoir lieu. Cette réussite démontre un cycle de collecte et de publication ; elle ne démontre ni un lancement horaire ni l'absence d'arriéré.

## Correctifs backend locaux

Le fil expose désormais `lastPublishedAt`, calculé depuis la dernière insertion dans `news_items.created_at`. Cette date reste identique sur les différentes pages de l'historique et ne change ni à la consultation ni lors d'une collecte sans nouvel article. Une réingestion déjà connue ne la fait pas avancer. Le champ est facultatif et nullable pour accepter les aperçus et réponses précédentes. `checkedAt` garde son sens de date de collecte ; `publishedAt` reste la date donnée par l'éditeur de l'article. Aucune migration n'est nécessaire.

L'enregistrement des sources refuse désormais de remplacer un relevé plus récent par un ancien. Un lot déjà réservé peut terminer après une nouvelle collecte ; il ajoute toujours ses articles, mais conserve les statuts et la date du relevé le plus récent. Le correctif empêche aussi de rétablir un ancien statut réussi après un échec de source plus récent.

La reprise de traduction article par article propage désormais l'expiration du budget. Le code précédent pouvait transformer cette interruption en résultat réussi et classer les candidats restants comme refusés, avec vingt-quatre heures d'attente. Le traitement échoue maintenant et laisse la réservation expirer pour permettre une reprise normale.

Les corrections portent sur `src/domain/news-preview.ts`, `src/lib/news-store.ts` et `src/pipeline/news-generation.ts`, avec des régressions dans `test/news-store.test.ts` et `test/news-generation.test.ts`.

## Validation backend et limites

Sept suites backend News ont été exécutées avec Vitest : **57 tests réussis**. Les régressions ajoutées vérifient les trois dates distinctes, l'absence de modification lors d'une réingestion, la stabilité de la date de publication pendant la pagination, la conservation d'un relevé plus récent et l'expiration pendant une reprise de traduction. Les tests de stockage utilisent PostgreSQL WASM ; aucun test de cette série n'écrit dans la base distante. `git diff --check` ne signale pas d'erreur d'espacement.

Le contrôle global, la vérification des vues et l'audit des classements sont complétés par les autres volets de ce lot. Le nouveau champ `lastPublishedAt` et les protections backend ne sont pas encore présents en production. La cause des événements GitHub absents reste à établir. La cadence réelle et l'évolution de l'arriéré devront être vérifiées après livraison autorisée, sur plusieurs événements planifiés successifs.
