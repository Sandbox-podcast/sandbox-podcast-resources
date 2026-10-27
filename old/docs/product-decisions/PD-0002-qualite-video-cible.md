# PD-0002 — Qualité vidéo cible des sources

- Statut : acceptée
- Date : 2026-10-05

## Contexte

La qualité vidéo détermine le débit, le stockage, la charge CPU et la possibilité de recadrer en 9:16 pour les clips sans perdre en netteté.

## Question posée

Quelle qualité vidéo cible pour les sources ?

## Options présentées

- A. 1080p30 avec repli automatique en 720p (recommandée)
- B. 720p30 fixe
- C. 1080p60

## Réponse retenue

Option A. Précision donnée par le propriétaire : « quelque chose de suffisant pour faire des podcasts vidéo sur YouTube en 2026 ».

## Motifs

Résolution suffisante pour recadrer un clip vertical, avec un repli quand la machine ou le réseau ne suit pas.

## Conséquences

- La cible s'applique à ce que chaque participant publie. Comme l'enregistrement est fait par le serveur ([ADR-0004](../adr/ADR-0004-enregistrement-serveur-par-piste.md)), la qualité enregistrée dépend du flux WebRTC reçu. Elle sera mesurée, pas supposée.
- « Suffisant pour YouTube » doit devenir des seuils numériques (résolution, images par seconde, débit minimal, audio). Ils seront proposés à partir des mesures du POC 3 et du POC 1, puis validés.
- La politique de repli de 1080p vers 720p (déclencheurs, retour) est à définir et à tester.
