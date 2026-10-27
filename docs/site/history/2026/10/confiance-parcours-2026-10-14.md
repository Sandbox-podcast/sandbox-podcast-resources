# Confiance et parcours, 14 octobre 2026

Correction locale des actions A01 et A02 de l'audit du 14 octobre (suivi dans l'[issue #68](https://github.com/Sandbox-podcast/sandbox-podcast-site/issues/68)). Décision : [DD-0025](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0025-confiance-pages-et-archives.md).

## Changements

Les fiches historiques `/projects`, `/models` et `/moves` alimentées par des snapshots `mock` affichent désormais un écran de démonstration sans mesures ni avis simulés. Les liens de récupération mènent aux classements et aux podcasts. Le `noindex` est explicite et les images de partage ne montrent plus les faux rangs. La neutralisation et ses liens sont traduits dans les quatre langues du site. Les fixtures n'ont pas été modifiées.

La route `/charts/skills/[platform]` capturait `2026-10-10` avant `/charts/[slug]/[week]`, puis cherchait un catalogue de plateforme inexistant. Elle reconnaît maintenant les dates et semaines ISO et utilise le rendu des archives. Le catalogue par plateforme reste accessible. La méthode Skills, également masquée par cette route spécialisée, a une route explicite. Le routeur partagé entre langues distingue les mêmes cas.

Le rendu des archives ignorait aussi la date demandée au premier affichage et choisissait la dernière édition. L'initialisation reçoit désormais la date du chemin pour les archives de classement, Rising et l'historique général. Une archive absente ne se rabat pas sur une autre date.

## Vérifications

- Site public : 77 URL contrôlées par GET, 76 valides. La seule erreur est `/charts/skills/2026-10-10` : 404, `noindex` et canonical de la page d'erreur. Rapport complet : `apps/site/.local/trust-routes/sitemap-public-before.json`.
- Serveur local corrigé, base PGlite éphémère : 79 URL du sitemap, 79 réponses 200 indexables avec canonical correspondant. Ce jeu contient des éditions de test identifiées, différentes des données de production. Rapport : `apps/site/.local/badges-public-routes/sitemap.json`.
- Suite de tests du site : 417 tests réussis dans 70 fichiers. Les nouveaux cas couvrent les historiques mixtes réel/simulé, toutes les anciennes fiches et cartes générées, les images neutralisées, la date d'archive conservée malgré une édition plus récente, l'absence d'archive, les filtres, les langues et les erreurs HTTP du sitemap.

## Relancer les contrôles

Depuis la racine du dépôt :

```powershell
pnpm --filter @podcast/site sitemap:check https://www.sandboxpodcast.fr .local/trust-routes/sitemap-public-after.json
pnpm --filter @podcast/site test:public-routes
pnpm check
pnpm build
```

Le contrôle du sitemap échoue si une URL renvoie une redirection, une erreur, un contenu autre que HTML, un `noindex`, un canonical absent ou différent. Il ne suit pas les URL hors domaine et n'utilise aucune session. Les tests de parcours démarrent un serveur sur loopback et une base de test en mémoire ; ils ne migrent ni n'écrivent dans Neon.

## Fichiers concernés

- Provenance et écran public : `src/domain/demo-content.ts`, `src/lib/demo-content.ts`, `src/components/demo-content-page.tsx`, `entity-screen.tsx`, `chart-screen.tsx`.
- Fiches, cartes et aperçus : routes françaises `projects/[slug]`, `models/[slug]`, `moves/[chart]/[week]/[entity]` et `src/lib/og.tsx`.
- Archives : routes `charts/skills/[platform]`, `charts/skills/methodology`, `charts/[slug]/[week]`, `charts/history/[week]`, `charts/rising/[week]`, `charts-experience.tsx`, `shared-pages.tsx`, `i18n/page-routes.ts`.
- Sitemap : `src/app/sitemap.ts`, `src/domain/sitemap-health.ts`, `src/lib/sitemap-audit.ts`, `scripts/check-sitemap.ts`, `scripts/test-public-routes.mjs`, `scripts/badges-fixture-server.mjs`, `package.json`.
- Tests et traductions : `test/demo-content.test.ts`, `test/skills-archive-route.test.ts`, `test/sitemap-health.test.ts`, `test/localization.test.ts`, dictionnaires `en.json`, `es-es.json`, `de-de.json`.
- Documentation : cette livraison, DD-0023 et les index.

Les chemins de code ci-dessus sont relatifs à `apps/site`. Les travaux locaux déjà présents ont été conservés.

## Limites et suite

La correction reste locale. Aucune donnée réelle, migration appliquée, publication, commit ou push n'a été modifié. Le site public conserve donc l'erreur tant que cette livraison n'est pas déployée. Après un déploiement autorisé, relancer le contrôle des 77 URL publiques et vérifier les anciens liens partagés.

L'action A03 sur la cohérence des dates et des méthodes reste à traiter avec l'issue #44. Les contrôles de cette livraison ne valent pas audit complet d'accessibilité, de sécurité ou de performance.
