# POC 4 — Synchronisation multipiste

Résultat : **PASS avec limites** pour des publieurs Chrome (une seule machine, 20 minutes). Le premier essai, avec des publieurs de test `livekit-cli`, montrait une dérive audio/vidéo de 38 ppm ; l'essai Chrome établit qu'elle venait du publieur de test, pas d'Egress ni du SFU (les mêmes dans les deux essais). Code produit : `pocs/poc-04-multitrack-sync` (31 tests). Décision : [ADR-0010](../adr/ADR-0010-seuils-et-alignement-multipiste.md).

## Méthode

La source de test publie, toutes les 10 s à partir de t = 10 s, un **éclair blanc** de 3 images (100 ms) et un **bip** de 1 kHz de 100 ms, exactement au même instant dans la vidéo (1080p30) et l'audio (Opus ou AAC). Le décalage audio/vidéo de la source est nul par construction (vérifié : la source seule donne 0 ms sur 6 repères).

Deux essais, même salle de test, même Egress (`TrackEgress`, un fichier par piste, disque local, [ADR-0005](../adr/ADR-0005-sorties-egress-locales-et-envoyeur-verifie.md)) :

1. **Publieurs `livekit-cli`** : 3 conteneurs identiques, 1 800 s, 180 repères par piste.
2. **Publieurs Chrome 154** : 3 navigateurs distincts (un processus Chrome chacun), H.264, simulcast 2 couches, 6 Mb/s, abonnement adaptatif ([ADR-0006](../adr/ADR-0006-parametres-de-publication-chrome.md)), un fichier MP4 à repères joué dans la page et capturé par `captureStream()` (image et son), 1 200 s, 120 repères par piste.

On retrouve ensuite les repères dans chaque fichier avec ffmpeg : luminance moyenne de chaque image pour la vidéo (front montant à 128), niveau efficace par fenêtre de 2,5 ms pour l'audio (front montant à −30 dB). Mesures : décalage « heure du bip − heure de l'éclair » par participant, décalage de chaque participant par rapport au premier, et pente ajustée par moindres carrés avec son erreur-type. 1 ppm = 3,6 ms par heure.

Environnement : Windows 11, Docker Desktop, LiveKit 1.13.7, Egress 1.14.1, ffmpeg 9.0.2, une seule machine (horloges communes). Charge pendant l'essai `livekit-cli` : Egress 18 % d'un cœur en moyenne (241 Mio au plus), LiveKit 7 %.

## Résultats

Aucun repère manquant ni intervalle irrégulier dans les 12 séries.

### Entre participants (par rapport au premier) : l'alignement tient dans les deux essais

| Essai         | Participant | Vidéo : amplitude | Vidéo : pente (± erreur-type) | Audio : amplitude |
| ------------- | ----------- | ----------------- | ----------------------------- | ----------------- |
| `livekit-cli` | 2 contre 1  | 10 ms             | −0,22 ± 0,29 ppm              | 0 ms              |
| `livekit-cli` | 3 contre 1  | 15 ms             | −0,17 ± 0,30 ppm              | 0 ms              |
| Chrome        | 2 contre 1  | 67 ms             | −1,1 ± 2,1 ppm                | 0 ms              |
| Chrome        | 3 contre 1  | 36 ms             | +7,8 ± 4,0 ppm (+9,2 ms)      | 0 ms              |

L'audio est exact à l'échantillon près pendant toute la session, dans les deux essais. La vidéo varie de 10 à 67 ms d'amplitude : un repère vidéo n'est connu qu'à l'image près (33,3 ms), donc l'écart entre deux séries vidéo peut valoir deux images (66,7 ms) sans aucune dérive. Les pentes sont toutes compatibles avec zéro à 2 erreurs-types près (le +7,8 ppm de Chrome est à 1,9 erreur-type).

### Audio contre vidéo d'un même participant

| Essai         | Participant | Décalage moyen | Amplitude | Pente (± erreur-type) | Dérive sur la session | Résidu (rms) |
| ------------- | ----------- | -------------- | --------- | --------------------- | --------------------- | ------------ |
| `livekit-cli` | 1           | +184,6 ms      | 73,3 ms   | 38,3 ± 0,3 ppm        | +68,5 ms              | 1,8 ms       |
| `livekit-cli` | 2           | +225,3 ms      | 73,3 ms   | 38,5 ± 0,3 ppm        | +68,9 ms              | 1,9 ms       |
| `livekit-cli` | 3           | +125,2 ms      | 76,7 ms   | 38,5 ± 0,3 ppm        | +68,8 ms              | 1,9 ms       |
| Chrome        | 0           | −62,2 ms       | 34 ms     | +2,1 ± 1,8 ppm        | +2,5 ms               | 6,7 ms       |
| Chrome        | 1           | −125,2 ms      | 35 ms     | +3,2 ± 2,0 ppm        | +3,8 ms               | 7,5 ms       |
| Chrome        | 2           | −99,8 ms       | 39 ms     | −5,7 ± 3,6 ppm        | −6,7 ms               | 13,5 ms      |

