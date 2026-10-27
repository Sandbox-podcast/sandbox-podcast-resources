# Audit et stabilisation du 19 octobre 2026

Demande de Lou : corriger les classements et News, intégrer leurs accès, simplifier la Time Machine et préparer la production. L'analyse complémentaire a été exécutée avec Sol 6.1. Décisions : [DD-0063](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0063-stabilisation-des-classements-news-et-time-machine.md).

## Périmètre et état du dépôt

La branche locale `codex/kits-relais-videos-autonomes` part d'un ancien HEAD (`a6be3ee`) et contient un lot important de changements. L'audit a d'abord comparé cet état avec `origin/main` à `4fafc1ed6014dad3eae890eafb5d29da055e0a07`, puis avec `da46093bf67b12e6ca0217334de15a7aa7f41756` après la fusion de la PR 94. Les ajouts distants non conflictuels ont été réintégrés ; les correctifs locaux ont été conservés et les différences examinées. Les sauvegardes initiales et de réconciliation restent dans `apps/site/.local/audit-2026-10-19/before/` et `pr94/`. Aucun historique Git n'a été réinitialisé.

Les PR 77, 79, 80, 90, 92, 93 et 94 sont fusionnées. Les PR 84, 85, 86 et 89 sont fermées et regroupées. Aucune PR ouverte n'a été trouvée lors de la consultation initiale. Les éditions Models observées de la PR 92 et la navigation News de la PR 93 manquaient dans la branche locale ; elles ont été réintégrées. La PR 94 a publié entre-temps le registre de 105 sources, la file, ses réservations et des corrections d'épisodes. Ses deux contrôles CI quality sont en échec : le test News attend un select masqué après les filtres. La recette locale attend désormais l'hydratation et pilote explicitement le volet de filtres ; elle passe avec dix groupes de contrôles. Les travaux de vidéos et de relais sociaux présents avant l'audit restent à relire séparément avant tout commit global.

## Constats en production

Contrôles HTTP publics et journaux GitHub relus le 19 octobre, puis schéma Neon consulté sans écriture.

| Fonction          | Résultat observé                                                                                                        |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------- |
| GitHub            | Édition `2026-10-19T00:00Z`, vingt entrées, méthode `github-momentum-observed`                                          |
| Skills            | Même date, vingt entrées, méthode `skills-installs-observed`                                                            |
| Models            | Même date, vingt entrées, méthode `models-quality-observed`                                                             |
| À suivre / Rising | API HTTP 202, aucune édition publiée                                                                                    |
| News              | Vingt fiches visibles, relevé du 19 octobre à 08 h 20 Paris, huit sources accessibles sur dix                           |
| File News         | Table `news_candidates` absente de la branche principale Neon consultée ; `news_items` et `news_source_status` existent |

Le contrôle public `node apps/site/scripts/charts-refresh.ts --check` sort avec le code 1 : les trois premières familles sont fraîches, Rising est absent. Les classements ne sont donc pas tous anciens au moment de cet audit.

Le dernier [run News planifié](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39209168955), à 06:18:38 UTC, a publié cinq fiches et annoncé zéro résumé généré. Le [lancement manuel précédent](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39195822047), à 03:40 UTC, avait publié quinze fiches, également sans génération. Ces succès montrent l'ingestion d'articles préécrits ; ils ne démontrent pas l'autonomie de la rédaction de nouvelles fiches. Aucun run News plus récent n'apparaît lors de la relecture à 13 h UTC. Les passages antérieurs à 01:20, 22:27 et 19:27 sont marqués `skipped`.

Le dernier [run des classements](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39226752024), à 08:59 UTC, est réussi. Celui de 07:53 a échoué sur la fraîcheur ; celui de 06:09 est annulé. Le workflow contrôlait trois familles et pouvait donc réussir malgré Rising vide.

Après le déploiement de la PR 94, `node apps/site/scripts/news-health.ts` confirme une collecte en retard de plus de trois heures : `checkedAt=2026-10-19T06:20:36.786Z`. Le nouveau code est livré, mais son pipeline n'est pas opérationnel en production tant que la file est absente de la base et que les passages horaires ne sont pas confirmés.

