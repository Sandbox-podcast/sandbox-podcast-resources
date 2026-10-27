# Ouverture des classements depuis la salle

20 octobre 2026. Lou constate environ cinq secondes entre le clic sur GitHub et l'ouverture du classement. Le journal du serveur local confirme une requête de 5,3 secondes, dont 4,5 secondes de compilation Next.js en développement, 718 ms de préparation des paramètres et 57 ms de code applicatif. La requête suivante prend 72 ms. Skills présente le même profil : 4,4 secondes au premier passage, dont 3,9 secondes de compilation, puis 118 ms.

## Correction

Les quatre liens de la salle demandent désormais un préchargement complet avec `prefetch={true}`. En production, Next.js prépare la route et ses données quand le lien devient visible. Dans le serveur de développement, où ce mécanisme est désactivé, l'entrée dans la salle lance quatre requêtes HEAD pour préparer la compilation avant le clic. Les URL suivent la langue active. Le préchargement reste facultatif pour la navigation et ses requêtes sont annulées au démontage.

Un état « Ouverture du classement… », traduit dans les quatre langues, apparaît sur le terminal dès que la navigation commence. Le retour visuel reste dans le terminal : une frontière de chargement commune aux routes a été écartée lors de la recette d'intégration, car elle envoyait les en-têtes HTTP avant la détection des archives absentes et transformait leurs statuts 404 en 200. Le clic conserve ainsi un retour visible lorsque le réseau ou le serveur tarde.

Cette correction est locale et réversible, décidée par l'agent sur délégation (PD-0003). Elle ne modifie ni les données des classements ni leurs règles de publication.

## Mesure après correction

La recette utilise Edge, une fenêtre neuve pour chaque famille et le même serveur local sur le port 3100. Elle attend la préparation des quatre routes avant le clic, puis attend le vrai titre de destination. Il s'agit donc d'un délai après préchargement, à distinguer d'une première compilation à froid.

| Classement | Clic → titre affiché |
| ---------- | -------------------: |
| GitHub     |               862 ms |
| Skills     |               420 ms |
| Models     |               339 ms |
| Rising     |               247 ms |

La préparation de la salle et des quatre routes a pris 10,3 secondes dans le premier contexte, puis entre 1,5 et 2,6 secondes dans les suivants. Le coût initial de compilation en développement est déplacé en amont ; il n'est pas supprimé.

Un second scénario bloque volontairement la requête de navigation. Le statut d'ouverture apparaît en 109 ms ; après libération de la requête, le bon classement et son titre sont affichés. Aucune erreur JavaScript relevée.

Script reproductible : `apps/site/scripts/test-room-rankings-navigation.mjs`. Mesures : `apps/site/.local/rankings-navigation-performance/report.json`. Les résultats ne constituent pas une mesure de production ni une garantie de temps sous tous réseaux.

## Validation du lot

`pnpm check` réussit : format, lint, TypeScript, 144 fichiers et 1154 tests du site, ainsi que les autres suites du dépôt. La compilation `pnpm --filter @podcast/site build` réussit également. Les journaux sont `apps/site/.local/cinema-posters-navigation-check.log` et `cinema-posters-navigation-build.log`. Travail local ; aucune publication.
