# PD-0001 — Navigateurs et appareils du MVP

- Statut : acceptée
- Date : 2026-10-05

## Contexte

Le choix des navigateurs fixe les API disponibles pour l'enregistrement local (MediaRecorder, OPFS, WebCodecs), les codecs, la segmentation (WebGPU) et la taille de la matrice de tests.

## Question posée

Quels navigateurs et appareils le MVP supporte-t-il officiellement ?

## Options présentées

- A. Chrome + Edge desktop (recommandée)
- B. Chromium + Safari desktop
- C. Desktop, 4 navigateurs
- D. Desktop + smartphone invité

## Réponse retenue

Réponse libre : « Chrome ». Interprétation : Chrome desktop uniquement.

## Motifs

Un seul moteur à tester, les API d'enregistrement et de segmentation les plus complètes, périmètre de test réduit pour le MVP.

## Conséquences

- La matrice de tests du MVP est Chrome desktop. Les POC sont mesurés sur Chrome.
- Edge, Firefox, Safari et les mobiles sont hors périmètre officiel. Aucune compatibilité n'est promise.
- Edge repose sur Chromium, mais n'a pas été retenu explicitement. Si l'équipe veut le supporter, il faut le dire et ajouter Edge à la matrice.
- Ouvert : le device check doit-il bloquer les autres navigateurs ou seulement avertir ? À trancher avec la conception du device check.
- Le support d'autres navigateurs sera reconsidéré après le MVP (V2).
