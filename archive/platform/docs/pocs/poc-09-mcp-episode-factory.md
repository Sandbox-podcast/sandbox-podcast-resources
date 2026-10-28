# POC 9 — Episode Factory et serveur MCP

Résultat : **PASS** pour la logique et les garde-fous, en mémoire, sans authentification réelle ni client IA réel. Code produit : `packages/episode-factory` (22 tests) et `packages/mcp-server` (61 tests). Décision : [ADR-0009](../adr/ADR-0009-mcp-et-episode-factory.md).

## Ce qui est construit

**Episode Factory.** À partir d'une version de template (séquences, scènes, assets, checklists, presets d'export, thèmes), `createEpisodeFromTemplate` produit l'espace de travail complet d'un épisode : brief vide, conducteur, quatre séquences (INTRO, SÉQUENCE A, SÉQUENCE B, CONCLUSION dans le template standard), scènes affectées aux séquences, assets, un emplacement de présentation par séquence, checklists, espaces vides pour l'enregistrement, les clips et les exports, droits initiaux, origine complète. Tout est validé avant d'écrire, l'écriture est atomique et idempotente.

**Serveur MCP.** Neuf tools, un cœur indépendant du transport (`Platform`), un adaptateur MCP (SDK officiel 1.32) :

| Tool                           | Scope                | Type                | Idempotence / précondition             |
| ------------------------------ | -------------------- | ------------------- | -------------------------------------- |
| `create_episode_from_template` | `episode:write`      | mutation            | `idempotencyKey`                       |
| `get_episode`                  | `episode:read`       | lecture             | —                                      |
| `list_segments`                | `episode:read`       | lecture             | —                                      |
| `update_segment`               | `episode:write`      | mutation            | `expectedRevision`                     |
| `list_assets`                  | `asset:read`         | lecture             | —                                      |
| `get_presentation`             | `presentation:read`  | lecture             | —                                      |
| `create_presentation`          | `presentation:write` | mutation            | même contenu = sans effet              |
| `update_presentation`          | `presentation:write` | mutation            | `expectedHash`                         |
| `publish_presentation_version` | `presentation:write` | mutation, confirmée | confirmation à usage unique, rejouable |

Les présentations sont des documents du serveur collaboratif ([POC 7](poc-07-collaboration.md)) : l'agent écrit côté serveur, les humains connectés reçoivent le changement en direct.

## Résultats

| Critère              | Vérifié par                                                                                                                                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AC-FACTORY-001, 004  | structure complète générée ; origine (template, thèmes, presets, clé) conservée                                                                                                                                                            |
| AC-FACTORY-002, 003  | version des assets figée ; un template v2 publié ensuite ne change pas un épisode existant ; une ancienne version reste demandable                                                                                                         |
| AC-FACTORY-005       | même clé = même épisode (y compris deux demandes simultanées) ; autre demande avec la même clé refusée ; même clé dans deux podcasts = deux épisodes                                                                                       |
| AC-FACTORY-006       | demande, template, scène vers séquence inconnue, assets manquants (tous rapportés), thème absent : erreur structurée, aucun épisode écrit                                                                                                  |
| AC-RUNDOWN-001, 002  | conducteur ordonné ; chaque séquence porte notes, questions, scènes, assets, présentation, jingle, appel à l'action                                                                                                                        |
| AC-MCP-001           | un agent crée un épisode via un vrai client MCP relié en mémoire ; on le retrouve dans le dépôt                                                                                                                                            |
| AC-MCP-002           | l'agent écrit puis met à jour une présentation ; un `CollabClient` humain reçoit chaque changement sans rafraîchir ; une modification humaine intermédiaire provoque `CONFLICT` et n'est pas écrasée                                       |
| AC-MCP-003           | sans scope : `FORBIDDEN` avec les scopes manquants, pour les 9 tools ; lecture seule : 4 tentatives de mutation refusées, aucune écriture                                                                                                  |
| AC-MCP-004           | un credential du podcast B reçoit `NOT_FOUND` sur 8 tools visant le podcast A, état de A intact ; templates privés non visibles ; argument `podcastId` refusé                                                                              |
| AC-MCP-005           | une entrée par tentative (OK, CONFLICT, INVALID, NOT_FOUND, DENIED, RATE_LIMITED, ERROR) avec tous les champs ; lectures réussies non journalisées                                                                                         |
| AC-MCP-006           | idempotence par tool, décrite dans la description MCP                                                                                                                                                                                      |
| AC-MCP-007           | patch invalide (6 cas) et HTML dangereux (5 cas, création et mise à jour) rejetés avant toute écriture                                                                                                                                     |
| Confirmation (§26.3) | non approuvée = rien ; approbation par un non-producteur refusée ; refus définitif ; expiration ; autre credential ; autre libellé ; contenu modifié après approbation ; usage unique ; rejeu ; deux appels simultanés = une seule version |
| Autres               | révocation et retrait de scope immédiats sur session ouverte ; expiration ; limite de débit par credential avec délai conseillé ; erreur interne sans fuite de détail                                                                      |

## Sensibilité des tests

Trente-trois mutations du code ont été essayées sur les deux paquets (règle d'idempotence inversée, scope ignoré, isolation retirée, révocation ignorée, expiration ignorée, limite de débit retirée, contrôles de confirmation retirés un par un, précondition de hash retirée, validation HTML retirée, audit étendu aux lectures, etc.). Toutes sont détectées. Deux survivaient au premier passage et ont donné de nouveaux tests : l'usage unique d'une confirmation pendant une publication en cours (cas simultané), et le caractère définitif d'une décision humaine (un refus ne peut pas être suivi d'une approbation, une confirmation expirée ne peut plus être approuvée).

## Limites

- Aucune authentification : le transport doit authentifier l'agent et choisir le credential. Pas de transport stdio ni HTTP en place, seulement le transport mémoire des tests.
- Aucun client IA réel n'a été essayé : la façon dont un modèle utilise ces tools (erreurs de schéma, boucles de réessai, réaction à `CONFIRMATION_REQUIRED`) n'est pas observée.
- Stockage, journal d'audit, limite de débit et confirmations en mémoire ; en production : PostgreSQL, journal en ajout seul, état partagé entre instances.
- Pas de tools pour les assets (téléversement), les transcriptions, les clips, les exports, les scènes ni le podcast : seuls les tools nécessaires aux critères du POC existent. `get_recording_metadata` et `get_job_status` du prompt maître viendront avec les parties correspondantes.
- L'injection de prompt par du contenu hostile lu par l'agent n'est pas traitée : les garde-fous bornent les dégâts, ils ne les empêchent pas.
- Le contenu HTML n'est contrôlé que par une liste de motifs (aide à l'auteur) : la protection réelle est le bac à sable ([ADR-0007](../adr/ADR-0007-isolation-des-presentations-html.md)).
- Une présentation modifiée après publication reste marquée publiée avec l'ancienne version ; l'écart entre brouillon et publié n'est pas encore exposé.

## Suite

Authentification et transport HTTP du serveur MCP, tools de scènes, d'assets, de transcription, de clips et d'exports, quota de coût pour les tools coûteux, essai avec un vrai client IA, journal d'audit durable, politique d'expiration des credentials.
