# Refonte locale de l'accueil du 16 octobre 2026

Demande de Lou : améliorer la beauté, l'identité et les animations de la landing, puis vérifier son ergonomie. Décision : [DD-0049](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0049-accueil-cinematique-et-mouvements.md).

Prévisualisation : http://127.0.0.1:3219/.

Les captures ont été faites sur la version compilée, servie temporairement à l'adresse locale http://127.0.0.1:3220/. Son catalogue d'épisodes était vide ; le bouton "Découvrir l'émission" est donc affiché. La prévisualisation de développement conserve l'épisode disponible dans son environnement. Aucun contenu n'a été supprimé. Le serveur temporaire a été arrêté après les captures.

## Réalisation

- Plateau composé comme une affiche, titre Newsreader et italique cyan, action distincte et lien visible vers la suite.
- Défilement natif, hauteur stable, entrée de scène courte et profondeur au pointeur sur ordinateur.
- Défilement doux signalé à Next.js dans les deux layouts racines : il reste actif pour les ancres et se désactive pendant les changements de page.
- Chapitres numérotés, collection d'animateurs tactile, projets animés par transformations, deux destinations visuelles et replay final.
- Commande commune de réduction des mouvements, préférence système, navigation clavier et contenu disponible sans JavaScript.
- Quatre nouveaux textes traduits en anglais, espagnol et allemand. La promesse française et le paragraphe de présentation sont conservés.

Les illustrations, portraits, biographies, liens et données métier existants sont réutilisés, hormis les deux illustrations d'exploration décrites plus bas. Aucun contenu distant n'est modifié. Aucune dépendance n'est ajoutée.

## Contrôles

Première recette exécutée le 16 octobre 2026 sur la copie locale :

- `pnpm check` : réussi après les derniers correctifs. Formatage, ESLint et TypeScript valides ; 678 tests du site dans 106 fichiers, 7 tests de l'introduction vidéo, 4 tests des jingles et 22 tests du projet BIS passent, soit 711 tests.
- `pnpm --filter @podcast/site exec next build --webpack` : réussi, 203 pages statiques générées.
- `git diff --check` : réussi.
- Navigateur Codex : douze formats contrôlés, de 320 × 740 à 3 440 × 1 440, dont les seuils 900/901 et 1 100/1 101 pixels. Aucun débordement horizontal, titre dégagé des portraits et action principale contenue dans la scène. Le rail mobile conserve son propre défilement horizontal.
- Zones du décor : clics de la voiture contrôlés sur cinq formats d'ordinateur, y compris deux écrans panoramiques. L'en-tête transparent laisse passer les interactions. Les destinations Time Machine et vidéoclub ont été ouvertes ; la porte mène bien au vidéoclub après sa transition.
- Navigation : depuis le panneau des classements, la page Sandbox Charts s'ouvre en haut, sans déplacement animé hérité de la position dans l'accueil.
- Équipe : lien "La suite", défilement du rail à la flèche droite et ouverture de la biographie de Loïc vérifiés.
- Projets : boutons précédent/suivant, touche End, destination sélectionnée et maintien du focus vérifiés. Les trois panneaux gardent la même largeur et la même hauteur ; leur transition porte sur transform.
- Pause : toutes les révélations deviennent visibles, le carrousel passe en pause, les trois cartes réinitialisent leurs reflets et leur inclinaison, leurs transitions passent à zéro.
- Langues : titres anglais, espagnol et allemand vérifiés à 390 pixels, sans débordement. Le français est couvert par la matrice complète.

Le débordement des cartes en perspective sur les petits écrans a été corrigé pendant cette recette avec un confinement visuel du rail. La préférence système de réduction des mouvements est traitée dans le code et les styles ; seule la commande de pause de la page a été essayée dans le navigateur. Les tests du rendu serveur vérifient que le contenu est livré visible avant JavaScript. Les scripts de recette navigateur du dépôt ont été adaptés, mais les essais interactifs ont été exécutés avec le navigateur Codex, sans lancer ces scripts.

## Seconde passe

