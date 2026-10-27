# Six pièces : recette locale du 20 octobre 2026

Suite à la demande de Lou, le mobile et les autres formats desktop ont ensuite été vérifiés et corrigés. La [recette responsive des six salles](six-rooms-responsive-2026-10-20.md) consigne 128 cas de disposition, 42 parcours tactiles, les redimensionnements WebGL et les contrôles complets réussis. Elle remplace le report du mobile mentionné dans cette première recette.

**25 cas desktop, 79 tests ciblés, le parcours WebGL et quatre modes de secours réussis.** `pnpm check` passe : formatage, lint, types et tests.

Dernière consigne de Lou : portail sur toute l'illustration, destination choisie dans les commandes contextuelles, ouverture au curseur et clic dans le décor pour traverser. L'ordinateur est prioritaire ; Lou a reporté le travail mobile. Les résultats antérieurs à cette correction ne valident pas le nouveau comportement.

Références : [DD-0070](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0070-six-pieces-portails.md), [direction des six pièces](sandbox-six-pieces-direction-2026-10-20.md), [décors et provenance](six-rooms-artwork-2026-10-20.md), [vision.md](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/vision.md).

## Réalisation locale

Le premier écran occupe 100 svh avec l'accroche seule dans le plateau. Aucun bouton n'y est visible au repos. Les six cartes sous le hero sont retirées ; les commandes de visite deviennent contextuelles au survol, avec un accès clavier. Le sélecteur « Les pièces », les liens vers l'émission et l'équipe et les liens sociaux se trouvent après ce premier écran. Sans JavaScript, six liens natifs donnent accès aux rubriques.

Le plateau, le vidéoclub, les classements, la Time Machine, le cinéma et le Radar forment un parcours à six destinations. Le scroll qui allumait et retournait le studio quitte l'accueil. Les commandes contextuelles choisissent la pièce à révéler. L'ouverture suit le curseur sur l'illustration ; au clic dans le décor, une caméra WebGL avance jusqu'au seuil puis rejoint le point de vue de destination.

La pièce de destination est orientée selon le rayon du point de vue de repos vers le portail. La caméra rejoint cette orientation pendant le trajet. Le changement de repère final conserve la position et la rotation relatives à la pièce ; le test compare aussi la projection de points placés à plusieurs profondeurs pour détecter un saut de perspective.

Les quatre nouveaux décors totalisent 896 612 octets en WebP. Les photographies du plateau et du vidéoclub sont conservées. Les quatre sorties générées ont été inspectées ; les prompts complets et la provenance figurent dans la documentation des décors.

Correction demandée après la première recette : renforcer le contraste entre le plateau et la salle visible derrière le portail. Le vidéoclub en cyan, néon rouge et graphite est intégré, avec la même géométrie de rayons : `/images/rooms/video-club-room-v2.webp`, 1672 × 941, 292 866 octets. Le parcours WebGL a été réexécuté avec ce décor. Les captures du portail à droite et du vidéoclub après arrivée ont été ouvertes : le contraste et l'alignement des pochettes sur les rayons sont vérifiés visuellement. La rubrique des projets utilise le même fichier. [Provenance et prompt](video-club-room-v2-2026-10-20.md).

Les contenus utilisables restent des liens HTML : projets existants, familles de classements, événements réels de la chronologie, replays publiés et fil News. Les classements et actualités détaillés restent dans leurs rubriques. Les salles ne présentent aucun faux score ni faux article.

La correction des contenus place les affiches dans les cadres du cinéma, répartit les projets dans les rayons du vidéoclub et conserve un seul moniteur interactif pour le Radar. Les captures de ces trois pièces ont été ouvertes et inspectées sur cette version. Les contrôles du catalogue complet, des états vides et de la pagination à trente replays passent dans la suite du site.

Les trois illustrations des blocs « Pour aller plus loin » utilisent désormais les mêmes WebP que la Time Machine, la salle des classements et le Radar. Aucun bloc cinéma ou vidéoclub distinct n'est présent dans cette section ; les visuels des fiches projet restent propres à chaque projet.

## Fichiers principaux

- `apps/site/src/components/sandbox-world.tsx` : contrôle de navigation, accès clavier, historique, reprise et parcours sans WebGL.
- `apps/site/src/components/sandbox-world-renderer.ts` : volumes projetés, cassettes, rendu du portail et déplacement de caméra.
- `apps/site/src/components/sandbox-world.module.css` : scène, surface globale d'interaction et commandes contextuelles de visite.
- `apps/site/src/components/sandbox-room-content.tsx` et son module CSS : objets HTML et contenus de chaque salle, pagination des replays.
- `apps/site/src/domain/sandbox-rooms.ts` : six salles, destinations et événements historiques sélectionnés.
- `apps/site/src/domain/sandbox-world-motion.ts` : placement du portail et trajectoire.
- `apps/site/public/images/rooms/` : nouveaux décors des classements, de la Time Machine, du cinéma et du Radar.

