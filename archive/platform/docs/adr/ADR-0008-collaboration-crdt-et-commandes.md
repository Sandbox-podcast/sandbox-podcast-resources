# ADR-0008 — Collaboration : CRDT pour les documents, commandes pour l'état critique

- Statut : acceptée
- Date : 2026-10-05
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

Le §13 du prompt maître demande une collaboration en temps réel et précise : « Ne pas utiliser un CRDT pour toutes les données par défaut. » Deux familles de données coexistent : des documents édités à plusieurs (code des présentations, notes, rundown) et un état critique piloté (Program, Preview, enregistrement).

## Options considérées

- A. Tout en CRDT : simple à raisonner pour la convergence, mais le Program n'a pas de sens à fusionner (deux « Program » simultanés), et les droits se vérifient mal sur un état fusionné.
- B. Tout en commandes serveur : exact, mais mal adapté à l'édition de texte (conflits, perte de frappe).
- C. CRDT (Yjs) pour les documents édités à plusieurs, commandes serveur pour l'état critique.

## Décision

Option C.

- **Yjs sur WebSocket** (`packages/collab`) pour : le code des présentations, les notes, le contenu du rundown, les commentaires. Les droits sont vérifiés par le serveur à chaque message. Sauvegarde automatique, versions nommées, restauration sans perte d'historique.
- **Commandes serveur** (`packages/studio-control`, [POC 6](../pocs/poc-06-regie.md)) pour : Program, Preview, état d'enregistrement, séquence courante, consentements. Version optimiste, clé d'idempotence, audit.
- Les deux se rejoignent par les identifiants : un document collaboratif est référencé par une scène ; la publication d'une version de présentation est une commande (`PUBLISH_PRESENTATION_VERSION`) qui fige une version.

## Conséquences

- Le contenu d'un document converge toujours, mais sans règle métier : deux personnes qui changent le même champ simple, le dernier gagne. Pour un champ qui ne doit pas être écrasé, passer par une commande.
- La mémoire d'un document est déchargée quand plus personne ne l'édite.
- Travail hors ligne : accepté sans limite pour l'instant, avec compteur d'octets en attente.
- Un document Yjs grossit avec son historique d'opérations (suppressions comprises) : prévoir une limite de taille et un nettoyage par instantané.

## Risques

- Plusieurs instances du serveur nécessitent un état partagé.
- Un utilisateur dont l'accès est retiré garde la copie locale de ce qu'il a déjà reçu : c'est inhérent à tout système de synchronisation.

## Plan de validation

Tests de `packages/collab` (19). À mesurer ensuite : latence sur un réseau réel, grande taille de document, nombre de clients par document.
