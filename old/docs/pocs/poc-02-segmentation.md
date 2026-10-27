# POC 2 — Segmentation et studio virtuel

Résultat : **PARTIAL**. Le coût du détourage et de la composition de 1, 3 et 5 flux 1080p30 dans Chrome est mesuré sur ce poste, et la régulation de qualité (fallback machine faible) est écrite, testée et vérifiée dans le navigateur **avec une machine faible simulée**. Mais : aucune **qualité visuelle** n'a pu être jugée (aucune séquence avec une personne), aucune **vraie webcam** ni **vraie machine modeste** n'a été utilisée, et le coût de réception WebRTC et d'encodage du Program n'est pas dans la mesure. Code : `packages/scene-quality` (22 tests), `pocs/poc-02-segmentation` (banc). Décision : [ADR-0012](../adr/ADR-0012-detourage-chez-le-producer-avec-regulation.md).

## Ce qui est construit

- **`packages/scene-quality`** : contrôleur de régulation de qualité à hystérésis. Un escalier de 5 niveaux, du plus fin au plus économe : `COMPLET` (détourage à chaque image, entrée 720p), `MASQUE_RÉDUIT` (une image sur 2), `MASQUE_BAS` (une sur 3, entrée 360p), `SANS_DÉTOURAGE` (aucun modèle, cadre elliptique aux bords adoucis), `SECOURS` (idem à 15 images/s). Il lit le coût de chaque image (travail synchrone + retard de l'image), lissé, et : dégrade d'un seul niveau après 1,5 s de surcharge continue (> 80 % du budget de 33 ms), remonte d'un seul niveau après 15 s de marge continue (< 45 %), impose 3 s de repos entre deux changements, écarte pendant 60 s un niveau dont la remontée vient d'échouer, ignore les 15 premières images (chargement du modèle) et accepte un verrou manuel du Producer.
- **Banc** `pocs/poc-02-segmentation` : une page qui joue N flux vidéo 1080p30, les détoure avec **MediaPipe Selfie Segmentation** (paquet npm `@mediapipe/selfie_segmentation`, Apache-2.0, modèle inclus, WebGL), les compose dans un décor commun de 1920×1080 et mesure ; un lanceur Chrome (fenêtre hors écran, GPU actif) qui relève le CPU de tous les processus Chrome et le GPU (`nvidia-smi`).

## Conditions

Windows 11, Chrome 154, GPU NVIDIA GeForce RTX 4090 (rendu WebGL matériel confirmé : « ANGLE (NVIDIA … Direct3D11) »), une machine de développement puissante. **Trois « webcams » = la même vidéo 1080p30 animée (sans personne) jouée avec des décalages**, détourée à partir d'une entrée 720p. Boucle de composition cadencée par `setTimeout` (précision de l'ordre de la milliseconde, pas calée sur l'affichage). Le coût GPU de bout en bout est échantillonné une image sur dix par une lecture de pixel.

## Résultats (essais de 45 à 60 s, après correction d'un défaut de mesure décrit plus bas)

| Essai                                   | Images/s | Détourage : médiane / p95 | CPU Chrome (part d'un cœur) | GPU moyen / max |
| --------------------------------------- | -------- | ------------------------- | --------------------------- | --------------- |
| 3 flux, composition seule (sans modèle) | 29,9     | —                         | 20 %                        | 22 % / 52 %     |
| 1 flux détouré                          | 29,4     | 0,8 / 3,1 ms              | 25 %, 25 %                  | 23 % / 43 %     |
| 3 flux détourés                         | 29,3     | 1,9 / 4,7 ms              | 51 %, 75 %                  | 27 % / 53 %     |
| 5 flux détourés                         | 28,9     | 2,9 / 5,5 ms              | 19 %, 82 %, 116 %           | 27 % / 49 %     |
| 3 flux, modèle « général » (0)          | 29,1     | 1,9 / 4,6 ms              | 53 %                        | 28 % / 41 %     |
| 3 flux, niveau sans détourage           | 30,0     | —                         | 19 %                        | 18 % / 35 %     |

- **Débit** : le détourage tient 29 à 30 images/s pour 1 à 5 flux sur ce poste ; chaque flux reçoit un nouveau masque à chaque image (29 masques/s). L'écart à 30 vient de la cadence par minuteur (le test sans modèle donne 29,9).
- **Latence du détourage** : 1 à 3 ms en médiane, 3 à 6 ms au 95e centile. Le modèle « paysage » (1) et le modèle « général » (0) sont indiscernables à cette précision.
- **Premier détourage** : chaque essai commence par un arrêt de 1,3 à 1,8 s (premier appel du modèle). À préchauffer avant l'antenne.
- **CPU : mesure peu reproductible.** Les mêmes essais répétés donnent de 51 à 75 % (3 flux) et de 19 à 116 % (5 flux) ; la valeur de 19 % pour 5 flux est incohérente avec les autres et n'est pas expliquée (la somme des temps CPU des processus Chrome n'est peut-être pas stable). On retient un **ordre de grandeur** : le niveau sans modèle consomme environ 20 % d'un cœur, le détourage de 3 flux ajoute de l'ordre de 30 à 55 points, celui de 5 flux davantage. Le GPU, lui, est stable : environ 27 % en moyenne (échantillonné toutes les 2 s, donc grossier).
- **Fluidité** : l'intervalle entre images est de 32 ms en médiane et de 47 ms au 95e centile, dans tous les essais y compris sans modèle : c'est la résolution du minuteur de Windows, pas le coût du détourage. Un vrai rendu doit se caler sur `requestAnimationFrame` ou les images vidéo.

## Régulation de qualité en situation (machine faible simulée)

La machine faible est **simulée** : chaque détourage lancé attend un temps ajouté (20 ms pour une entrée de 720 p, proportionnel à la hauteur d'entrée), soit 60 ms par image pour 3 flux au niveau complet.

| Essai (60 s ; 120 s avec régulation) | Images/s | Intervalle médian | Niveau final                               |
| ------------------------------------ | -------- | ----------------- | ------------------------------------------ |
| Sans régulation                      | 18,4     | 93 ms             | `COMPLET` (surchargé)                      |
| Avec régulation                      | 28,5     | 32 ms             | `MASQUE_BAS`, tenu 112 s, sans oscillation |

Chronologie de l'essai régulé : `COMPLET` → `MASQUE_RÉDUIT` à 4,5 s (charge 1,16) → `MASQUE_BAS` à 7,6 s (charge 1,16), puis stable. Le détourage est alors recalculé une image sur trois (9,7 masques/s par flux au lieu de 29) à 360 p, et la composition garde ses 30 images/s.

## Défauts de mesure trouvés et corrigés

1. **Lecture de pixels sur le canvas de sortie.** La première série échantillonnait le coût de bout en bout en lisant un pixel du canvas composé. Après environ 40 s, Chrome a basculé ce canvas en rendu logiciel (heuristique `willReadFrequently`), le coût par image est passé de 10 à 25 ms, et le contrôleur a dégradé la qualité de lui-même jusqu'au niveau de secours. Découvert grâce à une trace par seconde (niveau, coût synchrone, retard) ajoutée au banc. La lecture se fait maintenant sur un petit canvas annexe, et toute la série a été refaite. Les chiffres de la première série ne sont pas utilisés.
2. **Cadence.** Voir plus haut.

## Sensibilité des tests

15 mutations du contrôleur (seuils de surcharge et de marge, durées continues, repos, borne basse, interdiction après échec, verrou, images de chauffe, lissage, remise à zéro des compteurs…) : 12 détectées d'emblée, 3 avaient survécu (suppression du lissage, remise à zéro du compteur de surcharge, remise à zéro du compteur de marge). Elles ont donné trois tests nouveaux ; le dernier ne distingue le mutant que sans lissage, car avec le lissage par défaut la charge passe toujours par la zone intermédiaire qui remet le compteur à zéro (le mutant est équivalent dans ce cas).

## Ce qui n'est pas mesuré ni jugé

- **Qualité visuelle du détourage** : aucune personne dans la vidéo de test, donc le masque est vide et aucun bord, cheveu, main ou changement de lumière n'est jugé. C'est la limite la plus importante : on sait ce que le détourage **coûte**, pas ce qu'il **vaut**.
- **Machine modeste** : une seule machine, très puissante. La régulation est vérifiée avec un surcoût simulé, pas sur un portable sans GPU dédié.
- **Vraies webcams** : capture, décodage de MJPEG ou H.264 de la caméra, auto-exposition.
- **Réception WebRTC** de N flux et **encodage du Program** : le banc décode des fichiers vidéo locaux ; le Producer reçoit en plus par le réseau et doit encoder la composition. Ces coûts s'ajoutent.
- **Correction des couleurs et des lumières entre participants** (camera matching), recadrage automatique : non abordés.
- **Autres modèles** (MediaPipe Image Segmenter, WebGPU, modèles de matting plus fins) : non essayés ; le modèle de ce banc est l'ancien « Selfie Segmentation », choisi parce que son fichier est dans le paquet npm.
- Des essais de 45 à 60 s : pas de session longue (échauffement thermique, fuites de mémoire).

## Suite

1. Un jeu de séquences réelles (avec accord des personnes filmées) pour juger le masque : bords, mouvements, fond encombré, contre-jour. Comparer au moins un modèle de matting plus fin.
2. Mesures sur une machine modeste de référence (portable sans GPU dédié) pour fixer la configuration minimale du Producer.
3. Banc complet du Producer : réception de N flux WebRTC, détourage, composition, encodage du Program, sur 30 minutes.
4. Remplacer la cadence par minuteur par `requestAnimationFrame` / `requestVideoFrameCallback`.
