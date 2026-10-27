# Affiches cinéma des deux premiers épisodes

20 octobre 2026. Lou demande des affiches de film pour les replays de la salle cinéma. Deux compositions originales remplacent les visuels dérivés des miniatures dans cette salle. Les autres usages des affiches vintage restent inchangés.

Le premier épisode, associé à la vidéo `GgSiPkADCz4`, utilise une architecture sombre éclairée en cyan, en lien avec le titre court existant « Le modèle ne suffit pas ». Le second, vidéo `7KVqydbGow0`, réunit les animateurs dans une ambiance de café et d'atelier, avec des lumières ambre, pour « L’IA dans votre métier ». Les deux compositions reprennent les mêmes trois animateurs, un fond bleu nuit et une zone basse destinée au titre.

## Sources et production

Les photographies locales `team/lou-studio-lossless-v1.webp`, `team/loic-studio-lossless-v1.webp` et `team/nicolas-prod-2026-10-15.webp` servent de références d'identité. Elles ont été inspectées avant génération. Les titres et les identifiants vidéo proviennent des métadonnées publiées et du domaine `replay-posters.ts`.

La production utilise `image_gen` intégré : une première passe crée chaque composition, puis une édition retire toute typographie. Les images finales ne contiennent aucun titre français, numéro, crédit ou date. La typographie est ajoutée en HTML, dans la langue affichée par le site.

| Fichier dans `apps/site/public/images/home/replays/` | Dimensions  |          Poids |
| ---------------------------------------------------- | ----------- | -------------: |
| `episode-001-cinema-v2.webp`                         | 1024 × 1536 | 161 988 octets |
| `episode-002-cinema-v2.webp`                         | 1024 × 1536 | 168 224 octets |

Les PNG sources restent conservés dans le répertoire des images générées. La conversion WebP utilise Sharp, qualité 88, sans recadrage ni redimensionnement. Les [prompts et chemins de provenance](cinema-episode-posters-v2-2026-10-20-prompts.json) décrivent les deux passes.

## Intégration et contrôle

`cinemaPosterArtwork(videoId)` fournit ces images au seul traitement cinéma. L'association repose sur l'identifiant vidéo, pas sur le numéro d'épisode. Le mapping des affiches vintage est conservé pour les autres pages.

Les deux sorties ont été inspectées : trois portraits reconnaissables, deux ambiances distinctes, aucun texte de titrage intégré et une zone basse sombre disponible sur environ 38 % de la hauteur. Ce sont des compositions générées à partir des photographies des animateurs ; elles ne représentent pas une prise de vue documentaire.

Les trois tests du mapping et le lint ciblé ont réussi. La vérification du rendu HTML traduit et de l'intégration dans les cadres relève de la recette de la salle cinéma ; le contrôle des assets seuls ne la remplace pas.

## Rendu dans le site

La variante cinéma de `EpisodeArtwork` superpose le titre court, la marque et le numéro d'épisode en HTML. Le titre utilise une composition centrée en capitales, avec une couleur ivoire pour l'affiche ambre et un blanc froid pour l'affiche cyan. Les titres restent lisibles sur les petites affiches, sans la règle de masquage utilisée ailleurs pour les miniatures étroites. L'icône de lecture apparaît au survol ou au focus et laisse le titrage visible au repos.

Douze cas ont été contrôlés dans Edge : les quatre langues à 320, 1440 et 3440 pixels. Les deux images chargent, les titres restent dans les cadres, aucun débordement horizontal ni erreur JavaScript relevé. Les captures françaises à 1440 pixels et anglaises à 320 pixels ont été inspectées après fermeture de la bannière de consentement. Preuves : `apps/site/.local/cinema-posters-v2/report.json` et les captures de ce dossier. Les tests du composant vérifient également les titres traduits dans les quatre langues.

## Validation du lot

`pnpm check` réussit : format, lint, TypeScript, 144 fichiers et 1154 tests du site, ainsi que les autres suites du dépôt. La compilation `pnpm --filter @podcast/site build` réussit également. Les journaux sont `apps/site/.local/cinema-posters-navigation-check.log` et `cinema-posters-navigation-build.log`. Travail local ; aucune publication.
