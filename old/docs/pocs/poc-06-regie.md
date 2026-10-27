# POC 6 — Régie Preview / Program

Résultat : **PASS** pour la logique de commande, en mémoire. Code produit : `packages/studio-control` (34 tests). Latence réelle de bout en bout non mesurée.

## Ce qui est construit

- `handleCommand` : fonction pure qui applique une commande à l'état d'un studio. Elle retourne le nouvel état et les événements d'audit, ou une erreur structurée sans toucher à l'état.
- `StudioService` : point d'entrée unique des commandes (UI, API, WebSocket, MCP). Il garantit qu'une commande n'a d'effet qu'une fois, que les écritures concurrentes ne produisent jamais d'état incohérent, et que tout est audité.
- `InMemoryStudioStore` : stockage de test. Il suit le contrat d'une transaction PostgreSQL : état, événements et résultat de la commande écrits ensemble, seulement si la version n'a pas changé, avec unicité de la clé de commande.

Chaîne d'une commande : permission, version attendue, validation, règles métier, exécution, écriture atomique, audit.

## Règles

- `SET_PREVIEW` ne touche jamais au Program.
- `TAKE` (avec la Preview que l'opérateur a sous les yeux) : la Preview doit être celle attendue et prête. Elle passe en Program et l'ancien Program devient la Preview, comme un mélangeur vidéo.
- Un média en chargement ou en erreur bloque le `TAKE`. Une erreur sur le média du Program est signalée par un événement (`ProgramAssetError`) mais ne change pas le Program : décision de l'opérateur.
- `CUT` direct. Une coupure manuelle arrête le réalisateur automatique (§11.2 : la reprise manuelle est immédiate). Le réalisateur automatique, lui, ne peut que couper, et seulement quand il est actif : une décision automatique périmée après une reprise manuelle est refusée.
- Un seul enregistrement actif par studio. Il exige le consentement des participants requis, donné par eux seuls.
- Changer de séquence ne touche ni au Program ni à l'enregistrement.
- Permissions : Producer et Admin pilotent la régie, un Host seulement si la politique l'autorise, personne d'autre (invité, éditeur, agent MCP sans rôle). L'enregistrement, lui, reste réservé aux Producer et Admin. Seul le système peut rapporter l'état d'un média.

## Critères d'acceptation

| Critère                                         | Vérifié par                                                                                  |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------- |
| AC-REGIE-001 Preview indépendante, AC-SCENE-006 | `SET_PREVIEW` laisse le Program inchangé                                                     |
| AC-REGIE-002 `TAKE`                             | Preview prête devient Program une seule fois, audité                                         |
| AC-REGIE-003 média en erreur                    | Program intact, `TAKE` refusé, reprise possible avec une source valide                       |
| AC-REGIE-004 types                              | 8 types de source acceptés                                                                   |
| AC-REGIE-005, AC-SEC-002 permissions            | 4 acteurs refusés sur 7 commandes de régie, état intact, rejets audités                      |
| AC-REGIE-006 double commande                    | même clé rejouée : un seul effet ; deux `TAKE` concurrents : un seul réussit                 |
| AC-REC-009 double démarrage                     | une seule session, avec un ou deux processus                                                 |
| AC-REC-010 consentement                         | refus tant qu'un consentement manque                                                         |
| AC-RUNDOWN-003                                  | changement de séquence sans coupure                                                          |
| AC-SPK-005                                      | coupure manuelle arrête l'automatique, décision automatique périmée refusée                  |
| AC-SEC-007 audit                                | chaque commande, acceptée ou refusée, journalisée avec son auteur et un numéro d'ordre       |
| Concurrence                                     | 50 commandes en parallèle, une ou cinq instances du service : état cohérent, journal ordonné |

Performance du traitement métier : 100 000 paires `SET_PREVIEW` + `TAKE` en moins de 2 s sur ce poste (le test borne, il ne mesure pas finement). La latence entre un `TAKE` accepté et l'état Program observé par les clients (AC-PERF-003) dépend du transport et n'est pas mesurée.

## Comment les tests ont été validés

Huit mutations du code ont été essayées : `TAKE` sans vérifier que le média est prêt, version attendue ignorée, changement de Preview ignoré, second démarrage autorisé, consentement donné par n'importe qui, rapport de média ouvert à tous, coupure manuelle sans arrêter l'automatique, contrôle d'idempotence retiré du service. Sept sont détectées. La dernière est équivalente : le stockage détecte déjà le doublon à l'écriture, c'est une double protection voulue.

## Décisions de conception prises ici

- Commandes sérialisées par studio dans chaque processus, version optimiste en plus pour les autres processus. Sans sérialisation, 50 commandes concurrentes épuisaient les nouvelles tentatives de la seule version optimiste.
- Le `TAKE` échange Preview et Program (comportement d'un mélangeur) plutôt que de vider la Preview.

## Limites

- Tout est en mémoire. Le stockage PostgreSQL (transaction, contrainte d'unicité sur le studio et la clé de commande) reste à écrire, de même que la diffusion des événements aux clients (WebSocket) et l'application côté média (changer la scène du compositeur du Producer).
- Les transitions (`MIX`) sont enregistrées mais pas appliquées.
- Les superpositions (`overlays`) sont gérées de façon minimale.
- Pas de verrou explicite sur une ressource : la version optimiste suffit pour l'instant.
- Le chargement des médias (préchargement, repli) n'est pas construit : `REPORT_ASSET` en est l'interface.

## Suite

Stockage PostgreSQL, diffusion des événements, branchement du réalisateur automatique (POC 5) et du compositeur du Producer (POC 2), mesure de la latence réelle.
