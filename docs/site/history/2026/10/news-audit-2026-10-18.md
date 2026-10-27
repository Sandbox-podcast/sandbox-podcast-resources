# Audit de SANDBOX News et des tâches planifiées

État du 18 octobre 2026. Le périmètre retenu par Lou est "IA + Développement" : GitHub, open source, programmation et outils techniques inclus. Le site possède déjà l'hébergement, la base, les quatre langues et un ordonnanceur. La première implémentation peut réutiliser ces éléments ; la qualité éditoriale autonome dans les quatre langues reste à démontrer sans API payante.

Décisions : [périmètre News](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0052-sandbox-news-ia-et-developpement.md) et [optimisation des tâches](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0033-optimisation-des-taches-planifiees.md).

## Existant vérifié

| Domaine              | Constat dans le code                                                                                                        | Conséquence pour News                                                                                                                                    |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Application          | `apps/site`, Next.js déclaré `^16.3.8`, React `^19.3.0`, TypeScript strict, Zod, Tailwind 4                                 | Ajouter la rubrique dans cette application.                                                                                                              |
| Base                 | Client Neon, schéma Drizzle, migrations `0000` à `0015`                                                                     | Préparer des tables News séparées, avec une migration additive.                                                                                          |
| Données              | Publications et données de classements en Postgres, contenu initial et archives dans Git                                    | Lire les actualités en base sans redéployer pour chaque publication.                                                                                     |
| Internationalisation | `fr-FR`, `en`, `es-ES`, `de-DE`, composants communs, canoniques, alternates et barrières d'indexation                       | Réutiliser le routage existant ; une nouvelle route doit aussi être déclarée dans les pages partagées.                                                   |
| Traduction           | Dictionnaires et imports manuels du harnais, empreintes des sources et validations                                          | Les protections sont réutilisables ; le déclenchement manuel ne répond pas à l'autonomie de News.                                                        |
| Interface            | Archivo, Newsreader, JetBrains Mono, fond `#05090d`, accent `#1cb5ed`, en-tête et navigation communs                        | Une liste dense intégrée à SANDBOX ; conserver les autres pages.                                                                                         |
| GitHub               | Client REST/GraphQL, retries bornés, délais, validations Zod et traitement des quotas ; historique d'étoiles et de poussées | Réutiliser ces mécanismes et les observations admissibles. Ajouter les releases ; ne pas confondre signal d'étoiles et actualité.                        |
| RSS                  | `/feed.xml` émet les épisodes publiés                                                                                       | Ce flux n'est pas un collecteur de sources externes.                                                                                                     |
| IA                   | Aucun moteur de rédaction ou de traduction News dans l'application                                                          | Argos et l'inférence CPU restent des travaux nouveaux. L'API OpenAI de l'ancien outil YouTube est indépendante et ne doit pas être réutilisée pour News. |
| Sécurité et mesure   | Authentification admin, secret cron, CSP, GA4 soumis au consentement                                                        | Réutiliser les protections applicables ; garder les liens externes directs et les mesures non bloquantes.                                                |

Fichiers examinés : `package.json`, `src/db/client.ts`, `src/db/schema.ts`, `src/i18n/`, `src/components/shell.tsx`, `src/components/nav.tsx`, `src/app/globals.css`, `src/pipeline/github-client.ts`, `src/pipeline/github-bursts-jobs.ts`, `src/lib/github-bursts-store.ts`, `src/lib/content-translations-store.ts`, `src/app/feed.xml/route.ts`, `src/app/api/cron/[job]/route.ts`, scripts et workflows. Les chemins sans préfixe sont relatifs à `apps/site`. `old/` reste hors du périmètre.

## Comptes et consommations

Contrôles en lecture dans les consoles déjà connectées. Le connecteur Vercel n'accédait pas au projet ; le navigateur donne accès au bon compte et résout cette inconnue.

