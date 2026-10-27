# Produit

## Vision

Un studio audiovisuel collaboratif dans le navigateur. Plusieurs personnes à distance apparaissent côte à côte dans un même décor, sans fond vert. Une régie Preview/Program pilote la scène. Le serveur enregistre chaque participant séparément, comme un VOD Twitch : les postes restent légers pendant le live et les fichiers se téléchargent ensuite. L'IA, le MCP, la transcription et les clips viennent après.

Le détail des exigences est dans le prompt maître. Cette page ne garde que ce qui est décidé.

## Utilisation visée

- 3 participants en usage courant.
- Au moins 5 au MVP, sous réserve du benchmark du POC 1.
- Trois espaces : PREP (préparer), STUDIO (enregistrer, régie simple et stable), POST (replay, transcription, clips, export).

## Périmètre du MVP

Les 26 points du §39.1 du prompt maître restent la référence, avec une adaptation : l'enregistrement est fait par le serveur (une piste par participant), pas en local. Le point « upload progressif et reprise » du prompt maître ne s'applique donc plus tel quel.

Liste : authentification, podcast, rôles de base, Episode Factory avec quatre séquences, invitation de 3 à 5 participants, device check, WebRTC avec SFU, détourage, studio virtuel, Scene Engine minimal, active speaker, Auto Director simple, Preview/Program, enregistrement séparé par participant, reconstruction, replay, observabilité minimale, Golden Path E2E, CI/CD.

Hors MVP : transcription, MCP complet, présentations HTML collaboratives, suggestions de clips (V2) ; montage textuel, publication multi-plateforme, streaming externe, mobile (V3).

## Décisions produit

- [PD-0001](product-decisions/PD-0001-navigateurs-et-appareils-mvp.md) : Chrome desktop uniquement.
- [PD-0002](product-decisions/PD-0002-qualite-video-cible.md) : 1080p30 avec repli 720p, suffisant pour YouTube en 2026.
- [ADR-0003](adr/ADR-0003-composition-du-program-cote-producer.md) : le Program est composé dans le navigateur du Producer.
- [ADR-0004](adr/ADR-0004-enregistrement-serveur-par-piste.md) : l'enregistrement principal est fait par le serveur, par piste.

## Compromis assumés

Avec l'enregistrement serveur, la qualité des sources est celle du flux WebRTC et une coupure réseau d'un participant laisse un trou dans sa piste. En échange, aucun encodage supplémentaire sur les postes.

## Questions ouvertes

Voir [open-questions.md](open-questions.md).