- **`livekit-cli`** : dérive linéaire, régulière (résidu 1,8 ms) et identique chez les trois : 38 ppm, soit 69 ms en 30 minutes, certaine (plus de 100 erreurs-types). Elle vient du publieur : il cadence la vidéo brute et l'audio avec deux horloges distinctes. Le SFU et Egress sont les mêmes qu'avec Chrome.
- **Chrome** : pas de dérive établie (pentes de −5,7 à +3,2 ppm, chacune à moins de 2 erreurs-types de zéro), au plus 6,7 ms sur 20 minutes. La gigue (résidu de 7 à 13 ms) est celle des horodatages vidéo.

### Décalage constant entre fichiers, et manifestes

Dans les deux essais, le décalage audio/vidéo moyen est **différent pour chaque participant** (+125 à +225 ms avec `livekit-cli`, −62 à −125 ms avec Chrome) : il mêle les débuts décalés des fichiers et d'éventuels décalages réels du publieur. Les décalages de départ entre participants vont de 0,2 à 2,4 s selon les essais. Le décalage audio/vidéo prédit par les manifestes d'egress (`started_at`) diffère du mesuré de **94 à 189 ms** (livekit-cli) et de **92 à 128 ms** (Chrome) : **les manifestes ne suffisent pas à réaligner les pistes à 40 ms près.**

Un détail constaté : avec Chrome et un contenu très simple (fond noir quasi fixe), le fichier de piste reporte 640×360 au début (la première seconde, couche basse) mais est en 1920×1080 ensuite (121 images clés en 1080p, une toutes les 10 s). C'est le comportement déjà décrit au POC 1.

## Ce qu'on peut affirmer

1. Les pistes enregistrées par Egress **ne dérivent pas entre participants** (pente compatible avec zéro, au plus 9 ms sur 20 à 30 minutes) : une reconstruction alignée sur un repère commun le reste jusqu'à la fin des sessions mesurées.
2. **Avec Chrome, l'audio et la vidéo d'un participant ne dérivent pas** de façon établie sur 20 minutes (≤ 7 ms ajustés).
3. Le décalage de départ entre fichiers est de l'ordre de la seconde, **varie d'un fichier à l'autre**, se **mesure avec des repères**, mais ne se **déduit pas des manifestes**.

## Verdict sur AC-REC-006

Seuils ([ADR-0010](../adr/ADR-0010-seuils-et-alignement-multipiste.md)) : dérive ajustée ≤ 20 ms ; amplitude ≤ 40 ms pour l'audio seul et ≤ 70 ms (deux images) dès qu'une série vidéo est impliquée. L'essai Chrome respecte tous les seuils (aucun écart relevé). L'essai `livekit-cli` ne respecte pas le seuil de dérive audio/vidéo, à cause du publieur de test.

**Modification des seuils après coup** : le seuil d'amplitude de 70 ms pour la vidéo a été ajouté après avoir vu une amplitude de 67 ms entre deux séries vidéo Chrome, avec le seuil de 40 ms posé avant les mesures. Motif : 67 ms est la résolution de la méthode (deux images), pas un défaut ; la pente ajustée, insensible à cette quantification, reste le critère strict. Le seuil de dérive n'a pas été changé.

## Limites

- **Une machine**, donc des horloges communes. Avec des postes distincts, la dérive de chaque horloge de capture s'ajoute : non mesuré. C'est la limite la plus importante.
- **20 à 30 minutes**. L'extrapolation à 2 h n'est pas établie : avec Chrome, l'incertitude de pente (± 2 à 4 ppm) donne ± 14 à 26 ms à 2 h, du même ordre que la valeur extrapolée. Il faut une session de 2 h pour conclure.
- Contenu de test à faible complexité (fond noir bruité, 35 kb/s encodé) : la charge d'encodage et les décalages en cas de saturation du CPU ne sont pas représentatifs. Pas de visage, pas de parole.
- Repères toutes les 10 s : un saut isolé entre deux repères passerait inaperçu.
- Précision : vidéo 33,3 ms (une image), audio 2,5 ms.
- Pas de réseau dégradé ni de perte de paquets.
- Les repères sont dans le contenu publié. En production il n'y en a pas : il faut un mécanisme d'alignement fourni par la plateforme (ADR-0010), non testé ici.
- Lecture aléatoire dans les MP4 d'Egress non testée (peu d'images clés : une toutes les 10 s avec ce contenu).

## Suite

1. Session de 2 h avec des publieurs Chrome, idéalement sur des postes distincts.
2. Tester l'alignement fourni par la plateforme : relevé périodique, côté navigateur, de la correspondance entre l'horloge RTP et l'horloge murale (`RTCRtpSender.getStats`), conservé avec l'enregistrement.
3. Garder ce banc comme test de non-régression à chaque changement de version d'Egress, de LiveKit ou de paramètres de publication.