Les autres fichiers du lot concernent les illustrations de l'accueil, les traductions EN/ES/DE, la constante du décor du vidéoclub et les tests de navigation et de contenu.

## Contrôles exécutés sur les décors

| Contrôle                                         | Résultat                                                                                     |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| Inspection visuelle des quatre générations       | Réalisée : matériaux cohérents, cadres et écrans vierges, absence de texte éditorial généré. |
| Décodage et conversion en WebP avec Sharp        | Réalisés, qualité 87, sans recadrage ni redimensionnement.                                   |
| Dimensions                                       | 1672 × 941 pour classements, Time Machine et cinéma ; 1672 × 940 pour Radar.                 |
| Formatage des documents de provenance et prompts | Prettier exécuté.                                                                            |

## Résultats exécutés

Commande ciblée exécutée après la correction de rotation :

```powershell
pnpm --filter @podcast/site exec vitest run test/discovery-refonte.test.ts test/sandbox-world-motion.test.ts test/localization.test.ts test/published-episode-route.test.ts test/site-marketing.test.ts --reporter=dot
```

Résultat : **5 fichiers et 79 tests réussis**, sortie 0. Les tests couvrent notamment le plateau minimal, le sélecteur à six options, les six liens `noscript`, les commandes contextuelles masquées au repos, le canvas décoratif, les liens YouTube et Spotify, les routes d'épisodes et les coordonnées du portail. Le test de mouvement vérifie le départ depuis la pose réelle, le franchissement continu, la rotation progressive et la même projection avant/après changement de repère au centre et aux quatre coins. Des avertissements Next Image sur la qualité 90 et des messages de sitemap liés aux données simulées apparaissent dans la sortie ; ils ne provoquent pas d'échec.

La commande `node scripts/test-sandbox-world-responsive.mjs`, exécutée depuis `apps/site`, termine avec **25 cas réussis, aucune erreur JavaScript et aucun problème signalé** :

- 18 ouvertures directes : les six pièces à 1024 × 768, 1440 × 900 et 1920 × 1080.
- 6 cas à 1440 × 900 avec les tailles de texte doublées par CSS.
- 1 cas sans JavaScript à 1440 × 900.

Le navigateur est Edge en mode headless, sur `http://127.0.0.1:3100`, avec la préférence de réduction des mouvements. Cette recette vérifie la disposition et le parcours fixe ; elle ne valide pas le rendu WebGL. Le texte à 200 % est simulé en doublant les tailles calculées avant modification, sans utiliser le zoom natif du navigateur. Le contrôle de recouvrement compare les objets aux rectangles effectivement occupés par les textes et les actions, sans compter les espaces vides du conteneur de légende.

Les contrôles n'ont relevé ni débordement horizontal, ni contenu interactif coupé, ni recouvrement texte/objet, ni cible visible inférieure à 44 px, à la tolérance d'arrondi près. Le sélecteur contient six options, reçoit le focus avec un contour visible et reste après la scène. Les commandes contextuelles sont masquées au repos, le canvas porte `aria-hidden`, et le plateau initial ne présente aucun bouton visible.

Preuves locales, non destinées à Git :

- Rapport : `apps/site/.local/sandbox-world-responsive/report.json`.
- Sortie : `apps/site/.local/sandbox-world-responsive-run.log`.
- Captures ouvertes et inspectées : `1440x900-studio.png`, `1440x900-news.png`, `1440x900-cinema.png` et `1440x900-text200-projects.png`, dans `apps/site/.local/sandbox-world-responsive/`.

Le contrôle final `pnpm check` passe : formatage, ESLint, TypeScript, 143 fichiers de tests du site et 1 112 tests réussis, plus 35 tests des projets vidéo et du conducteur. Sortie : `apps/site/.local/six-rooms-check-final.log`.

La compilation finale `pnpm --filter @podcast/site build` passe également, code de sortie 0. Sortie : `apps/site/.local/six-rooms-build.log`.

La recette `node apps/site/scripts/test-sandbox-world.mjs`, exécutée depuis la racine avec WebGL actif à 1440 × 900 dans Edge, passe également. Elle vérifie l'aperçu du portail à gauche, à droite et en bas de l'illustration, l'arrivée dans les six pièces, le choix de destination au clavier, le focus sur le titre à l'arrivée, le retour navigateur, l'annulation par Échap avec restitution du focus sans rouvrir l'aperçu, l'absence de changement de pièce au scroll et l'ouverture directe du cinéma par hash. Aucune erreur de page ou de console n'a été relevée. Les captures et `browser-errors.json` sont dans `.local/sandbox-world/`. Le scénario enregistre une capture pendant le passage ; la continuité géométrique est couverte par les tests unitaires décrits plus haut.

Quatre scénarios de secours passent à 1440 × 900 dans Edge : WebGL indisponible dès le chargement, image du Radar refusée, perte du contexte au repos et perte pendant une traversée. Les six salles restent accessibles par le sélecteur sans WebGL ; les liens de projet et de replay ont été réellement ouverts. La perte pendant le trajet annule celui-ci et réactive le sélecteur. Aucune erreur JavaScript `pageerror` n'a été observée. Preuve : `apps/site/.local/rooms-polish/fallback-report.json`. Un premier délai dépassé lors de l'ouverture d'un replay n'a pas été reproduit dans le scénario isolé ni dans le second lot complet.