Le [run planifié suivant](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39260759503), créé à 13:30 UTC, échoue à 13:32 sur le précontrôle de la file : HTTP 503. Cela concorde avec la table absente du schéma Neon. Le contrôle de fraîcheur échoue aussi : le workflow de la PR 94 appelle `apps/site/scripts/news-health.ts`, mais le fichier n'a pas été livré. Le script, son module et un test vérifiant la présence des scripts appelés sont inclus dans le complément local. La branche `main` est déclarée `protected=false` par l'API GitHub ; exiger une CI réussie avant fusion reste un réglage à autoriser.

La variable GitHub `SANDBOX_NEWS_PUBLIC=true`, l'origine publique et le nom du secret cron sont présents. Aucune valeur secrète n'a été affichée. Le schéma Neon a été lu sur `fragrant-lab-14685793`, branche principale `br-ancient-union-b1zb56o3`, base `neondb`. Les métadonnées GitHub confirment un déploiement Vercel Production réussi à 12:52 UTC pour `da46093` (déploiement GitHub 7174252324). Le schéma Neon lu ensuite ne contient toujours pas la file : un déploiement de code réussi n'a donc pas appliqué les migrations nécessaires. L'accès Vercel direct n'est pas disponible pour vérifier les variables et logs de fonctions. La fraîcheur publique est vérifiable ; la parité complète de configuration Preview/Production reste à établir.

## Causes et corrections locales

| Problème                                         | Cause                                                                          | Correction                                                                                                       |
| ------------------------------------------------ | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Rising vide masqué par un run réussi             | Vérification limitée à GitHub, Skills et Models                                | Contrôle des quatre familles après le gel et dans `--check`                                                      |
| Repli Rising dépendant de GitHub                 | La décision d'édition observée utilisait le résultat du profil GitHub          | Conditions et version de scoring propres à Rising                                                                |
| Édition courante ancienne après gel              | Cache CDN de cinq minutes sur `current`                                        | Réponse courante `no-store`, cache conservé pour les archives                                                    |
| Attente Rising incompréhensible                  | Compteur de découvertes et critères de publication différents                  | Message explicite : vingt projets, deux fenêtres de sept jours, accélération positive ; accès à GitHub           |
| Nouveautés News non autonomes                    | Résumés locaux préécrits et modèle réel non validé                             | Modèle CPU installé, figé par révision et hash, essais de génération et traduction réels                         |
| Premiers candidats rejoués après un crash        | Absence de réservation et compteur incrémenté trop tard                        | Migration 0018, réservations de vingt minutes, cinq candidats par lot, trois tentatives, clôture par identifiant |
| File trop lente et sensible à un mauvais article | Un seul lot et rejet global sur traduction invalide                            | Plusieurs lots par run ; reprise article par article et isolement des échecs                                     |
| Passage dix → 105 sources incompatible           | Contrat d'ingestion exigeant exactement le registre du serveur                 | Sous-ensemble connu accepté pendant la transition ; nouveau worker exigeant protocole 2                          |
| Articles récents masqués par des liens anciens   | Six premiers liens HTML seulement, ordre des changelogs supposé                | Tri des liens datés, douze lectures par source, vingt entrées de changelog les plus récentes                     |
| Extraits et titres trompeurs                     | Métadonnées, voix de l'éditeur et titre généré indépendant                     | Paragraphes prioritaires, première personne refusée, titre tiré de la première phrase, citations contraintes     |
| Unités et nombres perdus en traduction           | Traduction automatique sans contrôle de ces pertes                             | Nombres vérifiés et termes entrée/sortie protégés ; fiche rejetée si le contrôle échoue                          |
| Historique News tronqué                          | Limite de 200 articles et fenêtre de quatorze jours appliquée aux publications | Fil Postgres cumulatif, pagination par curseur normalisé, fenêtre réservée à la collecte                         |
| Accès News incomplets                            | Réintégration locale incomplète et disponibilité dissociée                     | « Actualités » dans navigation et footer partagés, quatre langues, radar existant activé avec du contenu publié  |
| Time Machine difficile à piloter                 | Sélection au survol, années éloignées, archives anciennes en tête              | Choix explicite au clic/clavier, années près de la chronologie, archives récentes en premier                     |

