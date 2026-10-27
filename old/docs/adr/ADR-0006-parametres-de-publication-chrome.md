# ADR-0006 — Paramètres de publication vidéo dans Chrome

- Statut : acceptée sous réserve de mesures sur de vrais postes et réseaux
- Date : 2026-10-05
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

Le POC 1 ([poc-01-media-plane.md](../pocs/poc-01-media-plane.md)) a mesuré, avec un vrai Chrome, le coût CPU et la qualité de plusieurs réglages de publication. Le propriétaire veut éviter que les PC montent à 100 % de CPU pendant les lives et vise du 1080p30 « suffisant pour YouTube ».

## Options considérées

- A. H.264, une couche, 8 Mb/s : 1080p30, 59 à 69 % d'un cœur pour un participant, mais chaque participant reçoit les autres en pleine résolution.
- B. H.264, simulcast à 3 couches : sature l'encodeur logiciel (limitation « cpu » chez les 5 participants).
- C. H.264, simulcast à 2 couches (1080p et 360p), 6 Mb/s, abonnement adaptatif : 1080p30 tenu par 5 participants, 113 % d'un cœur par participant.
- D. VP8 ou VP9 : 164 % à 97 % d'un cœur, deux fois plus de CPU que H.264 pour un résultat équivalent.
- E. AV1 : aucune image publiée dans ce montage.

## Décision

Option C :

- codec H.264 (matériel indisponible en WebRTC, donc le moins coûteux en logiciel) ;
- simulcast à 2 couches : 1080p30 jusqu'à 6 Mb/s, plus une couche 360p ;
- `adaptiveStream` et `dynacast` activés : un abonné qui n'affiche qu'une vignette ne reçoit que la couche basse, et la couche haute n'est encodée que si quelqu'un la consomme ;
- le Producer, qui compose le Program, s'abonne à la couche haute des seuls participants affichés en grand ;
- l'enregistrement serveur s'abonne à la couche haute ;
- le plafond de 4 Mb/s est écarté : il donne du 720p.

## Conséquences

- Le budget CPU d'un participant est d'environ 1,1 cœur dans le scénario mesuré (encodage 2 couches, décodage de 4 vignettes, lecture de la source). À mesurer sur un portable ordinaire avant de promettre quoi que ce soit.
- Les sources enregistrées ne sont pas prêtes pour le montage (résolution variable au début, très peu d'images clés, erreurs de décodage sous charge). La post-production les normalise en ré-encodant à résolution et GOP constants, et conserve l'original.
- L'enregistrement devrait démarrer après la montée en débit, par exemple après la répétition.
- Si un navigateur permet un jour l'encodage matériel en WebRTC, ou si LiveKit permet de publier des flux encodés par WebCodecs, la décision est à revoir : le matériel est disponible sur cette machine via WebCodecs (H.264 et AV1).

## Risques

- Mesuré sur un seul poste, avec une caméra simulée et un réseau parfait.
- Les erreurs de décodage des fichiers enregistrés ont une cause inconnue.
- Le TURN et le réseau dégradé ne sont pas validés.

## Plan de validation

Répéter les mesures avec 3 puis 5 postes réels sur un réseau réel, sur un hébergement Linux, avec une vraie caméra.
