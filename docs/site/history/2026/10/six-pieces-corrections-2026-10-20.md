# Corrections de la visite du 20 octobre 2026

Complément à [DD-0070](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0070-six-pieces-portails.md) et à la [recette responsive](six-rooms-responsive-2026-10-20.md). Travail local, sans commit ni publication. Les ajustements de conception sont décidés par l'agent sur délégation (PD-0003), à partir des corrections de Lou.

## Portail et première vue

La destination ne suit plus le curseur. Seule l'ouverture se déplace : à gauche et à droite, elle révèle des portions différentes du vidéoclub. Une caméra distincte conserve le cadrage de la destination dans l'aperçu, au franchissement du seuil et à l'arrivée. La caméra de départ traverse le point cliqué. Cette composition en 2,5D évite d'exposer les faces absentes de la photographie ; elle ne constitue pas une exploration libre d'un lieu entièrement modélisé.

Le contrôle du même carré de 10 × 10 pixels, révélé par deux ouvertures différentes, mesure un écart moyen de 0,67 sur 255. Les captures gauche, droite et traversée ont été inspectées après suppression des prolongements étirés. Preuves : `apps/site/.local/fixed-room/report.json` et captures du même dossier. Les 24 tests de trajectoire et de projection passent.

L'accroche est inscrite sur la façade du bureau. Le texte reste un H1 en HTML, placé dans les coordonnées de l'image plutôt que dans un coin de la fenêtre. Sept formats ont été vérifiés, de 320 × 740 à 3440 × 1440 : position dans la façade, texte visible et absence de débordement. Preuves : `apps/site/.local/desk-inscription-audit/`.

Le bandeau de liens dispersés est remplacé par « Explorer les pièces », fermé au départ et placé après la scène. Son panneau contient le sélecteur natif des six pièces et le réglage des mouvements. Échap ferme le panneau ou annule une traversée et rend le focus à une commande visible. Les accès aux émissions, à l'équipe et aux réseaux restent dans les rubriques et le pied de page général.

## Contenus et salles

Le bloc équipe de l'accueil ne répète plus les trois prénoms dans son en-tête. Le paragraphe « Deux développeurs et un Product Manager. Nous confrontons… » et la phrase sous « Ce que nous construisons » sont retirés de toutes les versions linguistiques. Les portraits, noms et biographies restent présents. Sur `/about`, les deux paragraphes d'introduction s'alignent sur toute la largeur de la grille des portraits : 1232 pixels à une fenêtre de 1440 pixels, 358 pixels à une fenêtre de 390 pixels. Contrôle des quatre langues : `apps/site/.local/copy-layout/report.json`.

Le cinéma utilise une nouvelle illustration avec six cadres frontaux et rectangulaires. Les deux derniers replays publiés sont visibles simultanément, y compris à 320 pixels. Le contrôle de pagination n'apparaît que si la collection dépasse la capacité affichée ; ses boutons portent des libellés explicites. Les deux épisodes locaux sont conservés, sans contenu fictif ajouté. Six formats vérifiés : 320, 390, 1024, 1440, 1920 et 3440 pixels ; aucune affiche hors écran ni débordement. Preuves : `apps/site/.local/cinema-v2-review/`.

La salle Time Machine présente les 162 événements du corpus de 1996 à 2026, dans l'ordre chronologique. Une vue d'ensemble continue situe les événements ; cinq périodes donnent accès au rail et au détail avec ses sources. Les flèches, Début et Fin permettent de parcourir le corpus au clavier sans déplacer la page. La frise et la légende partagent le flux de mise en page : la frise défile à l'intérieur lorsque la hauteur manque. À moins de 600 pixels, les périodes occupent deux colonnes pour garder leurs noms lisibles. Preuves : `apps/site/.local/history-room-audit/` et `sandbox-world-responsive-history-final/`.

La [langue automatique](browser-locale-2026-10-20.md) s'applique à l'entrée par `/` : le choix manuel conservé dans un cookie prime sur les langues du navigateur. Les variantes EN, ES et DE ouvrent leur accueil ; le français sert de repli. Les URL explicites restent respectées. Les tests couvrent les poids de `Accept-Language`, les cookies invalides et les exclusions de routes. La recette Edge vérifie les quatre arrivées et la persistance des choix français et allemand. Preuves : `apps/site/.local/browser-locale/report.json`.

