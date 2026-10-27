# Plateau : responsive et zones cliquables

16 octobre 2026, après le merge de la PR 71.

Le déploiement de la PR 71 est présent en production. Le chevauchement signalé sur la capture vient du rapport largeur/hauteur : les portraits suivaient la largeur du décor, alors que le titre restait près du haut de l'écran.

## Corrections locales

- Portraits dimensionnés selon la hauteur, avec un espace libre sous le titre.
- Décor central cadré sur écran panoramique, côtés prolongés par une version sombre et floutée.
- Texte et boutons dimensionnés pour les grandes hauteurs.
- Zone cliquable de la voiture étendue à son cadre ; l'en-tête transparent ne bloque plus sa partie haute. Le sélecteur de langue garde la priorité dans son propre rectangle.
- Porte éclairée au survol : teinte chaude légère, contour et halo. Le focus clavier reste visible, l'ouverture conserve son animation.

Fichiers : `discovery-home.module.css`, `site-polish.css`, assertions réutilisables `scripts/home-stage-checks.mjs`. Décision : [DD-0047](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0047-parite-accueil-production.md).

## Vérification navigateur

Assertions exécutées dans le navigateur Codex sur le serveur local : 3438 × 1274 (capture de Lou), 2560 × 1080, 1920 × 1080, 1440 × 900, 1280 × 720, 1024 × 768, 4096 × 1440, 390 × 844, 320 × 740 et 844 × 390.

Aucun débordement horizontal. Sur ordinateur, au moins 24 px entre le titre et le portrait central. Les points visibles testés sur le cadre de la voiture reçoivent les clics, hors rectangle du sélecteur de langue. À 1024 px, le décor conserve son recadrage latéral ; seules les zones visibles sont contrôlées. Sur mobile, le plateau interactif est remplacé par la présentation éditoriale prévue.

Menu des langues ouvert et fermé. Survol réel de la porte vérifié par son style calculé et par capture. Focus clavier : contour de 2 px visible. Clic simple : arrivée dans le vidéoclub avec 34 cassettes. Navigation Time Machine et retour par le logo vérifiés.

## Contrôles du dépôt

- Prettier sur les cinq fichiers de ce lot : succès.
- ESLint sur `home-stage-checks.mjs` : succès.
- `pnpm check` : exécuté, bloqué par le formatage de trois fichiers modifiés en parallèle (`test-analytics-e2e.mjs`, `source-catalog.json`, `dictionary-loaders.ts`). Une première exécution a aussi permis de corriger un global non qualifié dans notre utilitaire.
- `pnpm test` : 673 tests du site réussis, 1 échec dans `charts-store.test.ts` (`seedExternal` absent au moment de l'exécution), 7 tests de la vidéo réussis. La suite globale s'arrête sur cet échec.
- `pnpm build` : compilation réussie, puis vérification TypeScript bloquée dans les fichiers modifiés en parallèle : type `Robots.index` dans la page localisée, `seedExternal` dans `charts-store.test.ts`, type du fournisseur dans `external-identity.test.ts`.

Ces résultats décrivent l'état observé pendant les modifications simultanées, et doivent être rejoués après leur stabilisation. Les changements de traduction, d'indexation, de classement et les fichiers OBS appartiennent à d'autres travaux. Le formatage de `external-identity.test.ts` a été appliqué sans changer sa logique.

L'aperçu à jour est le serveur de développement `http://127.0.0.1:3219/`, ouvert à la place de l'ancien aperçu compilé sur le port 3320. Le build complet reste à valider avant publication.

Ce lot n'est pas publié et aucune nouvelle PR n'est créée.
