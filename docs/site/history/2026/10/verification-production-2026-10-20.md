# Recette de production après la PR 99

Relevé du 20 octobre 2026. Les heures sont en UTC ; le site affiche Europe/Paris, soit deux heures de plus à cette date.

## Livraison

La [PR 99](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/99) a été fusionnée à 10:14:46 après ses contrôles verts. Le commit livré est `1f4ead0e8809a2408c1029817ccde393b2b0bbd5`. Vercel confirme son déploiement Production à 10:16:22, identifiant `7197142881`.

Le lot comprend News, Charts, le responsive, les traductions, le wording et les slides 003 de l'autre discussion. Les six pièces et Three.js restent un chantier distinct. Le checkout partagé est préservé ; la livraison utilise un worktree isolé. Les [six descriptions sociales](profils-vision-2026-10-20.md) sont enregistrées et relues. La propagation de Spotify aux applications d'écoute n'est pas mesurée.

## Contrôles exécutés

Avant fusion, `pnpm check` réussit : 1 114 tests, formatage, lint et types. Le build local génère 204 pages. Les deux CI de PR et de push réussissent sur le même arbre Git que le commit de fusion.

La première CI main dépasse les cinq secondes du test PGlite du limiteur admin, sans échec d'assertion. Ce fichier avait passé les deux CI avant fusion. Trois répétitions locales inchangées réussissent, puis la relance du seul job en échec termine avec succès à 10:27:23. Aucun seuil ni contrôle n'est modifié pour cette relance. [CI main, tentative 2](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39406566186).

La recette HTTP publique lit 24 pages dans les quatre langues et deux API : 300 contrôles, dont 296 réussis. Les quatre écarts concernent uniquement le titre d'accueil historique encore enregistré en production. Les vingt autres pages passent les contrôles prévus. Les introductions et métadonnées des quatre accueils sont correctes, ainsi que les dates News et Charts.

La recette mobile vérifie huit rendus : accueil, News, Charts et podcast anglais, à 320 × 740 et 390 × 844. Aucun débordement horizontal ni erreur JavaScript. Le logo est chargé et renvoie à l'accueil de sa langue. Ouverture, fermeture et Échap du menu sont vérifiés. Le footer mesure 254,5 px, avec deux rubriques repliables. Les titres, résumés et textes HTML des miniatures du podcast anglais sont traduits ; la langue française de l'audio reste annoncée. Edge est utilisé avec un écran mobile émulé ; Safari sur téléphone physique n'est pas couvert.

## Contrôle Cloudflare actif

Après CI main verte et déploiement confirmé, Wrangler active `ENABLED=true` et `DRY_RUN=false` à 10:28. Version : `ec966bd7-56b2-4ea3-a6da-052165f5c772`. Le cron reste `*/5 * * * *`. Le jeton GitHub dédié reste chiffré, limité à ce dépôt et à Actions, avec expiration le 18 janvier 2027.

| Passage réellement planifié | Heure UTC    | Écart avec le précédent |
| --------------------------- | ------------ | ----------------------- |
| Premier passage actif       | 10:30:12.305 |                         |
| Deuxième passage            | 10:35:12.326 | 5 min 0,021 s           |
| Troisième passage           | 10:40:12.481 | 5 min 0,155 s           |

Pendant les traitements, la santé renvoie HTTP 202, `schedulerOk=true` et `dataFresh=null`. Elle sépare le fonctionnement du contrôleur d'une publication entièrement confirmée. Aucun doublon News n'est créé aux passages de 10:35 et 10:40.

## Résultat News réellement publié

Le [run News 39408393129](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39408393129), en mode `due`, est créé à 10:30:14 et démarre à 10:30:17.

| Mesure publique                  | Avant activation | Après reprise                   |
| -------------------------------- | ---------------- | ------------------------------- |
| Dernière collecte                | 07:55:10.913     | 10:33:04.325                    |
| Dernière publication sur le site | 08:06:31.707     | 10:39:30.419, puis 10:43:07.447 |

