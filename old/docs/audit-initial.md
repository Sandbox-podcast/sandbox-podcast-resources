# Audit initial

Date : 2026-10-05.

## État du dépôt

- `C:\github\sandbox-podcast` n'était pas un dépôt git et ne contenait que le prompt maître (100 Ko, 4 835 lignes). Pas de code, README, `AGENTS.md`, configuration, test ni CI. Projet vierge.
- Outils présents : git 2.55, Node 24.12, npm 11.19, Docker 29.1 (démon arrêté lors de l'audit), Python 3.14, FFmpeg 9.0.2. pnpm absent (installé via corepack, version 12.9.1). Go et Rust absents.

## Éléments déjà présents

Le prompt maître : vision, 136 critères d'acceptation (`AC-*`), Golden Path de 36 étapes, 10 POC, roadmap MVP/V2/V3, Definition of Done, Quality Gates.

## Écarts principaux

- Tout restait à construire : dépôt, documentation, CI, squelette applicatif.
- Le périmètre couvre PREP, STUDIO, POST, les factories, l'IA et le MCP. Sans MVP strict, le risque est de s'éparpiller.

## Risques techniques prioritaires

1. Enregistrement local résilient : une perte de données est l'échec le plus grave, et les API navigateur varient.
2. Media plane stable à 3-5 participants, avec TURN et reconnexion. Sous Docker Windows, l'UDP WebRTC demande une configuration de ports.
3. Segmentation et composition de 3 flux dans le navigateur sur une machine minimale.
4. Dérive de synchronisation multipiste sur sessions longues.
5. Isolation des présentations HTML (risque sécurité principal).

## Décisions déjà résolues par le prompt maître

Media plane et Control plane séparés. SFU préféré au mesh, pas de SFU maison. Monolithe modulaire par défaut. CRDT seulement pour les documents collaboratifs. Commandes critiques côté serveur. Médias sources jamais écrasés. Enregistrement local-first, une piste par participant. Stockage objet S3-compatible en production. Cinq rôles RBAC. Quatre séquences par défaut. HTML toujours isolé. Quality Gates bloquants.

## Décisions prises le 2026-10-05

PD-0001 (Chrome desktop), ADR-0001 (monorepo TypeScript pnpm), ADR-0002 (LiveKit auto-hébergé), ADR-0003 (composition côté Producer).

Ajoutées le même jour, après la question sur les formats d'enregistrement : ADR-0004 (enregistrement serveur par piste, qui remplace l'enregistrement local d'abord du prompt maître) et PD-0002 (1080p30 avec repli 720p).

## Suite

Voir [open-questions.md](open-questions.md), [backlog.md](backlog.md) et [pocs/README.md](pocs/README.md).
