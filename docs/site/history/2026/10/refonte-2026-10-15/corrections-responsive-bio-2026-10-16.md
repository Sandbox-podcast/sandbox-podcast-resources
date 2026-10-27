# Accueil : portraits, formats étroits et bio de Lou

16 octobre 2026. Corrections locales demandées par Lou après ses captures à deux largeurs.

## Changements

Le décor reste plein écran, avec le titre superposé. Jusqu'à 1100 pixels de large, la scène cesse de suivre le défilement. Les portraits se placent en fonction de la largeur visible, avec une limite liée à la hauteur pour éviter de rejoindre le titre. Le paragraphe, les noms, le bouton de l'émission et les liens YouTube/Spotify forment un groupe centré. Le format intermédiaire utilise cette même composition.

Chaque animateur utilise désormais une seule image détourée complète. Ce choix remplace l'assemblage tête/buste, dont le raccord au cou était visible sur localhost. Les trois fichiers retouchés existants sont réutilisés, sans nouvelle génération. Les photos originales restent conservées dans la collection Animateurs. Les variantes retouchées ressemblent aux sources mais ne garantissent pas une identité de pixels sur les visages. Les [assets et prompts ImageGen intégrés](retouches-bustes-2026-10-16.md) restent documentés.

Lou fournit sa nouvelle biographie et le domaine "Jeux vidéo, éducation et apprentissage". Le texte exact est enregistré dans la collection Animateurs et dans le repli de l'accueil. Ses deux paragraphes restent séparés à l'affichage. Le titre et les paragraphes sont traduits dans les trois autres langues. Okodukai reste le projet mis en avant pour Lou.

Intégration décidée par l'agent sur délégation (PD-0003), selon les demandes de Lou. Aucun commit, push, déploiement ni PR.

## Fichiers concernés

- `apps/site/src/components/discovery-home.tsx`, `discovery-home.module.css` et `cinematic-stage.tsx` : composition et adaptation aux dimensions.
- `apps/site/src/domain/home-studio.ts` : portraits complets.
- `apps/site/content/hosts.json`, `src/domain/home-story.ts`, `src/components/discovery-story.tsx` et dictionnaires : biographie.
- `apps/site/test/discovery-refonte.test.ts` : un portrait par personne, fichiers transparents et bornés, biographie en deux paragraphes. Le test de copie pixel à pixel des têtes est remplacé car ces copies ne servent plus à l'assemblage.

## Validation

`pnpm check` réussit : format, lint, types, 619 tests du site dans 95 fichiers, 7 tests du générique et 4 tests des jingles. Aucun échec. Les nouveaux tests contrôlent les portraits complets et les deux paragraphes de Lou.

Contrôles dans le navigateur local : 320 x 640, 390 x 844, 600 x 880, 860 x 980 et 1440 x 900. Pas de défilement horizontal constaté. Le trio reste visible, le titre ne rejoint pas les têtes et les actions restent regroupées. À 320 x 640, le premier écran conserve une hauteur minimale de 720 pixels : les liens de chaînes restent accessibles par défilement. Le clic sur la porte à 600 pixels mène au vidéoclub après l'ouverture. Retour au plateau vérifié. La bio affichée reprend les deux paragraphes fournis, et les sources des portraits restent présentes. Aucune erreur de console observée ; un avertissement de rechargement du serveur de développement apparaît pendant les modifications.

Captures enregistrées dans `C:/Users/Lou/.codex/visualizations/2026/10/15/01a14076-a18e-77f1-a4b2-9ee6592e8d66/` :

- `accueil-responsive-mobile-v3.jpg` : 390 x 844.
- `accueil-responsive-600-v3.jpg` : 600 x 880.
- `accueil-responsive-intermediaire-v3.jpg` : 860 x 980.
- `accueil-responsive-large-v3.jpg` : 1440 x 900.
- `accueil-responsive-local-v3.jpg` : taille normale du navigateur, rétablie après les contrôles.
- `bio-lou-local-v3.jpg` : biographie complète.

La validation concerne localhost, sans publication. Aucun point bloquant restant pour ce lot local.