Ces lectures prouvent une nouvelle collecte et des insertions successives. Le workflow termine en échec à 10:46:31 : quatre lots, quinze candidats, quatre publications, onze candidats ignorés et un échec. La publication partielle est démontrée. Le processus Python/Qwen du dernier lot quitte avec un code non nul et aucun message stderr ; le code et le signal exacts n'étaient pas conservés. Aucun OOM ou autre cause native précise n'est démontré. Le rattrapage se déclenche seul à 10:50:14, run 39410728726 ; une nouvelle collecte à 10:51 est visible dans l'API et sur le site. La collecte signale 76 sources disponibles sur 105. Les sources indisponibles restent visibles et les publications reçues sont conservées.

Qwen produit les résumés et Argos les traductions dans GitHub Actions. Cette exécution ne consomme pas l'abonnement Codex. Cloudflare contrôle les dates et déclenche les workflows ; il ne produit pas le contenu.

## Deux écarts révélés par la recette distante

Le [run Charts discovery 39408394552](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39408394552) est créé à 10:30:15, démarre à 10:30:18 et termine en échec à 10:34:58. Les trois éditions publiques sont déjà à jour pour le créneau du matin : GitHub, Skills et Models répondent HTTP 200 avec vingt entrées et l'édition `2026-10-20T00:00Z`. Rising reste en attente ; cela ne déclenche pas à lui seul un recalcul.

Les réponses 503 de Trending et de la découverte sont des bilans métier partiels. La découverte traite 5 000 résultats sans erreur puis atteint son budget de 220 secondes. Vercel mesure 224,4 secondes sur un maximum de 300 : ce résultat ne correspond pas à un timeout de plateforme. Le code précédent recommence les partitions à zéro au prochain appel et assimile les limites normales de l'échantillonnage à une panne. Le code Trending fusionne les exclusions par critères et les métadonnées manquantes dans le même compteur d'échecs. Le bilan de production ne permet donc pas d'identifier rétroactivement la nature exacte de ses deux cas. Une lecture indépendante à 10:49:53 relève quinze dépôts actuels, tous disponibles : quatorze avec une licence admise, un avec NOASSERTION, légitimement exclu. La liste ayant changé, ce contrôle ne reconstitue pas les douze dépôts du run.

Le complément local conserve un checkpoint après chaque page enregistrée, reprend sous verrou et distingue l'échantillonnage borné des vraies réponses GitHub incomplètes. Les erreurs de réseau, de quota ou d'écriture continuent à échouer. La décision et les tests sont dans [DD-0072](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0072-reprise-persistante-decouverte-github.md). La correction locale exige une nouvelle recette réelle après déploiement ; ce relevé ne la présente pas comme déjà exécutée en production.

L'autre écart concerne deux valeurs éditoriales historiques de l'accueil, déjà attestées dans les dictionnaires Git. Leur ajout à la liste fermée de [DD-0068](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0068-wording-aligne-sur-la-vision.md) corrige le titre et son repère sans accès admin ni écriture du contenu stocké. Les textes personnalisés différents restent conservés. Les dix tests marketing passent, avec une revue indépendante des variantes proches et des quatre traductions.

Le diagnostic complémentaire Qwen conserve désormais le code de sortie et le signal dans le message d'erreur. Les délais, critères de qualité et limites de reprise restent inchangés. Dix-sept tests de processus simulé et de génération passent, dont les chemins timeout, arrêt et sortie réussie ; les dix-neuf tests de réservation et de reprise existants ont aussi été rejoués.

## Preuves et limites

Rapports JSON, journaux et captures : `.local/watchdog/` du worktree de livraison. Captures navigateur : aussi `apps/site/.local/watchdog/` du checkout partagé. Ces dossiers sont ignorés par Git ; les preuves publiées n'exposent aucun jeton.

La régularité de trois passages et une publication News ne constituent pas un SLA. Le renouvellement du jeton, la disponibilité des sources et des runners restent nécessaires. L'historique du contrôle local avant PR 99 reste dans [le relevé précédent](validation-lot-2026-10-20.md).
