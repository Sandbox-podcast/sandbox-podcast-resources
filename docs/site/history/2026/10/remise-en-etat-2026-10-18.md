# Classements, News et recherche : corrections du 18 octobre 2026

Lou demande une revue des issues, des PR et du code, avec correction des classements et des pages News. Le lot est préparé dans le dossier local existant. Les changements déjà présents pour YouTube, les épisodes et les kits de relais sont conservés.

## État vérifié sur GitHub et en production

- Les PR [84](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/84), [85](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/85) et [86](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/86) sont ouvertes. Elles traitent les issues 81, 83 et 82. Leurs CI s'arrêtent sur le formatage de `docs/site/issue-68-2026-10-18.md`, avant les autres contrôles.
- Les PR 79 et 80 sont fusionnées sur `main`, mais absentes du checkout de départ, au commit `a6be3ee`. Leurs correctifs sont repris localement avant les nouvelles corrections.
- Le domaine public répond 200 pour l'accueil et les classements GitHub, Skills et Models. `/news` répond 404. L'API `/api/charts/models/current` sert `2026-10-12` avec `week: 12`, alors que cette date appartient à la semaine ISO 42.

## Corrections

Les semaines des éditions datées et des créneaux UTC sont calculées selon ISO 8601, y compris l'année ISO à la frontière de décembre et janvier. Le stockage Markdown accepte aussi les éditions quotidiennes et les créneaux, sans les perdre à la relecture.

La collecte Models conserve les mesures non ambiguës lorsqu'une autre identité présente un conflit. Les candidats en conflit restent en attente, avec un diagnostic explicite. La collecte n'écrit aucune mesure sur une identité choisie arbitrairement. Les versions corroborées v3 demandent toujours leur revue et leur calibration. Les règles des éditions observées GitHub et Skills reprises de la PR 80 restent celles d'ADR-0035.

Le rejeu d'un créneau GitHub exclut les avis OpenSSF collectés après sa fermeture, y compris les observations historiques `legacy`. L'API restitue aussi les références GitHub et OpenSSF réellement figées, que son ancien schéma rejetait. Les tests distinguent une édition corroborée d'une édition observée sans preuve OpenSSF.

La commande `pnpm --filter @podcast/site charts:identities --output=diagnostic-models.json` produit un inventaire en lecture seule des références Models dupliquées, des fiches actives et exclues, des volumes de relevés et des positions déjà publiées. Elle peut lire un export avec `--file=export-models.json`. Les propositions canoniques restent `approved: false` ; la commande n'effectue aucune fusion et refuse d'écraser un rapport existant. Voir [ADR-0036](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0036-isolement-des-identites-models-en-conflit.md).

La recherche lit le dernier Top publié de chacune des quatre familles. Elle couvre les noms, descriptions et identifiants des dépôts et modèles, puis ouvre leur fiche publique. Les brouillons et anciennes éditions ne remplacent pas une publication récente vide. Une panne de base laisse la recherche éditoriale disponible, y compris sur les routes traduites. Les titres de l'accueil sont traduits en anglais, espagnol et allemand.

Les layouts et les dictionnaires publics conservent leur dernière publication chargée, ou les fichiers Git si aucun contenu n'a encore été chargé, pendant une panne Postgres. Ils réessaient après cinq secondes. Les lectures et écritures admin continuent à signaler leurs erreurs. Les tests vérifient aussi la reprise après rétablissement et la conservation des snapshots.

News utilise un chemin Python adapté à Windows et Linux. L'extraction préfère un corps exploitable à une métadescription trop courte. L'accueil peut ouvrir la rubrique publique après activation explicite. Une rubrique activée sans article affiche une attente ; une panne SQL affiche une indisponibilité distincte. Ces deux états restent en `noindex`. Le drapeau de publication fermé conserve les 404.

Le formatage du document qui bloque les trois CI est corrigé. ESLint exclut les copies générées de `gsap.min.js` dans les rendus vidéo de révision, comme il exclut déjà les dépendances du projet de montage initial. Les sources et les tests du dépôt restent contrôlés.

## Vérifications

Les tests ciblés couvrent les identités Models et les éditions, la recherche Postgres et son repli, les métadonnées traduites et les états News. Une traduction Argos réelle produit une fiche complète en EN/ES/DE sur le poste local.

La recette navigateur News utilise une base PGlite éphémère sur loopback. Elle vérifie les quatre langues sur ordinateur et mobile, le secret d'ingestion, l'insertion idempotente, les filtres, les liens sources, les canoniques et les liens de langues. Elle simule aussi une table SQL absente. Les sept groupes de vérification passent sans erreur JavaScript. Commande reproductible : `pnpm --filter @podcast/site test:news:e2e`.

| Contrôle                      | Résultat                                                                               |
| ----------------------------- | -------------------------------------------------------------------------------------- |
| `pnpm check`                  | Formatage, lint, types et 916 tests réussis : 881 site, 7 générique, 4 jingles, 24 BIS |
| Build de production définitif | Réussi, 204 pages générées                                                             |
| `content:check`               | Zéro erreur, zéro avertissement                                                        |
| Audit des dépendances         | Aucune vulnérabilité connue signalée                                                   |
| Images OpenGraph              | Les 13 routes incluent leurs cinq polices                                              |
| Sécurité admin et badges HTTP | Réussis sur le build définitif, sans base distante                                     |
| Sitemap et parcours publics   | 333 URL valides, 49 contrôles HTTP réussis                                             |
| Consentement navigateur       | 27 contrôles réussis, services externes simulés                                        |
| News navigateur               | Sept groupes de vérification réussis, zéro erreur JavaScript                           |

Les parcours HTTP couvrent les recherches par identifiant GitHub et par slug Skills/Models dans les quatre langues, les liens vers les fiches, les titres d'accueil traduits, les archives, les méthodes et les images de partage.

Le premier audit du sitemap a dépassé le délai de trente secondes pendant la compilation à froid de l'accueil, alors que plusieurs builds et recettes tournaient. La relance avec moins de charge passe sans modifier ce délai. Le premier contrôle global a aussi révélé qu'un test de bibliothèque vide lisait la publication locale réelle. La suite est isolée avec une doublure de lecture et une remise à zéro du contenu ; son assertion est conservée. La dernière exécution de `corepack pnpm check` termine avec le code zéro et tous les tests réussis.

## Mise en service et limites

Aucun commit, push, changement de PR, déploiement, migration Neon ou article publié en production n'est effectué pendant cette tâche. Le code local et ses essais ne changent pas le site public.

L'accès Vercel connecté refuse la lecture du projet sous le scope `sandboxpodcastpro-5518` avec HTTP 403. La CLI Vercel n'est pas installée et les accès Postgres de production ne sont pas disponibles dans l'environnement local. Le plugin Neon est disponible dans le catalogue, mais il n'est pas installé ni connecté pendant cette tâche. La revue effective des 36 références Models et l'isolation Neon Preview/Production ne sont donc pas confirmées.

Pour ouvrir News, appliquer la migration 0016 si elle manque, configurer les variables et vérifier un premier cycle réel selon DD-0057, puis activer `SANDBOX_NEWS_PUBLIC=1` dans le déploiement autorisé. La recette locale ne remplace pas ce cycle réel de génération. Les identités Models contradictoires demandent une correspondance canonique après examen de leurs références et de leurs historiques. Aucune édition nouvelle ni baseline absente n'est inventée.
