# Accueil V4 : équipe, projets, puis rubriques

15 octobre 2026. Version locale disponible sur `http://127.0.0.1:3340/`. Le parcours suit [DD-0034](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0034-accueil-equipe-projets-puis-rubriques.md).

## Résultat

Le premier écran conserve le plateau de télévision, le trio, le pitch et l'accès au dernier épisode. Le logo et la langue restent en haut ; les onglets, la recherche et le menu mobile sont masqués sur l'accueil.

Le deuxième écran présente les portraits et les bios de Lou, Loïc et Nicolas. Lou a choisi de partir des projets documentés. Les textes ne supposent aucun parcours personnel. Une biographie renseignée dans la collection Animateurs remplace automatiquement le texte de repli.

Le troisième écran présente Not My Fault, Song Maker et Sillage, avec un lien vers chaque fiche et vers le catalogue. La Time Machine et les classements arrivent ensuite, avant le dernier replay et le pied de page. Le lien "La suite" rejoint directement les biographies.

## Vérifications réalisées

| Contrôle                            | Résultat                                                                                                                                                               |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pnpm check`                        | Réussi : format, ESLint, TypeScript, 605 tests du site, 7 tests de l'intro et 4 tests des jingles, soit 616 tests. Journal : `.local/refonte-v4-check.log`.            |
| `pnpm --filter @podcast/site build` | Réussi : compilation, vérification des types et génération de 203 pages statiques. Journal : `.local/refonte-v4-build.log`.                                            |
| Ordre et contenu de l'accueil       | Test de rendu : plateau, équipe, projets, rubriques, replay ; les liens attendus sont présents.                                                                        |
| Contenu éditorial                   | Test : une bio publiée est prioritaire ; les profils absents ou fictifs sont exclus ; aucune réalisation manquante n'est inventée.                                     |
| Replay publié après le build        | Test adapté : un seul article de replay, indépendamment des trois articles de présentation des animateurs.                                                             |
| Ordinateur, 1440 × 1000             | Trois colonnes, biographies et projets chacun dans leur section de 1000 pixels. Ancre des bios à la bonne position. Captures relues.                                   |
| Mobile, 390 × 844 et 320 × 740      | Une colonne, contenu en hauteur naturelle, menu masqué, aucun débordement horizontal. Portrait et biographie relus à 390 pixels.                                       |
| Navigation vers un projet           | Clic réel sur Song Maker, fiche chargée et navigation complète visible sur cette fiche.                                                                                |
| Anglais                             | Titres, trois bios et liens de projets localisés vérifiés dans le navigateur sur `/en`. Les textes ajoutés existent aussi dans les dictionnaires espagnol et allemand. |
| Médias                              | Portraits et couvertures utilisent le chargement différé de Next Image. Le plateau existant conserve son préchargement et son comportement de mouvement.               |
| Diff et rédaction                   | `git diff --check` sans erreur ; vérificateur de rédaction française appliqué à DD-0034 et à ce rapport.                                                               |

Les premières exécutions ont détecté des assertions non nulles interdites par ESLint, puis un ancien test qui comptait tous les éléments `article` comme des replays. Ces points ont été corrigés ; aucun gate n'a été désactivé.

## Fichiers du lot

- `apps/site/src/domain/home-story.ts` : biographies de repli et sélection des trois projets.
- `apps/site/src/components/discovery-story.tsx` : sections équipe, projets et exploration.
- `apps/site/src/components/discovery-home.tsx` et sa feuille de style : insertion et mise en page des sections.
- `apps/site/src/app/(fr)/page.tsx` : passage des animateurs publiés et des projets à l'accueil.
- `apps/site/src/app/site-polish.css` : navigation de l'accueil et décalage des ancres.
- `apps/site/src/i18n/dictionaries/` : textes ajoutés dans les trois langues et catalogue source.
- `apps/site/test/discovery-refonte.test.ts` et `published-episode-route.test.ts` : critères du parcours et unicité du replay.
- `docs/SANDBOX_UX_STRATEGY.md`, les index de documentation et DD-0034 : décision et ordre des sections.

## Captures et limites

Captures locales dans `.local/refonte-captures/` :

- `home-v4-desktop.jpg` : arrivée sans onglets.
- `home-v4-team.jpg` : biographies sur ordinateur.
- `home-v4-projects.jpg` : sélection de projets.
- `home-v4-explore.jpg` : Time Machine et classements après les projets.
- `home-v4-mobile-team.jpg` : portrait et bio sur mobile.

Le plateau reste un photomontage provisoire. Les biographies présentent les réalisations connues ; des éléments de parcours pourront les enrichir plus tard. L'environnement de prévisualisation utilise les fixtures locales existantes pour les classements. Cette itération ne valide pas une publication distante ni les traductions par une relecture humaine. L'avertissement Next.js préexistant sur la convention `middleware` reste présent dans le build.

Aucun commit, push, PR ou déploiement n'a été effectué. La prochaine étape est la revue visuelle locale avec Lou.