## Raccord des bustes au bureau

Lou signale ensuite un espace entre les corps et la table sur grand écran. La coupe horizontale à mi-hauteur ne suivait pas le bord courbe du bureau. Le masque suit désormais ce bord dans les coordonnées du décor, et le bas des bustes descend derrière lui. Le masque et les portraits partagent le même plan pendant les changements de taille et le mouvement de la scène. La taille de Lou augmente et celle de Nicolas diminue légèrement sur grand écran pour rapprocher leurs proportions de celles de Loïc. Les réglages de largeur mobile sont conservés.

Correction locale dans `apps/site/src/components/discovery-home.module.css`, décidée par l'agent sur délégation (PD-0003). Le contrôle pertinent est visuel, au raccord exact du vêtement et du décor ; aucun test des valeurs CSS littérales n'est ajouté. Les points du masque sont relevés sur le bord photographique, de 200 à 1500 pixels en abscisse. Les mesures aux positions des portraits sont identiques dans les variantes du décor avec et sans porte.

Contrôle visuel de la correction : 1980 x 1100, 390 x 844 et fenêtre normale de 1032 x 884. Le raccord suit la table sur les trois personnes, y compris pendant le zoom au défilement. Aucun débordement horizontal constaté. Captures dans le même dossier de restitution : `accueil-raccord-table-large-v4.jpg`, `accueil-raccord-table-scroll-v4.jpg`, `accueil-raccord-table-mobile-v4.jpg` et `accueil-raccord-table-local-v4.jpg`. Ces captures remplacent les V3 pour le raccord au bureau.

Deux exécutions de `pnpm check` valident format, lint et types, puis échouent sur les délais de cinq secondes de deux tests PGlite : `episode-thumbnails.test.ts` et `host-photo-upload.test.ts`. Leurs dix tests passent ensemble en exécution isolée. La suite entière passe ensuite avec `pnpm --filter @podcast/site exec vitest run --maxWorkers=2` : 619 tests, 95 fichiers. Les sept tests du générique et les quatre tests des jingles passent également. Aucun délai, test ni réglage du dépôt n'est modifié. Le lancement standard reste sujet à ces dépassements sous charge ; il n'est pas présenté comme réussi pour cette correction.

## Têtes alignées juste au-dessus des sièges

Lou demande de réduire le dépassement au-dessus des dossiers et d'aligner les trois têtes. Les marges transparentes des fichiers sont désormais compensées : le sommet visible se trouve à 39 pixels pour Lou, 150 pour Loïc et 117 pour Nicolas. Ces trois repères rejoignent une même ligne à 37,5 % de la hauteur du décor, soit environ 20 pixels au-dessus des dossiers dans l'image originale. Les portraits conservent leur rapport largeur/hauteur et le masque courbe de la table. Les positions horizontales se rapprochent sur téléphone. Aucune image n'est modifiée.

Correction dans `home-studio.ts`, `discovery-home.tsx` et `discovery-home.module.css`, décidée par l'agent sur délégation (PD-0003). Le test existant dans `discovery-refonte.test.ts` vérifie maintenant les dimensions réelles des fichiers et mesure leur première ligne suffisamment opaque. Il détectera un changement de fichier qui invaliderait les repères.

Contrôles visuels : 320 x 720, 390 x 844, 860 x 980, 1440 x 900 et 1980 x 1100, ainsi que le zoom au défilement sur grand écran. Les sommets mesurés restent alignés à moins de 0,01 pixel près et aucun débordement horizontal n'est observé. Les bustes rejoignent le bureau. Les captures `accueil-tetes-alignees-desktop-v5.jpg`, `accueil-tetes-alignees-mobile-v5.jpg` et `accueil-tetes-alignees-tablette-v5.jpg`, ainsi que les mesures `accueil-tetes-alignement-v5.json`, sont enregistrées dans le dossier de restitution indiqué plus haut. Le navigateur retrouve sa taille normale après vérification.

