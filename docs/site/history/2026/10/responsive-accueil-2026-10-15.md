# Accueil et responsive : vérification locale du 15 octobre 2026

Demande de Lou : placer les classements en premier sur l'accueil, corriger le mobile et vérifier les fronts dans un navigateur sur localhost. Time Machine reste à l'autre tâche, conformément à sa réponse explicite. Décision : [DD-0028](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0028-accueil-classements-et-navigation-mobile.md).

## Résultat

L'accueil affiche le classement interactif avant les podcasts dans les quatre langues. Les filtres se restaurent au rechargement. Un seul titre de niveau 1 décrit la page ; le titre de l'épisode passe au niveau 2.

Le menu mobile remplace les liens comprimés jusqu'à 1024 px, avec recherche, liens de 48 px, fermeture après navigation et par Échap. Sur les petits écrans, le mouvement des classements se place sous le score, les filtres occupent la largeur disponible et les titres longs se répartissent sur plusieurs lignes. Les onglets de l'administration passent à la ligne. Les champs mobiles gardent une taille de texte de 16 px.

## Vérifications exécutées

Playwright utilise Edge Chromium sur une base PGlite éphémère, avec un épisode publié de test, des noms de projets longs et des comptes réservés à cet aperçu. Les requêtes du navigateur vers les services tiers sont bloquées. Le contenu local de test est isolé dans `.local/front-content.json` ; le fichier éditorial habituel n'est pas écrasé. Un test vérifie que ce drapeau de prévisualisation est ignoré en production.

| Contrôle                                                                            | Résultat |
| ----------------------------------------------------------------------------------- | -------- |
| 20 routes publiques et administration, largeurs 320, 375, 390, 768, 1024 et 1440 px | 120/120  |
| 34 fiches projets, largeurs 320 et 390 px                                           | 68/68    |
| Dernière passe des six pages retouchées, aux six largeurs                           | 36/36    |
| Parcours interactifs à 320, 390 et 1440 px                                          | 21/21    |
| Tests ciblés sur les changements, sept fichiers                                     | 49/49    |
| Suite complète Vitest, 75 fichiers                                                  | 465/465  |
| `pnpm typecheck`                                                                    | Réussi   |
| `pnpm build` (compilation de production et génération de 214 pages)                 | Réussi   |
| ESLint ciblé sur les fichiers modifiés par cette tâche                              | Réussi   |

Les parcours interactifs vérifient l'ordre de l'accueil, le menu, les filtres et détails de classement, le lien vidéo vers un chapitre, la recherche vide et sa réinitialisation, la galerie, les sections d'administration, une réponse serveur 503 suivie d'une nouvelle tentative et un refus 403 de publication pour un compte en lecture seule.

Les contrôles de pages vérifient les réponses HTTP, les titres, les erreurs JavaScript et les débordements horizontaux. Aucun débordement ni erreur JavaScript n'a été relevé dans les passes finales. Les captures mobile et ordinateur ont été inspectées visuellement. La première passe avait trouvé un manque de styles sur le classement intégré à l'accueil : l'import a été ajouté, puis les pages concernées ont été revérifiées.

`pnpm check` a été exécuté. Au moment de cette vérification, sa dernière relance s'arrête sur le formatage de trois fichiers Time Machine en cours de réécriture : `time-machine-chart.tsx`, `time-machine.tsx` et `domain/time-machine.ts`. Le lancement séparé de `pnpm lint` relève 42 erreurs dans quatre fichiers de cette rubrique (`time-machine-chart.tsx`, `time-machine.tsx`, `domain/time-machine-export.ts` et `domain/time-machine.ts`). Ces fichiers restent à la tâche désignée par Lou ; aucun gate n'a été désactivé. Les tests Vitest ont dû être relancés hors du bac à sable Windows, qui empêchait leurs workers de retrouver les fichiers temporaires ; cette relance complète réussit.

## Reproduire

Depuis la racine du dépôt :

```powershell
pnpm --filter @podcast/site dev:fronts
```

Le serveur écoute sur `http://127.0.0.1:3317`. Dans un autre terminal, avec Playwright installé ou accessible via `SANDBOX_PLAYWRIGHT_PATH` :

```powershell
$env:SANDBOX_PLAYWRIGHT_PATH = 'C:/Users/Lou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'
pnpm --filter @podcast/site test:fronts
pnpm --filter @podcast/site test:fronts:interactions
```

`SANDBOX_TEST_PATHS`, `SANDBOX_TEST_WIDTHS` et `SANDBOX_TEST_REPORT` permettent une passe ciblée du premier script. Les rapports et captures se trouvent dans `apps/site/.local/fronts/` (`report.json`, `projects.json`, `final-changes.json`) et `apps/site/.local/front-interactions/`. Ces fichiers sont locaux et ignorés par Git.

## Fichiers concernés et limites

- Accueil et navigation : `src/app/(fr)/page.tsx`, `src/components/shared-pages.tsx`, `nav.tsx`, `shell.tsx`.
- Responsive : `src/app/site-polish.css`, `src/components/charts-compact.module.css`, `admin-charts.css`.
- Aperçu isolé : `src/lib/admin-persistence.ts`, `scripts/badges-fixture-server.mjs`, `scripts/fronts-local.mjs`, `package.json`.
- Vérifications : `scripts/test-fronts.mjs`, `scripts/test-front-interactions.mjs`, `test/admin-local-fixture.test.ts`, `public-navigation.test.ts`, `published-episode-route.test.ts`, `localization.test.ts`.
- Documentation : cette page, DD-0026, les index de documentation et de tests.

Cette validation porte sur Chromium et ses dimensions mobiles simulées. Elle ne remplace pas un essai sur Safari iOS ou un téléphone physique. Le chargement de l'iframe vidéo est testé ; la lecture réelle du service distant ne l'est pas. Time Machine et son Wrapped sont exclus du périmètre confié à cette tâche. Aucun commit, push ou déploiement n'a été effectué. Après intégration de l'autre tâche, relancer `pnpm check` pour disposer d'un résultat global sans réserve.
