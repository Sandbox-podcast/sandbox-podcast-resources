# POC 10 — Pipeline de post-production

Résultat : **PARTIAL**. La chaîne sources → reconstruction → transcription → suggestion de clip → export court tourne de bout en bout sur de vrais fichiers enregistrés, et l'alignement est vérifié sur le fichier produit. Mais la transcription est simulée (aucun modèle de parole disponible ici), la suggestion de clip vient d'un texte écrit à la main, et seul l'export d'un clip existe (pas le replay complet). Code : `packages/post-production` (86 tests) et `pocs/poc-10-post-production` (essai de bout en bout). Décision : [ADR-0011](../adr/ADR-0011-post-production.md).

## Ce qui est construit

- **Alignement** (`alignment.ts`) : à partir des repères d'une piste et de ceux de la référence, ajuste `fichier = (T − départ) × (1 + dérive)` et rend le décalage de départ, la dérive en ppm, le nombre de repères et le résidu. Refuse un alignement fondé sur trop peu de repères.
- **Transcription** (`transcript.ts`, `transcription-job.ts`) : segments `{locuteur, début, fin, texte}` validés (fin après début, dans la durée du média, pas de chevauchement d'un locuteur avec lui-même) ; document versionné (chaque correction crée une version, le journal garde avant/après, l'acteur, l'instant, le média n'est jamais touché) ; navigation (segment à un instant donné avec tolérance, position du lecteur avec amorce) ; tâche de transcription avec essais bornés (4), délai doublé à chaque échec (30 s, plafond 10 min), échec final explicite, relance manuelle, **sortie du fournisseur validée avant acceptation** ; l'accès au média ne dépend jamais de l'état de la tâche.
- **Clips** (`clips.ts`) : suggestion `{début, fin, titre, accroche, raison, score}` ; validation **avant** application (schéma, dans la durée réelle, début et fin recalés sur des limites de segments existants à 0,25 s près, durée de 15 à 90 s, doublons écartés au profit du mieux noté) ; ajustement IN/OUT et format ; cadrage 9:16 centré sur un sujet avec correction manuelle ; contrôle des zones de sécurité (valeurs **indicatives**, à valider avec les plateformes).
- **Export** (`export.ts`) : liste de décisions de montage qui référence les sources sans jamais les modifier ; arguments ffmpeg d'un clip (tableau d'arguments, jamais de shell) ; tâche d'export par étapes RENDER, VERIFY, CHECKSUM avec reprise sans refaire les étapes réussies, annulation qui supprime uniquement le dossier temporaire du job, et enregistrement de traçabilité (épisode, version du preset, version de la liste de montage, pistes sources, date, auteur, empreinte SHA-256).

## Essai de bout en bout

Entrée : les 6 fichiers Chrome du [POC 4](poc-04-multitrack-sync.md) (3 participants, 20 minutes).

1. **Reconstruction** : les repères des 6 fichiers donnent départ et dérive de chaque piste sur la ligne de temps de la vidéo du premier participant : départs de −0,32 à +0,06 s, dérives de −1,1 à +7,8 ppm, 120 repères chacune, résidus de 6,7 à 15 ms.
2. **Transcription** : faux fournisseur déterministe (tours de parole réguliers de 20 s, 60 segments). **Ce n'est pas une transcription de l'audio.**
3. **Suggestions** : 6 propositions écrites à la main, dont des pièges. 2 acceptées (le passage de 60 à 120 s, un autre de 800 à 860 s) ; refusées : un doublon d'une suggestion mieux notée, un timecode inventé, une fin après la fin du média et une durée de 900 s, un objet sans champ `reason`.
4. **Export** : clip 9:16 de 60 s (caméra du premier locuteur, recadrage 608×1080 puis 1080×1920, mix des 3 micros alignés, normalisation à −16 LUFS en une passe). Rendu en 5,6 s sur ce poste. Les trois étapes réussissent, vérification de la durée (±0,25 s), du format et de la présence de l'audio, empreinte enregistrée.
5. **Mesure sur le fichier produit**, comparée à un témoin exporté **sans** alignement (même clip, mêmes entrées) :

| Export          | Étendue d'un bip (3 micros mixés) | Bip − éclair |
| --------------- | --------------------------------- | ------------ |
| Aligné          | 117 ms                            | −20 ms       |
| Sans alignement | 390 ms                            | −64 ms       |