Lou a demandé de poursuivre après le premier aperçu. Le plateau, la collection et les projets sont reliés par un fil lumineux au défilement. Les titres, les cartes, la galerie et les panneaux ont chacun leur entrée. Les cartes de collection s'ouvrent en éventail sur ordinateur et verticalement sur téléphone. Les halos et les contacts restent discrets, sans animation permanente.

La géométrie du fil ignore les transformations des révélations. Les changements de taille, de police et l'ouverture d'une biographie recalculent les raccords. Un défilement ne relit aucune géométrie. Chaque portion du fil reste limitée à la hauteur de son chapitre.

Contrôles après intégration de cette passe :

- `pnpm check` : réussi. Formatage, lint et types valides ; 686 tests du site dans 107 fichiers et 33 tests des autres projets, soit 719 tests réussis.
- Build Next.js avec webpack : réussi, 203 pages statiques générées.
- Sept formats supplémentaires contrôlés pour le fil : 320, 390, 900, 901, 1 100, 1 280 et 1 920 pixels de largeur, dont le paysage court en 1 100 x 540. Aucun débordement horizontal. Les raccords mesurés restent à moins d'un pixel des contacts.
- Ouverture et fermeture de la biographie de Lou : le fil suit la nouvelle hauteur. Le raccord au chapitre suivant reste à moins d'un pixel du contact.
- Focus clavier sur le panneau Time Machine encore en attente : contenu immédiatement visible, sans translation ni animation.
- Pause globale : les onze révélations deviennent visibles ; translation, rotation, échelle, masque et animation sont supprimés. Seul le câble décoratif fixe reste affiché.
- Captures réelles du navigateur sur le build local : parcours ordinateur de 15 secondes et parcours mobile de 20 secondes. Encodage H.264 à 24 images par seconde pour la consultation dans la conversation. Cette cadence est celle des aperçus, pas une mesure de performance du site.
- Lecture complète des deux vidéos vérifiée dans le lecteur isolé de prévisualisation, dont la version portrait à 390 pixels. Aucun échec de décodage ni débordement du lecteur mobile.

Les fichiers des captures restent dans le dossier de cette conversation, hors du dépôt. Les lecteurs utilisent les vidéos enregistrées, sans reconstitution de l'interface.

## Périmètre

Après ces deux passes, Lou demande de nouvelles illustrations pour Explorer l'IA, puis précise une direction photoréaliste. La Time Machine présente un assemblage de scènes du passé, du présent et d'un futur imaginé. Les classements présentent trois fiches en papier numérotées. Les sources, prompts et contrôles sont détaillés dans [le rapport des illustrations](illustrations-exploration-2026-10-16.md).

Les composants concernés sont `DiscoveryHome`, `DiscoveryStory`, `CinematicStage`, `HomeMotion`, `HomeSignal`, `HomeHostCard` et `HomeProjectSpotlight`, leurs styles et leurs tests. Les calculs du fil sont isolés dans `domain/home-signal.ts`. Les deux layouts racines reçoivent l'attribut de gestion du défilement. Les dictionnaires reçoivent seulement les nouvelles chaînes de cette refonte. Les autres modifications présentes dans la copie de travail appartiennent à des lots précédents ou à d'autres travaux.

Les essais locaux ne constituent pas une mesure de performance en production ni un audit complet avec lecteur d'écran. Le serveur de développement ajoute ses propres scripts.

## Préparation de la PR

Le 16 octobre, Lou demande de tout vérifier puis de créer une PR. Le lot de l'accueil est repris sur une branche isolée issue de `origin/main`. Les changements de collecte, d'indexation et de mesure déjà proposés dans la PR 72 restent dans leur propre lot.

Les trois revues finales couvrent la direction artistique, les mouvements et l'ergonomie. Elles détectent un conflit entre l'animation d'entrée et l'effacement du titre pendant l'ouverture du vidéoclub. L'animation ne conserve plus son état final et ne s'applique plus pendant l'ouverture. Le contrôle réel dans le navigateur confirme une opacité nulle du titre pendant la transition, puis l'arrivée dans le vidéoclub.

Les résultats de la recette sur cette branche sont consignés dans [le rapport de vérification avant PR](verification-landing-pr-2026-10-16.md).