- Vercel : équipe `sandboxpodcastpro-5518`, projet `sandbox-podcast`, forfait Hobby. La production suit `main` dans `apps/site`. La page Cron Jobs affiche l'aide de démarrage et aucune tâche configurée ; l'option générale est activée. La valeur vide de `vercel.json` concorde avec cette page.
- Vercel, fenêtre affichée du 18 septembre au 18 octobre : 1,46 Go de transfert sur 100 Go, 858,77 Mo de transfert origine sur 10 Go, 52 816 invocations sur 1 000 000, 25 040 lectures ISR sur 1 000 000 et 17 142 écritures ISR sur 200 000. Ces compteurs concernent le périmètre de l'équipe affiché, pas une mesure du futur trafic News.
- Neon : `neon-yellow-planet`, projet `fragrant-lab-14685793`, Frankfurt, forfait Free géré par Vercel. La ressource est reliée au projet `sandbox-podcast` pour Preview et Production. Cette connexion ne prouve pas à elle seule l'isolation des branches.
- Neon, compteurs affichés depuis le 7 octobre : 21,36 CU-heures, 78,38 Mo de stockage, 2,68 Mo d'historique et 1,2 Go de transfert réseau. La branche principale utilise un compute de 0,25 CU, Postgres 18 et six heures de rétention d'historique. Ces six heures ne sont pas une politique de conservation des actualités.
- GitHub : dépôt `Sandbox-podcast/sandbox-podcast-site` public, trois workflows actifs, runners `ubuntu-latest` dans leur configuration.

