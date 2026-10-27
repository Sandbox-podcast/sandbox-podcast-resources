# Time Machine : refonte illustrée du 16 octobre 2026

## Changements

La chronologie présente un rail de cinq cartes illustrées sur ordinateur, inspiré des Expanded Cards de Scrolltide. La sélection s'élargit, avec date, titre court et résumé sur l'image. Le survol à la souris, le clic, le toucher et le clavier fonctionnent. Les explications longues et les sources sont repliées sous le rail. La courbe reste disponible, derrière un accès secondaire. Les filtres, le curseur temporel et les commandes de lecture sont conservés.

Les archives annuelles deviennent des cartes illustrées. Chacun des 151 événements garde son texte complet et toutes ses références dans le HTML initial, consultables sans JavaScript. Le récapitulatif annuel conserve ses calculs, ses liens de partage et ses exports.

La feuille de style est reconstruite pour cette disposition. Sur mobile, la carte sélectionnée occupe toute la largeur, avec deux vignettes voisines en dessous. La fenêtre du rail reste stable pendant le survol et les légendes ne changent pas de largeur pendant l'animation. Les boutons de navigation, de lecture, de vitesse et d'export ont une hauteur minimale de 44 pixels. Aucun fait du corpus n'est modifié.

L'illustration principale se charge immédiatement ; les autres images restent différées. Un fond étoilé décoratif accompagne les changements de date, avec arrêt lorsque les animations sont réduites ou que la vue annuelle est affichée. Le composant dédié arrête également le mouvement lorsque l'onglet est masqué.

Décision : [DD-0043](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0043-time-machine-inventions-illustrees.md).

## Fichiers de l'interface

- apps/site/src/components/time-machine.tsx
- apps/site/src/components/time-machine.module.css
- apps/site/test/time-machine-ui.test.ts
- apps/site/src/domain/time-machine-cards.ts
- apps/site/test/time-machine-cards.test.ts

Les illustrations et le fond étoilé sont réalisés dans des composants séparés. Leur production et leurs tests sont documentés par les autres agents du lot.

## Vérification

- Tests Time Machine UI, SEO, domaine et exports : 27 tests réussis dans 5 fichiers.
- ESLint ciblé : réussi.
- Formatage des fichiers de l'interface : réussi.
- Vérificateur Human Quality sur DD-0043 : réussi.
- Les nouveaux tests confirment la priorité de la fiche sur la courbe, les détails fermés au chargement, la conservation du contexte de chaque événement et de toutes ses références.

Le premier lancement Vitest a échoué à lire ses fichiers SSR temporaires dans la redirection Windows du sandbox. Le même contrôle relancé hors de cette redirection a réussi. Les tests navigateur et le contrôle global du lot sont exécutés par les agents de validation et de coordination ; leurs résultats complètent ce rapport.

Le travail reste local. Aucun commit, push, publication ou nouvelle PR n'est réalisé pour cette refonte.

Correction finale de Lou : retrait de la ligne des chiffres, de la plage et de la date de revue sous le titre. La vérification et les références restent accessibles dans Sources et méthode, sans rallonger le premier écran.

La collection finale comprend [151 affiches distinctes avec leur provenance](../time-machine-affiches-distinctes-2026-10-16.md), après la demande de Lou de supprimer les images répétées. La fiche principale utilise le chargement immédiat ; les archives restent différées. Les boutons précédent et suivant conservent leur focus quand la date change, et les détails de la nouvelle fiche reviennent fermés.

Le composant de chargement de la route est retiré pour conserver les fiches visibles sans JavaScript ; les tests navigateur couvrent aussi ce parcours. Le corpus étant lu localement, aucun nouvel état d'attente réseau n'est introduit. Les 19 images partagées de la première passe ne sont plus utilisées. La date de la carte active est mise en avant en haut de l'image, avec une grande année et les précisions disponibles.
