# POC 3 — Enregistrement serveur par piste (LiveKit Egress)

Résultat : **PARTIAL**. Exécuté le 2026-10-05 sur Windows 11 avec Docker Desktop.

La chaîne d'enregistrement fonctionne et produit des fichiers conformes. Par défaut, elle perd des données si Egress plante ou si le stockage est indisponible à l'arrêt. Les protections de l'[ADR-0005](../adr/ADR-0005-sorties-egress-locales-et-envoyeur-verifie.md) (sorties locales, envoyeur vérifié, superviseur de récupération) ont été construites et validées dans les scénarios S3b à S3e. Reste ouverte la synchronisation audio/vidéo (POC 4) et la qualité avec un vrai navigateur (POC 1). Ce POC remplace « Enregistrement local résilient » après [ADR-0004](../adr/ADR-0004-enregistrement-serveur-par-piste.md).

## Objectif

Démontrer que le serveur peut enregistrer, pendant un live, chaque piste de chaque participant dans le stockage objet, avec une qualité suffisante pour [PD-0002](../product-decisions/PD-0002-qualite-video-cible.md), un coût CPU serveur connu, et un comportement honnête quand quelque chose tombe.

## Environnement

Pile dans `pocs/poc-03-server-recording/` : LiveKit v1.13.7, Egress v1.14.1, Valkey 9.0 (compatible Redis), SeaweedFS 3.99 (stockage S3-compatible), livekit-cli v2.18.8 comme publieur de test. Docker Desktop sur 24 CPU et 15,5 Go de mémoire.

Réseau : tout tourne dans le réseau Docker du poste, publieurs compris. Aucun navigateur, aucun réseau domestique, aucune perte de paquets.

## Limites de ce POC

- Le publieur de test (`lk room join --publish`) envoie des fichiers H.264 déjà encodés, sans ré-encodage ni adaptation de débit. Il valide la chaîne d'enregistrement, pas la qualité qu'un vrai Chrome produirait sur un réseau domestique. Cette mesure revient au POC 1.
- Les mesures de CPU portent sur 4 pistes (2 vidéos 1080p30 à 4 Mb/s et 2 audios), un seul poste, 5 relevés par exécution. Je ne les extrapole pas à 10 pistes.
- Le décalage audio/vidéo n'est pas mesuré : le média de test ne contient pas de repère de synchronisation. C'est le sujet du POC 4.
- Non testés : disque d'Egress plein, indisponibilité du stockage à l'arrêt, plusieurs instances d'Egress, 5 participants.

## Démarrer

Depuis `pocs/poc-03-server-recording/`, Docker Desktop démarré :

```bash
pnpm env:init     # secrets aléatoires dans .local/ (ignoré par git)
pnpm media:make   # médias de test 1080p30 H.264 et Opus, 180 s
pnpm stack:up     # LiveKit, Egress, Valkey, SeaweedFS
pnpm s1           # scénarios S1 et S2
pnpm s3:kill      # S3, arrêt brutal d'Egress (ou s3:stop)
pnpm s4           # S4, redémarrage du SFU
pnpm s5           # S5, coupure et retour d'un participant
```

Un fichier H.264 brut ne porte pas sa cadence : le publieur reçoit `--fps 30`. Les rapports détaillés sont écrits dans `.local/results/` (ignoré par git).

## Résultats

### S1 et S2 : enregistrement normal, 2 participants, 60 s (3 exécutions)

- 12 fichiers de piste sur 12 conformes : vidéo H.264 en MP4, 1920×1080, 30,00 images/s, environ 4,0 Mb/s ; audio Opus en Ogg, environ 130 kb/s.
- Un egress passe de `STARTING` à `ACTIVE` en 2 s environ.
- Les fichiers n'apparaissent dans le stockage qu'à l'arrêt : aucun objet visible pendant les 60 s, tous écrits à l'instant de l'arrêt, finalisation et envoi en environ 1 s. Il n'y a pas d'envoi progressif.
- Egress ajoute aussi un manifeste JSON par fichier (identifiant, `started_at`, `ended_at`).
- Durées de 59,1 à 61,3 s pour 60 s demandées (deux exécutions relevées en détail). Les vidéos sont plus courtes que la durée de l'egress de 0,4 à 1,9 s sur tous les fichiers comparables (S1, S4, S5). Cela concorde avec une vidéo qui démarre au premier keyframe reçu (la source en émet un toutes les 2 s). Non vérifié dans les logs.
- CPU et mémoire, pour 4 pistes (2 exécutions) : Egress 12,9 % puis 12,2 % d'un cœur, 147 à 160 MiB ; LiveKit environ 5 % d'un cœur, 42 à 46 MiB ; SeaweedFS 0,1 %.

