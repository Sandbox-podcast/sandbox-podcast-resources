# Accueil Sandbox : impact de l'IA et plateau au scroll

20 octobre 2026. Source éditoriale : [vision.md](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/vision.md). Décision : [DD-0064](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0064-accueil-impact-ia-et-plateau-au-scroll.md).

## Changements

- Promesse, description, titres des sections et métadonnées recentrés sur l'impact de l'IA dans les entreprises et les équipes tech. Traductions EN, ES et DE ajoutées.
- Plateau large sans les trois portraits, sombre à l'arrivée sur ordinateur, puis éclairé par révélation localisée de la photographie. Radar compact à l’éclat vert atténué ; accès aux rubriques par clic sur les objets, sans boutons sous le décor.
- Avancée et rotation du point de vue vers une contre-vue photoréaliste du même studio, avec des affiches de cinéma vintage cliquables. Seuls les épisodes vidéo disponibles alimentent les affiches ; le lien vers toutes les émissions reste visible.
- Cartes à collectionner remplacées par les vrais portraits, biographies et profils publiés de l'équipe. Tracé décoratif entre chapitres retiré de la homepage.
- Titres de l’accueil en Archivo, droits et plus compacts, avec des tailles adaptées au mobile.
- Page LinkedIn Sandbox ajoutée dans le footer avec les autres réseaux.

## Fichiers principaux

- `apps/site/src/components/studio-landing.tsx` : contenu du plateau et mur de replays.
- `apps/site/src/components/studio-scroll.tsx` : progression du scroll, pause et focus.
- `apps/site/src/components/studio-landing.module.css` : lumières, perspective et parcours mobile.
- `apps/site/src/domain/studio-scroll.ts` : calcul pur des phases, testable dans les deux sens.
- `apps/site/src/domain/replay-posters.ts` : correspondance entre les deux affiches vintage et les identifiants YouTube.
- `apps/site/src/components/discovery-home.tsx`, `discovery-story.tsx` et `discovery-chapters.module.css` : composition et présentation de l'équipe.
- `apps/site/src/components/shell.tsx` et `apps/site/src/app/(fr)/page.tsx` : footer et métadonnées.
- `apps/site/src/i18n/dictionaries/` : textes traduits.
- `apps/site/test/studio-scroll.test.ts`, `footer-socials.test.ts`, `discovery-refonte.test.ts`, `home-image-delivery.test.ts` : tests.
- `apps/site/scripts/test-home-studio.mjs` : recette navigateur locale.

`vision.md` a uniquement été formaté avec Prettier pour respecter le contrôle du dépôt. Son contenu éditorial reste la source fournie par Lou.

## Validation

- pnpm check réussi : formatage, ESLint, types, 967 tests du site répartis dans 135 fichiers, 7 tests du générique, 4 tests des assets vidéo et 24 tests BIS. Le relevé final est conservé dans apps/site/.local/home-studio/check.log.
- Build de production Webpack exécuté : compilation, TypeScript et génération de 204 pages réussis. Le relevé est conservé dans apps/site/.local/home-studio/build.log.
- Recette navigateur : 20 contrôles de progression et de rendu sur six configurations (1440 x 900, 1280 x 720, mobile 375 x 812, mobile avec mouvements réduits, ordinateur avec mouvements réduits et sans JavaScript). Retour arrière, raccourcis, pause, clics des objets, portraits et lien LinkedIn vérifiés. Un mur de huit affiches dupliquées uniquement dans le navigateur de test contrôle la place disponible, sans modifier le catalogue.
- Après les dernières corrections : recette navigateur relancée avec succès. Contrôle complémentaire à 1440 x 900 et 375 x 812 : Archivo appliquée aux titres, aucun italique sur le titre principal, quatre objets directement cliquables avec leur nom accessible, aucun libellé sous les objets et aucun débordement horizontal. Captures desktop-final.png et mobile-final.png.
- Cadrage complémentaire vérifié à 3412 x 1263 : photographie entièrement contenue dans la fenêtre. Ouvertures réelles de /episodes/1, /episodes/2 et /news : HTTP 200, avec leur titre attendu.
- Relecture du texte avec verifier.py : aucune alerte dans les nouveaux composants et documents.

Les captures et report.json se trouvent dans apps/site/.local/home-studio/. Les tests ciblés vérifient aussi l'association de chaque affiche à sa vidéo et le repli sur la miniature éditoriale des autres épisodes.

## Limites

Le catalogue public du 20 octobre contient [deux épisodes](https://www.sandboxpodcast.fr/podcast). La source locale initiale ne contenait que le pilote. La recette copie les métadonnées publiques de l'épisode 2 dans .local/studio-content.json et utilise SANDBOX_FRONT_PREVIEW=1, SANDBOX_FRONT_CONTENT_FILE=studio-content.json et SANDBOX_NEWS_PREVIEW=1. Ce fichier de recette isolé ne modifie ni le contenu publié ni .site-content.local.json. Les deux affiches ouvrent les replays locaux correspondants.

Les images proviennent de l'outil intégré ImageGen. Le [fichier de prompts](studio-photos-2026-10-20-prompts.json) donne les références et chemins. Les versions WebP servent le site ; les PNG restent disponibles comme sources.

L'effet de caméra repose sur des transformations CSS des deux photographies du studio, sans géométrie 3D du plateau. Les vérifications navigateur portent sur Edge/Chromium local ; elles ne certifient pas Safari sur un appareil réel ni les performances sur un téléphone physique.

Le premier lancement avec Turbopack a rencontré une erreur de compilation CJS pendant le préchargement d'une fiche d'épisode. L'aperçu de recette utilise Webpack, sans modification de la configuration du dépôt.

La compilation de production a aussi révélé une union undefined explicite incompatible avec les types de page générés par Next pour la méthodologie des classements. Sa suppression dans Props corrige le typage sans changer le comportement de cette page.

Aucune publication, migration, modification des comptes sociaux, PR, opération Git distante ou dépense n'a été effectuée. Le lien LinkedIn provient de l'URL donnée par Lou.
