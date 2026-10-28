# Rapport de fin de tâche

Date : 2026-10-06. Destinataire : le propriétaire (Lou). Rédigé par l'agent, qui a travaillé sur délégation (PD-0003) : chaque décision de conception est dans un ADR ou une PD, avec la mention correspondante. **Rien n'est commité ni publié.** Rien n'a été dépensé.

## En une page

Le prompt maître demandait une plateforme complète. Ce qui existe : les **briques risquées prouvées ou mesurées** (10 POC), des **modules de logique testés** (11 paquets), et un **noyau serveur** (`apps/api`) qui les réunit autour de PostgreSQL, de l'authentification, des rôles et de l'audit. Ce qui n'existe pas : une **interface web minimale écrite mais jamais ouverte dans un navigateur** (47 tests sans navigateur, ADR-0014), **aucun service d'enregistrement déployable** (le superviseur reste un POC), **aucun Golden Path de bout en bout**, aucune mesure sur des postes distincts, ni sur un vrai réseau, ni avec de vraies personnes à l'image.

Tests : **645 tests** passent (`pnpm check` : format, lint, typecheck, tests ; dernier passage complet le 2026-10-06). Les tests qui ont besoin de PostgreSQL sont **sautés avec un avertissement** si la base n'est pas lancée : lire le résumé de Vitest pour les nombres sautés. La CI GitHub a été écrite mais **jamais exécutée**.

## Résultat par POC

| POC | Sujet                            | Résultat             | Ce qui reste                                                                      |
| --- | -------------------------------- | -------------------- | --------------------------------------------------------------------------------- |
| 1   | Media plane avec Chrome réel     | PARTIAL              | TURN forcé non validé, réseau dégradé, vrais postes                               |
| 2   | Segmentation, studio virtuel     | PARTIAL              | qualité visuelle du détourage non jugée, machine modeste, coût du Program complet |
| 3   | Enregistrement serveur par piste | PARTIAL              | promouvoir le superviseur en service, erreurs de décodage non expliquées          |
| 4   | Synchronisation multipiste       | PASS avec limites    | une machine, 20 min ; 2 h et postes distincts                                     |
| 5   | Auto Director                    | PASS (logique)       | calibrage sur de vraies voix                                                      |
| 6   | Régie Preview/Program            | PASS (logique)       | diffusion temps réel, interface                                                   |
| 7   | Collaboration temps réel         | PASS (boucle locale) | réseau réel, taille de document                                                   |
| 8   | Bac à sable HTML                 | PASS                 | autres navigateurs (hors périmètre)                                               |
| 9   | Episode Factory et MCP           | PASS en mémoire      | transport HTTP du MCP, vrai client IA                                             |
| 10  | Post-production                  | PARTIAL              | vraie transcription, replay complet, prévisualisation                             |

Détails, chiffres et limites : `docs/pocs/`.

## Décisions prises par l'agent (à confirmer ou corriger)

ADR-0003 à 0013 (voir `AGENTS.md`). Les plus lourdes : **enregistrement côté serveur par piste** (ADR-0004, qui remplace le « local-first » du prompt maître, selon votre réponse) ; **publication Chrome en H.264 avec simulcast à 2 couches** (ADR-0006) ; **détourage chez le Producer** (ADR-0012) ; **authentification interne, rôles par podcast, REST** (ADR-0013). Les **seuils de synchronisation** (ADR-0010) sont des seuils d'ingénieur, à valider : le seuil d'amplitude vidéo a été ajouté **après** les mesures, c'est écrit dans l'ADR.

## Ce que seul le propriétaire peut trancher

Voir `docs/open-questions.md`. Les bloquantes avant une mise en production : **stockage et durée de conservation des médias**, **consentement et cadre légal de l'enregistrement** (zone géographique), **TURN et réseau dégradé** (à mesurer avec de vrais clients), **hébergement et budget** (le modèle de coût donne des quantités, pas de prix : `docs/cost-model.md`). Et : fournisseur de transcription et de modèles IA, quel navigateur pour les invités autres que Chrome.

## Risques principaux

`docs/threat-model.md` (section 6). Les trois premiers : authentification sans MFA ni récupération de mot de passe ; superviseur d'enregistrement non branché sur l'API ; jeton du WebSocket collaboratif dans l'URL. Un risque que j'ai moi-même créé pendant ce travail : les mesures lourdes (Chrome, Docker, enregistrements de 30 minutes) ont saturé la mémoire de votre poste à un moment et l'ont fait planter ; je les fais désormais une à la fois, et seulement quand c'est nécessaire.

## Limites des mesures

Tout a été mesuré sur **ce poste** (24 cœurs, RTX 4090) : les chiffres de CPU, de GPU et de débit ne se transposent pas à un portable ordinaire. Les mesures de CPU de Chrome sont très dispersées (de 19 à 116 % d'un cœur pour 5 flux détourés) : seuls les ordres de grandeur sont utilisables. Aucun test de qualité visuelle ni d'écoute n'a été fait. Un défaut de mesure (lecture de pixels qui faisait basculer un canvas en rendu logiciel) a été trouvé et corrigé en cours de route, et les mesures concernées refaites.

## Comment rejouer

```bash
pnpm install
pnpm check                                   # tout, sans PostgreSQL les tests de l'API sont sautés
cd apps/api && pnpm env:init && pnpm db:up   # PostgreSQL de test, puis pnpm test
```

Les POC média demandent Docker (pile LiveKit de `pocs/poc-03-server-recording`, `pnpm env:init`, `pnpm stack:up`) et Chrome. La note `docs/handoff.md` donne les commandes et l'état détaillé.

## Étape suivante proposée

1. **Vérifier l'interface web dans Chrome** (rendu, connexion LiveKit réelle, clavier), avec une seule fenêtre à la fois et seulement quand le poste a de la mémoire disponible ; puis la compléter (édition des présentations, composition visuelle de la régie).
2. **Service d'enregistrement** : promouvoir le superviseur du POC 3 en service qui lit les commandes de la régie et n'accepte que des identités UUID.
3. **Golden Path E2E** sur cette base, puis une session de 2 h avec des postes distincts.
4. Vos décisions sur la liste ci-dessus.
