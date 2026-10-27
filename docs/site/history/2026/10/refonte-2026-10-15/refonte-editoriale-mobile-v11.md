# Accueil V11, 16 octobre 2026

Lou demande une refonte complète du mobile, retire le montage de l'ouverture et confirme le maintien du plateau avec sa porte cachée sur ordinateur. Voir [DD-0039](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0039-accueil-mobile-editorial-et-plateau-desktop.md).

## Changements

L'ouverture compacte est reconstruite autour du titre de Lou, avec un fond ivoire, une grande typographie Newsreader et une action sombre. Le montage des trois personnes est masqué ; aucune miniature composée ne le remplace. Les liens YouTube et Spotify précèdent la vignette du vidéoclub. Le plateau, son cadrage et son ouverture de porte restent affichés sur grand écran.

Les biographies utilisent leurs photos sources dans des cadres distincts. Les projets sont regroupés dans une section sombre. Les titres, les espacements, les actions, l'exploration et le replay sont repris. Le texte de Lou, les liens et la sélection de projets sont conservés. Aucun visuel n'est généré ni retouché.

Fichiers concernés : `discovery-home.tsx`, `discovery-home.module.css`, les styles communs `site-polish.css`, le sélecteur d'accueil de `analytics-consent.module.css` et `discovery-refonte.test.ts`. Les contrôles de rendu devenus propres à l'ancienne miniature sont remplacés par des contrôles du bouton principal, des photos sources dans les biographies et des deux accès au vidéoclub. Les autres tests fonctionnels sont conservés.

## Vérifications

Les 19 tests ciblés de découverte passent. Le navigateur intégré est testé avec Playwright à 320 x 740, 390 x 844, 768 x 1024, 900 x 980, 844 x 390, 1024 x 900 et 1440 x 900. Les sept formats n'ont aucun débordement horizontal, le titre reste dans la largeur visible et il n'y a qu'un H1. Le bouton principal mesure 60 pixels de haut sur les formats compacts, 52 sur les deux formats de bureau.

Le plateau est masqué sur les cinq formats compacts. La vignette de porte est visible sous les plateformes. Sur les deux formats de bureau, le plateau est visible et la vignette compacte est masquée. Le clic sur la porte à 1440 x 900 confirme l'état d'ouverture puis l'arrivée à `/nos-projets/video-club?from=studio`.

Les captures sont enregistrées dans `C:/Users/Lou/.codex/visualizations/2026/10/15/01a14076-a18e-77f1-a4b2-9ee6592e8d66` : `accueil-mobile-ivoire-v11.jpg`, `accueil-mobile-equipe-v11.jpg`, `accueil-mobile-320-v11.jpg` et `accueil-desktop-porte-v11.jpg`. Le rapport de mesures est `responsive-refonte-v11.json`.

Les contrôles concernent le navigateur intégré. Aucun appareil Safari physique n'est testé. Aucun commit, push, PR ni déploiement.

## Compléments demandés pendant la revue

Le vidéoclub reprend l'habillage de l'accueil : cadre du magasin, en-tête, recherche, navigation, liste, sélection de VHS et fiche sur fond clair. Les photographies et l'inventaire restent intacts. La recherche de Sillage, sa sélection, l'ouverture de sa boîte, la fiche et la fermeture sont vérifiées dans le navigateur. Aucun lecteur vidéo ne se charge à l'ouverture de la fiche. La recherche sans résultat affiche son message et la remise à zéro restaure les projets. Les mesures de cadrage sont protégées par un test des bords du décor sur les rayons latéraux.

Les titres sous les prénoms sont remplacés à la demande de Lou. Les biographies de Loïc et Nicolas sont complétées et la bio exacte de Lou est conservée : 517, 525 et 521 caractères, deux paragraphes par personne. À 1440 pixels, le navigateur mesure les mêmes hauteurs pour les trois premiers paragraphes (176,3 pixels), les trois seconds paragraphes (100,75 pixels) et les trois colonnes (894,9 pixels). Le test vérifie deux paragraphes et moins de 10 % d'écart de longueur.

Les portraits utilisent une qualité de compression de 90 au lieu de 75. Les URL réellement chargées sont vérifiées dans le navigateur : `/team/lou.png`, `/team/loic.png` et `/team/nicolas-prod-2026-10-15.webp`. Les sources mesurent respectivement 1334 x 1179, 1254 x 1254 et 800 x 800 pixels. Leur qualité initiale limite le détail disponible ; aucune retouche de visage ni génération n'est utilisée. Sur tablette, les biographies restent dans le même parcours vertical que sur téléphone.

Pendant la revue, un changement de configuration provoque l'arrêt du serveur : Next refuse une règle avec une liste vide d'en-têtes en développement. La règle de CSP réservée à la production est désormais ajoutée uniquement dans cet environnement. Sa valeur et le nonce d'administration restent conservés. Un test protège le démarrage local ; le test des slides consulte désormais la politique réellement appliquée par le middleware. Le serveur est relancé en arrière-plan sur le port 3219.

Fichiers supplémentaires du lot : `video-club.tsx`, `video-club.module.css`, `domain/video-club.ts`, `domain/home-story.ts`, `content/hosts.json`, les trois dictionnaires, `next.config.ts`, les tests de découverte, de vidéoclub et des en-têtes locaux. Deux tests CSP et les fichiers générés de traductions sont seulement remis au format du dépôt pour terminer le contrôle commun.

Captures supplémentaires : `accueil-bios-equilibrees-v11.jpg`, `videoclub-mobile-refonte-v11.jpg`, `videoclub-desktop-refonte-v11.jpg`, `videoclub-vhs-refonte-v11.jpg` et `videoclub-fiche-refonte-v11.jpg`.

## Résultat des contrôles finaux

Les 35 tests ciblés du lot passent dans six fichiers : découverte, vidéoclub, en-têtes locaux et CSP des pages concernées. Le dernier `pnpm check` valide le format, le lint et les types, puis termine avec 633 tests réussis et un test en échec sur 634. Cet échec concerne la couverture anglaise du catalogue de traductions régénéré pendant le travail, avec de nombreuses clés sans traduction. Les nouveaux titres et biographies sont traduits dans les trois dictionnaires, y compris les formes complètes utilisées ailleurs que sur l'accueil. Aucun test n'est désactivé et aucune traduction manquante n'est remplacée par un texte français pour faire passer le contrôle.

Les tests sont exécutés avec `VITEST_MAX_WORKERS=2`, variable limitée à la commande. Cette option évite les dépassements de délai au démarrage de PGlite sans modifier les délais ni la configuration permanente. Les tests du générique (7) et des jingles (4) passent lors de leurs exécutions dans le lot. Le test de consultation des slides est adapté au middleware CSP ; un test de classement modifié en parallèle remplace deux assertions non nulles par des vérifications explicites des fixtures.

Le vidéoclub est contrôlé à 320 x 740, 390 x 844, 844 x 390 et 1440 x 900. Le décor couvre les quatre bords du cadre sur le rayon de Nicolas, la navigation reste dans la largeur visible et aucun défilement horizontal n'apparaît. Le rapport est `videoclub-responsive-v11.json`. La tablette à 768 x 1024 confirme les biographies en parcours vertical, sans dépassement des prénoms. L'aperçu local est rétabli après la correction de configuration.

Limite restante : compléter ou corriger le catalogue anglais régénéré avant de considérer le contrôle global comme réussi. La revue française locale des changements demandés est terminée. Aucun commit, push, PR ni publication.
