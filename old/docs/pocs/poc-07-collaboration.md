# POC 7 — Collaboration temps réel

Résultat : **PASS** sur une boucle locale, en mémoire. Code produit : `packages/collab` (19 tests). Décision : [ADR-0008](../adr/ADR-0008-collaboration-crdt-et-commandes.md).

## Ce qui est construit

- `CollabServer` : serveur WebSocket qui parle le protocole Yjs (y-websocket). Pour chaque connexion : autorisation par jeton, droit en lecture ou écriture, présence, sauvegarde automatique, historique de versions.
- `CollabClient` : client avec reconnexion automatique. Ce qui est écrit hors ligne s'accumule dans le document local et part à la reconnexion. Même protocole dans un navigateur avec l'API WebSocket native.
- `DocumentStore` : contrat de persistance (état courant et versions nommées). `InMemoryDocumentStore` pour les tests ; PostgreSQL en production.

Les droits sont vérifiés par le serveur **à chaque message**, pas seulement à la connexion : un lecteur peut demander l'état, jamais l'écrire. Une révocation s'applique sans reconnexion.

## Résultats

| Critère                        | Vérifié par                                                                                                                                                     |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-COLLAB-001, AC-HTML-002     | une modification de A apparaît chez B ; p50 0,07 ms, p95 0,28 ms, max 1,6 ms sur 500 modifications (boucle locale, mesure ponctuelle)                           |
| AC-COLLAB-002                  | modifications simultanées de texte, de liste et de la même clé : aucune perte de texte, convergence ; 2 000 modifications entrelacées de 3 personnes convergent |
| AC-COLLAB-003, AC-RECOVERY-005 | coupure sèche, écritures des deux côtés pendant la coupure, fusion à la reconnexion (`A: début :B`) ; reprise après une longue absence                          |
| AC-COLLAB-004                  | présence des autres affichée et retirée au départ ; un client muet (coupure silencieuse) est retiré au bout de 2 intervalles de test de vie                     |
| AC-COLLAB-005                  | accès retiré : connexion fermée et pas de reconnexion automatique ; droit d'écriture retiré : écritures refusées sans reconnexion                               |
| AC-SEC-001, AC-SEC-002         | jeton invalide refusé ; lecteur refusé en écriture (contenu du serveur et de l'auteur intact) et écritures refusées comptées                                    |
| AC-RECOVERY-001, 002           | sauvegarde automatique ; un nouveau serveur retrouve l'état                                                                                                     |
| AC-HTML-003, 004               | versions nommées ; restauration qui ajoute une version « avant » et une version « restauration » sans rien effacer                                              |

Charge : 5 000 insertions envoyées d'un coup sont toutes reçues par l'autre client en 186 ms.

## Défaut trouvé et corrigé

Les `Awareness` de Yjs gardent un minuteur interne : sans `destroy()`, un processus ne se termine pas, et chaque document ouvert restait en mémoire pour toujours. Le serveur décharge maintenant un document quand le dernier utilisateur part (après sauvegarde), et `close()` détruit tout. Le client a une méthode `destroy()`.

## Sensibilité des tests

Dix mutations du code ont été essayées, toutes détectées : écriture autorisée pour tous, jeton non vérifié, présence non retirée, test de vie sans coupure, révocation sans effet, droit non mis à jour, pas de sauvegarde, client sans reconnexion, reconnexion après révocation, pas de demande d'état. Un test était trop faible (compteur d'écritures refusées jamais incrémenté, assertion toujours vraie) et a été corrigé.

## Limites

- Tout tourne en boucle locale avec un stockage en mémoire. La latence sur un vrai réseau, la reprise avec des centaines de clients et la taille maximale d'un document ne sont pas mesurées.
- Pas de verrou par ressource : le CRDT n'en a pas besoin pour le texte, mais pas de protection contre deux modifications qui se contredisent sémantiquement (par exemple deux titres différents : le dernier gagne).
- Le travail hors ligne n'est pas borné : un client coupé longtemps peut accumuler beaucoup de modifications. `pendingOfflineBytes` permet de l'afficher, aucune limite n'est imposée.
- La restauration de version gère les types texte, table et liste, déclarés par l'appelant (`schema`).
- La vérification des jetons est une fonction injectée : l'authentification réelle n'existe pas encore.
- Le serveur tourne sur un seul processus : plusieurs instances demanderaient de partager l'état (Redis ou équivalent), non fait.

## Suite

Stockage PostgreSQL, authentification, éditeur CODE | PREVIEW dans l'application, diffusion des mises à jour de présentation vers la régie, mesure sur un vrai réseau, limite de taille des documents.
