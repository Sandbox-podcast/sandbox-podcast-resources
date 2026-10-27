# Validation de l'accueil et de la Time Machine

Date : 2026-10-16. Lot local, après la livraison groupée de la PR 69. Aucun commit, push, nouvelle PR ou déploiement n'est réalisé pour ces retouches.

## Résultat

L'accueil abandonne le panneau vert au profit d'une suite sur fond noir neutre, avec des textes clairs et des accents cyan. Le plateau desktop et ses easter eggs restent en place. Le mobile conserve son accueil typographique et l'entrée séparée du vidéoclub.

Les trois projets, Okodukai, Song Maker et Sillage, utilisent un carrousel manuel inspiré du Spotlight Carousel de Scrolltide. Song Maker possède une couverture musicale de concept. Sillage utilise l'image fournie par Lou, enregistrée localement en WebP sans modification de son contenu. Les captures réelles du catalogue restent dans les fiches des projets.

Les animateurs possèdent chacun une carte fantastique à cadre argenté holographique. Les illustrations reprennent leurs photos comme références. Les photographies originales de l'équipe restent identiques à celles du commit de départ, vérification par empreinte Git. Les titres deviennent "Créateur de quêtes du quotidien", "Inventeur, même sans Wi-Fi" et "Chef d'orchestre des agents". Les biographies complètes et les liens sociaux sont conservés.

La désignation publique de l'émission devient Talk Show, dans les pages, la navigation, la recherche, les métadonnées et les trois traductions. Les URL existantes et les identifiants techniques restent compatibles. La correction du pilote reconnaît aussi sa rédaction historique, pour conserver le bon titre et ses liens vers Sillage.

La Time Machine utilise un rail Expanded Cards, avec cinq cartes sur ordinateur. Sur téléphone, une carte active occupe toute la largeur et deux vignettes donnent accès aux voisines. Chaque événement possède son affiche vectorielle distincte. Onze logos provenant de sources officielles identifient les éditeurs concernés. Les dates ressortent en haut des cartes, les détails et sources restent accessibles à la demande et les statistiques d'en-tête demandées en retrait ne sont plus affichées.

Le fond étoilé accélère pendant les déplacements temporels, puis revient à une image fixe. La réduction des mouvements, l'onglet masqué et la vue annuelle l'arrêtent. Les cartes holographiques n'effectuent aucun mouvement sur tactile et respectent la préférence système.

## Vérifications exécutées

- pnpm check : réussi. Formatage, lint et types réussis ; 656 tests du site et 11 tests des médias réussis.
- Compilation de production Next.js avec Webpack : réussie, 203 pages générées.
- Carrousel : navigation par flèches, boutons, clavier, maintien du focus, glissement, clic natif vers le projet et chargement des couvertures réussis à 320, 390, 768 et 1440 pixels.
- Cartes des animateurs : trois illustrations dédiées en qualité 90, titres positifs, biographies intégrales, liens sociaux natifs, volets au clavier, inclinaison limitée et arrêt du mouvement vérifiés aux quatre tailles. Aucun débordement ni erreur JavaScript.
- Time Machine : 37 contrôles navigateur réussis aux quatre tailles. Navigation souris, tactile et clavier, filtres, état vide, récapitulatif, exports, sources et trois légendes longues vérifiés. Les 151 fiches et leurs sources restent consultables sans JavaScript après retrait de la frontière loading.tsx.
- Dates et logos : 20 combinaisons vérifiées sans chevauchement ni rognage après ajustement du cadrage. Le script navigateur vérifie les dimensions réellement affichées et protège ce cas de régression.
- Étoiles : six contrôles complémentaires réussis après le réglage du glissement continu. Plusieurs dessins pendant le déplacement, puis zéro dessin au repos ; arrêt manuel et préférence système vérifiés.
- Illustrations : 151 fichiers et géométries distincts, reproduction exacte par le générateur, budgets de poids et absence de contenu SVG actif ou externe vérifiés.
- Parcours publics : accueil, catalogue du Talk Show, recherche, version anglaise, Sillage et replay du pilote répondent correctement. Aucune ancienne désignation publique de Sandbox comme podcast hors marque Apple Podcasts. Aucun défaut JavaScript constaté.

Les premiers tests ont révélé quatre attentes de textes devenues obsolètes et un cas de compatibilité du résumé historique du pilote. Les attentes et la compatibilité ont été corrigées ; le contrôle global final réussit. La redirection temporaire du sandbox Windows empêche certains lancements Vitest et Edge ; les contrôles finaux utilisent le même code hors de cette redirection.

## Fichiers et décisions

