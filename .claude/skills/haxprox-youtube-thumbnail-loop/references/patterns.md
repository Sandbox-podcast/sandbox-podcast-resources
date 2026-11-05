# Patterns observés dans les sept chaînes

Relevé du 1 novembre 2026 : 1 128 miniatures récupérées, 32 planches examinées, 21 exemples revus en agrandissement. Il s'agit de toutes les entrées publiques retournées pour les sept onglets `/videos`, sans limite de nombre. Les anciennes miniatures remplacées, vidéos privées ou supprimées, Shorts et directs hors de ces onglets ne sont pas couverts.

Les observations viennent des images locales, pas de la réputation des chaînes. La couverture exacte et les identifiants sont dans `assets/corpus/2026-11-01/coverage.json` et `review.json`. La galerie `assets/corpus/2026-11-01/atlas.html` permet de retrouver chaque image et sa vidéo. Aucune donnée de CTR ni expérience contrôlée n'a été obtenue. Les règles de création ci-dessous sont des choix déduits de l'analyse visuelle.

## Ce qui se répète et sert à composer

Un sujet reconnaissable domine : gros visage, logo, objet tenu en main ou résultat de l'outil. Le titre de la vidéo porte souvent une explication plus complète ; la miniature ajoute une question courte, un résultat ou une comparaison. Les compositions sombres séparent ce sujet par une lumière, une bordure ou un aplat clair. Les fonds clairs de certains guides obtiennent cette séparation avec du texte sombre et un écran coloré.

Les portraits se lisent surtout comme des têtes et des épaules. Le regard et les mains dirigent vers l'objet ou l'interface. Plusieurs anciennes séries montrent davantage de buste, mais Lou a explicitement demandé un cadrage serré pour son propre système. Appliquer [sa correction](apprentissage.md) plutôt que moyenner tous les cadrages du corpus.

Les créateurs utilisent aussi des compositions chargées. Leur présence dans le corpus ne prouve pas qu'il faille multiplier les logos. Pour Lou, partir d'un visage, d'un sujet principal et d'un texte court ; garder plusieurs logos seulement si les relations entre outils constituent le sujet du tutoriel.

Les flèches, cercles et comparaisons ont une fonction précise lorsqu'ils relient deux états ou désignent un détail. Éviter de les ajouter sans cible. Une scène avec un objet lumineux peut rendre un concept abstrait visible ; une capture réelle convient mieux lorsqu'il faut montrer le résultat du tutoriel.

## Chaînes et évolutions

