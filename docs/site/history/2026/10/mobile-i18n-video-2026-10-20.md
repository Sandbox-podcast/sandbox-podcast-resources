# Vidéos, miniatures et traductions : correctifs du 20 octobre 2026

Lou signale des traductions incomplètes dans les textes et miniatures vidéo. Le contrôle de `/en/podcast`, `/es-es/podcast` et `/de-de/podcast` reproduit le titre français de l'épisode 2. Les affiches de l'accueil contiennent également une légende française intégrée à l'image. La solution de présentation est consignée dans [DD-0067](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0067-miniatures-video-et-textes-localises.md).

## Changements locaux

Le titre et le résumé publiés de l'épisode 2 disposent maintenant de traductions anglaise, espagnole et allemande. Les libellés de ressources provenant de la description sont aussi traduits : chaîne YouTube, site et ressources, épisode audio Spotify, liens Sillage et mentions du ministère du Travail. Les noms de projets, versions, numéros et liens sont conservés.

L'export de traduction utilise les mêmes chapitres et ressources calculés que la fiche publique. Il inclut donc leurs libellés même lorsque l'épisode les conserve uniquement dans sa description. Une régression couvre ce cas.

Le nouveau composant `EpisodeArtwork` rend les miniatures françaises existantes. Dans les autres langues, il compose une vignette avec les portraits recadrés des affiches connues et de vrais textes HTML traduits. Les petites vignettes gardent le numéro lorsque la légende ne tient pas ; leur titre complet reste traduit à côté. Pour une vidéo inconnue, une couverture typographique reprend le titre disponible. Aucun fichier image n'est écrasé.

Les replays de l'accueil, la page podcast, les cartes et la façade du lecteur partagent ce composant. Les pages podcast et épisode annoncent la langue française de la vidéo. La façade conserve son fonctionnement : aucun lecteur YouTube n'est chargé avant le clic, sauf demande explicite d'un horodatage.

La régénération du catalogue a aussi révélé des textes locaux récents sans traduction : accueil, messages d'attente des classements et derniers événements de la Time Machine. Les trois dictionnaires ont été complétés à partir de ces sources, en conservant leurs faits et noms propres. Le catalogue compte **2 504 clés renseignées sur 2 504** dans chacune des trois langues. Ce contrôle de présence ne remplace pas une relecture native et ne constitue pas une nouvelle vérification des faits historiques.

## Vérifications

- TypeScript : `node node_modules/typescript/bin/tsc --noEmit -p apps/site/tsconfig.json`, réussi.
- Vitest : huit suites concernées, **73 tests réussis**, dont les nouveaux cas de vignettes localisées, de ressources et d'export depuis la description.
- Chromium : `node scripts/test-video-localization.mjs` depuis `apps/site`, **27 contrôles réussis** sur l'accueil, le podcast et l'épisode 2, en EN/ES/DE, à 320, 390 et 1440 pixels. Aucun débordement horizontal ni erreur JavaScript détecté. La façade reste fermée avant clic.
- Captures relues : vignette et texte de replay anglais à 320 pixels, affiches allemandes à 390 pixels. Le recadrage garde les portraits et retire le bandeau français de l'image.

Le rapport navigateur et les captures résident dans `apps/site/.local/video-localization/`. Le contrôle global et les autres recettes sont pilotés avec le reste du lot.

## Fichiers concernés

Le lot ajoute `src/components/episode-artwork.tsx` et son module CSS, `scripts/test-video-localization.mjs` et `test/episode-artwork-localization.test.ts`. Il adapte `studio-landing.tsx`, `podcast-replays.tsx`, `cards.tsx`, `client.tsx`, les pages podcast et épisode, le registre `domain/replay-posters.ts`, l'export `domain/content-translations.ts` et son test. Les dictionnaires EN/ES/DE et le catalogue source sont mis à jour.

Les nouvelles publications restent soumises au passage manuel de traduction défini par ADR-0022. La piste audio et les textes internes du lecteur YouTube ne sont pas modifiés par ce lot. Aucun appel payant, aucune écriture distante, aucun commit ni déploiement n'a été effectué.
