# Jaquettes visibles dans le portail, 21 octobre 2026

Lou signale un écart entre les anciennes pochettes de l'aperçu et les jaquettes illustrées visibles après l'entrée dans le vidéoclub.

Le portail utilisait `HOME_PROJECT_ARTWORK` ou les captures produit. Il dessinait ensuite une texture simplifiée, avec un titre coupé à 22 caractères. La salle utilisait déjà `VHS_PROJECT_ARTWORK` et son habillage VHS.

## Correction locale

`vhsProjectArtwork` sélectionne désormais la même illustration pour le portail, la salle et le catalogue. Les médias produit restent disponibles en repli pour les projets sans jaquette. Le renderer reprend le bandeau SANDBOX/VHS, la couleur du projet, l'illustration recadrée, le dégradé et le titre complet réparti sur plusieurs lignes. Les faces latérales restent sombres. Les coordonnées des emplacements viennent de `videoClubTapeSlot`, également utilisé par le contenu HTML de la salle.

Le portail conserve un rendu canvas de l'habillage ; les titres, liens et commandes accessibles de la salle restent en HTML. Les deux moteurs peuvent présenter de légères différences de rasterisation et de retour à la ligne.

## Vérifications

Les tests du domaine vérifient les jaquettes de chaque projet de l'aperçu, la disposition des rayons et le repli sur les médias produit. La suite Vitest du site réussit avec 1 258 tests dans 153 fichiers.

La recette `apps/site/scripts/test-portal-project-covers.mjs` utilise Edge headless à 1440 × 900 et 1920 × 1080. Elle vérifie le chargement des jaquettes, compare une zone de l'illustration Akasha OS dans le portail et dans la salle, puis traverse le portail. Le seuil accepté est un écart moyen inférieur à 30 sur 255 par canal ; les deux mesures initiales sont 25,56 et 22,05. Les captures ont été inspectées : illustration VHS, bandeau et dégradé présents dans l'ouverture. Aucune erreur JavaScript n'a été relevée. Captures et rapport : `apps/site/.local/portal-project-covers/`.

`pnpm check` a été lancé. Il s'arrête sur le formatage d'un fichier déjà modifié avant cette correction, `docs/site/suivi-issue-68-2026-10-20.md`. Ce fichier ne fait pas partie du correctif. Les contrôles suivants sont exécutés séparément et leurs résultats sont consignés à la fin de ce document.

Les contrôles séparés réussissent : `pnpm lint`, `pnpm typecheck` et `pnpm test` (1 258 tests du site, plus les suites vidéo et BIS). Après correction des remarques de lint dans les nouveaux tests, les huit tests ciblés ont été répétés avec succès. Prettier valide tous les fichiers du correctif et `git diff --check` ne signale aucune erreur. Les journaux sont dans `apps/site/.local/portal-covers-{check,lint,types,tests}.log`.

La recette existante `test-vhs-project-artwork.mjs` réussit aussi à 1440 et 390 pixels, avec les mouvements réduits : 33 projets accessibles, aucune image manquante, ouverture de la fiche et aucune erreur JavaScript. Elle vérifie la salle et le catalogue, sans prétendre tester un portail WebGL sur mobile. Preuves : `apps/site/.local/vhs-projects/report.json`.

La recette initiale a été réalisée en local. Les essais navigateur utilisent une émulation et ne constituent pas une recette sur appareils physiques.

## Préparation de la PR

À la demande de Lou, le correctif est repris le 21 octobre dans un worktree créé depuis `origin/main`, sur la branche `codex/portal-vhs-covers`. Les autres changements présents dans le dossier partagé restent hors de cette PR. Dans cet espace isolé, le contrôle complet `pnpm check` et le build de production réussissent ; le document qui bloquait le premier contrôle appartient aux autres travaux locaux.

L'audit des dépendances détecte alors une vulnérabilité élevée dans Vite 8.3.2. L'override passe à 8.3.3, version corrigée selon [GHSA-587h-7wmj-h5pm](https://github.com/advisories/GHSA-587h-7wmj-h5pm), et le lockfile est régénéré avec pnpm 12.9.1. Après cette mise à jour, `pnpm audit --audit-level=high` ne signale plus de vulnérabilité connue. Cette mise à jour corrective nécessaire au passage du contrôle de sécurité est décidée par l'agent sur délégation (PD-0003).

Les journaux de préparation sont dans `.local/portal-pr/` du worktree. Cette demande autorise la création de la PR ; aucune fusion ni publication en production n'est effectuée.