| Chaîne | Images / planches | Observations et adaptation pour Lou |
|---|---:|---|
| [THEYO](https://www.youtube.com/@THEYO_/videos) | 163 / 5 | Les entrées récentes montrent portraits, objets lumineux, profondeur et fond sombre ; certaines ont très peu de texte. Les anciennes séries Bubble, visibles notamment aux indices 121 à 144 du relevé, répètent violet, pose pointée et libellé de fonctionnalité. Retenir la mise en scène d'un objet ou d'un résultat, en variant selon le sujet. |
| [Yassine Sdiri](https://www.youtube.com/@yassine-sdiri/videos) | 114 / 3 | Visage souvent frontal, gestes proches du visage, panneaux de guide et logos. Les blocs de texte blancs, rouges ou jaunes et les couples avant/après rendent l'angle explicite. Utiliser un panneau clair ou une comparaison réelle ; garder une seule accroche. |
| [Jon Gregor IA](https://www.youtube.com/@JonGregor_IA/videos) | 30 / 1 | Gros portraits et textes de bénéfice ou d'alerte. Certains tutoriels app emploient un fond clair, un ordinateur montrant le résultat et une flèche verte. Reprendre le contraste portrait/résultat et la lisibilité, sans reprendre les promesses financières ou temporelles des images. |
| [Ludo Salenne](https://www.youtube.com/@LudovicSalenne/videos) | 457 / 12 | De nombreux portraits serrés à droite, logos ou captures à gauche, flèches rouges et gros texte blanc. Les anciennes familles marketing ont une palette orange et gris foncé ; les premiers visuels peuvent être de simples captures. Réutiliser la hiérarchie visage/outil/message et les comparaisons de migration quand la vidéo les démontre. |
| [Devart Studio](https://www.youtube.com/@devart-studio/videos) | 136 / 4 | Portraits pensifs ou sceptiques, atelier réel, interfaces et formulations éditoriales. Des séries plus anciennes utilisent violet/bleu et des gabarits techniques ; certains récents mêlent objets et rendu cinématographique. Bonne référence pour expliquer un usage concret ou poser une question précise. |
| [Parlons Cyber](https://www.youtube.com/@ParlonsCyber/videos) | 59 / 2 | Fonds noirs, blanc/jaune/vert, flèches épaisses, captures de logiciels et mascotte détective sur une partie du catalogue. D'autres visuels utilisent OSINT, fichiers ou appareils sans mascotte. Retenir le schéma lisible et le contraste ; remplacer le rôle du personnage par Lou, sans reprendre la mascotte. |
| [Tom's Basement](https://www.youtube.com/@TomsBasement/videos) | 169 / 5 | Atelier chaud, objet réel au premier plan, gestes démonstratifs et photos de résultats. Les séries anciennes de montage Voron utilisent des fonds clairs répétitifs ; d'autres familles ont des aplats très colorés. Référence utile pour montrer une réalisation, un détail matériel ou un avant/après visible. |

Les indices renvoient au manifeste figé du relevé ; ils ne sont pas des dates. Le nombre d'images varie beaucoup entre chaînes. Pour concevoir, sélectionner des exemples pertinents par sujet et famille, sans laisser les 457 images de Salenne déterminer seules le style de Lou.

## Exemples vérifiables

Chaque identifiant renvoie à `https://www.youtube.com/watch?v=IDENTIFIANT`. Les observations portent sur la miniature récupérée à la date du relevé ; elles ne valident pas les affirmations de la vidéo.

| Chaîne / identifiant | Composition observée | Décision utile |
|---|---|---|
| THEYO / `uqjTVioVEtg` | Tête centrale, objet vert lumineux, fond noir. | Un objet symbolique suffit lorsque le texte apporte peu. |
| THEYO / `nFyxQ01EjW0` | Portrait très serré à droite, figurine tenue et titre Claude Skills à gauche, lumière chaude. | Rapprocher visage et objet pour former une seule scène. |
| THEYO / `nVBp6p78iPo` | Deux écrans mobiles à gauche, tête surprise à droite. | Montrer le type de résultat avant les détails techniques. |
| Sdiri / `sVul67gL1fk` | Visage central, sphère bleue en main, question blanche en haut. | Faire de l'objet le support d'une question précise. |
| Sdiri / `y4AAFTlA6ak` | Panneau clair Claude Skills relié à des services, portrait à droite. | Un schéma court peut porter un tutoriel d'intégration. |
| Sdiri / `vxKtbHQXWEk` | Deux canettes, avant/après rouge et vert, portrait central. | Comparer deux résultats visibles plutôt que décrire un gain abstrait. |
| Gregor / `bYj8kcfytTo` | Fond clair, portrait à gauche, app sur ordinateur et flèche verte. | Le produit fini peut devenir le sujet principal. |
| Gregor / `r-TWRLk8Wwg` | Ordinateur pointé, même famille claire, texte idée vers app. | Conserver une famille de composition pour un sujet récurrent. |
| Gregor / `ifJfGyQ3y0E` | Portrait à droite, blanc/rouge à gauche, logo ChatGPT. | Une couleur d'alerte convient seulement à un risque traité. |
| Salenne / `fhj7wALyiKo` | Portrait à gauche qui désigne trois outils reliés et un résultat vidéo. | Montrer la relation entre les outils sans simuler de preuve. |
| Salenne / `nHXND_R4Jy8` | Fond blanc, grand texte noir/orange, visage à droite. | Un guide peut être lisible sans fond sombre. |
| Salenne / `Sz7pWrYWpHs` | Logos, croix/coche, flèche rouge, MIGRER et portrait à droite. | Une comparaison s'exprime avec peu d'éléments. |
| Devart / `i-L6qD5Rr_Y` | Titres et marques sur papier déchiré, portrait pensif. | Un traitement éditorial peut servir une question d'actualité. |
| Devart / `rxVPmEck2wY` | Laptop et téléphone, titre IA privée, portrait à droite, bleu. | Montrer un usage multi-appareils avec les vrais supports du tutoriel. |
| Devart / `YP2TC4wfiV0` | Portfolio web et mobile agrandis, portrait sur le côté. | Laisser de la place au résultat construit. |
| Parlons Cyber / `8NewbH_MQ6M` | Workflow central, titre en haut, mascotte et grosse flèche. | Simplifier le workflow autour d'une relation compréhensible. |
| Parlons Cyber / `ITTwEqPyqJ0` | Workflow, trois logos en bas et personnage qui pointe. | Garder plusieurs outils seulement si le mécanisme le nécessite. |
| Parlons Cyber / `gXUXN6oCjrg` | Deux fichiers EXE et PNG et une flèche jaune. | Un changement d'état peut être expliqué sans grand portrait. |
| Tom / `skkcLVn7bhU` | Capteur tenu vers l'objectif, atelier flou, flèche orange. | Donner une grande taille à l'objet démontré. |
| Tom / `pAjoZYqHKQk` | Deux impressions photographiées, séparation et flèche rouge. | Utiliser la preuve visuelle du résultat quand elle existe. |
| Tom / `1ra6VcNIJv4` | Petit ordinateur tenu en main, tête à gauche, question locale. | Relier une question technique à un objet concret. |

## Traduction en trois propositions

Ces trois pistes sont des points de départ pour un tutoriel, à adapter au brief. Elles ne doivent pas imposer un résultat ou une transformation absents de la vidéo.

1. Résultat visible. Portrait de Lou serré sur un côté, réalisation ou capture réelle de l'autre, texte bref qui précise l'angle. Références possibles : THEYO `nVBp6p78iPo`, Devart `YP2TC4wfiV0`, Tom `skkcLVn7bhU`.
2. Comparaison ou mécanisme. Deux états ou outils lisibles, Lou au centre ou sur le côté, une relation visible. Références possibles : Sdiri `vxKtbHQXWEk`, Salenne `Sz7pWrYWpHs`, Parlons Cyber `gXUXN6oCjrg`.
3. Objet ou question. Gros visage de Lou et un objet dominant, fond moins détaillé, lumière orientée ; texte réduit à la question utile ou au nom du sujet. Références possibles : THEYO `nFyxQ01EjW0`, Sdiri `sVul67gL1fk`, Tom `1ra6VcNIJv4`.

Pour une vidéo qui ne se prête pas à l'une de ces pistes, choisir une autre famille documentée. Les trois miniatures doivent montrer des choix de composition différents et respecter le cadrage serré demandé par Lou. La couleur change avec le sujet ; aucun bleu, jaune, vert ou orange n'a été validé comme charte exclusive de sa chaîne.