## Clics des classements

Le blocage signalé n'a pas été reproduit. Vingt-quatre clics réels ont ouvert la bonne page avec son titre : les quatre familles, avec WebGL ou mouvements réduits, directement ou après ouverture du portail, à 1024, 1440 et 1920 pixels. Les liens recevaient bien le clic au-dessus de la surface globale. GitHub et Skills ont aussi été ouverts dans l'onglet existant du navigateur intégré.

Preuves : `apps/site/.local/rankings-click-audit/`, `rankings-hover-click-audit/`, `rankings-click-sizes-audit/`. Aucun changement spéculatif de ces liens n'a été ajouté.

## Prévisualisation locale

Le serveur de développement s'est bloqué pendant la recette et a été relancé sur le port 3100. Le premier redémarrage utilisait le fichier éditorial par défaut, qui contient un seul épisode. Les variables de prévisualisation ont ensuite été rétablies pour charger `.local/studio-content.json`, où les deux épisodes sont publiés. Aucun fichier éditorial n'a été modifié pour ajouter un replay.

Le serveur local utilise aussi le cache News existant du 18 octobre en mode prévisualisation. Cette recette ne vérifie pas la fraîcheur du fil de production et n'a pas besoin d'une connexion Postgres.

## Contrôles

Le menu a été vérifié au clavier et au pointeur à 320, 390 et 1440 pixels. La matrice finale valide 128 cas : 107 cas conservés, puis les 21 cas histoire repris après correction des périodes mobiles et du texte agrandi à 200 %. Deux contrôles supplémentaires tactile et sans JavaScript ont également été répétés. La reprise finale compte 23 cas sans erreur ni anomalie. Preuves : `apps/site/.local/room-explorer/`, `sandbox-world-responsive/` et `sandbox-world-responsive-history-final/`.

La recette WebGL finale passe sur la version stabilisée : aperçu à gauche, à droite et en bas, visite des six salles, sélection clavier, focus à l'arrivée, retour navigateur, Échap depuis le menu, défilement, ouverture par hash, quatre redimensionnements de 901 à 3440 pixels et retour du mode portrait au mode WebGL. Aucune erreur navigateur relevée. Preuves : `apps/site/.local/immersive-corrections-webgl.log`, `.local/sandbox-world/browser-errors.json` et `resize-report.json`. L'échec de contexte WebGL observé pendant les modifications à chaud n'a pas été reproduit lors de cette passe stabilisée.

Les essais mobiles utilisent l'émulation Edge et ne remplacent pas une recette sur appareils physiques.

## Fichiers concernés

Le lot est réparti entre les composants `sandbox-world`, son renderer et `sandbox-room-content`, le domaine et les tests des salles et des trajectoires, les décors de `public/images/rooms`, la transmission des données depuis l'accueil et les dictionnaires. Les suppressions de texte concernent `discovery-story` et son CSS ; la largeur de l'introduction équipe est définie dans `site-polish.css`. La langue automatique concerne `proxy.ts`, `domain/browser-locale.ts` et le sélecteur de `nav.tsx`. Les scripts Playwright `test-sandbox-world.mjs` et `test-sandbox-world-responsive.mjs` conservent la recette reproductible.

## Résultat final

`pnpm check` réussit après les corrections : format, ESLint, génération des types, TypeScript et tests. Les 144 fichiers de tests du site comptent 1148 tests réussis ; les autres suites du dépôt passent également. Le test de l'accueil qui attendait encore trois affiches a été actualisé pour vérifier les deux derniers replays et l'accès aux suivants. Log : `apps/site/.local/immersive-corrections-check.log`.

`pnpm --filter @podcast/site build` réussit, avec génération des routes et du proxy. Log : `apps/site/.local/immersive-corrections-build.log`. La recette WebGL finale se termine avec un code de sortie nul et `browser-errors.json` vide. Le lot est finalisé en local ; aucun commit, push, PR ni déploiement n'a été effectué.
