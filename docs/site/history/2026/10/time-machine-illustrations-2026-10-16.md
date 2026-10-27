# Illustrations de la Time Machine

Statut : première collection remplacée par [151 affiches distinctes](time-machine-affiches-distinctes-2026-10-16.md). Ce document conserve la provenance de la première passe ; ces 19 images partagées ne sont plus utilisées par la Time Machine.

Date : 2026-10-16. Conception décidée par l'agent sur délégation (PD-0003), à la demande de Lou.

Chaque événement reçoit une illustration dans la fiche principale, les archives et le récapitulatif annuel. La collection comprend 19 visuels de concept, partagés entre les événements d'un même sujet. Ce ne sont pas 151 photographies uniques ni des documents d'archives. Aucun logo, portrait ou écran de produit réel n'est reconstitué.

Les sujets séparent notamment les échecs du Go, les protéines des matériaux, la fusion du climat et les jeux vidéo du code. Les 151 identifiants du corpus sont affectés explicitement. Un futur événement conserve un visuel de repli selon sa catégorie jusqu'à sa revue éditoriale.

## Production

Outil intégré image_gen.imagegen, sans API payante configurée par l'agent. Chaque image a sa propre génération. Les prompts complets, les chemins livrés et les événements associés sont dans [le relevé de production](time-machine-artwork-prompts-2026-10-16.json).

Les sources PNG restent dans le répertoire generated_images de Codex. Les fichiers livrés sont des WebP de 1200 x 800 pixels, encodés avec Sharp, qualité 86, sans modification du contenu de l'image. Les médias sources existants et le corpus ne sont pas modifiés.

Le composant HistoryArtwork utilise les variantes responsives de Next Image. L'image principale se charge immédiatement ; les archives et Wrapped utilisent le chargement différé. Les images sont décoratives pour les lecteurs d'écran : le titre adjacent et les sources portent l'information.

## Validation

Le test time-machine-artwork.test.ts vérifie la couverture exacte du corpus, l'absence de doublon, l'existence locale et le poids de chaque fichier, la séparation des sujets scientifiques et le rendu accessible. Le contrôle navigateur de l'interface est réalisé dans le lot Time Machine.

Les trois tests ciblés passent le 16 octobre à 13 h 22. Les 19 images ont été inspectées. Leur décodage avec Sharp confirme le format WebP et les dimensions de 1200 x 800 pixels. Le total livré est de 3 044 540 octets ; le fichier le plus lourd pèse 250 888 octets. Le vérificateur Human Quality passe sur ce document.

Les contrôles globaux du site et le compte rendu de rendu mobile sont consignés par l'agent principal. Aucune publication, dépense, migration, modification des données, commit ou push n'est inclus dans cette retouche.
