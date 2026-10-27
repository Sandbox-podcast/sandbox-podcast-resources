# Décors des six salles Sandbox

20 octobre 2026. À la demande de Lou, le site réunit six pièces : plateau, vidéoclub, classements, Time Machine, cinéma et Radar. La direction des nouveaux décors est décidée par l'agent sur délégation (PD-0003), à partir de [vision.md](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/vision.md).

## Direction

Les salles appartiennent au même studio : murs bleu nuit, tasseaux de noyer, métal sombre, lumière ambre et touches cyan. Le Radar ajoute le vert de l'instrument déjà présent sur le plateau. Les espaces servent les usages du talk-show : comparer les outils, consulter l'histoire de l'informatique, regarder les émissions et suivre les actualités.

Les écrans et cadres des nouveaux décors sont vierges. Les titres, classements, affiches et liens restent des contenus HTML issus du site. Les accessoires des images sont des éléments de décor générés, sans valeur documentaire.

## Fichiers

| Salle        | Image                                                     | Dimensions | Poids          |
| ------------ | --------------------------------------------------------- | ---------- | -------------- |
| Plateau      | `apps/site/public/images/home/studio-wide-lit-v6.webp`    | existant   | conservé       |
| Vidéoclub    | `apps/site/public/images/rooms/video-club-room-v2.webp`   | 1672 × 941 | 292 866 octets |
| Classements  | `apps/site/public/images/rooms/rankings-room-v1.webp`     | 1672 × 941 | 251 486 octets |
| Time Machine | `apps/site/public/images/rooms/time-machine-room-v1.webp` | 1672 × 941 | 255 380 octets |
| Cinéma       | `apps/site/public/images/rooms/cinema-room-v1.webp`       | 1672 × 941 | 157 128 octets |
| Radar        | `apps/site/public/images/rooms/radar-room-v1.webp`        | 1672 × 940 | 232 618 octets |

Le plateau conserve sa photographie. Le vidéoclub reçoit une [version cyan, rouge et graphite](video-club-room-v2-2026-10-20.md), demandée par Lou pour mieux distinguer la salle visible derrière le portail. Sa source existante reste conservée. La contre-vue `studio-reverse-gallery-v1.webp` a été examinée pour assurer la continuité du décor ; le cinéma dispose de son propre intérieur.

## Génération et provenance

Les quatre nouveaux décors ont été générés avec l'outil intégré `image_gen`, sans API ni CLI de repli. Chaque salle a reçu un prompt distinct, avec un cadrage large et des matériaux communs. Les [prompts complets](six-rooms-artwork-prompts-2026-10-20.json) sont conservés.

Les PNG originaux restent dans `C:/Users/Lou/.codex/generated_images/01a158a4-3068-7a62-bc71-c5bd30744104/` :

- Classements : `exec-eaa03d75-fd11-4492-bd5d-f23e736da105.png`.
- Time Machine : `exec-a065aaf5-55a4-4b2b-869e-15889a8b71f2.png`.
- Cinéma : `exec-640cdd11-f662-4569-9a21-62c9e94f072a.png`.
- Radar : `exec-0dc7203d-9e4d-4182-be91-49e62c7ef643.png`.

Les fichiers consommés par le site sont copiés dans le dépôt et encodés en WebP avec Sharp, qualité 87, sans recadrage ni redimensionnement. Aucun média existant n'a été écrasé.

## Contrôle visuel et limites

Les quatre sorties ont été inspectées. Les perspectives, les matériaux et les zones réservées aux contenus conviennent au parcours entre salles. Aucun texte ni chiffre éditorial n'est intégré aux nouvelles images. Le cadran et les points du Radar sont décoratifs.

Ces décors sont des images planes. Ils apportent la matière visuelle à l'expérience ; le déplacement de caméra, l'ouverture des passages et les interactions dépendent de l'implémentation du site. Ils ne fournissent ni volumes 3D ni géométrie permettant de regarder derrière chaque objet.

La validation fonctionnelle et le contrôle global du dépôt relèvent de l'intégration du parcours. La génération des décors n'a modifié aucun composant, CSS, dépendance ni donnée éditoriale.
