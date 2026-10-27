# Référencement de Sandbox et plan de progression

Audit du 18 octobre 2026. Objectif de Lou : faire découvrir Sandbox aux personnes qui recherchent des actualités et des informations sur l'IA, puis en faire une référence francophone.

Suite locale : les [correctifs d'images et de traductions](correctifs-locaux.md) répondent aux problèmes relevés ici. L'audit ci-dessous décrit la production consultée avant leur déploiement.

Le contrôle HTTP ne révèle aucun blocage général d'indexation sur les 301 URL du sitemap. La progression dépend surtout de contenus originaux accessibles par sujet, de classements à jour et de la collecte des données Search Console. La mesure mobile de laboratoire révèle aussi un LCP à améliorer. Aucun objectif de trafic ni de position n'est annoncé sans point de départ mesuré.

## Ce qui a été contrôlé

- Sitemap public, puis 301 URL, sans session et sans suivre les redirections. Réemploi du contrôle du dépôt `inspectSitemapPage` : statut, type HTML, robots et canonique.
- Cinq lectures supplémentaires : robots, RSS, recherche, vidéoclub et une URL inexistante. Au maximum deux requêtes simultanées.
- Métadonnées, titres, H1, langues, liens de langue, premiers caractères du contenu principal et liens contextuels. Les scripts Next sont retirés avant l'analyse du HTML.
- Rendu navigateur d'un épisode lors du premier diagnostic et d'une fiche anglaise pendant cet audit. Les données structurées du podcast et de la vidéo sont présentes ; aucun test Google de résultats enrichis n'a été effectué.
- GA4 sur le compte Sandbox, Speed Insights Production Desktop/Mobile et PageSpeed Insights Mobile.
- Création des demandes de validation Search Console Domaine et Préfixe d'URL. La propriété vérifiée, l'inspection Google et la réception du sitemap attendent encore la validation DNS.
- Échantillon de résultats et lecture de sites concurrents. Cet échantillon ne fournit ni volumes de recherche ni classement Google géolocalisé reproductible.

Preuves publiques résumées dans [inventaire-url.csv](inventaire-url.csv). Les réponses détaillées, captures et états des tableaux sont dans `.local/seo-audit-2026-10-18/`, hors Git. Les durées HTTP du crawl ne sont pas des Core Web Vitals.

## Indexabilité technique

| Contrôle                    | Résultat au 18 octobre                                                         | Interprétation                                                            |
| --------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| Sitemap XML                 | HTTP 200, 301 URL uniques                                                      | Accessible depuis le réseau de contrôle ; réception Google non confirmée  |
| URL du sitemap              | 301 sur 301 en HTTP 200, HTML, robots indexables, canonique conforme           | Conditions techniques vérifiées ; ne prouve pas l'indexation Google       |
| Français                    | 76 URL                                                                         | Inclut un épisode, 34 projets personnels et 20 profils de projets classés |
| Anglais, espagnol, allemand | 75 URL par langue                                                              | L'indexabilité ne valide pas la qualité de traduction                     |
| Liens de langue HTML        | Aucune cible hors sitemap ni absence de retour détectée sur les liens déclarés | Les pages sans liens de langue ne sont pas comptées comme erreurs         |
| Recherche                   | HTTP 200, `noindex, follow`, hors sitemap                                      | Conforme à la restriction prévue                                          |
| Vidéoclub                   | HTTP 200, `noindex, nofollow`, hors sitemap                                    | Conforme au choix existant                                                |
| URL inexistante de contrôle | HTTP 404, `noindex`                                                            | Pas de faux statut 200 sur cette URL                                      |
| Robots                      | Exploration publique autorisée ; administration exclue ; sitemap annoncé       | Pas de blocage général observé                                            |
| Domaine HTTPS sans www      | 308 vers HTTPS avec www                                                        | Destination cohérente avec les canoniques                                 |
| Domaine HTTP sans www       | 308 vers HTTPS sans www, puis 308 vers www                                     | Deux sauts ; simplification secondaire                                    |
| RSS                         | HTTP 200                                                                       | Accessible ; pas de conclusion sur sa consommation par les moteurs        |

Le sitemap peut être soumis à Google sans être intégralement indexé. La décision finale dépend de l'exploration et de l'évaluation des pages. [Guide Search Console de Google](https://developers.google.com/search/docs/monitor-debug/search-console-start).

### Échantillon destiné à l'inspection Google

| URL                       | HTTP, robots, canonique | Inspection Search Console             |
| ------------------------- | ----------------------- | ------------------------------------- |
| `/`                       | Conforme                | En attente de validation de propriété |
| `/podcast`                | Conforme                | En attente                            |
| `/episodes/1`             | Conforme                | En attente                            |
| `/charts/github`          | Conforme                | En attente                            |
| `/charts/skills`          | Conforme                | En attente                            |
| `/charts/ai-models`       | Conforme                | En attente                            |
| `/time-machine`           | Conforme                | En attente                            |
| `/en/nos-projets/sillage` | Conforme                | En attente                            |

Pour chaque inspection : relever l'état d'indexation, la dernière exploration, la canonique choisie par Google, celle déclarée par le site et l'éventuelle raison d'exclusion. Demander une indexation après correction seulement pour les pages prioritaires concernées.

## Search Console et mesure actuelle

Le compte Google Sandbox est accessible. L'ajout de la propriété Domaine `sandboxpodcast.fr` demande une validation DNS chez IONOS. La connexion IONOS exige un code envoyé par email ; le code a été demandé à Lou dans le chat. Aucun enregistrement DNS n'est encore ajouté.

Une propriété Préfixe `https://www.sandboxpodcast.fr/` a également été préparée pour tester la vérification avec GA4. Google refuse cette méthode : il ne trouve pas de code de suivi sur l'accueil. Le chargement conditionné au consentement reste conservé. La validation DNS est indépendante de ce chargement. Le TXT reste dans le dialogue privé de Search Console, pas dans ce dépôt. [Méthodes officielles de validation](https://support.google.com/webmasters/answer/9008080).

Une fois la validation obtenue : soumettre `https://www.sandboxpodcast.fr/sitemap.xml`, relire son état, effectuer les huit inspections ci-dessus et relever les requêtes du rapport Performances. Un écran indiquant que les données sont en cours de traitement ne doit pas être remplacé par des zéros inventés.

GA4 affiche, pour les sept derniers jours présentés du 11 au 17 octobre : 10 utilisateurs actifs, 103 vues, 184 événements et 15 sessions affichées en Direct. Les visites de recette documentées peuvent être incluses. La mesure ne couvre que les visiteurs ayant consenti. Ces chiffres ne constituent pas une audience organique certifiée ni un taux de conversion YouTube.

### Tableau de suivi à remplir à partir des données disponibles

| Mesure                                        | Source                                 | Fréquence d'analyse proposée                   | Décision associée                                            |
| --------------------------------------------- | -------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------ |
| URL indexées et raisons d'exclusion           | Search Console                         | Après mise en service, puis chaque semaine     | Corriger la découverte, les doublons ou le contenu           |
| Clics et impressions hors marque, France, Web | Search Console                         | Toutes les deux semaines, périodes de 28 jours | Choisir les sujets et les pages à approfondir                |
| Requêtes par page, CTR et position            | Search Console                         | Même période et mêmes filtres                  | Vérifier l'adéquation du titre et de la réponse              |
| Pays et appareil                              | Search Console                         | Mensuel                                        | Prioriser langue et expérience mobile                        |
| Pages d'entrée et sessions par source         | GA4                                    | Mensuel                                        | Comprendre les parcours avec la limite du consentement       |
| Clics vers replay et sources                  | GA4, événements existants              | Mensuel                                        | Améliorer les liens utiles ; un clic n'est pas une vue vidéo |
| LCP, INP, CLS mobiles au 75e centile          | CrUX, Search Console ou Speed Insights | Quand l'échantillon existe                     | Corriger les pages les plus utilisées                        |

Le suivi décrit une méthode d'analyse. Aucune automatisation récurrente n'est créée dans ce lot.

## Performance mobile

| Mesure                                                         | Observation                                                     | Limite                                                                |
| -------------------------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------- |
| Speed Insights Production Mobile, sept derniers jours affichés | `No events collected`                                           | Aucun résultat mobile réel disponible                                 |
| Speed Insights Desktop, même fenêtre                           | RES 77, 20 événements                                           | Peu d'événements, pouvant inclure la recette ; pas un résultat mobile |
| CrUX dans PageSpeed                                            | Aucune donnée                                                   | Aucun bilan mobile réel disponible dans ce rapport                    |
| Lighthouse Mobile                                              | Performance 88, accessibilité 100, bonnes pratiques 96, SEO 100 | Test automatique de laboratoire ; pas une note de positionnement SEO  |
| FCP                                                            | 1,4 s                                                           | Valeur affichée arrondie                                              |
| LCP                                                            | 3,8 s                                                           | À améliorer ; laboratoire uniquement                                  |
| TBT                                                            | 0 ms affiché                                                    | Ne mesure pas l'INP des utilisateurs                                  |
| CLS                                                            | 0                                                               | Une session testée                                                    |
| Speed Index                                                    | 2,9 s                                                           | Laboratoire uniquement                                                |

[Rapport PageSpeed du 18 octobre, 14 h 02, heure de Paris](https://pagespeed.web.dev/analysis/https-www-sandboxpodcast-fr/un2kyezu6b?form_factor=mobile). Moto G Power émulé, 4G lente, chargement initial, Lighthouse 13.5.0.

L'image LCP identifiée est l'entrée du vidéoclub mobile, `entrance-cinematic-v2.webp`. Elle porte `loading=lazy` et le rapport demande une priorité de chargement élevée. L'image est déjà découverte dans le HTML initial. Le correctif à étudier est donc ciblé sur cette image, sans précharger toutes les images de la page.

Lighthouse estime 567 Kio d'économies sur les images, notamment les portraits, les couvertures de projets et le logo du footer. Le logo est servi dans une variante de 3 840 pixels pour un affichage relevé de 252 pixels de large. Ces économies sont des estimations de l'outil, pas une mesure après correction. Le CSS bloquant représente aussi une économie estimée de 560 ms ; 102 Kio de JavaScript inutilisé sont signalés. Traiter d'abord l'image principale et les dimensions/compressions, puis mesurer de nouveau.

La collecte réelle est déjà installée derrière le consentement. Attendre des visites mobiles réelles et consenties ; ne pas alimenter artificiellement le tableau avec des recettes présentées comme de l'audience. Aucun abonnement payant n'est activé.

## Freins éditoriaux observés

### Peu de pages répondent à une recherche d'actualité

Les 76 URL françaises du sitemap contiennent 34 projets personnels, 20 profils de projets classés, 15 pages de classement ou d'archives et un seul épisode. Aucune route d'article d'actualité autonome n'y figure. Le nombre de traductions multiplie les URL, sans créer autant de sujets originaux.

L'accueil explique le Talk Show et présente le trio. Son H1 ne nomme pas l'actualité IA. La fiche d'épisode rend environ 408 mots dans le contenu principal, principalement des chapitres et des ressources. Ce comptage inclut l'interface et ne constitue pas un seuil de qualité. La page répond surtout à l'intention de regarder le replay. Des articles séparés répondraient aux questions précises discutées dans l'émission, avec un lien vers le bon passage.

Conserver le lecteur et la fiche compacte décidés dans DD-0022. Aucun rétablissement automatique de la description longue n'est nécessaire pour développer ces articles.

### Fraîcheur des classements

Les pages publiques annoncent elles-mêmes une mise à jour en retard. GitHub et Skills affichent le 10 octobre ; Models le 12 octobre. Il faut rétablir et vérifier les collectes existantes avant de promettre un suivi quotidien ou de publier des analyses de progression récentes. Ce problème est déjà suivi dans l'issue 68 ; ne pas créer un second pipeline SEO concurrent.

Les notes visibles distinguent correctement les étoiles cumulées, les installations et les benchmarks. Conserver cette séparation : un rang de popularité ne justifie pas une affirmation de qualité fonctionnelle.

### Titres et différenciation des pages

Les H1 de plusieurs destinations de classement sont tous `Sandbox Charts`. Ajouter une désignation propre à chaque famille, à sa mesure et à sa date aiderait le lecteur à comprendre la page. Les balises title actuelles sont distinctes entre familles, mais restent génériques et partiellement anglaises.

Le début des contenus principaux est identique sur plusieurs URL : `/charts`, `/charts/github`, l'édition GitHub du 10 octobre et l'archive globale de cette date ; des paires analogues existent pour Skills et Models. L'analyse automatique ne compare que les 2 600 premiers caractères. Elle justifie une revue des rôles, pas une canonicalisation générale ni la suppression des archives. Un hub doit expliquer les familles, une page courante montrer l'édition actuelle et une archive documenter son état historique.

Les archives globales du 11, du 12 octobre et de la semaine 41 contiennent environ 126 mots et le même début de contenu. Contrôler leur sélection initiale : une archive indexable doit rendre immédiatement les données de sa période, quelle que soit la famille disponible.

Correctif local du 18 octobre : le titre H1 distingue maintenant la collection, les archives et chaque famille de classement, avec une traduction dans les quatre langues. Le nom de la collection structurée suit le H1. Ce changement ne modifie ni les directives d'indexation ni le contenu des éditions ; voir le rapport des [correctifs locaux](correctifs-locaux.md).

### Traductions et confiance

Sur 63 familles d'URL, les quatre langues exposent le même title. Certains titres de marque peuvent être identiques légitimement. La fiche Sillage anglaise confirme cependant un défaut précis : title descriptif en français et liste de fonctionnalités encore en français, au milieu d'une page largement traduite. Le `hreflang` cohérent ne corrige pas ces textes. Revoir les métadonnées composées et les blocs de liste ; respecter l'autorisation d'indexation donnée dans DD-0048.

La page À propos se limite surtout aux liens sociaux, avec environ 65 mots de contenu principal. Les biographies présentes sur l'accueil peuvent alimenter une présentation plus explicite des auteurs, de leur pratique de l'IA et de leurs projets. Lou a déjà refusé la publication de la procédure de signalement proposée : conserver l'email du footer et ne pas publier cette procédure à nouveau sans demande.

## Concurrence et territoire proposé

| Site ou famille observée                                                       | Organisation visible                                              | Conséquence pour Sandbox                                                                          |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| [ActuIA](https://www.actuia.com/)                                              | Veille pour décideurs, sujets, secteurs, dossiers, newsletter     | Choisir un angle utile aux praticiens plutôt que reproduire une couverture sectorielle exhaustive |
| [Actu.ai](https://www.actu.ai/)                                                | Fil d'actualité, nombreuses rubriques, accès à l'équipe et au RSS | Publier des articles autonomes et rendre leur découverte simple                                   |
| [Les Numériques](https://www.lesnumeriques.com/intelligence-artificielle.html) | Rubrique IA regroupant actualités et dossiers                     | Associer les annonces aux essais pratiques et aux explications                                    |
| [Skills Guide](https://skills-guides.com/fr/skills/meilleurs/claude-code)      | Page dédiée aux skills Claude Code et explication des critères    | Une page par plateforme ne suffit pas ; documenter compatibilité, méthode et essais               |

Les comparatifs Claude Code/Codex apparaissent déjà dans plusieurs publications observées, dont ZDNet et des sites spécialisés. Cette demande mérite une étude dans Search Console ; elle ne doit pas être qualifiée de peu concurrentielle. Aucun trafic concurrent, nombre de liens ou score d'autorité n'est disponible.

Recommandation de départ : actualité des outils IA, agents de code et IA locale/open source, expliquée à partir de réalisations et d'essais. C'est une inférence fondée sur vos projets et l'épisode public, pas une étude de lectorat. L'ambition généraliste reste possible à mesure que la couverture et les moyens progressent.

## Priorités de travail

| Priorité | Travail                                                     | Résultat attendu et critère de recette                                                           |
| -------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| P0       | Valider Search Console par DNS, soumettre le sitemap        | Propriété validée, sitemap reçu, état daté et inspecté                                           |
| P0       | Inspecter les huit URL prioritaires                         | État Google et canonique choisie consignés, sans confusion avec le seul HTTP                     |
| P1       | Résoudre la fraîcheur des collectes dans le suivi existant  | Éditions réelles récentes, critères et preuves des collectes respectés                           |
| P1       | Concevoir et préparer la rubrique éditoriale                | Articles réels, auteurs et sources ; revue locale avant publication autorisée                    |
| P1       | Traiter l'image LCP mobile et le poids des images           | Comparaison avant/après avec les mêmes conditions ; contrôle visuel                              |
| P1       | Corriger titres localisés et listes non traduites           | Texte dans la langue attendue, canonique et langues toujours cohérentes                          |
| P2       | Différencier hub, familles et archives                      | Chaque page rend sa fonction et ses données sans action préalable                                |
| P2       | Renforcer la présentation des auteurs                       | Expérience vérifiable et liens vers leurs travaux, email de contact conservé                     |
| P2       | Relier articles, replay, projets et classements             | Liens contextuels pertinents ; pas de nouvelle page orpheline                                    |
| P2       | Analyser les requêtes puis enrichir les pages déjà visibles | Priorités justifiées par les impressions et les besoins des lecteurs                             |
| P3       | Préparer Google Actualités et Discover                      | Images pertinentes, dates, auteurs et règles éditoriales conformes ; aucune garantie de présence |
| P3       | Évaluer les citations dans les moteurs IA                   | Échantillon de questions daté, sources citées relevées ; pas de promesse de gain                 |

## Google Actualités, Discover et moteurs IA

Les articles devront avoir des URL durables, des titres descriptifs, des auteurs, des dates exactes et leurs sources. Le balisage `Article` ou `NewsArticle` devra correspondre au contenu visible. Les schémas podcast et vidéo existants restent affectés à leurs contenus respectifs. [Documentation Article](https://developers.google.com/search/docs/appearance/structured-data/article).

Google Actualités sélectionne automatiquement les contenus éligibles. Discover ne demande pas de balise spéciale et recommande des images pertinentes d'au moins 1 200 pixels de large. Prévoir ces images dès la préparation des articles, sans assimiler le logo de partage à une illustration éditoriale. [Google Actualités](https://support.google.com/news/publisher-center/answer/9607025?hl=fr), [Discover](https://developers.google.com/search/docs/appearance/google-discover).

Pour les moteurs IA : privilégier des essais reproductibles, des faits datés, des tableaux utiles et des sources primaires. Les passages doivent être compréhensibles sans forcer une longueur artificielle. Vérifier les accès de découverte des robots et les protections CDN si un refus est observé. Le robots générique du site les autorise actuellement ; il ne prouve pas l'absence de filtrage dans toutes les couches.

`llms.txt` reste secondaire. Google indique qu'il ne l'utilise pas pour la visibilité dans Search ou ses fonctions génératives. Aucun gain chiffré de citations n'est annoncé. [Guide officiel Google](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide).

## Mise en oeuvre sur 90 jours

Les périodes suivantes sont un ordre de travail proposé, pas un engagement d'équipe ni une prévision de résultats.

- Jours 1 à 7 : validation Search Console, sitemap et inspections ; backlog technique confirmé ; premiers sujets retenus à partir des sources déjà disponibles.
- Jours 8 à 30 : traiter les défauts ciblés ; préparer les premiers articles et un guide maintenu ; prévoir leurs liens avec le replay. La mise en ligne reste soumise aux règles du dépôt.
- Jours 31 à 60 : analyser les premières requêtes disponibles ; enrichir les pages ayant des impressions ; publier les essais et analyses de données réellement documentés après accord.
- Jours 61 à 90 : concentrer la production sur les sujets qui trouvent leur public ; revoir les mises à jour et les liens ; évaluer la charge avant d'élargir la couverture.

Le [plan éditorial](plan-editorial.md) fournit les intentions, URL proposées et preuves nécessaires. Aucun nouvel article public, DNS, abonnement, déploiement, commit, push ou PR n'est réalisé par cet audit à ce stade.

## Validation des fichiers locaux

Le premier `pnpm check` réussit avec le pnpm 11.25.0 disponible dans le terminal : format, lint, types, 702 tests du site, 7 tests du générique, 4 tests des jingles et 24 tests BIS. Il décrit l'état du dépôt à son exécution.

La version requise 12.9.1 a ensuite été chargée avec Corepack. `corepack pnpm check` s'arrête au formatage de deux fichiers du lot épisode 003, étrangers à cet audit : `apps/site/public/slides/episode-003/show.js` et `apps/site/test/episode-003-slides.test.ts`. Ils évoluent pendant cette session et ne sont pas reformattés par le lot SEO. Les étapes suivantes de cette seconde exécution ne sont donc pas validées. Aucun contrôle n'est désactivé.

Le vérificateur de texte français ne signale pas de caractère interdit dans les deux nouveaux documents. L'inventaire contient un en-tête et 301 lignes. Les modifications SEO portent sur la documentation ; aucun test artificiel de contenu n'est ajouté et aucun code produit n'est modifié.