Validation de cette correction : `pnpm check` valide format, lint et types, puis retrouve les deux délais dépassés des migrations PGlite (617 tests réussis sur 619). La suite complète avec `--maxWorkers=2` valide les 619 tests dans 95 fichiers en 28,84 secondes, y compris le nouveau contrôle des repères. Les 7 tests du générique et les 4 tests des jingles réussissent. Le lancement standard reste donc en échec sous charge ; aucun test ni délai n'est modifié. La correction est disponible sur localhost, sans commit, push, PR ou publication.

## Sans chaises, avec les bustes visibles et espacés

Lou rejette la V5 : le respect littéral du haut des dossiers avait enfoncé les personnes derrière le bureau. Après un essai de dossiers indépendants, Lou autorise leur retrait. La version retenue supprime toutes les chaises et remonte les bustes. Les photos utilisées restent inchangées. Le mur sans chaises est un nouvel asset ImageGen, affiché uniquement dans la bande des anciens sièges ; le décor supérieur, la porte et le bureau viennent toujours du fond original. Le masque du bureau conserve son bord courbe.

Sur mobile, à la demande de Lou, les portraits occupent au plus 29 % de la largeur visible et leurs centres sont espacés de 32 %. Leurs cadres ne se chevauchent plus. Le point d'appui vertical dépend de la largeur des portraits pour garder les épaules visibles et le bas des bustes derrière la table. Les repères des sommets des têtes restent communs. La taille minimale du premier écran reste de 720 pixels de haut.

Fichiers : `home-studio.ts`, `discovery-home.tsx`, `discovery-home.module.css`, `discovery-refonte.test.ts` et `public/images/home/studio-chairless-v2.webp` (194 588 octets). Le test vérifie le chargement du mur sans chaises et l'absence de l'asset de dossier indépendant. Sources et prompts : [retouches](retouches-bustes-2026-10-16.md). La décision est consignée dans DD-0038, décidée par l'agent sur délégation (PD-0003).

`pnpm check` réussit pour cette version : format, lint, types, 619 tests du site dans 95 fichiers, 7 tests du générique et 4 tests des jingles. Aucun échec ni modification des délais. Les captures V7 sans chaises remplacent les V5 et l'essai V6 : `accueil-sans-chaises-mobile-v7.jpg` et `accueil-sans-chaises-desktop-v7.jpg`, dans le dossier de restitution. Le résultat reste local, sans commit, push ou publication.

## Vérification Playwright demandée par Lou

Contrôle du 16 octobre dans le navigateur local avec l'API Playwright : 320 x 640, 390 x 844, 600 x 880, 860 x 980, 1440 x 900, 1980 x 1100 et 844 x 390. Une huitième mesure vérifie le zoom après 225 pixels de défilement à 1440 x 900. Pour chaque vue, neuf assertions contrôlent les trois personnes, les images chargées, l'absence de débordement horizontal et de chevauchement, l'alignement des têtes, la séparation avec le titre, les portraits contenus dans la largeur visible, les bustes prolongés derrière le bureau et l'absence de l'asset de chaise.

Le premier passage détecte un défaut en paysage à 844 x 390 : le titre descend à 201,7 pixels alors que les têtes commencent à 189,5 pixels. Une règle dans `discovery-home.module.css`, limitée aux fenêtres de 1100 pixels de large et 540 pixels de haut au maximum, réduit la taille du titre et sa marge supérieure. Après correction, le titre finit à 147,2 pixels, laissant 42,3 pixels avant les cheveux. Les autres formats conservent leurs règles.

Résultat final : 72 assertions réussies sur les sept tailles et la vue défilée. Les cadres des portraits sont séparés d'au moins 9,15 pixels à 320 pixels de large, et de 11,25 pixels à 390 pixels. Aucune erreur de console remontée. Captures `playwright-rendu-*.jpg` et mesures `playwright-rendu-rapport.json` dans le dossier de restitution indiqué plus haut. Les assertions géométriques complètent les captures ; elles ne constituent pas une validation esthétique. Sur les écrans de moins de 720 pixels de haut, la scène conserve sa hauteur minimale et ses actions se rejoignent par défilement. Tests effectués dans le navigateur Chromium intégré, sans validation Safari ou appareil physique.

