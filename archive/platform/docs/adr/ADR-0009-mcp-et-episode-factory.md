# ADR-0009 — Serveur MCP et Episode Factory : un cœur sans transport, des garde-fous à chaque appel

- Statut : acceptée
- Date : 2026-10-06
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

Le §26 du prompt maître demande un serveur MCP sécurisé qui laisse des IA autorisées créer des épisodes, modifier des séquences et écrire des présentations. Le §33.12 et §33.13 fixent les critères : création atomique et idempotente d'un épisode depuis un template (AC-FACTORY), scopes, isolation entre podcasts, audit, idempotence, validation des sorties d'un modèle (AC-MCP).

Une IA est un acteur peu fiable par construction : elle se trompe, elle peut être manipulée par le contenu qu'elle lit, et elle peut rejouer un appel. Les garde-fous ne peuvent pas dépendre de sa bonne conduite.

## Décision

1. **Un cœur sans transport.** `Platform.execute(credentialId, tool, args)` porte toute la logique. L'adaptateur MCP (`createPlatformMcpServer`) n'est qu'une fine couche qui enregistre chaque tool auprès du SDK et renvoie une enveloppe structurée. Le même code servira une API HTTP ou les tests.
2. **Le podcast vient du credential, jamais de l'appel.** Un credential est lié à un podcast et à un humain responsable. Aucun tool n'accepte `podcastId` (schémas stricts : un argument inconnu est refusé). Tout accès passe par `episodes.get(credential.podcastId, id)` : un identifiant d'un autre podcast répond `NOT_FOUND`, pas `FORBIDDEN`, pour ne pas révéler son existence. Les catalogues (templates, assets, thèmes) sont aussi résolus par podcast.
3. **Chaque appel repasse par la même chaîne**, dans cet ordre : credential relu à chaque appel (révocation et expiration immédiates, même sur une session ouverte) → limite de débit → scopes → validation des arguments → exécution → audit. Le client MCP n'est jamais une frontière de sécurité.
4. **Scopes** : `episode:read`, `episode:write`, `asset:read`, `presentation:read`, `presentation:write`. Un tool sans le scope répond `FORBIDDEN` avec la liste des scopes manquants, et n'applique rien. `presentation:read` s'ajoute à la liste d'exemples du prompt : lire n'implique pas pouvoir écrire.
5. **Audit** : toute tentative de mutation est journalisée, réussie ou non (acteur, credential, podcast, tool, scope, cible, résultat, détail, horodatage, corrélation). Les lectures réussies ne le sont pas ; les lectures refusées (droits, limite, credential) le sont. L'identifiant de corrélation est aussi rendu à l'agent.
6. **Idempotence documentée par tool**, visible dans la description MCP :
   - création d'épisode : `idempotencyKey` obligatoire, empreinte de la demande, même clé avec une autre demande = `CONFLICT` ;
   - modification de séquence : révision attendue (`expectedRevision`) ;
   - modification de présentation : empreinte du contenu lu (`expectedHash`) ; si un humain a écrit entre-temps, l'agent reçoit `CONFLICT` au lieu d'écraser son travail ;
   - publication : portée par la confirmation (voir 8).
7. **Validation avant application** (AC-MCP-007) : schémas Zod stricts, patch non vide, HTML contrôlé par `validatePresentationHtml` (ressources externes, iframes, formulaires, redirections, `eval`) avant d'écrire. Cette validation aide l'agent à corriger tôt ; la sécurité réelle reste le bac à sable de l'[ADR-0007](ADR-0007-isolation-des-presentations-html.md).
8. **Publication = action publiante, confirmation humaine** (§26.3). Le premier appel crée une demande (`CONFIRMATION_REQUIRED` + identifiant). Un humain approuve **dans l'application** (`decideConfirmation`) : l'approbation n'est exposée par aucun tool MCP, et l'approbateur doit être PRODUCER de l'épisode. Le second appel publie. La confirmation est à usage unique, expire (10 minutes par défaut), est liée à la demande exacte (épisode, présentation, libellé) et à l'**empreinte du contenu approuvé** : si l'agent modifie le HTML après l'approbation, l'approbation tombe (`le contenu a changé`). Rejouer le même appel renvoie la même version sans republier.
9. **Limite de débit** par credential, à seau de jetons : lecture 1 jeton, mutation 5.
10. **Erreurs internes** : l'agent reçoit un message neutre avec l'identifiant de corrélation ; le détail reste dans l'audit.
11. **Episode Factory** (`packages/episode-factory`) : un template est une donnée versionnée et validée. La création valide tout (demande, template, cohérence interne, assets, thèmes) avant d'écrire, rapporte tous les problèmes trouvés d'un coup, puis écrit en **une seule opération atomique** (`createIfAbsent`, contrainte d'unicité sur podcast + clé d'idempotence). Les assets marqués `FREEZE` ont leur version figée dans l'épisode ; une nouvelle version du template ne change jamais un épisode existant. L'origine (version du template, des thèmes, des presets) est conservée.

## Conséquences

- Ajouter un tool = déclarer métadonnées, schémas, scope, effets de bord, politique d'idempotence et de confirmation ; la chaîne de garde-fous s'applique sans code supplémentaire.
- Le credential étant relu à chaque appel, une table des intégrations en base sera lue à chaque appel : prévoir un cache court.
- La corrélation est générée par appel ; un identifiant fourni par le transport (trace) n'est pas encore repris.

## Risques et limites

- Aucune authentification réelle : le transport doit authentifier l'agent et choisir le credential. Tout est en mémoire.
- Le journal d'audit est en mémoire ; en production il doit être en ajout seul, hors de portée des agents.
- Deux publications en parallèle sont sérialisées par la confirmation, pas par un verrou de base.
- La limite de débit est en mémoire et par processus.
- L'injection de prompt par le contenu lu n'est pas traitée par le serveur : une IA qui lit une présentation hostile peut être manipulée. Les garde-fous bornent les dégâts (scopes, podcast, confirmation humaine de la publication), ils ne les empêchent pas.

## Plan de validation

Tests de `packages/episode-factory` (22) et `packages/mcp-server` (61), mutations vérifiées ([POC 9](../pocs/poc-09-mcp-episode-factory.md)).
