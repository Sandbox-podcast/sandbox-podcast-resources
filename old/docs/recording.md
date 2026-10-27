# Enregistrement

État : l'enregistrement principal est fait par le serveur, une piste par participant ([ADR-0004](adr/ADR-0004-enregistrement-serveur-par-piste.md)). Le [POC 3](pocs/poc-03-server-recording.md) a été exécuté le 2026-10-05 : résultat PARTIAL. Ce document résume ce qui en découle.

## Principe

LiveKit Egress s'abonne à chaque piste publiée et l'écrit telle que le SFU la reçoit, sans transcodage, dans le stockage objet. Une piste audio et une piste vidéo sont deux fichiers distincts, accompagnés d'un manifeste JSON.

| Codec publié | Conteneur du fichier | Observé               |
| ------------ | -------------------- | --------------------- |
| H.264        | MP4                  | oui, 1080p30 à 4 Mb/s |
| VP8          | WebM                 | pas testé             |
| Opus         | Ogg                  | oui, environ 130 kb/s |

## Comportement observé

- Les fichiers n'arrivent dans le stockage qu'à l'arrêt de l'egress. Pendant l'enregistrement, ils n'existent que dans le dossier de travail d'Egress (`/home/egress/tmp/`).
- Un crash ou un arrêt du conteneur Egress perd les pistes en cours, et LiveKit continue d'afficher `ACTIVE`.
- Les fichiers de travail survivent dans un conteneur arrêté : l'audio Ogg est lisible, la vidéo MP4 non (pas d'index) mais récupérable en relisant ses NAL.
- Après un redémarrage du SFU, les egress vidéo envoient leur fichier, les egress audio restent `ACTIVE` sans rien envoyer tant qu'on ne les arrête pas.
- Un participant qui revient obtient de nouvelles pistes : il faut un nouvel egress.
- L'audio est complété par du silence là où il manque (la durée annoncée dépasse le contenu réel), la vidéo non.
- La vidéo commence au premier keyframe reçu : 0,4 à 1,9 s de moins que la durée de l'egress.
- Les egress sont des participants cachés de la salle, à ignorer dans la présence.

## Architecture retenue ([ADR-0005](adr/ADR-0005-sorties-egress-locales-et-envoyeur-verifie.md))

1. Egress écrit sur un disque local persistant (`/out`), son dossier de travail aussi. Pas de redémarrage automatique.
2. Un envoyeur envoie chaque fichier terminé vers le stockage, relit et compare le SHA-256, réessaie, et ne supprime qu'après vérification.
3. Un superviseur applique `planRecording` (`packages/recording-control`) sur l'état observé : LiveKit, Docker, disques. Sur un crash : récupération des fichiers de travail, envoi, redémarrage d'Egress, nouveaux egress. Validé dans les scénarios S3b à S3e du POC 3.

## États de sécurité côté serveur

Proposition issue du POC 3. Les noms viennent du §18 du prompt maître.

| État          | Sens                                                                                                              |
| ------------- | ----------------------------------------------------------------------------------------------------------------- |
| `SAFE`        | Fichier de piste dans le stockage objet, manifeste présent, `ffprobe` le lit et la durée de contenu est cohérente |
| `AT_RISK`     | Egress vivant mais rien dans le stockage : un crash perd la piste (cas par défaut pendant tout l'enregistrement)  |
| `RECOVERABLE` | Egress mort, fichiers de travail présents sur un volume persistant : audio lisible, vidéo à réparer               |
| `FAILED`      | Egress terminé en erreur (par exemple échec d'envoi vers le stockage), ou fichier illisible                       |
| `MISSING`     | Piste publiée sans egress vivant, trou dans la piste, ou aucun fichier récupérable                                |
| `UPLOADING`   | Réservé à une éventuelle sortie segmentée avec envoi progressif, non retenue à ce stade                           |

Règles d'affichage :

- Ne jamais montrer `SAFE` sans fichier vérifié.
- Le statut `ACTIVE` d'un egress vu par LiveKit ne prouve rien : le croiser avec l'état du conteneur Egress.
- La durée annoncée d'un fichier audio ne prouve pas son contenu.

## Réparation d'une vidéo MP4 tronquée

Pour un fichier laissé par un crash (`ftyp`, `free`, puis un `mdat` de taille 0) : lire les NAL à longueur de 4 octets du `mdat`, les réécrire en Annex B, puis remuxer avec FFmpeg. Implémenté dans `pocs/poc-03-server-recording/src/lib/mp4-recovery.ts`, testé en unitaire et sur un vrai fichier (28,3 s de 1080p30 récupérées). Limite : cadence supposée constante.

## Modèle de chunk local (en attente)

Le package `packages/recording-core` décrit des chunks d'enregistrement local, avec une copie locale (`NONE`, `MEMORY`, `DURABLE`) et un état d'envoi. Il est testé (46 tests) mais l'enregistrement local n'est pas retenu au MVP. Il pourrait resservir pour un enregistrement local de secours optionnel, ou pour une sortie segmentée. Décision à prendre plus tard.

## Critères d'acceptation à réviser

AC-REC-003 (coupure réseau et chunks locaux), AC-REC-004 (reprise d'upload), AC-REC-011 (stockage local saturé) et AC-REC-012 (upload en arrière-plan du live) du prompt maître supposent un enregistrement local. Ils doivent être réécrits pour l'enregistrement serveur, avec validation du propriétaire. Le POC 3 donne la matière : perte après crash d'Egress, récupération depuis un volume persistant, nouvel egress à la reconnexion.
