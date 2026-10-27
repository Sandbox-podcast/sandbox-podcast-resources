# Emails répétés du workflow News, 21 octobre 2026

Lou signale cinq emails GitHub annonçant un échec de `SANDBOX News refresh`, puis demande de passer temporairement le site en français et de retirer le choix de langue en haut à droite.

## Cause vérifiée

Les runs [39651794601](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39651794601) et [39649547194](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39649547194) échouent dans `news-translate-pending.ts`. Le moteur altère les marqueurs numériques ; la restauration produit `Nombre protégé News perdu` dans les trois langues. Le script termine avec cinq articles incomplets et un code de sortie 1. Les reprises suivantes retrouvent les mêmes articles. Les passages observés se succèdent à environ quinze à vingt-cinq minutes, en plus du planning horaire. Le mécanisme de reprise après échec est décrit dans [ADR-0039](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0039-controle-externe-des-traitements-planifies.md).

Le parcours ultérieur des dix pages de l’API publique retrouve six fiches ayant au moins une langue absente. Une première tentative de correction locale, essayée avec le vrai moteur sur ces six textes, en complète cinq ; la dernière échoue au contrôle du découpage d’une phrase allemande. Cette tentative de correction est retirée du lot après la demande de suspension de Lou.

Les derniers runs terminés de CI (39609071089), Charts (39624763575) et YouTube (39609071081) réussissent au moment du contrôle. Le diagnostic ne nécessite aucun changement de préférence email du compte.

## Décision retenue

Voir [DD-0075](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0075-suspension-traductions.md), décision explicite de Lou le 21 octobre 2026.

- Le sélecteur de langue est retiré de l’en-tête, sur ordinateur et mobile.
- Les requêtes de lecture vers `/en`, `/es-es` et `/de-de`, ainsi que leurs sous-pages, reçoivent une redirection temporaire 307 vers le chemin français. Les paramètres sont conservés. Une préférence de langue enregistrée et la langue du navigateur ne redirigent plus l’accueil vers une traduction.
- Le sitemap annonce uniquement le français. Les métadonnées publiques ne proposent plus de variantes étrangères.
- Le job `translations` est retiré du workflow News. La collecte, la rédaction française, la publication et les contrôles de santé restent actifs. Le worker publie déjà en français avec `deferTranslations: true`.
- Les dictionnaires, traductions stockées et outils de traduction sont conservés pour une réactivation ultérieure. Aucune donnée réelle n’est supprimée.

Les tests de parcours étrangers vérifient désormais leur redirection vers le français. Les tests des outils conservés continuent à contrôler leur fonctionnement hors publication publique.

## Validation et activation

Les essais utilisent des données publiques en lecture seule ou une base locale éphémère ; aucune traduction n’est écrite en production.

Résultats du lot final, sur la branche locale `codex/french-only-news` :

- `corepack pnpm check` réussit : formatage, lint, types, 1 300 tests du site, 7 tests du générique, 4 tests des assets et 24 tests BIS, soit 1 335 tests.
- `corepack pnpm build` réussit avec 207 pages générées.
- `test:public-routes` valide 85 URL du sitemap et 47 contrôles HTTP, dont les redirections temporaires des trois anciennes langues et la conservation des paramètres.
- `test:news:e2e` valide 11 groupes de vérification sans erreur JavaScript : publication dans la base de test, rendu français à 390 et 1 440 pixels, sélecteur absent, redirections, filtres, pagination et panne de base. Les deux captures ont été inspectées.
- `test:seo:e2e` valide 22 contrôles HTTP et navigateur, avec 10 captures.
- `git diff --check` réussit.

Les fichiers applicatifs modifiés concernent le workflow News, l’en-tête, la note du fil, la politique de langues publiques, les redirections, les métadonnées et le sitemap. Les tests et scripts de recette sont adaptés au mode français. Le diagnostic, DD-0075, l’index documentaire et les questions ouvertes consignent cette suspension.

Le lot est préparé dans un worktree issu de `main` (`a4b6d13`) pour préserver les changements du checkout principal. Le correctif doit être livré sur `main` pour arrêter les échecs distants liés aux traductions. Les commits, pushes et PR restent soumis à la demande explicite de Lou prévue par `AGENTS.md`. Après livraison, vérifier le sélecteur absent sur le site public et un nouveau run News sans job de traduction. La suspension ne promet pas la disparition d’alertes correspondant à d’autres pannes.
