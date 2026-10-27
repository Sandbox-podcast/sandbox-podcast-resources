# Issue 68 : traductions, collecte Models et mesure

16 octobre 2026. Décisions : [DD-0048](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0048-indexation-traductions-et-suivi-des-classements.md).

## Lot local

- ES/DE autorisés à l'indexation selon les restrictions de la page source. Canoniques et liens de langue réciproques dans les métadonnées et le sitemap. Recherche, démonstrations et vidéoclub restent exclus.
- 2 403 sources locales remplies dans les trois dictionnaires. Compléments pour l'épisode et les textes édités seulement en production, une phrase d'article et 24 descriptions publiques de classements, avec leurs extraits. Les liens et les données chiffrées restent communs.
- Models : priorité aux références exactes des fournisseurs. Les homonymes distincts sont isolés, les historiques et exclusions sont conservés, les vraies contradictions restent bloquées.
- Mesure des liens du plateau ajoutée. Speed Insights suit le consentement, sans paramètres d'URL ni administration.
- Email rétabli dans le footer. La publication de la procédure proposée est abandonnée.

## Vérifications de production

Le secret cron existe et la [relance du 16 octobre à 14 h 40 UTC](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/38917678851) atteint les collecteurs. GitHub manque d'historique, Skills reste partiel et Models échoue sur `phi4miniinstructgguf`. La source connue de ce dernier est `MaziyarPanahi/Phi-4-mini-instruct-GGUF` ; aucun rapprochement ni modification manuelle de données n'a été réalisé.

Les éditions publiques contrôlées restent au 10 octobre pour GitHub et Skills et au 12 octobre pour Models. Deux exécutions programmées réussies avec des éditions fraîches restent nécessaires. L'historique réel et la calibration des profils ne sont pas remplacés par le correctif de collision.

GA4 reçoit `youtube_open` avec `placement=home` et `experience_interaction`. Le contrôle Vercel Speed Insights n'affiche pas encore de mesures. Détails dans [le plan de mesure](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/site/google-analytics.md).

## Validation et mise en ligne

`pnpm check` passe : format, lint, types, 686 tests du site, 7 tests de la vidéo d'introduction, 4 tests des jingles et 24 tests BIS. La recette de consentement avec Edge et services tiers simulés passe : 8 contrôles en mode bloqué et 17 en mode actif, dont les liens de découverte sur ordinateur et mobile. Les tests Models couvrent l'intégrité des sources et mesures sur Postgres. Le build webpack passe avec 203 pages générées. `git diff --check` ne signale pas d'erreur.

Le contrôle HTTP du build final confirme les pages `/es-es/about` et `/de-de/about` indexables, leur canonique dans la langue attendue, les quatre liens de langue et l'email du footer. La recherche reste `noindex` et le sitemap exclut les routes traduites inexistantes. L'origine locale configurée est `http://localhost:3000` ; ce contrôle ne remplace pas celui du domaine public après déploiement.

Le lot n'est pas déployé. Le CLI Vercel local n'a accès qu'à l'équipe `loucore-9279`, tandis que le projet est dans `sandboxpodcastpro-5518`. Les accès de consultation du navigateur fonctionnent. Lou a autorisé le commit, le push et une PR regroupant ce lot.

Un suivi dans ce chat contrôle les classements et les mesures à 8 h 30 et 20 h 30. Il reste silencieux tant que le déploiement manque ou que l'état est inchangé. Il ne compte ni les relances manuelles ni les contrôles horaires comme rafraîchissements programmés réussis.
