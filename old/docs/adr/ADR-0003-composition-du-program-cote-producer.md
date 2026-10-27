# ADR-0003 — Composition du Program dans le navigateur du Producer

- Statut : acceptée sous réserve des POC 2 et 6
- Date : 2026-10-05
- Mise à jour du 2026-10-05 : le filet de sécurité n'est plus l'enregistrement local, voir [ADR-0004](ADR-0004-enregistrement-serveur-par-piste.md).

## Contexte

L'endroit où le décor, les participants détourés et les overlays sont assemblés détermine la charge CPU/GPU, le point de défaillance du live et l'architecture du Scene Engine. Dans tous les cas, les sources de chaque participant sont enregistrées séparément.

## Question posée

Où le Program est-il composé ?

## Facteurs de décision

Latence de la régie, coût d'infrastructure, rendu identique en Preview et en Program, tolérance à la panne de la machine du Producer.

## Options considérées

- A. Client du Producer : latence minimale, pas de serveur GPU, la machine du Producer est le point de défaillance du live.
- B. Serveur : indépendant du Producer, coût GPU/CPU et latence ajoutée.
- C. Hybride : Preview dans le navigateur, Program côté serveur, deux renderers à garder cohérents.
- D. Pas de Program live au MVP : le plus simple, la régie n'aurait pas de sortie enregistrée.

## Décision

Option A (recommandée), retenue.

## Conséquences

- Le Scene Engine sépare la définition d'une scène de son renderer (§8.4), pour permettre un rendu serveur plus tard (clips, replay).
- Le filet de sécurité est l'enregistrement serveur des pistes de chaque participant ([ADR-0004](ADR-0004-enregistrement-serveur-par-piste.md)) : si le navigateur du Producer plante, les sources continuent d'être enregistrées par le serveur et le Program se reconstruit en POST. Cela suppose que le SFU et Egress tiennent, ce que le POC 3 doit vérifier.
- Le Program Output produit par le Producer est un fichier de plus, il ne remplace pas les sources.
- Le budget CPU/GPU du poste du Producer à 5 participants doit être mesuré (POC 2). Ce poste n'a plus d'encodage d'enregistrement à porter, seulement la composition, la segmentation et le flux WebRTC.

## Risques

- Si le Producer perd sa machine, le live en cours est interrompu.
- Charge élevée : composition et segmentation sur la même machine que le flux WebRTC.

## Plan de validation

POC 2 (segmentation et composition, mesures FPS/CPU/GPU/RAM sur 3 puis 5 flux) et POC 6 (Preview/Program, asset invalide). Si le budget n'est pas tenu sur la machine minimale, rouvrir la question avec l'option C.
