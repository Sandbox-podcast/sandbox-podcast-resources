# Architecture

État : esquisse issue des décisions du 2026-10-05. À compléter après les POC 1, 2 et 3.

## Principes retenus

- Media plane (audio, vidéo, SFU) séparé du Control plane (auth, présence, scène active, commandes, audit).
- Monolithe modulaire. Des services séparés seulement quand une frontière de charge, de sécurité ou de cycle de vie le justifie.
- Médias sources non destructifs. Corrections et montages sont des décisions dérivées.
- Commandes critiques (START_RECORDING, TAKE_SCENE, etc.) validées côté serveur, idempotentes.
- L'enregistrement des sources est produit par le serveur, pas par les navigateurs ([ADR-0004](adr/ADR-0004-enregistrement-serveur-par-piste.md)).

## Conteneurs prévus

```
Navigateur Chrome (Producer, Host, Guest)
├── UI PREP / STUDIO / POST
├── Capture caméra et micro, publication WebRTC
└── Segmentation et composition du Program   (ADR-0003, Producer seulement)

Backend applicatif (Node, TypeScript)
├── Authentification et autorisation
├── Domaine podcast et épisode
├── Contrôle du studio (présence, Program/Preview, recording state)
├── Contrôle de l'enregistrement : un egress par piste publiée, suivi de son état
├── Envoyeur : fichiers Egress vers le stockage, avec vérification SHA-256
└── Superviseur : récupération après crash d'Egress, redémarrage, relance des egress

Infrastructure média
├── LiveKit (SFU)                            (ADR-0002)
├── LiveKit Egress : enregistre chaque piste telle que reçue, sur disque local persistant   (ADR-0004, ADR-0005)
└── TURN

Données
├── PostgreSQL
├── Stockage objet S3-compatible (SeaweedFS en local)
├── Redis (requis par LiveKit Egress)
└── File de jobs et workers FFmpeg (reconstruction, replay)
```

## Flux d'enregistrement

```
Caméra / micro (navigateur)
  → publication WebRTC vers le SFU
  → Egress s'abonne à chaque piste (Track egress, sans transcodage)
  → fichier par piste (H.264 en MP4, VP8 en WebM, Opus en Ogg)
  → fichier de travail local d'Egress pendant l'enregistrement
  → stockage objet, seulement à l'arrêt de l'egress
  → vérification (taille, checksum, contenu) par le Control plane
  → reconstruction et replay (worker FFmpeg)
  → téléchargement des sources
```

Ce que le [POC 3](pocs/poc-03-server-recording.md) impose au Control plane :

- démarrer un egress pour chaque piste publiée, y compris quand un participant revient (nouvelles pistes, nouvel egress) ;
- ne pas se fier au statut `ACTIVE` d'un egress : après un crash d'Egress il reste `ACTIVE` sans rien enregistrer, il faut surveiller la santé du conteneur ;
- arrêter explicitement les egress bloqués après un redémarrage du SFU ;
- ignorer dans la présence les participants cachés d'Egress (identité `EG_…`) ;
- ne pas redéployer Egress pendant un enregistrement.

Les états de sécurité des pistes sont dans [recording.md](recording.md).

## Frontières de modules

| Module                         | Rôle                                                                                  | État                 |
| ------------------------------ | ------------------------------------------------------------------------------------- | -------------------- |
| `packages/recording-core`      | Modèle de chunk local, checksum, états de sécurité (enregistrement local, en attente) | commencé, en attente |
| `pocs/poc-03-server-recording` | Pile Docker et scénarios du POC 3                                                     | en cours             |

Les autres modules sont définis quand leur POC démarre.

## Décisions

| Décision                         | Référence                                                            |
| -------------------------------- | -------------------------------------------------------------------- |
| Stack et monorepo                | [ADR-0001](adr/ADR-0001-stack-applicative-et-monorepo.md)            |
| SFU                              | [ADR-0002](adr/ADR-0002-serveur-sfu-livekit-auto-heberge.md)         |
| Composition du Program           | [ADR-0003](adr/ADR-0003-composition-du-program-cote-producer.md)     |
| Enregistrement serveur par piste | [ADR-0004](adr/ADR-0004-enregistrement-serveur-par-piste.md)         |
| Navigateurs                      | [PD-0001](product-decisions/PD-0001-navigateurs-et-appareils-mvp.md) |
| Qualité vidéo cible              | [PD-0002](product-decisions/PD-0002-qualite-video-cible.md)          |