Les composants principaux sont DiscoveryStory, HomeHostCard, HomeProjectSpotlight, TimeMachine, HistoryArtwork et TemporalStarfield, sous apps/site/src/components/. Les titres, sélections et chemins d'illustration vivent sous apps/site/src/domain/. Les textes et traductions sont dans apps/site/content/ et apps/site/src/i18n/. Le générateur reproductible des affiches est apps/site/scripts/generate-time-machine-artwork.mjs ; ses manifestes conservent les sources et empreintes.

Les décisions et la provenance sont consignées dans [DD-0042](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0042-accueil-noir-spotlight-talk-show.md), [DD-0043](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0043-time-machine-inventions-illustrees.md), [DD-0044](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0044-cartes-holographiques-des-animateurs.md), [les couvertures des projets](home-project-covers-2026-10-16.md), [les prompts des portraits fantastiques](home-host-fantasy-prompts-2026-10-16.json) et [les affiches distinctes](time-machine-affiches-distinctes-2026-10-16.md).

Les scripts de vérification sont test-home-spotlight.mjs, test-home-host-cards.mjs et test-time-machine-experience.mjs, sous apps/site/scripts/. Les captures et rapports détaillés restent sous apps/site/.local/home-spotlight/, home-host-cards/ et time-machine-experience/.

Les captures finales de la Time Machine sont time-machine-final-1440.png et time-machine-final-390.png. Elles incluent le dernier réglage de cadrage des logos et des grandes dates. La compilation de production a aussi été relancée avec succès après ce réglage.

## Passe des espacements publics

La passe demandée par Lou réduit les marges cumulées entre les sections de l'accueil, rapproche les contrôles du carrousel et resserre la transition vers le dernier épisode. La distance mesurée entre le lien Voir tous nos projets et le titre Explorer devient 119 pixels sur ordinateur et 99 pixels sur mobile, contre 183 pixels relevés avant correction sur mobile. Les entrées et fins de pages Talk Show, À propos, catalogue et confidentialité sont harmonisées. La date de mise à jour de la confidentialité retrouve son format de légende.

Le script test-site-rhythm.mjs vérifie douze routes à quatre tailles, soit 48 cas. Les captures de l'accueil attendent le chargement des images visibles. Le carrousel conserve son clavier, son glissement et ses liens natifs aux quatre tailles. Le contrôle pnpm check réussit : formatage, lint, types, 656 tests du site et 11 tests médias. La dernière correction du sélecteur de légende est ensuite vérifiée dans le navigateur et par les contrôles ciblés. Voir [DD-0046](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0046-rythme-et-espacements-publics.md). Les captures finales sont sous apps/site/.local/site-rhythm-after/.

## Limites et suite

Les portraits sont des illustrations fantastiques. Les affiches de la Time Machine sont des compositions vectorielles de concept, pas des photographies historiques ni des schémas d'architecture scientifique. La provenance des logos et les précisions des dates sont conservées.

Le vidéoclub conserve son activation locale et ses règles de non-indexation. Aucun accès externe, contenu publié, donnée réelle, migration ou configuration de production n'est modifié. Le dossier experiments/ contient du travail local extérieur à cette retouche et n'est pas modifié par ce lot.

Les retouches sont disponibles en local. Leur publication ou leur intégration dans une PR attend une nouvelle demande explicite de Lou.

## Retouche des commandes de la chronologie

La navigation avec les flèches gauche et droite fonctionne aussi sans sélectionner une carte. Elle laisse les champs de saisie, les curseurs, les sélecteurs et les onglets utiliser leurs touches habituelles. Huit contrôles navigateur vérifient le parcours sur quatre tailles, dont la saisie dans la recherche. Le footer affiche deux boutons avec icônes, vers la chaîne YouTube et l'émission Spotify configurées ; quatre contrôles navigateur valident les destinations, les cibles tactiles et l'absence de débordement. Les 656 tests du site et les 11 tests médias réussissent. Le nouveau lancement de pnpm check est arrêté par le formatage de trois fichiers du dossier experiments/episode-002-bis, hors du lot.

À la demande de Lou, les flèches précédent et suivant sont déplacées à l'intérieur du carrousel, sur les visuels. Huit contrôles Playwright réussissent aux quatre tailles : placement dans la zone illustrée, cible tactile, clic, focus, clavier et désactivation aux bornes. Les types, le lint des fichiers concernés, les 656 tests du site et les 11 tests médias réussissent. Le contrôle global rencontre une erreur de lint dans experiments/episode-002-bis/test/server.test.mjs (import setTimeout inutilisé), fichier extérieur à cette retouche.