La recette navigateur en production à 13:33 UTC reproduit le message : « 1350 dépôts suivis. Historique : 9 / 7 jours », avec zéro entrée dans Rising. Le chiffre neuf compte les jours de relevés distincts. L'interface utilisait le seuil de sept jours de GitHub pour Rising, alors que son accélération demande deux périodes de sept jours. Le correctif affiche neuf sur quatorze et explique les vingt projets requis ; un test de rendu couvre les deux seuils. L'agrégat public annonce une première date théorique GitHub au 17 octobre, calculée depuis le premier relevé du 10 octobre : la fenêtre Rising de quatorze jours ne peut donc pas être complète au 19 octobre. Quatorze jours après le premier relevé donnent le 24 octobre comme repère ; la tolérance des baselines peut faire varier la date effective. Ce repère ne garantit pas que vingt projets seront alors admissibles.

La même recette vérifie les six rubriques publiques (accueil, News, classements, Time Machine, podcast et projets), sans erreur JavaScript. Le lien News y porte encore « Actualité » en production. L'image radar est présente et son clic ouvre bien `/news` ; ce point a été livré par la PR 94. Le complément local harmonise le libellé en « Actualités » et ajoute les autres corrections de cet audit.

## Sources News : contrôle réel

Un autre défaut de fraîcheur a été corrigé : publier un lot de candidats remettait les statuts des sources à l'heure de publication, même si aucune nouvelle collecte n'avait eu lieu. Le worker conserve désormais le `checkedAt` reçu de la collecte, avec un test de régression. Une échéance commune de quatorze minutes couvre le résumé et toutes les traductions, y compris la reprise article par article ; elle annule les sous-processus avant l'expiration de la réservation.

Dernier relevé du 19 octobre à 13:13 UTC : 105 sources consultées en 96 secondes, 80 entièrement lisibles et onze en lecture partielle. Le collecteur a récupéré 426 fiches datées de moins de quatorze jours, provenant de 68 sources. Le schéma valide les identités et URL. Le volume détecté ne représente pas 426 résumés publiables ou déjà publiés. Les chemins localisés de Perplexity, les cartes placées dans des en-têtes et les dates visibles de Meta, Alibaba Cloud et Ai2 ont été corrigés après inspection des pages publiques.

| État restant                                       | Sources                                                                                                                                        |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| HTTP 403                                           | There's An AI For That, OpenAI, ChatGPT, xAI / Grok, Leonardo AI, Canva, MarkTechPost                                                          |
| HTTP 429                                           | VentureBeat AI                                                                                                                                 |
| Lecture partielle                                  | TLDR AI, Mistral AI, ByteDance Seed, Kling AI, Microsoft AI, Google Cloud AI, Genspark, Hugging Face Papers, Together AI, The Decoder, AI News |
| Aucune date, ancre ou liste d'articles exploitable | OpenAI API, Runway News, Kling AI Release History, PixVerse News, AIVA, MIT Technology Review                                                  |

Les refus et formats non pris en charge restent visibles. Aucun paywall ou blocage d'accès n'est contourné ; aucune date de publication n'est remplacée par celle du relevé. Ce relevé complète celui, antérieur aux derniers correctifs, de DD-0062. Le [relevé par source](news-sources-stabilisation-2026-10-19.csv) conserve les statuts et nombres de fiches. Les données brutes sont dans le dossier local ignoré `apps/site/.local/audit-2026-10-19/` ; les HTML et extraits ne sont pas destinés à Git.

## Time Machine