Les [crons Vercel Hobby](https://vercel.com/docs/cron-jobs/usage-and-pricing) sont limités à une fois par jour : ils ne conviennent pas à la collecte horaire. Les [runners GitHub standard sur dépôt public](https://docs.github.com/en/billing/concepts/product-billing/github-actions) ne facturent pas leurs minutes de calcul ; les caches et artefacts ont leurs limites propres. Il faut donc contrôler ces volumes, même ici.

Le [catalogue Neon Free consulté](https://neon.com/pricing) annonce 100 CU-heures et 1 Go de stockage par projet. L'usage News s'ajoutera à celui du site et des classements. Ces limites publiques ne remplacent pas la vérification des droits précis de l'intégration et la mesure en charge. La cible de coût est 0 euro ; l'audit ne démontre pas encore que tous les traitements éditoriaux y tiendront.

## Inventaire des tâches

Les horaires ci-dessous décrivent la configuration avant les corrections locales. Les expressions GitHub Actions utilisent UTC.

| Workflow ou tâche                    | Déclenchement                                          | Traitement                                                                                                    |
| ------------------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| CI                                   | Push et PR                                             | Format, lint, types, tests, build, parcours HTTP et navigateur, audit des dépendances, scan des secrets.      |
| Classements, découverte              | Chaque jour à 01:17                                    | Trending et découverte API GitHub, via les routes Vercel authentifiées.                                       |
| Classements, collecte et publication | 03:17 et 15:17, ou lancement manuel                    | Collecte des trois familles, reprises bornées, gel des éditions et contrôle de ce que les lecteurs reçoivent. |
| Classements, fraîcheur               | Chaque heure à la minute 23                            | Lecture des éditions publiques après installation Node/pnpm et des dépendances.                               |
| Classements, poussées                | Même déclenchement horaire, si l'indicateur est activé | Collecte du signal GitHub via une route authentifiée, dans un second runner.                                  |
| YouTube, tests                       | Push et PR                                             | Tests Python et journal Postgres isolé.                                                                       |
| YouTube, chaîne                      | Toutes les 30 minutes, ou lancement manuel             | Détection d'épisodes, propositions de miniatures, commentaires ou réponses selon les options autorisées.      |

Les exemples de planification décrits dans d'anciens ADR ne sont pas des tâches actives. Les Shorts sont traités par d'autres commandes ; le workflow de suivi ne les publie pas.

## Historique réel des Actions

Échantillon : les 100 dernières exécutions renvoyées par l'API lors du contrôle. Il comprend 33 exécutions CI, 47 YouTube et 20 Classements. Il ne constitue pas un mois complet.

- Les 19 exécutions programmées et l'exécution manuelle des Classements sont toutes en échec dans cet échantillon. Le [dernier contrôle horaire](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39122853660) reçoit les éditions du 10 octobre pour GitHub et Skills, et du 12 octobre pour Models. Leur ancienneté explique son échec.
- Ce contrôle utilise environ 35 secondes de job : checkout de 8 secondes, préparation pnpm de 7 secondes, préparation Node de 8 secondes, installation de 4 secondes et contrôle public de 4 secondes. Mesure d'une seule exécution, sans projection de gain garanti.
- Le [dernier rafraîchissement détaillé](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39110199782) dure environ 7 minutes 38 secondes. GitHub et Skills rapportent des collectes partielles ; Models rapporte des échecs. Les reprises ne corrigent pas les données ou accès manquants. Retirer le contrôle de fraîcheur masquerait ce problème.
- Le [dernier suivi YouTube](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39123502566) dure environ 18 secondes de job. Il installe ses dépendances pendant 7 secondes, puis appelle le programme sans OAuth configuré. Le code produit alors un passage sans effet. Les 14 suivis programmés de l'échantillon durent de 20 à 40 secondes entre début et fin de workflow ; ces durées ne sont pas des minutes facturées.
- Les tests push et PR existent dans les deux workflows concernés. Une PR vérifie son contexte d'intégration ; ce n'est pas une raison suffisante pour supprimer un gate exigé par `AGENTS.md`.

GitHub indique que les [déclenchements planifiés peuvent être retardés ou omis](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule). Ils se désactivent aussi après 60 jours sans activité sur un dépôt public. News doit conserver un curseur durable par source et rattraper les données encore accessibles, sans promettre une exécution exacte chaque heure ni un rattrapage illimité si une source ne garde qu'un historique court.

## Optimisations locales

Lou a demandé un lancement YouTube manuel à l'ajout de l'épisode hebdomadaire. Le cron de 30 minutes est retiré du fichier local ; le traitement garde ses prérequis et les tests restent automatiques.

Le contrôle OAuth passe avant les installations, le cache pip est activé et les verrous des tests et du traitement sont séparés. Les poussées GitHub sont regroupées avec le contrôle horaire dans un seul job. La collecte manuelle et la collecte programmée partagent désormais un verrou propre, pour éviter deux rafraîchissements simultanés.

Ces changements n'activent ni publication YouTube, ni API payante. Le workflow distant garde son ancienne configuration jusqu'au push autorisé. Les gains après activation restent à mesurer. L'arrêt du cron YouTube retire 48 déclenchements théoriques quotidiens ; ce nombre n'est pas un relevé d'exécutions effectives.

## Implémentation News proposée

1. Ajouter une rubrique `/news`, `/en/news`, `/es-es/news` et `/de-de/news`, rendue côté serveur avec les composants et les règles SEO existants. Une ligne par événement, source, date réelle, catégories, recherche, tri et pagination par curseur. Le compteur de sources et la date de synchronisation viennent de résultats réels.
2. Réutiliser le déclenchement horaire de GitHub Actions. Ajouter un job News indépendant plutôt qu'un nouveau planificateur. Exécuter collecte, déduplication et traitements locaux sur le runner ; Vercel sert les données déjà enregistrées. Aucun redéploiement par actualité ni inférence à la lecture.
3. Préparer des tables `news_sources`, `news_runs`, `news_candidates`, `news_events`, `news_translations` et un historique des décisions. Garder les états de collecte par source, les identifiants externes, les empreintes, les corrections et les références secondaires. Un registre en base, modifiable par une CLI validée, évite un backoffice complexe et permet les changements de source sans redéploiement.
4. Collecter par RSS/Atom ou API vérifiés, avec ETag, Last-Modified, pagination et fenêtres de reprise bornées. Valider les URL et les réponses, bloquer SSRF et redirections dangereuses, borner taille, durée et retries. Un échec reste propre à sa source. Le succès de collecte et le nombre d'actualités publiées ont des états distincts.
5. Dédupliquer URL et identifiant, puis entité, produit, version, événement et proximité temporelle. Une URL nettoyée ne perd que ses paramètres de tracking connus. Les titres seuls et les étoiles ne suffisent pas. Les rapprochements multilingues ambigus attendent un traitement complémentaire.
6. Calibrer le scoring déterministe sur un corpus réel avec décisions justifiées. Générer une phrase seulement quand les faits sont suffisants. Sans modèle, les annonces structurées telles que les releases sont les cas les plus contrôlables ; une couverture large de presse avec reformulations naturelles n'est pas démontrée par des modèles de phrases.
7. Évaluer [Argos Translate](https://argos-translate.readthedocs.io/en/latest/) pour les seules actualités retenues. Mettre en cache les paquets et traductions par empreinte, conserver noms, nombres et versions. Une traduction invalide n'est pas déclarée prête. Les contrôles déterministes ne prouvent pas toute l'équivalence sémantique.
8. Tester ensuite un seul petit modèle CPU quantifié, parmi ceux demandés, avec [llama.cpp](https://github.com/ggml-org/llama.cpp). Mesurer son apport avant de l'activer ; aucune bascule vers un fournisseur payant. Les contenus collectés sont des données non fiables, y compris pour le modèle, sans accès à des outils ou secrets.

Le catalogue complet reste à vérifier source par source. Les ouvertures web tentées sur certains flux n'ont pas donné de réponse exploitable ; cela ne prouve pas leur indisponibilité. Aucun flux n'est déclaré actif dans ce bilan. Les endpoints [GitHub Releases](https://docs.github.com/en/rest/releases/releases#list-releases) et [Search repositories](https://docs.github.com/en/rest/search/search#search-repositories) sont documentés officiellement ; chaque connecteur doit encore être testé sur ses dépôts cibles. Aucun endpoint officiel Trending n'est supposé.

## Mesures requises avant mise en service

Pour 30 publications quotidiennes, compter 900 publications sur un mois de 30 jours et 720 déclenchements horaires théoriques. Avec une proportion retenue `p`, le modèle devra traiter jusqu'à `30 / p` candidats quotidiens s'il participe à la sélection de tous les présélectionnés. Les rejets doivent entrer dans la mesure.

Le benchmark doit comparer le pipeline déterministe et le modèle local sur les mêmes candidats : téléchargement à froid, démarrage à chaud, mémoire maximale, temps par candidat, erreurs factuelles, qualité des quatre langues et stabilité. Le total mensuel estimé combine les 720 préparations, les candidats acceptés et rejetés, les traductions et les reprises. Aucune durée par actualité ni proportion retenue n'est encore mesurée.

Prévoir les tests de rejeu, doublons entre sources et langues, corrections, source inaccessible, dates invalides, liens directs, pagination, sécurité des URL et des écritures, informations insuffisantes, traductions manquantes, charge et mode sans publication. Le journal durable ne doit pas être remplacé par un cache Actions. La rétention des candidats, logs et caches doit tenir dans les quotas sans suppression de données réelles non autorisée.

## Validation du lot

`corepack pnpm check` passe avec Node 24.12.0 et pnpm 12.9.1 : format, lint, types et 715 tests du site, plus 7 tests de timeline, 4 tests média et 24 tests Épisode BIS. Les 12 nouveaux tests couvrent le précontrôle YouTube, les conditions du lancement manuel, les prérequis d'écriture, les étapes coûteuses et les verrous des deux workflows. Les tests existants du contrôleur et de la découverte restent valides.

Les tests Bash nécessitent ici une exécution hors du bac à sable Windows : leur processus y échouait au démarrage, y compris dans la suite existante. Aucun test n'a été désactivé. Les trois nouveaux documents passent le vérificateur rédactionnel et `git diff --check` ne relève pas d'erreur.

Fichiers de ce lot : les deux workflows `charts-refresh.yml` et `youtube-growth.yml`, `apps/site/test/workflow-optimization.test.ts`, le README de `tools/youtube-growth`, ce bilan, DD-0052, ADR-0033, la note de remplacement de cadence dans ADR-0025, l'index `docs/README.md` et `docs/open-questions.md`. Les deux derniers fichiers contenaient déjà des modifications, conservées.

Les modifications locales antérieures de slides, SEO et réseaux sociaux sont conservées. Aucun service ni compte n'est créé, aucune base réelle n'est modifiée et aucune actualité n'est publiée. La fonctionnalité News n'est pas encore implémentée : ce lot livre son audit, sa proposition et l'optimisation des workflows existants.
