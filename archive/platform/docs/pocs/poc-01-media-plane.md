# POC 1 — Media plane avec un vrai Chrome

Résultat : **PARTIAL**. Exécuté le 2026-10-05 sur Windows 11 (24 threads, RTX 4090), Chrome 154, pile Docker du [POC 3](poc-03-server-recording.md).

Avec un vrai Chrome, 5 participants publient en 1080p30 H.264 vers LiveKit et le serveur enregistre chaque piste, sur ce poste. Le réseau dégradé et le TURN n'ont pas pu être validés ici. Décision tirée : [ADR-0006](../adr/ADR-0006-parametres-de-publication-chrome.md).

## Ce qui est mesuré, et ce qui ne l'est pas

Mesuré : encodeur réellement utilisé, CPU de Chrome (temps CPU cumulé de tous ses processus, via CDP), statistiques WebRTC de l'émetteur (résolution, images/s, débit, raison de limitation), CPU et mémoire de LiveKit et d'Egress, utilisation du GPU (nvidia-smi), qualité des fichiers enregistrés (ffprobe, ffmpeg), comportement lors de reconnexions simulées.

Limites de l'environnement :

- Tout tourne sur le même poste : Chrome, Docker Desktop, SFU, Egress, stockage. Les CPU de LiveKit et d'Egress sont dans une machine virtuelle Linux de Docker Desktop. Aucun réseau réel : RTT de 1 à 4 ms, aucune perte.
- La caméra est une vidéo animée de 1080p30 avec un peu de bruit (18 Mb/s une fois encodée en H.264), jouée dans la page et capturée par `captureStream()`. La caméra factice intégrée de Chrome est trop simple (≈600 kb/s) et ne sort qu'à 20 images/s. Ce n'est pas un visage : la difficulté d'encodage réelle sera différente.
- Les participants reçoivent aussi les autres : leur décodage est inclus dans le CPU mesuré. Les vidéos de la page sont rendues en 320×180.
- Chaque participant est un Chrome distinct (`--isolate true`). Avec un seul Chrome pour 5 participants, un seul processus GPU décode 25 flux et la qualité s'effondre : ce n'est pas représentatif d'un studio où chacun a son PC.

## Résultats

### Encodage : quel codec, quel encodeur

1 participant, 1080p30, caméra vidéo animée, mêmes conditions, 40 à 60 s.

| Codec            | Plafond | Résolution atteinte              | Débit    | CPU de Chrome        | Encodage par image |
| ---------------- | ------- | -------------------------------- | -------- | -------------------- | ------------------ |
| H.264 (OpenH264) | 4 Mb/s  | 720p30, limitation « bandwidth » | 4,0 Mb/s | 52 % d'un cœur       | 11,4 ms            |
| H.264 (OpenH264) | 8 Mb/s  | 1080p30 après 14 s               | 7,8 Mb/s | 59 à 69 % (3 essais) | 13,3 à 13,8 ms     |
| VP8 (libvpx)     | 8 Mb/s  | 1080p30 après 7 s                | 7,8 Mb/s | 92 %                 | 13,3 ms            |
| VP9 (libvpx)     | 8 Mb/s  | 1080p30 immédiat                 | 4,5 Mb/s | 97 %                 | 15,7 ms            |
| AV1              | 8 Mb/s  | aucune image publiée             | 0        | —                    | —                  |

- **Aucun encodage matériel en WebRTC** : l'encodeur est toujours logiciel (OpenH264, libvpx, libaom) et l'encodeur de la RTX 4090 reste à 0 %, avec Chrome piloté ou lancé normalement, avec ou sans fenêtre. WebCodecs, lui, accepte l'encodage matériel H.264 et AV1 sur cette machine (`prefer-hardware`). Il n'est pas utilisable aujourd'hui avec le chemin WebRTC de LiveKit.
- À 4 Mb/s, la résolution se stabilise à 720p : pour du 1080p30 avec un contenu chargé, il faut un plafond d'au moins 6 Mb/s.
- Le plafond de débit demandé n'est pas le débit de départ : WebRTC monte progressivement. La résolution passe par 480×270, 640×360, 960×540, 1280×720 puis 1080p en une dizaine de secondes, selon le débit disponible.

### Plusieurs participants

H.264, un Chrome par participant, chacun publiant en 1080p30 et recevant les autres.

| Configuration                                                                   | CPU de Chrome par participant | Qualité publiée                                                              | Egress (10 pistes max.) | LiveKit |
| ------------------------------------------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------- | ----------------------- | ------- |
| 3 participants, 8 Mb/s, sans simulcast                                          | 85 % d'un cœur                | 1080p30 pour les 3                                                           | 40 %                    | 33 %    |
| 5 participants, 8 Mb/s, sans simulcast                                          | 117 %                         | 3 en 1080p, 2 en 720p, 3,7 à 6,4 Mb/s                                        | 72 %                    | 71 %    |
| 5 participants, simulcast 3 couches                                             | 126 %                         | limitation « cpu » active chez les 5                                         | 65 %                    | 42 %    |
| **5 participants, simulcast 2 couches (1080p et 360p), 6 Mb/s, flux adaptatif** | **113 %**                     | **1080p30 pour les 5 (28 à 30 images/s, 4,9 à 5,9 Mb/s), aucune limitation** | 55 %                    | 38 %    |
| 3 participants, VP8, 6 Mb/s (comparaison)                                       | 164 %                         | 1080p30                                                                      | 40 %                    | 32 %    |
| 3 participants, H.264, 6 Mb/s (comparaison)                                     | 77 %                          | 1080p30                                                                      | 36 %                    | 27 %    |