### S3 : crash d'Egress (arrêt brutal `kill` et arrêt propre `stop`)

- Dans les deux cas : 0 fichier dans le stockage, y compris les 25 à 28 s déjà enregistrées. Egress redémarré ne reprend rien.
- LiveKit continue de montrer les 4 egress en `ACTIVE` pendant toute l'observation, même après le redémarrage d'Egress. **Le statut `ACTIVE` ne prouve pas qu'une piste est enregistrée.**
- Les fichiers de travail survivent dans le conteneur arrêté, sous `/home/egress/tmp/<egress>/` :
  - audio Ogg : lisible tel quel, environ 25 s pour 28 s de crash, soit environ 3 s de fin perdues (non expliqué) ;
  - vidéo MP4 : illisible (`moov atom not found`, l'index n'est écrit qu'à la fin).
- La vidéo MP4 est récupérable : en relisant les NAL du `mdat` et en les remuxant avec FFmpeg (`pnpm recover-mp4`), j'ai obtenu 879 NAL, 28,3 s de 1080p30, décodés sans erreur, pour un egress qui avait tourné environ 28,2 s. Limite : cadence supposée constante, horodatages d'origine perdus.
- Cette récupération suppose que le dossier de travail d'Egress soit sur un volume persistant. Ce n'est pas le cas dans la configuration actuelle et ce n'est pas encore testé.

### S4 : redémarrage du SFU en plein enregistrement

- Les egress vidéo se terminent aussitôt et envoient un fichier lisible, couvrant ce qui précède le redémarrage (environ 29 à 30 s).
- Les egress audio restent `ACTIVE` sans rien envoyer, au moins 180 s, tant qu'on ne les arrête pas.
- Après un `stopEgress` explicite, les 4 fichiers sont produits. Le fichier audio annonce 80 s mais contient 30,2 s de son suivies de 49,8 s de silence : Egress comble les trous d'audio avec du silence, pour garder la ligne de temps. La durée d'un fichier audio ne prouve donc pas son contenu.
- Rien n'est enregistré après le redémarrage : la salle a disparu, les participants doivent se reconnecter.

### S5 : un participant se coupe puis revient avec la même identité

- LiveKit garde l'ancienne session au moins 12 s après la coupure (jusqu'au retour du participant, seul moment observé) ; les egress de ses pistes restent `ACTIVE` pendant ce temps, puis se terminent et envoient leur fichier environ 3 s après le retour.
- Au retour, les pistes ont de nouveaux identifiants (`sid`). L'ancien egress ne reprend pas : il faut en démarrer un nouveau.
- Les 6 fichiers sont conformes. Le trou dans la piste de guest-a (environ 16 s) correspond à son absence réelle. Le premier fichier audio annonce 34 s alors que le participant est parti à 20 s (silence ajouté).
- Les egress sont des participants cachés de la salle (`kind` EGRESS, identité `EG_…`) : une présence naïve les compterait. Le Control plane doit les ignorer.

### S6 : écart de démarrage entre pistes

- D'après les manifestes, les pistes d'un même enregistrement démarrent avec un écart de 0 à 74 ms (maximum relevé : 74 et 73 ms en S1, 64 ms en S4, 66 ms en S5 avant la coupure).
- La vidéo démarre au premier keyframe, jusqu'à environ 2 s après le début de l'egress. Le décalage entre l'audio et la vidéo d'un participant ne se lit donc pas dans les manifestes. Non mesuré ici : POC 4.

## Suite du POC : protections validées (S3b à S3e)

Ces scénarios testent les protections décrites dans [ADR-0005](../adr/ADR-0005-sorties-egress-locales-et-envoyeur-verifie.md).

### S3b : dossier de travail persistant

- Avec `./.local/egress-tmp` monté sur l'hôte, après un `kill` d'Egress : 9 fichiers de travail restent sur le disque. Récupération des 4 pistes : audio copié (24,96 s), vidéos réparées (27,3 et 28,2 s), toutes conformes (1080p30, ~4 Mb/s).
- Un `docker kill` ne déclenche pas le redémarrage automatique du conteneur (`unless-stopped`). Un vrai crash du processus le déclencherait : non testé.
- **Egress efface son dossier de travail au démarrage** (9 fichiers avant, 0 après). Il faut donc récupérer avant tout redémarrage : Egress est configuré sans redémarrage automatique, le superviseur le relance.

