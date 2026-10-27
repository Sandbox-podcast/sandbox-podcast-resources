# Vidéoclub : lumière cyan et néon framboise

20 octobre 2026. Lou demande une différence visible de design et de luminosité entre le plateau et la pièce située derrière le portail.

## Direction

Le plateau garde ses lumières ambre. Le vidéoclub reçoit des rayons gris graphite et des panneaux bleu nuit, éclairés par des lignes cyan froides. Le néon existant devient rouge framboise, avec un reflet sur le plafond. Le sol anthracite reprend discrètement ces deux couleurs. L'exposition doit être plus sombre que le plateau, tout en laissant les pochettes lisibles.

Le cadrage et la perspective de la photographie existante servent de repères. Les trois baies, les étagères et leurs panneaux supérieurs doivent garder leurs positions pour conserver l'alignement des projets HTML. Aucun projet ni texte éditorial n'est ajouté dans les rayons par génération.

## Source et production

- Source : `apps/site/public/video-club/room-photoreal-v1.webp`, 1672 × 941 pixels.
- Outil : édition par `image_gen` intégré, source fournie comme image de référence et cible.
- Sortie : `apps/site/public/images/rooms/video-club-room-v2.webp`, 1672 × 941 pixels, 292 866 octets.
- PNG généré : `C:/Users/Lou/.codex/generated_images/01a158a4-3068-7a62-bc71-c5bd30744104/exec-1c667c94-52a5-4329-ad11-5c620e1caa27.png`.
- Conversion WebP avec Sharp, qualité 89. La génération possède déjà les dimensions exactes de la source ; aucun recadrage n'a été appliqué.
- Le fichier source reste conservé.

Le [prompt complet](video-club-room-v2-2026-10-20-prompt.json) décrit les invariants géométriques et les changements de matériaux et d'éclairage.

## Vérification

Le PNG et le WebP ont été inspectés. La photographie conserve visuellement le cadrage, la perspective, les trois baies, les panneaux et les lignes des rayons. Les surfaces destinées aux projets restent vides. La palette froide et les reflets rouges distinguent le vidéoclub du plateau ambre.

Ce contrôle est visuel ; il ne mesure pas l'écart de chaque bord au pixel près. Après intégration dans les catalogues des salles et du vidéoclub, le parcours WebGL a été réexécuté. Les captures du portail et de l'arrivée à 1440 × 900 confirment visuellement le contraste avec le plateau et l'alignement des pochettes HTML sur les rayons.