Egress et LiveKit : pourcentages d'un cœur dans la machine virtuelle de Docker Desktop.

Conclusions : H.264 coûte deux fois moins de CPU que VP8 à qualité égale. Le simulcast à 3 couches sature l'encodeur logiciel, 2 couches suffisent et tiennent.

### Qualité des fichiers enregistrés

- Par défaut, Egress enregistre la couche la plus haute. Avec le simulcast, le fichier commence sur la couche basse (360p) pendant environ 1 s, puis passe en 1080p (99 % des images ensuite).
- Sans simulcast, le fichier passe par les résolutions intermédiaires de la montée en débit : une résolution qui change dans un MP4 n'est pas un fichier propre pour un logiciel de montage.
- **Très peu d'images clés** : 3 à 8 par fichier pour 60 s, produites seulement lors de changements de résolution, aucune périodique. Le fichier n'est presque pas navigable. Forcer des images clés avec `generateKeyFrame` dans un transformateur d'encodage n'a eu aucun effet (6 images clés avec, 8 sans).
- **Erreurs de décodage** dans les fichiers : de 1 à 551 lignes d'erreur FFmpeg par fichier, en croissant avec la charge (8 pour 1 participant, 67 pour 3, 184 pour 5 sans simulcast ; 551 pour 5 avec simulcast). VP8 en WebM en a aussi à charge égale (176 pour 3). Les publieurs de test `lk` (flux régulier, image clé toutes les 2 s) n'en ont aucune. Cause non établie : ni perte de paquets mesurée à l'émission (0 sur ~30 000), ni message de perte dans les logs d'Egress.
- Conséquence : les sources enregistrées ne sont pas prêtes pour le montage. Il faut les normaliser (ré-encodage à résolution et GOP constants) en post-production, et conserver l'original.

### Reconnexions simulées pendant l'enregistrement (1 participant, Chrome)

| Scénario LiveKit                         | Reconnexion | Effet sur l'enregistrement                                                                    |
| ---------------------------------------- | ----------- | --------------------------------------------------------------------------------------------- |
| `signal-reconnect` (signalisation seule) | 2,0 s       | aucun : un seul fichier de 50 s, sans trou                                                    |
| `resume-reconnect` (redémarrage ICE)     | 2,4 s       | l'egress se termine, un fichier de 19,5 s, la suite n'est plus enregistrée sans nouvel egress |
| `full-reconnect`                         | 2,0 s       | idem                                                                                          |

Avec le superviseur du POC 3 branché : après `resume-reconnect` et `full-reconnect`, il détecte la fin de l'egress, envoie le fichier, relance un egress sur les nouvelles pistes (environ 1 s après la reconnexion) et vérifie les envois. Deux segments qui couvrent 56,6 s sur environ 58 s (18,96 s puis 37,66 s).

### Non validé

- **TURN forcé** (`iceTransportPolicy: relay`) : la connexion de Chrome échoue (`could not establish pc connection`), alors qu'Egress se connecte bien par le relais TURN de LiveKit. L'environnement (Docker Desktop, traduction d'adresses, LiveKit annonçant l'IP du poste) est le suspect principal. À refaire sur un hébergement Linux.
- **Réseau dégradé** (pertes, latence, bande passante limitée) : pas testé. Chrome sur le poste ne peut pas être limité sans réglage système, et un Chrome en conteneur avec `tc netem` n'a pas été mis en place.
- **Qualité avec une vraie caméra et un visage**, CPU sur un portable ordinaire, 5 participants sur des postes distincts : non testés.

## Verdict

PARTIAL. Le chemin média fonctionne avec un vrai Chrome et tient 5 participants en 1080p30 sur ce poste, avec un coût CPU mesuré, et la reprise de l'enregistrement après une reconnexion est validée. Il reste le TURN, le réseau dégradé et les mesures sur un vrai réseau et de vrais postes.

## Recommandation

1. H.264, simulcast à 2 couches, plafond 6 Mb/s, abonnement adaptatif et dynacast : [ADR-0006](../adr/ADR-0006-parametres-de-publication-chrome.md).
2. Démarrer l'enregistrement après une période de montée en débit (répétition, device check) pour éviter les premières secondes basses.
3. Normaliser les sources en post-production (ré-encodage à résolution et GOP constants), garder l'original.
4. Chercher la cause des erreurs de décodage (voir [open-questions.md](../open-questions.md)), en priorité sur un hébergement Linux avec des tampons UDP corrects (LiveKit signale un tampon de réception trop petit dans Docker Desktop).
5. Refaire le TURN et le réseau dégradé sur une infrastructure réelle.
