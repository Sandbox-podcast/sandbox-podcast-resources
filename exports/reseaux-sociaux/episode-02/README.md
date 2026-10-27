# SANDBOX #2 : Shorts corrigés

Mise à jour du 19 octobre 2026. La révision `camera-unique-v2` remplace le montage qui affichait deux fois la même caméra.

## Fichiers à utiliser

Les chemins `shorts/`, `revisions/` et `.local/` ci-dessous désignent les fichiers du poste de production ; les médias et captures lourds sont exclus de Git. Les [sources des trente compositions et le pipeline de reproduction](../../../tools/social-network-manager/episode-02/camera-unique-v2/README.md) sont versionnés. Un nouveau clonage doit préparer les médias avant de reproduire ces montages.

Les **30 MP4 corrigés** et leur manifeste (`shorts/` et `shorts/manifest-camera-unique-v2.json`) restent sur le poste de production et ne sont pas inclus dans ce dépôt. Le manifeste donne les empreintes SHA-256 et les chemins des anciennes versions archivées. Les sources et les six publications déjà en ligne sont conservées.

Chaque montage utilise une seule vue vidéo, avec un cadrage adapté aux changements de disposition de l’émission. Les titres, extraits, voix et sous-titres sont conservés. Les vues de groupe restent des vues de groupe ; aucun participant n’est ajouté une seconde fois.

Les quatre coupes Instagram sous 90 secondes sont dans `shorts/upload-variants/instagram/`. Les variantes d’envoi X et TikTok utilisent les MP4 corrigés de référence. Les anciennes variantes sont archivées et ne doivent plus être utilisées.

| Élément                                 | Emplacement                            |
| --------------------------------------- | -------------------------------------- |
| Vidéos corrigées et images de contrôle  | `shorts/`                              |
| Fichiers, timecodes, titres et révision | `clips-plan.json`                      |
| File de publication et preuves natives  | `publication-queue.json`               |
| Calendrier des créneaux                 | `calendrier.md`                        |
| Résultats vidéo                         | `render-status.json`                   |
| Contrôle audio et images examinées      | `revisions/camera-unique-v2/`          |
| Projets HyperFrames corrigés            | `revisions/camera-unique-v2/projects/` |
| Anciens MP4, variantes et suivi         | `revisions/avant-correction-camera/`   |

## État des remplacements en ligne

Un fichier corrigé sur le disque ne remplace pas à lui seul la vidéo sur un réseau. Le statut `replacement_pending` indique qu’il faut encore enregistrer et vérifier la nouvelle programmation native. Dans ce cas, les identifiants et les preuves de l’ancien média restent dans l’historique.

| Réseau    | Publications existantes conservées | Nouvelles versions programmées et vérifiées | Remplacements restant à confirmer |
| --------- | ---------------------------------- | ------------------------------------------- | --------------------------------- |
| youtube   | 3                                  | 27                                          | 0                                 |
| instagram | 1                                  | 29                                          | 0                                 |
| x         | 1                                  | 29                                          | 0                                 |
| tiktok    | 1                                  | 29                                          | 0                                 |

Les 27 anciens Shorts YouTube programmés ont été rendus privés. Les anciens Reels Instagram programmés ont été déplacés en brouillons avant le remplacement. Les 24 anciennes réservations TikTok ont été supprimées après confirmation explicite de Lou. Sur X, chaque ancien média est remplacé dans sa réservation existante. Les routines locales Meta et TikTok restent en pause ; les réservations natives assurent la diffusion.

Les heures de `publication-queue.json` sont en Europe/Paris et les réservations se répartissent du 19 au 24 octobre. Les neuf derniers Reels Instagram ont été réconciliés avec leurs identifiants natifs et les créneaux approuvés des 23 et 24 octobre. La file compte 114 réservations corrigées et six publications existantes conservées, sans remplacement en attente.

Meta conserve une tentative supplémentaire « Pâtissiers » (`1067034329496463`) marquée « Failed to publish ». Elle n'est pas comptée comme une réservation valide. La réservation retenue est `1726874871716795`, le 23 octobre à 13 h. Ne pas renvoyer cet extrait ; conserver le constat et les captures du 19 octobre dans `.local/social-network-manager/2026-10-19/`.

## Vérifications

Les 30 exports ont été décodés intégralement sans erreur : 720 × 1280, 30 images/s, durée conforme et une piste audio. Le début, le milieu et la fin de chaque vidéo ont été examinés, soit 90 images. Les cadrages s’appuient sur les dispositions visibles dans la source.

Pour chaque vidéo, trois fenêtres audio ont été comparées à la source. La corrélation dépasse 0,97 avec un décalage inférieur ou égal à 10 ms. Cette mesure vérifie la conservation et la synchronisation de la voix ; elle ne remplace pas une écoute intégrale. Les sous-titres viennent de la transcription automatique déjà corrigée ; les 30 vidéos n’ont pas été réécoutées intégralement.

## Spotify

Les titres enregistrés suivent le même format :

- SANDBOX #1 (pilote) | Mistral Large 4, Claude Haiku 5.5, Gemini at Work, Sillage et les harnais IA
- SANDBOX #2 | IA au travail : cas d’usage, débats et actualités

## Reprise

Lire la file et la liste native avant tout nouvel import. Ne jamais republier les six lignes `published_confirmed`. Ne pas utiliser les anciens projets `composition/projects/`, ni relancer `compose-e02.py`, `render-e02.py` ou `calendar-e02.py` sur ce lot. Les deux anciens scripts de montage sont désactivés pour éviter le retour de la double caméra.

Le journal détaillé et les captures sont dans `.local/social-network-manager/`. L’ancien README a été conservé dans `revisions/avant-correction-camera/README-avant-correction.md` pour l’historique.
