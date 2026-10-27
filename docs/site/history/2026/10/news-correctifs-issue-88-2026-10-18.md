# News : corrections de l'issue 88

Le 18 octobre 2026, la lecture du code confirme deux réponses 404 prévues sur `/news` : le drapeau `SANDBOX_NEWS_PUBLIC` fermé et l'absence de fiche récente en base. La première protège une fonctionnalité non activée ; la seconde masquait le début d'exploitation ou un flux devenu vide.

Le lot local conserve l'activation explicite. Une fois le drapeau ouvert, le site affiche une attente quand le flux est vide et un message distinct quand Postgres échoue. Ces états restent `noindex`. La carte d'accueil et le radar ouvrent aussi News après son activation publique. La décision figure dans [DD-0059](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0059-disponibilite-news-et-collecteur-linux.md).

Deux défauts du collecteur sont corrigés : le traducteur cherchait le Python Windows sur le runner Ubuntu ; le parseur pouvait conserver une courte description au lieu du corps d'article, puis le générateur refusait cet extrait insuffisant. Les chemins du moteur ne dépendent plus du dossier courant et restent compatibles avec la compilation Turbopack de Next.

## Vérifications locales

Les six suites News passent : 69 tests couvrent notamment les contrôles de source, les citations, les quatre traductions, le stockage idempotent, la migration 0016, l'authentification cron, le drapeau public et les états de page. Le moteur Argos installé a aussi produit une fiche complète EN/ES/DE en 46 secondes sur le CPU local. Cette durée décrit un essai local, sans garantie de débit sur GitHub Actions.

La recette `pnpm --filter @podcast/site test:news:e2e` utilise un serveur Next et une base PGlite éphémères, accessibles uniquement sur `127.0.0.1`. Elle n'appelle aucun média réel. Les articles de test portent la mention FIXTURE et restent dans cette base locale.

| Parcours                         | Résultat observé                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------------ |
| Drapeau fermé                    | 404 sur les quatre pages et l'API                                                                |
| Drapeau ouvert, sans secret cron | API 401 en lecture et en écriture                                                                |
| Flux sans fiche                  | Quatre pages 200, attente explicite, noindex                                                     |
| Premier envoi puis répétition    | Une insertion, puis aucune ; URL enregistrée accessible à l'API authentifiée                     |
| Fiche publiée                    | FR/EN/ES/DE vérifiés à 1440 et 390 px : titre, trois phrases, lien source, canonique et hreflang |
| Recherche et filtre média        | Résultats filtrés puis rétablis par le bouton de réinitialisation                                |
| Table News indisponible          | Quatre pages avec message d'indisponibilité et noindex ; API 503                                 |

Le navigateur ne remonte aucune erreur JavaScript. Le rapport JSON et les captures restent dans `apps/site/.local/news-e2e/`. Le contrôle des layouts publics contre une panne éditoriale complète fait partie du lot global de correction.

## À mettre en service après accord

Le test de migration emploie PGlite ; il ne modifie pas Neon. Aucune variable Vercel ou GitHub, aucune donnée réelle et aucun déploiement n'ont été modifiés pour cette correction. La production reste soumise à [DD-0057](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0057-automatisation-production-news.md) : migration 0016, drapeau Vercel, variable GitHub, secret cron concordant et contrôle d'un premier cycle réel de collecte, génération et traduction. La qualité des résumés et l'accessibilité actuelle des médias restent à vérifier lors de ce cycle.
