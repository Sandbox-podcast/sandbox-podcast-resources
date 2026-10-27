# ADR-0005 — Sorties Egress sur disque local, envoyeur vérifié, superviseur de récupération

- Statut : acceptée sous réserve de la validation en conditions réelles
- Date : 2026-10-05
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

Le POC 3 ([poc-03-server-recording.md](../pocs/poc-03-server-recording.md)) a mesuré trois pertes de données avec l'envoi direct d'Egress vers le stockage objet :

1. un crash ou un arrêt du conteneur Egress perd les pistes en cours, sans que LiveKit le signale ;
2. si le stockage est indisponible à l'arrêt, les egress échouent après environ 8 s et leurs fichiers sont supprimés ;
3. Egress efface son dossier de travail à chaque démarrage, donc un redémarrage automatique détruit les fichiers récupérables.

## Options considérées

- A. Garder l'envoi direct d'Egress vers le stockage et ajouter seulement la récupération après crash : ne couvre pas la panne du stockage.
- B. Egress écrit sur un disque local persistant, un envoyeur à nous pousse vers le stockage : couvre les deux pannes, ajoute un composant.
- C. Enregistrement local de secours dans le navigateur : écarté, il recharge les PC (voir [ADR-0004](ADR-0004-enregistrement-serveur-par-piste.md)).
- D. Sortie segmentée (HLS) : n'existe pas pour Track egress, imposerait un Track composite qui transcode.

## Décision

Option B, avec trois éléments :

1. Egress écrit ses fichiers dans un dossier persistant de l'hôte (`/out`), et son dossier de travail (`/home/egress/tmp`) est aussi persistant.
2. Un envoyeur envoie chaque fichier terminé vers le stockage, calcule son SHA-256, le relit pour le comparer, réessaie avec un délai croissant, et ne supprime le fichier local qu'après vérification.
3. Egress n'a pas de redémarrage automatique. Un superviseur détecte l'arrêt du conteneur, récupère les fichiers de travail (audio copié, vidéo MP4 réparée), puis redémarre Egress.

La logique de décision du superviseur est une fonction pure, testée : `packages/recording-control`.

## Conséquences

- Un fichier n'est `SAFE` que s'il est vérifié dans le stockage. Tant qu'il est local, il est `UPLOADING`.
- Le disque de l'hôte d'Egress doit avoir de la place pour les enregistrements en cours. À dimensionner, avec une alerte d'espace libre.
- Une panne du disque de l'hôte pendant l'enregistrement reste une perte possible. Elle n'est pas couverte, par choix.
- La réparation d'une vidéo MP4 suppose une cadence constante : les horodatages d'origine sont perdus. Acceptable pour une récupération après incident.
- Le superviseur et l'envoyeur sont des composants à exploiter et à surveiller.

## Risques

- Validé sur un poste, un seul Egress, des publieurs de test. Pas validé avec plusieurs instances d'Egress ni sur un hébergement réel.
- L'envoyeur lit les fichiers en mémoire : pour des enregistrements de plusieurs heures (plusieurs Go), il faudra des envois par morceaux.

## Plan de validation

Scénarios du POC 3 : S3b (crash avec dossier persistant), S3d (stockage indisponible à l'arrêt), S3e (superviseur automatique).
