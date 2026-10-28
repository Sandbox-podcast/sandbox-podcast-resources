# ADR-0004 — Enregistrement principal côté serveur, par piste (LiveKit Egress)

- Statut : acceptée sous réserve du POC 3
- Date : 2026-10-05
- Remplace, pour le MVP, l'approche « enregistrement local d'abord » du prompt maître (§4.4 et §17). Le propriétaire du produit a tranché explicitement.

## Contexte

La question posée portait sur le format d'enregistrement local des pistes. La réponse (texte libre) a changé le cadrage : choisir une solution gratuite et adaptée, ne pas faire monter les PC à 100 % de CPU pendant les lives, et fonctionner comme Twitch, avec l'enregistrement conservé sur le serveur et téléchargé ensuite. Côté qualité : suffisant pour des podcasts vidéo sur YouTube en 2026 (voir [PD-0002](../product-decisions/PD-0002-qualite-video-cible.md)).

## Question posée

Où l'enregistrement des sources est-il produit : dans le navigateur de chaque participant ou sur le serveur ?

## Facteurs de décision

Charge CPU des postes pendant le live (détourage, composition, WebRTC), coût logiciel nul, sources séparées par participant, simplicité d'exploitation.

## Options considérées

- A. Enregistrement serveur par piste avec LiveKit Egress (Track egress). Chaque piste audio ou vidéo est enregistrée telle que le SFU la reçoit, sans transcodage (H.264 en MP4, VP8 en WebM, Opus en Ogg), vers un stockage S3-compatible. Egress est sous licence Apache-2.0, s'auto-héberge avec Redis. Aucun encodage supplémentaire sur les postes.
- B. Room composite egress : un seul fichier du Program, produit côté serveur via Chrome. Coûteux en CPU serveur et sans sources séparées. Écarté comme enregistrement principal, éventuellement utile plus tard pour le Program.
- C. Enregistrement local de chaque participant (option de la question initiale). Meilleure qualité et résistance aux coupures réseau, mais encodage supplémentaire sur des postes déjà chargés. Écarté pour le MVP.

## Décision

Option A, retenue. Les faits ci-dessus sont tirés de la documentation LiveKit consultée le 2026-10-05.

## Conséquences

- Aucune charge d'enregistrement ajoutée sur les postes. Les fichiers restent sur le serveur et se téléchargent ensuite.
- La qualité enregistrée est celle du flux WebRTC publié (débit adapté au réseau, éventuelles pertes). Elle est inférieure à une capture locale. Elle doit être mesurée pour vérifier qu'elle reste suffisante.
- Une coupure réseau d'un participant laisse un trou dans sa piste : il n'existe pas de copie locale pour le combler.
- Le Control Plane devient responsable de démarrer et d'arrêter un egress par piste publiée, y compris quand un participant se reconnecte et republie une piste. Il doit suivre l'état de chaque egress.
- Tous les médias sont sur nos serveurs : l'espace de stockage, le trafic de téléchargement et la rétention deviennent des sujets structurants.
- La documentation LiveKit ne dit rien sur la synchronisation entre pistes, sur le moment de l'upload (pendant ou après l'enregistrement) ni sur le comportement en cas de crash d'Egress. Le POC 3 doit le mesurer.
- Les états de sécurité (SAFE, AT_RISK, etc.) sont à redéfinir côté serveur. Le modèle de chunk local de `packages/recording-core` est mis en attente.
- Les critères AC-REC-003, 004, 011 et 012 du prompt maître décrivent un enregistrement local. Ils doivent être réécrits pour l'enregistrement serveur, avec votre validation.
- [ADR-0003](ADR-0003-composition-du-program-cote-producer.md) : le filet de sécurité contre une panne du Producer devient l'enregistrement serveur des pistes.

## Risques

- Qualité insuffisante en conditions réelles (réseau domestique, 1080p30). À mesurer avec un navigateur réel (POC 1).
- Si Egress plante sans avoir écrit dans le stockage, la piste en cours est perdue. À vérifier, et à corriger si besoin par une sortie segmentée (HLS) qui envoie des segments au fur et à mesure.
- Le serveur est un point de défaillance unique pour l'enregistrement.

## Plan de validation

POC 3 révisé : [poc-03-server-recording.md](../pocs/poc-03-server-recording.md). Mesure du CPU serveur par piste, disponibilité des fichiers, comportement en cas de crash d'Egress, de redémarrage du SFU et de coupure d'un participant.

## Résultats du POC 3 (2026-10-05)

Détail dans [poc-03-server-recording.md](../pocs/poc-03-server-recording.md). Résultat PARTIAL : la décision tient, avec des protections à ajouter.

- Les fichiers sont conformes (1080p30 H.264, Opus) et Egress coûte environ 12 à 13 % d'un cœur pour 4 pistes sans transcodage. Mesures faites avec un publieur de test, pas avec un navigateur.
- Les fichiers n'arrivent dans le stockage qu'à l'arrêt de l'egress. Un crash ou un arrêt du conteneur perd les pistes en cours, sans que LiveKit le signale (le statut reste `ACTIVE`).
- Les fichiers de travail d'Egress survivent dans un conteneur arrêté, et une vidéo MP4 sans index a pu être réparée (28,3 s sur 28,2 s). Cela suppose un volume persistant, à tester.
- Le Control plane doit donc, en plus de ce qui précède : surveiller la santé d'Egress sans se fier au statut LiveKit, arrêter les egress bloqués après un redémarrage du SFU, ignorer les participants cachés d'Egress dans la présence, et ne pas redéployer Egress pendant un enregistrement.

## Pistes non décidées

Un enregistrement local de secours, activable seulement sur les postes qui le supportent, pourrait être ajouté plus tard. Il n'est pas retenu aujourd'hui (voir [open-questions.md](../open-questions.md)).