### S3c : stockage indisponible à l'arrêt, envoi direct vers S3

- Les 4 egress échouent après environ 8 s (`S3 upload failed`) et **leurs fichiers sont supprimés** : perte totale, signalée par un statut `FAILED` mais sans donnée à récupérer.

### S3d : sortie locale et envoyeur vérifié

- Egress écrit dans `/out` (dossier de l'hôte). Stockage éteint à l'arrêt : les 4 egress terminent en `COMPLETE`, les fichiers restent sur le disque.
- L'envoyeur échoue sans rien perdre (8 échecs, 2 tentatives chacun), puis, après le retour du stockage, envoie les 8 fichiers (4 pistes et 4 manifestes) avec relecture et comparaison SHA-256 : 8 vérifiés. 4 pistes sur 4 conformes dans le stockage.
- Limite : l'envoyeur lit chaque fichier en mémoire.

### S3e : crash d'Egress géré par le superviseur seul

Le superviseur (`src/lib/supervisor.ts`) applique `planRecording` de `packages/recording-control` (23 tests) sur l'état observé auprès de LiveKit, de Docker et des disques.

- Egress tué à t=27,7 s. Détection à 30,2 s (2,5 s), alertes `WORKER_DOWN` et `ZOMBIE_EGRESS`, état des segments `RECOVERABLE`.
- Récupération de 4 pistes en 6 s (audio copié 20,8 s, vidéos réparées 23,6 et 24,4 s), puis `UPLOADING` et envoi vérifié, puis redémarrage du worker, puis nouveaux egress à t=44,8 s.
- **Trou d'enregistrement : environ 17 s**, de la mort d'Egress à la reprise sur les mêmes pistes. Une première version mettait 29,5 s à cause de tentatives d'arrêt des egress fantômes (3 s de timeout chacune, car leur worker n'existe plus). Ces arrêts sont supprimés : un egress périmé ne peut plus être arrêté.
- À l'arrêt de l'enregistrement : arrêt des 4 nouveaux egress, envoi, vérification. 8 segments, 8 fichiers dans le stockage, tous vérifiés.
- Les anciens egress restent `ACTIVE` chez LiveKit pour toujours. Le contrôleur les reconnaît comme périmés (démarrés avant le worker actuel) et ne s'y fie pas.

## Verdict

- S1 : conforme. S2 : coût mesuré sur 4 pistes. S3 : perte par défaut, désormais couverte par S3b. S4 : egress audio bloqués tant qu'on ne les arrête pas. S5 : conforme, nouvel egress exigé à chaque reconnexion. S3c : perte totale si le stockage tombe avec l'envoi direct, corrigée par S3d. S3e : crash géré de bout en bout, trou de 17 s. S6 : partiel.
- Résultat : **PARTIAL**. Les objectifs de résilience du serveur sont atteints avec les protections de l'ADR-0005. Il reste deux réserves : la synchronisation audio/vidéo n'est pas mesurée (POC 4) et la qualité avec un vrai navigateur non plus (POC 1).

## Recommandation

Continuer avec LiveKit Egress et l'architecture de l'ADR-0005. À faire ensuite :

1. Le trou de 17 s après un crash peut baisser : détection plus rapide que 2 s, récupération en parallèle, redémarrage d'Egress pendant l'envoi. Non optimisé.
2. Démarrer les egress avant l'annonce de l'enregistrement pour ne pas perdre jusqu'à 2 s de vidéo en début de piste (à mesurer).
3. Ne pas redéployer Egress pendant un enregistrement : un arrêt propre perd aussi les données si rien n'est récupéré ensuite. Le superviseur couvre ce cas.
4. Envoyer les fichiers par morceaux (multipart) pour de longs enregistrements.
5. Mesurer le choix du codec (H.264 ou VP8) avec un vrai navigateur : POC 1.
6. Rotation des fichiers (un nouvel egress toutes les N minutes) : non retenue, la récupération après crash la rend moins utile. À revoir si la panne du disque de l'hôte devient un risque.

Décision : continuer. À réviser si la qualité obtenue avec un vrai navigateur (POC 1) est insuffisante.
