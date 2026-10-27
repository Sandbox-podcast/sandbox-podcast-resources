# Proofs of concept

Chaque POC se termine par PASS, PARTIAL ou FAIL, avec hypothèses, environnement, mesures, captures ou logs, limites, coût estimé, recommandation et décision (continuer, modifier, abandonner). Aucune mesure n'est inventée : tant qu'un POC n'a pas tourné, son résultat est « non exécuté ».

| POC | Sujet                                                           | Résultat                                          |
| --- | --------------------------------------------------------------- | ------------------------------------------------- |
| 1   | [Media plane avec un vrai Chrome](poc-01-media-plane.md)        | PARTIAL                                           |
| 2   | [Segmentation et studio virtuel](poc-02-segmentation.md)        | PARTIAL (coût mesuré, qualité visuelle non jugée) |
| 3   | [Enregistrement serveur par piste](poc-03-server-recording.md)  | PARTIAL                                           |
| 4   | [Synchronisation multipiste](poc-04-multitrack-sync.md)         | PASS avec limites (Chrome, 1 machine, 20 min)     |
| 5   | [Auto Director](poc-05-auto-director.md)                        | PASS (logique, traces synthétiques)               |
| 6   | [Régie Preview / Program](poc-06-regie.md)                      | PASS (logique, en mémoire)                        |
| 7   | [Collaboration temps réel](poc-07-collaboration.md)             | PASS (boucle locale, en mémoire)                  |
| 8   | [Bac à sable des présentations HTML](poc-08-html-sandbox.md)    | PASS                                              |
| 9   | [Episode Factory et serveur MCP](poc-09-mcp-episode-factory.md) | PASS (logique, en mémoire)                        |
| 10  | [Pipeline post-production](poc-10-post-production.md)           | PARTIAL (transcription simulée, un clip exporté)  |

Le POC 3 était « Enregistrement local résilient » dans le prompt maître. Il a changé avec [ADR-0004](../adr/ADR-0004-enregistrement-serveur-par-piste.md).

Environnement de référence : Windows 11, Chrome desktop ([PD-0001](../product-decisions/PD-0001-navigateurs-et-appareils-mvp.md)).
