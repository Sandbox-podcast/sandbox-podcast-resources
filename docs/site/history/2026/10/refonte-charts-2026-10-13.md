# Refonte des classements du 13 octobre 2026

La version locale est visible sur `http://127.0.0.1:3000/charts`. Elle utilise les données de démonstration du dépôt et les signale au-dessus des onglets. Le serveur existant a été réutilisé.

## Changements

Le titre est compact. Les onglets donnent directement accès à GitHub, Skills, Models et Rising. La période, la catégorie ou la capacité, et l'édition se choisissent dans trois menus. La liste remplace le podium répété. Les lignes affichent une seule mesure principale ; les détails gardent les descriptions, les avis, les métriques et les sources.

Les blocs de mouvements, les signaux, la couverture mensuelle et les records sont retirés de cette page. La sélection éditoriale et le lien d'inscription apparaissent seulement s'ils ont un contenu utilisable. La méthode et les archives restent accessibles. Le partage et le mode 16:9 passent dans Options, qui se referme après une action.

Décision : [DD-0017](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0017-interface-compacte-des-classements.md), décidée par l'agent sur délégation (PD-0003).

## Validation

- `pnpm test` : 57 fichiers et 316 tests réussis, dont 10 nouveaux cas pour la présentation compacte. Les tests vérifient les rangs conservés, les mesures sans doublon, les données manquantes, les erreurs, la sélection éditoriale, les fixtures et les nouveaux libellés traduits.
- `pnpm typecheck` : réussi.
- `pnpm build` : réussi, 178 pages statiques générées. L'avertissement existant sur la convention `middleware` reste présent.
- ESLint sur les trois composants modifiés et les deux fichiers de tests : réussi.
- Prettier sur les fichiers de la refonte : réussi.
- `pnpm check` : arrêté au contrôle de format sur des fichiers hors refonte déjà présents dans le dépôt. Aucun gate n'a été désactivé.
- `pnpm lint` global : arrêté par dépassement de la limite mémoire de 4 Go. La relance avec 8 Go s'arrête pour la même raison. La vérification ciblée ne remplace pas ce contrôle global.

Dans le navigateur, les quatre onglets chargent leurs lignes. Le filtre Code conserve les rangs 1, 7, 8, 13 et 15 de l'aperçu GitHub. Le filtre Voix vide propose le retour à toutes les catégories. Les périodes, le choix d'une archive et la capacité Code des modèles mettent à jour l'URL. Le partage ouvre son dialogue. Le mode 16:9 montre le podium et masque la liste et les filtres.

La liste et un détail ouvert ont été vérifiés à 390 px. La liste a aussi été vérifiée à 360 px. La largeur du document reste égale à celle de la zone visible, sans débordement horizontal. Les captures ordinateur et mobile sont enregistrées dans les artefacts locaux de la conversation. Aucune erreur de console n'a été relevée pendant ces parcours.

## Fichiers concernés

- `apps/site/src/components/charts-experience.tsx`
- `apps/site/src/components/charts-ranking.tsx`
- `apps/site/src/components/charts-features.tsx`
- `apps/site/src/components/charts-compact.module.css`
- `apps/site/src/i18n/dictionaries/en.json`
- `apps/site/src/i18n/dictionaries/es-es.json`
- `apps/site/src/i18n/dictionaries/de-de.json`
- `apps/site/src/i18n/dictionaries/source-catalog.json`
- `apps/site/test/charts-compact.test.ts`
- `apps/site/test/charts-public-language.test.ts`
- `docs/site/README.md`
- `docs/design-decisions/DD-0017-interface-compacte-des-classements.md`
- Ce rapport.

## Limites et suite

Cette validation porte sur le front local et les fixtures, pas sur une nouvelle collecte en production. Les nouveaux textes espagnols et allemands restent soumis à la relecture native prévue pour le site. Les permissions, les calculs et le stockage ne sont pas modifiés.

Les changements des slides déjà présents dans l'espace de travail ont été conservés. Aucun commit, push ou déploiement n'a été effectué. Aucune décision de conception ne reste ouverte ; le retour de Lou sur l'aperçu et la publication restent à faire.
