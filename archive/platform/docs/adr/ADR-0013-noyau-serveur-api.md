# ADR-0013 — Noyau serveur : Fastify, PostgreSQL sans ORM, sessions en base

- Statut : acceptée
- Date : 2026-10-06
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

L'[ADR-0001](ADR-0001-stack-applicative-et-monorepo.md) fixe TypeScript, un monorepo pnpm, des services Node et PostgreSQL. Les POC ont produit des paquets de logique pure (régie, conducteur, collaboration, MCP, enregistrement) qui attendent un stockage persistant, une identité fiable et des droits vérifiés. Le [modèle de menaces](../threat-model.md) liste les manques à combler en premier : authentification, identité de participant fixée par le serveur, journal d'audit durable, WebSocket collaboratif durci.

## Décision

1. **Serveur HTTP : Fastify** (mature, validation par schéma, journalisation structurée intégrée). Les paquets de logique restent indépendants du serveur.
2. **PostgreSQL via `pg`, SQL écrit à la main, pas d'ORM.** Le schéma est petit et central pour la sécurité (contraintes, déclencheurs) ; un ORM cacherait ce qui compte.
3. **Migrations en fichiers SQL numérotés**, avec empreinte SHA-256 enregistrée. Une migration déjà appliquée dont le contenu change fait **échouer le démarrage** (règle « ne jamais modifier une migration appliquée »). Chaque migration s'exécute dans une transaction.
4. **Authentification interne** (pas de fournisseur externe pour l'instant) : e-mail et mot de passe, haché par **scrypt** (`node:crypto`, sans dépendance native), politique de longueur, verrouillage temporaire après des échecs répétés, message d'erreur identique pour un compte inconnu et un mauvais mot de passe. Évaluer un fournisseur managé ou OAuth/MFA plus tard reste possible : la session est découplée du mode de connexion.
5. **Sessions opaques en base** : jeton aléatoire de 256 bits, seule son empreinte SHA-256 est stockée ; durée limitée, révocable. Transport : cookie `HttpOnly`, `SameSite=Strict`, `Secure` hors développement, ou en-tête `Authorization: Bearer` pour les clients non navigateur. Pour les requêtes qui modifient l'état avec le cookie : l'en-tête `Origin` doit correspondre à une origine autorisée (protection CSRF).
6. **Autorisation** : rôles par podcast (`ADMIN`, `PRODUCER`, `HOST`, `EDITOR`, `VIEWER`) évalués par une fonction pure testée ; chaque lecture et écriture passe par (podcast, id).
7. **Identité LiveKit attribuée par le serveur** : l'identité d'un participant est l'identifiant de sa ligne `participants` (UUID). Le nom affiché est du texte nettoyé qui ne sert jamais dans un chemin de fichier. Le jeton de salle est signé par le serveur, court, avec des droits selon le rôle.
8. **Audit en ajout seul** : table `audit_log` protégée par un déclencheur qui refuse `UPDATE` et `DELETE` ; l'écriture est dans la même transaction que l'action.
9. **Corrélation** : chaque requête a un identifiant (`x-correlation-id` accepté s'il est bien formé, sinon généré), renvoyé en réponse, présent dans les journaux et l'audit.
10. **Tests d'intégration contre un vrai PostgreSQL** (conteneur local `postgres:16-alpine`, port dédié, mot de passe généré dans `.local/`), qui se **sautent explicitement** si la base n'est pas joignable : jamais un échec silencieux présenté comme un succès.

## Conséquences

- Les paquets `episode-factory`, `studio-control` et `collab` reçoivent des implémentations PostgreSQL de leurs interfaces de stockage.
- L'enregistrement serveur (Egress, superviseur) reste dans `pocs/poc-03-server-recording` : le promouvoir en service est une étape suivante. L'API ne fait qu'enregistrer l'intention (commandes `START_RECORDING` et `STOP_RECORDING`) et fournir des jetons.
- L'inscription ouverte est **désactivée par défaut** : les comptes sont créés par une commande d'administration ou par invitation.

## Risques

- Sessions en base : une lecture par requête authentifiée ; prévoir un cache court si la charge l'exige.
- La limite de tentatives de connexion est par e-mail, pas par adresse IP (l'adresse n'est pas stockée par choix de confidentialité) : un attaquant peut verrouiller le compte d'une victime. À arbitrer avec le propriétaire (verrouillage progressif, captcha, MFA).
- scrypt avec des paramètres raisonnables (coût 2¹⁷) mais non réglés sur le matériel de production.