`pnpm check` réussit après la correction paysage : format, lint, types, 619 tests du site, 7 tests du générique et 4 tests des jingles. Aucune modification des photos, aucun commit, push ou déploiement.

## Une composition dédiée au mobile

Lou signale que la table reste disproportionnée par rapport au trio, malgré les contrôles géométriques, et demande une autre présentation. La V8 remplace le plateau sur les écrans de 900 pixels de large ou moins et sur les formats paysage de 1100 x 540 pixels au maximum. Le titre est suivi de trois portraits rapprochés dans des cartes avec prénoms, puis du texte et des boutons. Aucun décor ni bureau n'est affiché dans cette composition. Le premier écran suit la hauteur de son contenu au lieu d'imposer une scène plein écran. Les portraits existants servent aux deux présentations, sans nouvelle image générée.

Le plateau reste affiché sur ordinateur. La porte mobile prend la forme d'une petite icône, sans libellé visible, avec une cible de 44 pixels. Elle garde le nom accessible et le lien vers le vidéoclub ; sa navigation est directe, sans zoom d'un décor absent. Les noms des cartes sont masqués aux lecteurs d'écran pour ne pas répéter les alternatives des photos. La mise en page reste rendue côté serveur et adaptée par CSS, sans composant client supplémentaire.

Fichiers modifiés : `discovery-home.tsx`, `studio-door.tsx`, `discovery-home.module.css` et DD-0038. Conception décidée par l'agent sur délégation (PD-0003), selon la demande de Lou.

Validation Playwright adaptée au nouveau choix : 320 x 640, 390 x 844, 860 x 980 et 844 x 390. Les 44 assertions vérifient trois cartes chargées, leur séparation, une hauteur minimale de 150 pixels, le titre avant les portraits, le texte après les cartes, les boutons après le texte, une cible tactile suffisante, l'absence de débordement et la mise en page dans le flux. Les captures sont aussi examinées : le contrôle précédent du seul alignement des têtes ne permettait pas de valider les proportions de la scène.

À 390 pixels, le premier bloc mesure 648 pixels de haut ; à 320 pixels, 655 pixels. En paysage, le contenu défile normalement. Le clic sur la porte mobile rejoint `/nos-projets/video-club?from=studio`, puis le retour restaure l'accueil. À 1440 x 900, le décor du plateau reste affiché et les noms propres aux cartes mobiles restent masqués. Captures `accueil-mobile-editorial-390-v8.jpg` et `accueil-mobile-editorial-320-v8.jpg`, mesures `accueil-mobile-editorial-tests-v8.json`, dans le dossier de restitution indiqué plus haut.

`pnpm check` réussit : format, lint, types, 619 tests du site, 7 tests du générique et 4 tests des jingles. Le test navigateur du lien mobile complète les tests existants du lien natif et du portrait unique. Pas de publication ni de modification des fichiers photos. La validation concerne le navigateur intégré, pas Safari sur appareil physique.

## Miniature vidéo et vignette du vidéoclub

Lou demande une miniature plus travaillée, puis une image de la porte sous YouTube et Spotify. La V9 remplace les trois cartes par une composition 16:9 unique : fond du studio recadré sans table, les trois portraits existants, leurs prénoms et un habillage Sandbox doré. Le cadre entier est un lien vers l'épisode disponible ou la page podcast. Les images existantes sont composées dans l'interface ; aucune nouvelle génération ni modification des visages.

La petite porte isolée est retirée. Une vignette 2:1 apparaît après les liens des plateformes, avec la porte du décor et le libellé "Le vidéoclub". Le lien ouvre le magasin local et reste conditionné à `videoClubEnabled`. Le décor de bureau et sa porte animée sont conservés. Fichiers : `discovery-home.tsx`, `discovery-home.module.css`, `studio-door.tsx`, `discovery-refonte.test.ts` et DD-0038.

