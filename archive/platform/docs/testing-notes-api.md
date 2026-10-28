# Notes de tests de l'ancienne API (extraites de `docs/testing.md`)

## Exception de lint documentée : tests HTTP de l'API

`apps/api/test/api.test.ts` et `apps/api/test/harness.ts` désactivent les règles `no-explicit-any`, `no-unsafe-*` et `restrict-template-expressions` (voir `eslint.config.js`). Ces tests lisent des corps de réponse JSON dont la forme est précisément ce qu'ils vérifient ; les typer un à un doublerait les tests sans les rendre plus sûrs. Le code de `apps/api/src` n'a aucune exception.

## Tests d'intégration avec PostgreSQL

`apps/api/test/api.test.ts` utilise un vrai PostgreSQL (`pnpm env:init && pnpm db:up` dans `apps/api`), un schéma isolé par suite. Si la base est injoignable, ces tests sont **sautés avec un avertissement explicite** (le résumé de Vitest indique le nombre de tests sautés) : un résultat vert avec des tests sautés n'est pas une preuve, à lire dans le résumé.
