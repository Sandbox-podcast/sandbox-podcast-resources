# Portail du plateau vers le vidéoclub

Prototype local du 20 octobre 2026, selon [DD-0069](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0069-portail-vers-le-videoclub.md).

## Fichiers

- `src/components/studio-portal.tsx` et `studio-portal.module.css` : aperçu, pochettes, lumière, parallaxe, traversée et replis.
- `src/components/studio-landing.tsx` et `discovery-home.tsx` : intégration dans la porte du plateau et passage des projets existants.
- `src/domain/studio-portal.ts` : calcul borné du déplacement et sélection des pochettes.
- `test/studio-portal.test.ts` : limites de déplacement, entrées invalides et fidélité au catalogue.
- `scripts/test-studio-portal.mjs` : recette navigateur reproductible, limitée à une origine locale.

Les chemins ci-dessus sont relatifs à `apps/site`. Les captures et journaux sont conservés hors Git dans `apps/site/.local/studio-portal/` et `apps/site/.local/studio-portal-*.log`.

## Contrôles

- Formatage des fichiers du portail : réussi. ESLint global et typage global : réussis séparément.
- `pnpm test` : 1 081 tests du site dans 142 fichiers, 7 tests du générique, 4 tests des assets vidéo et 24 tests BIS réussis.
- Recette Edge/Chromium à 1440 × 900 : aucun média de portail au chargement initial, aperçu au survol avec pochettes, parallaxe bornée, fermeture par Échap, focus et Entrée, traversée vers une route HTTP 200, retour arrière et annulation pendant la traversée.
- Mobile émulé à 390 × 844 : cible d'au moins 44 pixels, absence de débordement et accès direct. Sans JavaScript et avec mouvements réduits : accès direct vérifié ; l'aperçu clavier réduit n'a pas de transition perceptible.
- Image du magasin bloquée par le navigateur de recette : le portail vide reste masqué et la navigation fonctionne. Aucune erreur JavaScript dans ces parcours.
- Version anglaise : aperçu et traversée à la souris vers `/en/nos-projets/video-club?from=studio` vérifiés.
- `pnpm check` a été exécuté deux fois. Le premier arrêt concernait le formatage de `apps/site/public/slides/episode-003/show.css`, déjà modifié avant cette tâche. Le second concernait `docs/site/profils-vision-2026-10-20.md`, apparu pendant le travail parallèle dans le dépôt. Ces fichiers sont hors du lot portail ; ils n'ont pas été modifiés ici. Le contrôle global n'est donc pas déclaré réussi.

La recette réutilise l'aperçu local existant sur le port 3100. Les captures `desktop-preview.png`, `desktop-entry.png`, `mobile.png`, `reduced.png` et `no-js.png` montrent les états réels. Les résultats détaillés sont dans `report.json`.

## Limites

Le décor et les projets sont photographiques ; leur profondeur est simulée par CSS. L'aperçu montre au plus six projets par auteur, puis le vidéoclub donne accès au catalogue complet. Les essais navigateur utilisent Edge/Chromium local et une émulation tactile. Aucun essai sur Safari ou sur téléphone physique, aucune mesure matérielle de FPS ou consommation GPU n'est revendiquée.