Contrôles Playwright : à 390 pixels, la vignette de porte mesure 327 x 163,5 pixels, son image est chargée et elle se trouve sous les plateformes. Le clic rejoint `/nos-projets/video-club?from=studio` ; le retour restaure l'accueil. La miniature principale rejoint `/podcast` en l'absence d'épisode. À 320 pixels, le cadre conserve exactement le rapport 16:9, reste dans la largeur visible et ne provoque aucun défilement horizontal. La porte arrive après les plateformes dans le flux de la page. Capture : `accueil-mobile-miniature-videoclub-v9.jpg`, dans le dossier de restitution indiqué plus haut.

Un test vérifie le placement de la vignette après Spotify, sa destination, son absence lorsque le club est désactivé et l'absence de chargement de l'intérieur du magasin avant le clic. Le premier contrôle complet de la miniature réussit avec 619 tests ; le contrôle final incluant ce nouveau test est consigné ci-dessous.

Contrôle final : `pnpm check` réussit, avec format, lint, types, 620 tests du site dans 95 fichiers, 7 tests du générique et 4 tests des jingles. L'assertion du nouveau lien a été corrigée pour vérifier ses attributs sans imposer leur ordre de sérialisation. À 1440 x 900, les deux nouveaux liens mobiles sont masqués et la porte de bureau reste visible. Le viewport est rétabli après contrôle. Aucun commit, push ou déploiement.

## V10 : composition mobile éditoriale

Demandes de Lou : retirer le logo répété et le bouton doré, restaurer l'épisode manquant, puis reprendre l'esthétique mobile. Le titre est aligné à gauche, les portraits occupent une miniature commune sans habillage de marque supplémentaire, les actions sont simplifiées et les sections suivantes utilisent des titres en Newsreader. Les biographies passent à un portrait compact, avec leur texte intégral. La porte reste sous les plateformes. La composition de bureau est conservée.

Fichiers modifiés : `discovery-home.tsx`, `discovery-home.module.css`, `discovery-refonte.test.ts` et DD-0038. Aucun asset photo modifié. Le test ajouté vérifie le nom accessible et la destination de la miniature avec et sans épisode, ainsi que l'absence du logo répété et du pictogramme décoratif.

Le catalogue Git local ne contient aucun épisode. Le pilote publié existait dans `.local/refonte-public-pilot.json` ; ses données ont été validées puis réintégrées au contenu éditorial actuel dans `.site-content.local.json`, stockage local ignoré par Git. Cette correction ne change pas les règles de publication ni les données de production. Le navigateur confirme l'affichage du pilote sur `/podcast`, le lien du replay vers `/episodes/1` et la présence du lecteur à consentement. L'accueil propose de nouveau le dernier épisode.

Contrôles Playwright et visuels dans le navigateur intégré : 320 x 740, 390 x 844, 860 x 980, 844 x 390 et 1440 x 900. Aucun débordement horizontal ; les cadres des trois personnes restent séparés. La vignette de porte est sous Spotify sur les formats compacts et rejoint le vidéoclub au clic. Sur ordinateur, les deux liens propres au mobile sont masqués. Un contrôle effectué immédiatement après redimensionnement a rencontré une image encore en chargement ; le contrôle suivant à 860 pixels confirme leur chargement. La coupe inférieure des bustes vue sur tablette est corrigée par un cadrage plus court.

Le contrôle complet initial réussit : format, lint, types, 621 tests du site, 7 tests du générique, 4 tests des jingles. Les captures V10 et le rapport `responsive-mobile-v10.json` sont conservés dans le dossier de restitution. La validation porte sur le navigateur intégré, pas sur Safari sur appareil physique. Aucun commit, push ou déploiement.

Contrôle après le dernier ajustement : format, lint et types réussissent. Le second `pnpm check` rencontre deux dépassements de délai de 5 secondes au démarrage de PGlite, dans les tests d'import de photo et de miniature. La suite du site relancée avec `pnpm exec vitest run --maxWorkers=2` réussit : 95 fichiers et 621 tests. Aucun test ni délai modifié. Le premier passage complet avait également validé les tests vidéo. Le viewport a été rétabli et l'accueil local laissé ouvert.