Le contenu comporte 162 événements, dont 52 en 2026, avec une revue éditoriale datée du 18 octobre et un dernier événement du 17 octobre. Les onze derniers liens de source primaire ont été contrôlés : neuf réponses HTTP 200 et deux HTTP 403 (Jais 3 et Rosalind). Ces deux réponses empêchent une vérification automatique ; elles ne démontrent pas que les événements sont faux ni que les liens sont morts. Les données déjà actualisées localement sont conservées, ainsi que leurs onze illustrations.

Le parcours principal devient : choisir une année, parcourir la chronologie, ouvrir un événement et sa source. Les outils avancés et le Wrapped restent accessibles sans occuper le premier niveau de lecture.

## Validations

Les recettes couvrent la collecte réelle, la génération CPU et les traductions, la base Postgres locale, les API authentifiées et les pages navigateur. Aucune de ces recettes n'est une publication en production.

- `pnpm check` : format, lint, types et 981 tests réussis (946 pour le site, sept pour l'intro, quatre pour les jingles et 24 pour BIS).
- Build de production réussi : 204 pages statiques générées.
- `pnpm audit --audit-level=high` : aucune vulnérabilité connue signalée. `git diff --check` ne signale pas de défaut d'espacement.
- Tests Python du résumé : trois tests réussis.
- Les régressions couvrent une panne réseau sur le registre complet, la conservation de la date de collecte, les nombres et unités en traduction, les échéances des traitements et les fichiers appelés par le workflow. La collecte est bornée à huit minutes.
- Génération réelle de trois articles absents de **NEWS_EDITORIAL** : trois résumés acceptés et leurs traductions EN/ES/DE en 134,9 secondes sur le CPU du poste. Les faits et les prix de cet échantillon ont été relus avec les extraits. Les titres exagérés et les pertes d'unités détectés lors des premiers essais ont été corrigés avant ce passage.
- Ces trois sorties ont traversé l'API privée, une réservation, Postgres, la déduplication, la clôture de la file et l'API publique. Les huit pages FR/EN/ES/DE à 390 et 1440 pixels affichent les textes et liens attendus, sans erreur JavaScript.
- Recette News de régression : dix groupes réussis, dont secret obligatoire, drapeau fermé, migrations 0016/0017/0018, fil vide, publication idempotente, filtres, pagination de 30 à 36 articles anciens, radar et panne SQL.
- Recette Time Machine : 41 contrôles réussis à 320, 390, 768 et 1440 pixels, avec sélection par clic, absence de sélection au survol, changement d'année, clavier, filtres, état vide, Wrapped, exports et sources sans JavaScript.
- Recette classements, badges et Awards : 43 contrôles réussis sur une base de test, dont le calcul des éditions, les pages projet, les preuves, les variantes linguistiques, les états vides et les retraits ; aucune erreur JavaScript. Rapport dans `apps/site/.local/badges-e2e-85416/`.

Les rapports et captures de recette sont conservés dans apps/site/.local/news-e2e/, apps/site/.local/time-machine-experience/ et apps/site/.local/audit-2026-10-19/real-e2e/. Les premières captures d'échecs restent dans les dossiers locaux pour conserver les diagnostics ; le résultat final est celui des fichiers report.json.

## Préparation du déploiement

1. Relire les différences de fichiers par rapport à `origin/main` (y compris les fichiers non suivis par le vieux HEAD local) et séparer les changements médias étrangers à cet audit avant le commit. Le registre et les migrations de la file figurent déjà dans la PR 94 ; conserver leurs fichiers et n'ajouter que les correctifs complémentaires. Le 19 octobre, Lou a autorisé le commit, le push, une PR unique, sa fusion, le déploiement et les migrations après sauvegarde. Le lot est préparé dans une branche isolée de main ; les travaux médias locaux sont préservés.
2. Après accord, créer une sauvegarde de la branche Neon cible et valider le schéma attendu. Tester 0017 puis 0018 sur une copie avant la mise en service. Ce sont des migrations additives ; ne pas réécrire une migration déjà appliquée.
3. Livrer le complément de l'application, des scripts et workflows sur `main` avant d'ouvrir la file en production, afin d'utiliser le modèle Qwen3-4B vérifié et son hash figé. Le précontrôle continue à refuser une file absente ; les articles déjà publiés restent lisibles. L'ancien worker à dix sources reste compatible avec l'ingestion pendant la transition.
4. Appliquer les migrations manquantes 0017 et 0018 sur la cible autorisée, après contrôle du journal. Vérifier la lecture authentifiée de `/api/cron/news-candidates`, le protocole 2, les 105 sources, l'absence d'erreur 503 et les permissions. Vérifier le temps d'installation sur un runner Linux froid et les minutes GitHub disponibles. Aucun forfait supplémentaire n'est engagé.
5. Lancer un premier cycle distant après accord de publication. Confirmer de nouveaux résumés absents du catalogue préécrit, leurs traductions, leur présence Postgres, leur affichage et l'absence de doublon au deuxième passage. Vérifier l'âge du plus ancien candidat en attente et les rejets.
6. Rejouer le contrôle des quatre classements. Diagnostiquer Rising depuis les mesures réelles : historique de quatorze jours, projets éligibles et accélération. Ne pas baisser les seuils ni réutiliser des démonstrations pour le faire passer au vert.
7. Observer au moins deux déclenchements automatiques distants consécutifs, puis un cycle sur vingt-quatre heures. Les runs GitHub déjà observés ont des trous de plusieurs heures. Une exigence stricte de collecte chaque heure reste bloquée tant qu'un planificateur adapté n'est pas choisi et configuré avec les autorisations de compte nécessaires.

## Points encore ouverts

- La PR 95 et les migrations 0017/0018 sont livrées après sauvegarde. Un premier cycle distant réussit avec quatre nouvelles fiches générées ; les passages planifiés consécutifs et le suivi sur vingt-quatre heures restent à confirmer.
- Rising sans édition réelle : le diagnostic SQL est terminé, mais aucun projet mesuré le 19 ne possède encore ses deux baselines. La constitution des vingt projets admissibles dépend des prochains relevés réels.
- Couverture News incomplète pour les 26 sources en erreur ou en lecture partielle sur le passage distant ; compléter les adaptateurs ou obtenir un accès public utilisable lorsqu'il existe.
- Garantie horaire non démontrée par GitHub Actions. Le contrôle de fraîcheur signale un retard lorsqu'il s'exécute ; il ne réveille pas lui-même un planificateur défaillant.
- Résumés et traductions automatiques : les contrôles structurels et les citations ne garantissent pas l'exactitude sémantique de tous les articles. La recette porte sur un échantillon ; mesurer les rejets et relire les premières sorties réelles après livraison.
- Budget CPU/minutes, capacité et rétention de la file à suivre avec le volume des 105 sources. Les données publiées ne sont pas supprimées par ce lot.
- Protection de `main` à configurer après accord : la PR 94 a été fusionnée malgré l'échec de son contrôle quality. Les réglages GitHub n'ont pas été modifiés par cet audit.

## Livraison autorisée et sauvegarde Neon

Lou a autorisé le 19 octobre le commit, le push, une PR unique, sa fusion, le déploiement et les migrations après sauvegarde. Le complément est assemblé depuis `main` (`da46093`) sur `codex/stabilisation-classements-news`, dans un worktree distinct du chantier médias.

La sauvegarde `backup-main-2026-10-19-stabilisation` (`br-withered-sound-b1bzhj83`) a été créée à 13:52:56 UTC depuis la branche de production `br-ancient-union-b1zb56o3`, sans expiration automatique. La copie de recette `test-migrations-news-2026-10-19` (`br-plain-thunder-b1ejdusl`, expiration le 20 octobre) en est issue. Avant migration, elle contient 17 entrées du journal, 20 actualités, dix statuts de source et aucune table de candidats. Les hashes du dernier journal et des migrations 0017/0018 ont été contrôlés.

Les migrations 0017/0018 ont réussi sur cette copie dans une transaction avec vérification du journal et délai de verrouillage. Le résultat comporte 19 migrations, une file vide et les 20 actualités existantes. La sauvegarde reste intacte. L'application sur la branche de production attend la livraison du worker corrigé ; aucun schéma de production n'a encore été modifié à ce stade.

La validation du worktree isolé passe : `pnpm check` (981 tests), build (204 pages), trois tests Python et audit des dépendances sans vulnérabilité connue. Un ajout en doublon du script `test:episode:e2e`, déjà présent dans main, a été retiré avant commit.

## Contrôles après livraison en production

La PR 95 a été fusionnée le 19 octobre à 14:07:06 UTC après réussite de tous les contrôles, y compris CI quality, source-pipelines, secret-scan et Vercel Preview. Commit du lot : `e041eae29ac7c3efe8f2421724e27ae839d67069`. Fusion : `488bf767a59f8d59667032f74a888af55b76666a`.

Le déploiement Vercel Production `5sSwo6e2NHzGnD3sdVMaR4vbbqnM` est prêt à 14:08:38 UTC pour cette fusion. L'API GitHub confirme le succès du déploiement `7176017213`. Les variables DATABASE_URL/POSTGRES_URL et SANDBOX_NEWS_PUBLIC existent en Production et Preview ; CRON_SECRET est présent en Production. Les secrets sont restés masqués.

Les migrations 0017/0018 ont ensuite été appliquées sur main avec la même transaction testée sur copie. Le contrôle confirme 19 migrations, dix colonnes dans news_candidates, zéro candidat initial et les 20 actualités conservées. Preuve locale : `apps/site/.local/audit-2026-10-19/neon-production-migrations.png`.

À 14:10 UTC, les six pages publiques répondent 200 sans erreur JavaScript : accueil, News, classements, Time Machine, podcast et projets. Le menu porte Actualités ; le radar ouvre /news. Rising affiche neuf jours sur quatorze. Les quatre API courantes répondent sans cache ; les deux routes News privées refusent les requêtes non authentifiées (401).

Le diagnostic SQL effectué sur la copie de sauvegarde porte sur 15 702 relevés, 3 032 projets observés et neuf dates distinctes du 10 au 19 octobre (le 14 manque). Parmi 1 428 projets mesurés le 19, 175 ont une première baseline à sept jours avec la tolérance du code ; aucun n'a les deux baselines nécessaires. Les dernières collectes GitHub sont partielles à cause d'OpenSSF, mais les relevés GitHub sont bien persistés. Le dernier lot a traité 268 projets sur 268 avec deux erreurs de scorecard. Cela explique aussi pourquoi lastSuccessfulCollectAt peut être plus ancien que les mesures réelles.

Deux cycles manuels distants ont été lancés après migration : News `39266494010` et classements `39266500369`. Leur résultat, les nouveaux articles et les passages planifiés restent à relever.

### Première collecte et publication distantes

Le runner News a terminé sa collecte en 1 min 47 s et stocké 403 candidats. L'API publique affiche désormais 105 sources, dont 79 entièrement lisibles sur ce passage, et le relevé `2026-10-19T14:10:46.757Z`. L'installation froide a pris 1 min 37 s pour les traductions et 18 s pour le modèle de résumé. Le contrôle de fraîcheur public passe. Cela valide la collecte, sans encore prouver à lui seul la génération.

La première publication générée par le runner est enregistrée à 14:18:07 UTC : l'article AlphaSignal sur RoboParty RP1, daté du 19 octobre. Il est absent de NEWS_EDITORIAL. La base conserve son empreinte de source ; le candidat est `published`, avec une tentative et sa réservation libérée. Ses quatre titres et quatre synthèses de trois phrases sont présents. Le premier lot a publié une fiche sur cinq, les quatre autres ayant été écartées par les contrôles et reportées.

Les huit pages FR/EN/ES/DE à 390 et 1440 pixels affichent cette nouvelle fiche, les trois phrases et le lien source exact, sans erreur JavaScript ni débordement horizontal. Preuve : `apps/site/.local/audit-2026-10-19/production-generated-news/report.json`.

La Time Machine passe 41 contrôles sur la production. La première exécution mesurait une image différée avant son décodage ; la recette de production attend désormais `image.decode()` avant cette mesure, sans ignorer les échecs de chargement. Le second passage réussit aux quatre largeurs et sans JavaScript pour les sources. Rapport : `apps/site/.local/time-machine-production/report.json`.

### Complément de recette : curseurs News

La recette prolongée a identifié une régression du lot : normaliser published_at dans le curseur modifie la clé lexicographique de cette colonne texte. Une date sans heure peut faire rejouer des lignes ; un horodatage sans millisecondes peut en faire sauter. Le curseur conserve désormais exactement la valeur stockée. Le schéma accepte déjà les deux formes de date.

Deux tests échouent avant correction (date seule et horodatage sans millisecondes). Le test parcourt 215 lignes à date identique pour chacun des trois formats, avec une borne contre les boucles ; la recette HTTP pagine aussi des dates sans heure. Ce complément appartient au même lot de stabilisation. Le 19 octobre au soir, Lou autorise une PR corrective supplémentaire, sa fusion et son déploiement après les contrôles. Le correctif est contrôlé sur la branche du lot avant sa livraison.

### Bilan du premier run terminé et validation du complément

Le run News `39266494010` est réussi à 14:25:22 UTC. Il a détecté 422 candidats, en a ajouté 403 à la file, puis traité dix candidats en deux lots : quatre nouvelles fiches générées, traduites et publiées, six écartées, zéro erreur de traitement. La file n'est pas vidée. Les modèles sont sauvegardés dans le cache distant pour les prochains passages. Le fil contient 24 fiches après ce run.

Le run classements `39266500369` termine à 14:19:34 UTC. Il confirme les vingt entrées publiées pour GitHub, Skills et Models au créneau `2026-10-19T12:00Z`. Il sort en échec uniquement parce que Rising n'a aucune édition valide, conformément au diagnostic des baselines. Les trois autres publications ont bien été réalisées malgré cet état.

Après correction du curseur texte, `pnpm check` passe avec 983 tests, dont 948 pour le site. Le build génère 204 pages. La recette News réussit ses dix groupes, y compris la pagination de 30 à 36 articles avec des dates sans heure. Les deux cas nouvellement couverts échouaient avant correction. Les tests et gates n'ont pas été désactivés.

### Déclenchements horaires : contrôle à 19:05 UTC

Aucun run News planifié n'a été créé depuis celui de 13:30 UTC. Le lancement manuel de 14:10 réussit, mais la date de collecte publique dépasse ensuite cinq heures. Le workflow reste actif, présent sur main avec un cron horaire, et son drapeau est activé. Les autres workflows planifiés montrent aussi des trous de plusieurs heures. Le contrôle planifié des classements de 15:42 échoue uniquement sur Rising ; les trois autres éditions sont valides.

GitHub a déclaré un [incident Actions/Pages/Webhooks](https://www.githubstatus.com/incidents/8tzbpcnl75jp) de 15:49 à 16:56 UTC. Cet incident peut expliquer une partie des retards ; il ne prouve pas la cause de tous les créneaux absents. La [documentation GitHub](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows#scheduled-workflow-stopped-running) décrit le changement du cron comme moyen de relancer un planning arrêté. Le cron News passe de la minute 23 à la minute 37, avec un contrat de test qui conserve la fréquence horaire, le drapeau public, main et l'absence d'annulation d'un passage en cours. Ce réenregistrement doit encore être validé par un événement schedule réel ; un lancement manuel ne le remplace pas.

Le plan Hobby Vercel ne permet pas de cron horaire. Aucun compte externe ni forfait payant n'est ouvert. Si les créneaux GitHub restent absents après cette reprise, le choix d'un autre planificateur et les accès de compte devront être validés par Lou.

Le complément de reprise passe pnpm check avec 984 tests (949 site, 35 autres). La recette HTTP et le build du correctif de curseur avaient déjà réussi avant le changement de minute du cron. Un run de rattrapage manuel, 39308199122, est lancé à 19:06 UTC ; il ne compte pas comme preuve de déclenchement automatique.
