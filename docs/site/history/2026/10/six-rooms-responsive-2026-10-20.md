# Six salles : vérification mobile et desktop

20 octobre 2026. Lou demande de vérifier avec Playwright les tailles d'écran mobiles et desktop. Cette demande reprend le travail mobile précédemment reporté dans [DD-0070](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0070-six-pieces-portails.md).

## Défauts observés et corrections

La première matrice couvre les six salles sur vingt formats, de 320 à 3 440 pixels de large. Elle met en évidence trois défauts :

- Sur téléphone et tablette, les rayons du vidéoclub chevauchent la légende ; les baies les plus hautes dépassent parfois le haut de la scène.
- Sur tablette en portrait, le cadrage desktop coupe des projets, des jalons historiques et le terminal du Radar.
- Au cinéma, certaines affiches sortent du cadre en paysage court et sur les écrans très larges.

Les collections occupent maintenant le flux normal sur les petits écrans et les cadrages dont le rapport largeur/hauteur est inférieur à 6/5. La légende suit les objets. Les trois baies restent accessibles dans un rail horizontal et s'alignent par le haut. Le plateau d'entrée conserve une hauteur minimale correspondant au viewport.

Les affiches du cinéma choisissent leurs cadres d'après les dimensions réelles de la scène, avec une requête de conteneur CSS. Leur cible mesure au moins 44 pixels de large. Les anciennes dimensions fixes destinées aux écrans bas sont retirées : elles agrandissaient les cassettes au point de faire chevaucher deux rangées en paysage.

Le contrôle des intersections entre objets détecte également deux jalons historiques latéraux qui recouvrent leurs voisins entre 901 et 1 024 pixels de large. Sur les fenêtres desktop jusqu'à 1 200 pixels, ces deux jalons descendent vers le pupitre au premier plan.

Le moteur WebGL utilise le même seuil de cadrage que la mise en page. Il se désactive lorsque la fenêtre passe en portrait étroit et se réactive en paysage compatible. La pièce sélectionnée est conservée. Le parcours tactile conserve ses contenus HTML et son sélecteur, sans dépendre du survol.

Ces corrections locales et réversibles sont décidées par l'agent sur délégation (PD-0003). Les contenus et les routes publiques ne changent pas.

## Matrice de disposition

Script : `node apps/site/scripts/test-sandbox-world-responsive.mjs --include-mobile`.

| Groupe                              | Dimensions testées                                                               |
| ----------------------------------- | -------------------------------------------------------------------------------- |
| Téléphones et petits écrans         | 320 × 568, 360 × 640, 375 × 667, 390 × 844, 430 × 932                            |
| Tablettes et formats intermédiaires | 600 × 960, 768 × 1024, 820 × 1180, 900 × 700, 901 × 700, 1024 × 768, 1024 × 1366 |
| Paysage court                       | 844 × 390, 932 × 430                                                             |
| Desktop                             | 1280 × 720, 1366 × 768, 1440 × 900, 1920 × 1080                                  |
| Écrans larges                       | 2560 × 1080, 3440 × 1440                                                         |

Chaque format ouvre les six salles. Le script mesure les débordements horizontaux, les contrôles coupés, les chevauchements avec les légendes et entre les objets, les cibles de moins de 44 pixels et le focus du sélecteur. Il ajoute les six salles avec un texte agrandi à 200 % par CSS, un parcours tactile et une ouverture sans JavaScript : 128 cas au total.

Résultat final : **128 cas, aucune erreur JavaScript ni anomalie géométrique détectée**, code de sortie 0. Les captures du vidéoclub mobile, de la Time Machine à 901 pixels et du cinéma à 3 440 pixels ont notamment été ouvertes pour vérifier les corrections visuellement.

## Navigation et redimensionnement

Le script `apps/site/scripts/test-sandbox-world.mjs` passe avec WebGL actif. Il traverse les six pièces, place le portail à plusieurs endroits, vérifie le clavier, Échap, le retour navigateur et les URL de salle. Il ajoute quatre traversées après redimensionnement : 901 × 700, 1366 × 768, 2560 × 1080 et 3440 × 1440. Le passage à 1024 × 1366 désactive WebGL ; le retour à 1366 × 768 le réactive en conservant la salle.

Les 24 parcours tactiles en 320 × 740, 390 × 844, 768 × 1024 et 844 × 390 passent après correction. Les tests ouvrent réellement les fiches de projet, les classements, un jalon historique, les replays et les actualités. Ils vérifient aussi les pages suivantes des projets, les deux replays à 320 pixels et une rotation portrait/paysage/portrait. Aucun débordement horizontal global ni erreur JavaScript n'a été relevé sur ce lot.

Les parcours tactiles passent aussi en 932 × 430, 1024 × 1366 et 1366 × 1024, pour un total de 42 cas sur sept formats. Deux attentes de navigation vers les classements ont expiré lors de la première passe des grands formats. Le contrôle isolé vérifie ensuite que le toucher atteint le bon lien et que les requêtes RSC répondent HTTP 200 ; les douze parcours concernés repassent avec le même critère d'attente initial. La cause des délais initiaux reste indéterminée, sans défaut CSS ou serveur démontré.

Le contrôle final `pnpm check` passe : formatage, lint, TypeScript et 1 112 tests du site dans 143 fichiers, plus les 35 tests vidéo et conducteur. La compilation `pnpm --filter @podcast/site build` passe aussi. Les deux commandes terminent avec le code 0 ; sorties dans `apps/site/.local/responsive-check.log` et `apps/site/.local/responsive-build.log`.

## Fichiers et preuves

- `sandbox-world.tsx` et `sandbox-world.module.css` : seuil du rendu, scène et dimension de livraison de la photographie.
- `sandbox-room-content.module.css` : collections dans le flux, placement des affiches, dimensions des cassettes et des cibles.
- `test-sandbox-world-responsive.mjs` et `test-sandbox-world.mjs` : matrices et vérification du redimensionnement.
- `apps/site/.local/sandbox-world-responsive/report.json` et captures associées.
- `apps/site/.local/rooms-touch-audit/report.json` : 24 parcours tactiles.
- `apps/site/.local/rooms-touch-large-audit/report.json` : 18 parcours supplémentaires et les deux délais initiaux conservés.
- `apps/site/.local/rooms-touch-large-recheck/report.json` : reprise réussie des douze parcours concernés.
- `apps/site/.local/rooms-touch-large-audit/charts-diagnostic.json` : contrôle du toucher et des réponses réseau.
- `.local/sandbox-world/resize-report.json` et `browser-errors.json` : redimensionnement WebGL.

L'audit des blocs situés sous les salles et du menu est consigné séparément dans [la recette de l'accueil](accueil-responsive-2026-10-20.md).

## Limites

Les tests utilisent Edge piloté par Playwright, avec émulation du viewport et du tactile. Ils ne constituent pas une recette Safari sur iPhone physique ni une mesure de fluidité sur du matériel mobile. Le texte à 200 % est simulé par CSS. Les vingt formats et les deux orientations couvrent les cas testés ; ils ne prouvent pas toutes les dimensions possibles.

Le travail reste local, sans commit, push ni publication.
