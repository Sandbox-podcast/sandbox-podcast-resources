# ADR-0001 — Stack applicative et organisation du dépôt

- Statut : acceptée
- Date : 2026-10-05

## Contexte

Il faut un squelette commun avant d'écrire les POC et la CI. Le prompt maître cite Next.js, React, TypeScript, PostgreSQL, un stockage S3-compatible et FFmpeg comme pistes à évaluer.

## Question posée

Quelle stack applicative et quelle organisation de dépôt ?

## Facteurs de décision

Types et schémas partagés entre front, back et MCP. Un seul langage pour l'agent de développement. Frontières de modules nettes. Workers média isolés.

## Options considérées

- A. Monorepo TypeScript pnpm : `apps/web` (Next.js), services Node modulaires et workers, packages partagés (domaine, schémas Zod). Local : PostgreSQL, un stockage S3-compatible, Docker Compose.
- B. Next.js full-stack unique : démarrage rapide, mal adapté aux WebSocket, workers longs et jobs média.
- C. Front TypeScript + backend Python ou Go : meilleur écosystème IA ou temps réel, mais deux langages et types non partagés.

## Décision

Option A (recommandée), retenue.

## Conséquences

- pnpm 12 comme gestionnaire, workspaces `apps/*`, `packages/*`, `pocs/*`.
- TypeScript 6.0.x. Version 7 écartée pour l'instant : typescript-eslint n'accepte que `<6.1.0` (vérifié le 2026-10-05).
- Validation des données par Zod.
- Stockage S3-compatible local pour les POC : SeaweedFS (Apache-2.0). MinIO n'a pas été retenu car son image est introuvable sur Docker Hub au 2026-10-05. Choix réversible, limité à l'environnement local ; le stockage de production dépend de la décision d'hébergement.
- Les traitements média lourds passent par FFmpeg dans des workers isolés, pas par du code Node.
- Cette ADR fixe le langage et l'outillage. Elle ne tranche pas l'hébergement, l'authentification ni le style d'API, qui restent des questions ouvertes.

## Risques

- Traitements média en Node moins performants que du code natif : à compenser par FFmpeg et des workers dédiés.
- Dépendance à un écosystème JS qui évolue vite : versions épinglées, lockfile commité.

## Plan de validation

Les POC et la CI tournent sur ce squelette. À réévaluer si un POC montre qu'un composant doit être écrit dans un autre langage.