## Recette fonctionnelle

| Contrôle                                                             | Preuve prévue                                                               | État                                         |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------- |
| Ouverture directe des six pièces                                     | 18 cas desktop, captures et état de pièce attendu                           | Réussi avec mouvements réduits               |
| Ouverture au curseur sur toute l'illustration et clic pour traverser | Aperçus à gauche, à droite et en bas, puis entrée dans la destination       | Réussi avec WebGL                            |
| Choix de destination dans les commandes contextuelles                | Flèche droite au clavier, aperçu attendu puis entrée                        | Réussi avec WebGL                            |
| Continuité avant, pendant et après le seuil                          | Projection testée au centre et aux quatre coins ; capture de traversée      | Tests unitaires réussis, capture enregistrée |
| Retrait du scroll de transformation du studio                        | Scroll sans changement de pièce et absence de `data-scroll-studio`          | Réussi avec WebGL                            |
| Clavier, focus, Échap et retour navigateur                           | Navigation, titre focalisé à l'arrivée, annulation et retour au déclencheur | Réussi avec WebGL                            |
| Mouvements réduits sur ordinateur                                    | 18 ouvertures directes, liens visibles et sélecteur                         | Réussi pour la disposition et les accès      |
| Mobile et paysage tactile                                            | À reprendre dans une étape ultérieure                                       | Reporté à la demande de Lou                  |
| Textes agrandis à 200 %                                              | Six salles, tailles doublées par CSS                                        | 6 cas réussis                                |
| Sans JavaScript                                                      | Six liens natifs `noscript` et canvas décoratif                             | 1 cas réussi                                 |
| Échec d'image ou indisponibilité WebGL                               | Quatre interruptions simulées, navigation et clics de contenu               | 4 cas réussis                                |
| Projets réels, jalons historiques et routes de classement            | `apps/site/test/sandbox-room-content.test.ts`                               | Réussi dans `pnpm check`                     |
| Tous les projets dans les rayons                                     | Comparaison avec le catalogue transmis, absence d'omission et de doublon    | Réussi dans `pnpm check`                     |
| Affiches dans les cadres et Radar sur un seul moniteur               | Captures 1440 × 900 ouvertes et inspectées                                  | Vérifié visuellement                         |
| Deux replays actuels, sans doublons de remplissage                   | Rendu du cinéma et test du contenu                                          | Réussi dans `pnpm check`                     |
| Pagination de trente replays                                         | Jeu de test, première et dernière pages, collection complète accessible     | Réussi dans `pnpm check`                     |
| Filtrage des brouillons et épisodes sans vidéo                       | Test du contenu                                                             | Réussi dans `pnpm check`                     |
| Collection vide et dernière page incomplète                          | Test du contenu                                                             | Réussi dans `pnpm check`                     |
| Localisation EN, ES et DE                                            | Test du contenu et routes localisées                                        | Réussi dans `pnpm check`                     |
| Trajectoire, rotation et changement de repère                        | `apps/site/test/sandbox-world-motion.test.ts`, inclus dans les 79 tests     | Réussi                                       |
| `pnpm check`                                                         | Sortie de commande, code de sortie 0                                        | Réussi                                       |

Les preuves de disposition, du parcours WebGL, des modes de secours et de la suite complète sont distinctes ; aucune de ces vérifications ne vaut mesure de performance sur appareil physique.

## Limites connues

Les photographies sont projetées sur cinq faces d'une pièce. Le vidéoclub ajoute des cassettes en volume. Les meubles des photographies ne disposent pas chacun d'une géométrie ni de faces cachées. Le déplacement reste limité à une légère variation de point de vue et aux traversées de 1,8 seconde ; aucune marche libre ou rotation complète n'est proposée.

La réalisation utilise WebGL et ne contient pas de Gaussian splatting. La comparaison avec la référence doit porter sur l'ouverture disponible sur toute l'illustration, la vue derrière le décor et la continuité pendant la traversée, sans annoncer une équivalence volumétrique.

Le parcours de remplacement utilise un décor fixe lorsque le moteur ne s'active pas, notamment en dessous de 901 px, avec un pointeur non fin ou avec les mouvements réduits. La recette mobile est reportée par Lou ; l'existence de ce remplacement ne constitue pas une validation mobile. Les mesures de GPU, de mémoire, de FPS et la fluidité sur téléphone physique restent à réaliser. Aucun score de performance n'est déduit de l'aspect des captures.

Le relevé de deux replays décrit la collection locale au moment de cette recette. Le jeu de trente épisodes est synthétique et réservé aux tests de pagination.

## Suite

Revue visuelle desktop par Lou, puis adaptation mobile dans une étape séparée. Le lot reste local, sans commit, push, PR ni déploiement.
