# Couvertures des projets sur l'accueil

Date : 2026-10-16. Conception décidée par l'agent sur délégation (PD-0003), après la demande de Lou.

Deux illustrations de concept remplacent les captures comme couvertures de Song Maker et Sillage dans le carrousel de l'accueil. Les captures réelles du catalogue et des fiches restent conservées.

Song Maker montre un atelier musical : clavier, console de mixage et pistes lumineuses qui se rejoignent. La composition traduit la génération de chansons, le travail des prises et le mixage décrits dans le catalogue. Sillage montre trois cœurs de calcul reliés à un espace de travail commun, avec des embranchements et des cartes de tâches abstraites. Les objets illustrent la coordination des agents et leur contexte partagé.

Les images utilisent les noirs, le cyan et l'ambre de Sandbox. Leur zone basse reste sombre pour recevoir les légendes. Elles ne représentent pas une interface réelle, un matériel vendu avec les applications ou une fonctionnalité supplémentaire.

## Production et fichiers

Outil intégré image_gen.imagegen. Une génération distincte par couverture. Les prompts complets et les chemins sont dans [le relevé de production](home-project-artwork-prompts-2026-10-16.json). Les PNG sources restent dans generated_images de Codex.

Les fichiers du site sont encodés en WebP avec Sharp, qualité 90, largeur 1200 pixels, sans modification du contenu :

| Projet     | Fichier                                                        | Dimensions | Poids          |
| ---------- | -------------------------------------------------------------- | ---------- | -------------- |
| Song Maker | apps/site/public/images/home/projects/song-maker-cover-v1.webp | 1200 x 751 | 133 668 octets |
| Sillage    | apps/site/public/images/home/projects/sillage-cover-v1.webp    | 1200 x 751 | 118 064 octets |

La carte HOME_PROJECT_ARTWORK, dans apps/site/src/domain/home-project-artwork.ts, fournit uniquement les deux substitutions de l'accueil. Le catalogue personal-projects.json n'est pas modifié par cette production.

## Vérification

Les deux images ont été inspectées. Le décodage avec Sharp confirme le format, les dimensions et un poids inférieur à 300 Ko par fichier. Le contrôle visuel du carrousel, les tests d'intégration et les vérifications globales appartiennent au lot de l'accueil.

Aucun commit, push, publication ou modification de données n'est inclus dans cette production.

## Correction demandée par Lou

La couverture Sillage générée v1 est remplacée dans l'accueil par l'image Sillage.png fournie par Lou le 16 octobre. Le fichier source dans Downloads reste intact. La version servie, apps/site/public/images/home/projects/sillage-cover-v2.webp, conserve l'image complète en 1200 x 800, avec une conversion WebP de qualité 90 (193 970 octets). La version v1 reste disponible comme historique local, mais n'est plus utilisée par le carrousel.
