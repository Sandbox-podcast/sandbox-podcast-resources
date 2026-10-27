# Documentation

Le prompt maître (`../PODCAST_PLATFORM_MASTER_PROMPT.md`) liste ce que la documentation doit couvrir (§36). On écrit chaque document quand son contenu existe, pas avant : un fichier vide ne documente rien.

## Écrits

| Document                                | Contenu                                                                                                                                                                                                                     |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [audit-initial.md](audit-initial.md)    | État du dépôt, risques, décisions résolues, au 2026-10-05                                                                                                                                                                   |
| [product.md](product.md)                | Vision courte, périmètre du MVP, décisions produit                                                                                                                                                                          |
| [architecture.md](architecture.md)      | Plans média et contrôle, conteneurs, flux d'enregistrement                                                                                                                                                                  |
| [recording.md](recording.md)            | Enregistrement serveur par piste, états de sécurité, limites                                                                                                                                                                |
| [testing-notes-api.md](testing-notes-api.md) | Notes historiques sur les contrôles de l’ancienne API                                                                                                                                                                          |
| [open-questions.md](open-questions.md)  | Décisions encore ouvertes et ce qu'elles bloquent                                                                                                                                                                           |
| [backlog.md](backlog.md)                | Backlog ordonné (valeur, risque, dépendance, effort)                                                                                                                                                                        |
| [traceability.md](traceability.md)      | Fonction → critère d'acceptation → ADR → code → test → statut                                                                                                                                                               |
| [pocs/](pocs/README.md)                 | Plan des 10 POC et résultats                                                                                                                                                                                                |
| [adr/](https://github.com/Sandbox-podcast/sandbox-podcast-resources/tree/main/old/docs/adr)                             | ADR-0001 à 0014 : stack, SFU, composition, enregistrement, sorties locales, publication Chrome, isolation HTML, collaboration, MCP, synchronisation, post-production, détourage, noyau serveur, application web |
| [product-decisions/](https://github.com/Sandbox-podcast/sandbox-podcast-resources/tree/main/old/docs/product-decisions) | PD-0001 navigateurs, PD-0002 qualité vidéo, PD-0003 délégation                                                                                                                                                              |
| [threat-model.md](threat-model.md)      | Modèle de menaces initial : acteurs, actifs, frontières, menaces, contrôles et leur état réel, risques résiduels                                                                                                            |
| [cost-model.md](cost-model.md)          | Quantités consommées par un épisode (stockage, trafic, calcul, transcription), valeurs mesurées ou hypothèses ; aucun prix inventé                                                                                          |
| [domain-model.md](domain-model.md)      | Entités du noyau serveur, rôles et droits par podcast, principes                                                                                                                                                            |
| [rapport-final.md](rapport-final.md)    | Rapport de fin de tâche : ce qui existe, ce qui manque, décisions, risques, étape suivante                                                                                                                                  |
| [handoff.md](handoff.md)                | Note de passation pour reprendre le travail                                                                                                                                                                                 |

## À écrire, avec le déclencheur

| Document                                                  | Quand                                                                             |
| --------------------------------------------------------- | --------------------------------------------------------------------------------- |
| domain-model.md                                           | avant la première migration de base de données                                    |
| realtime.md, media-pipeline.md                            | après le POC 1                                                                    |
| scene-engine.md, broadcast-design-system.md               | après les POC 2 et 6                                                              |
| podcast-factory.md, episode-template.md, asset-factory.md | avant l'Episode Factory                                                           |
| design-system.md                                          | avant le premier écran                                                            |
| security.md, privacy.md                                   | avant toute mise en ligne (le modèle de menaces initial existe : threat-model.md) |
| performance.md, observability.md                          | après les premières mesures des POC                                               |
| deployment.md, runbooks.md                                | après la décision d'hébergement                                                   |
| mcp.md, ai.md                                             | avant la V2                                                                       |