Un bip dure 100 ms à la source. Aligné, les trois bips coïncident (117 ms d'étendue, soit 17 ms de recouvrement imparfait et d'étalement de l'encodage AAC) ; sans alignement ils s'étalent sur 390 ms, c'est-à-dire qu'on entend trois bips successifs. L'écart bip−éclair passe de −64 à −20 ms, dans la précision d'une image (33 ms) du repère vidéo. Mesure sur 6 repères d'un clip de 60 s : elle valide l'alignement à cet endroit, elle ne mesure pas de dérive.

## Sensibilité des tests

29 mutations du code (bornes de validation, ordre des versions, délai exponentiel, essais maximum, fenêtre de tolérance, recouvrement des doublons, recalage du cadrage, zones de sécurité, reprise par étapes, nettoyage de l'annulation, signe et facteur de l'alignement, etc.) : toutes détectées. Une avait survécu (traçabilité donnée pour un export non réussi mais portant une empreinte) ; un test a été ajouté. Deux erreurs de mes propres tests ont été corrigées en cours de route (un seuil de durée mal choisi, un recouvrement exactement à la limite).

## Critères d'acceptation

| Critère                                    | État                                                                                                                               |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| AC-TRANSCRIPT-001, 003, 004, 005           | vérifiés (tests)                                                                                                                   |
| AC-TRANSCRIPT-002                          | logique vérifiée (segment à un instant, position avec amorce) ; le lecteur et le clic dans l'interface n'existent pas              |
| AC-CLIP-001, 003, 004, 005                 | vérifiés (tests) ; la raison est un champ obligatoire à afficher comme aide éditoriale                                             |
| AC-CLIP-002 (prévisualisation avant rendu) | **non fait** : demande un rendu basse définition et une interface                                                                  |
| AC-CLIP-006                                | géométrie du cadrage, zones de sécurité et correction manuelle vérifiées ; pas de détection de visage, valeurs de zone indicatives |
| AC-EXPORT-002, 003, 004, 005               | vérifiés (tests), et 002 et 004 sur l'essai réel                                                                                   |
| AC-EXPORT-001 (replay exploitable)         | **non fait** : seul un clip est exporté                                                                                            |

## Limites

- **Pas de vraie transcription ni de vraie suggestion par modèle.** Aucun modèle de parole n'est installé ici et en télécharger un demande une autorisation. L'abstraction de fournisseur est testée avec un faux ; la qualité d'un vrai fournisseur (justesse, locuteurs, coût, durée) n'est pas connue.
- Les repères d'alignement sont **artificiels** (éclair et bip dans le contenu). En production il n'y en a pas : l'alignement dépend du mécanisme décidé dans l'[ADR-0010](../adr/ADR-0010-seuils-et-alignement-multipiste.md), non testé.
- Export d'un clip seulement : pas de replay de session complet, pas de choix automatique de la caméra suivant le locuteur (la caméra est celle du premier locuteur du clip), pas de sous-titres, pas de gain par micro ni de réduction de bruit, mix simple.
- Normalisation en une passe (`loudnorm`) : le niveau obtenu n'a pas été mesuré en LUFS.
- Cadrage 9:16 sur une boîte fixe : aucune détection de visage.
- Vidéo de test de faible complexité (fond noir) : le temps de rendu (5,6 s pour 60 s de clip) n'est pas représentatif d'un vrai contenu.
- L'exécution réelle (ffmpeg, ffprobe, fichiers) n'est dans aucun test automatisé : elle est dans le script `pocs/poc-10-post-production/src/run-e2e.ts`, lancé à la main. Les tests de `packages/post-production` utilisent des exécuteurs simulés.
- Pas de file de tâches : un export tourne dans le processus qui l'a lancé ; une reprise après crash du processus n'est pas conçue ici.

## Suite

Brancher un vrai fournisseur de transcription (avec décision du propriétaire sur le fournisseur, les données envoyées et le coût), un vrai modèle de suggestion avec jeu d'évaluation, l'export du replay complet avec choix de caméra suivant le locuteur actif de la régie, la prévisualisation basse définition, la détection de visage pour le cadrage vertical, la mesure de loudness en deux passes, et un test automatisé du rendu sur un petit média généré.
