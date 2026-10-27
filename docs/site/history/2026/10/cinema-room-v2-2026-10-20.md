# Cinéma : une façade plane pour les affiches

20 octobre 2026. Lou demande de remplacer le décor dont les murs en perspective imposaient des affiches déformées. La nouvelle illustration place les six cadres sur une même façade vue de face. Le noyer, le bleu nuit, les éclairages ambre et les fauteuils restent cohérents avec les autres pièces.

## Production

- Source conservée : `apps/site/public/images/rooms/cinema-room-v1.webp`.
- Outil : `image_gen` intégré, édition de l'image source.
- Sortie : `apps/site/public/images/rooms/cinema-room-v2.webp`, 1672 × 941 pixels, 162 052 octets.
- PNG généré : `C:/Users/Lou/.codex/generated_images/01a158a4-3068-7a62-bc71-c5bd30744104/exec-e2887821-4dfc-4692-bccd-57968dcfd42e.png`.
- Conversion Sharp en WebP, qualité 89, sans recadrage ni changement de dimensions.
- [Prompt complet et provenance](cinema-room-v2-2026-10-20-prompt.json).

Les six panneaux et l'écran central restent vides pour accueillir les vrais contenus HTML. La génération n'ajoute ni émission, ni affiche, ni texte.

## Repères d'intégration

Les coordonnées suivantes sont relevées visuellement dans l'image de 1672 × 941 pixels. Elles décrivent l'intérieur des cadres, sans leur bordure métallique.

| Cadre                | Bord gauche | Bord droit | Haut | Bas |
| -------------------- | ----------: | ---------: | ---: | --: |
| Gauche extérieur     |          64 |        178 |  249 | 455 |
| Gauche intermédiaire |         220 |        334 |  249 | 455 |
| Gauche intérieur     |         376 |        492 |  249 | 455 |
| Droite intérieur     |        1178 |       1295 |  249 | 455 |
| Droite intermédiaire |        1337 |       1451 |  249 | 455 |
| Droite extérieur     |        1494 |       1608 |  249 | 455 |

L'écran central occupe approximativement le rectangle `(553, 192)` à `(1118, 484)`. Les deux cadres proches du centre accueillent les deux derniers replays ; leur proximité avec l'écran limite leur disparition lorsque l'image est recadrée en mode `cover`. Les coordonnées doivent suivre le même calcul de recadrage que le décor.

Les bords sont droits et parallèles : aucune déformation en perspective n'est nécessaire pour les affiches. Le contrôle du PNG confirme visuellement cette disposition. Le nombre d'épisodes visibles et leur pagination relèvent du composant de contenu ; l'illustration ne simule aucun replay supplémentaire. Les vérifications de l'intégration et du parcours sont consignées dans la recette de la visite.
