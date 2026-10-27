# Audit global de Sandbox

Date : 14 octobre 2026. Site examiné : [www.sandboxpodcast.fr](https://www.sandboxpodcast.fr/). Application : `apps/site`. Relevés HTTP à partir de 18:34, mesures PageSpeed entre 19:05 et 19:21, heure de Paris. Le dépôt est sur `3ccf406`, avec de nombreux changements non commités et des travaux apparus pendant l'audit.

Ce rapport recommande des actions. Il ne modifie aucune décision produit et n'autorise aucune publication. Les seules créations de cet audit sont ce rapport et ses quatre fichiers de preuves. Aucun code produit, donnée publiée, compte ou réglage système n'a été modifié par l'audit.

## Synthèse

Sandbox est utilisable : l'épisode se lit, les chapitres fonctionnent, les ressources se retrouvent, les classements se filtrent et le catalogue présente 34 projets. Le site possède déjà une identité reconnaissable. Une refonte générale n'est pas la première priorité.

Le risque principal concerne la confiance dans les données. Des fiches historiques de démonstration restent accessibles sans avertissement visible. Le classement courant annonce une actualisation toutes les 12 heures alors que GitHub et Skills montrent une édition du 10 octobre. Les méthodes publiques mélangent parfois état actuel et versions futures. Une archive Skills annoncée dans le sitemap renvoie 404.

La mesure d'audience n'est pas encore une base fiable pour décider : le site demande le script Google Analytics après acceptation, mais sa CSP interdit son domaine et les domaines de collecte. Aucun accès exploitable aux statistiques du domaine n'a été obtenu. Les performances mobiles sont perfectibles : 81 à 89/100 sur les quatre pages mesurées, avec un LCP de 2,9 à 4,0 secondes. La fiche épisode présente un CLS de 0,205 au premier passage, puis 0 au second : ce signal reste à reproduire et à expliquer.

L'offre gagnerait à être expliquée à partir de ce que l'équipe fait réellement : construire, montrer, essayer et débattre. Les épisodes et les projets donnent une matière originale. Les classements peuvent aider à choisir quoi examiner, à condition de rendre leurs limites explicites. Copier une newsletter quotidienne d'actualité ou multiplier les catalogues ajouterait beaucoup de travail avec peu de différence visible.

Les cinq priorités sont :

1. Retirer l'ambiguïté entre démonstration et données réelles, et réparer l'archive Skills.
2. Rendre cohérents les scores, les méthodes, les dates et la promesse d'actualisation.
3. Corriger puis vérifier la mesure d'audience et l'information sur les données personnelles.
4. Traiter les défauts mobiles mesurés et rétablir les contrôles de qualité du dépôt.
5. Clarifier la promesse éditoriale, relier les contenus et tester une diffusion soutenable.

## 1. Périmètre, preuves et limites

Les sources du dépôt ont été lues : instructions, index, conception du site, questions ouvertes, contexte marketing v1 draft, décisions sur l'indexation, les langues, les classements compacts, les épisodes, les projets et Analytics, ADR sur les données et les collectes, rapports SEO/UI/YouTube. `old/` est resté hors du périmètre.

Les preuves livrées sont :

- [Relevés HTTP et métadonnées](audit-global-2026-10-14-preuves.json) : 97 URL dans le premier passage, dont les 77 URL du sitemap, en-têtes, canonical, robots, JSON-LD et trois mesures de temps de réponse sur cinq pages.
- [Ressources et sondes complémentaires](audit-global-2026-10-14-ressources.json) : huit sondes de routes, dont une répétition de l'archive Skills, 13 liens externes de l'épisode, fichiers JavaScript/CSS initiaux et deux images publiques.
- [Mesures PageSpeed](audit-global-2026-10-14-mesures.json) : valeurs transcrites de l'interface officielle et liens vers les rapports.
- [Journal des parcours](audit-global-2026-10-14-parcours.md) : manipulations, lectures du DOM et résultats observés, références U01 à U24.

Les contrôles navigateur couvrent ordinateur, 390 x 844 et 320 x 740. Ils portent sur la découverte, la lecture, un chapitre, la recherche, les onglets et filtres de classements, le catalogue, les filtres croisés, les états vides, une galerie, une vidéo de projet, les préférences de mesure et une erreur 404. Ils ne constituent pas une étude d'usage avec des lecteurs.

L'API anonyme PageSpeed a répondu 429. Son interface a ensuite fourni les mesures. Elle indique "Aucune donnée" terrain : aucun INP réel, aucune distribution de Core Web Vitals ni aucune statistique de visiteurs n'est donc affirmé. Les mesures Lighthouse sont des passages de laboratoire, sans maîtrise du cache CDN. Les tests de lecture vidéo n'ont pas simulé une coupure réseau ni évalué l'émission entière.

Le connecteur Vercel trouve un projet `sandbox-podcast-site`, mais la vérification du domaine et des statistiques échoue selon le scope, en 403 ou 404. Le nom de projet historique `sandbox-podcast` n'est pas retrouvé. Le CLI Vercel n'est pas installé dans le PATH. Le rattachement du domaine au compte accessible n'est pas confirmé. Les coûts, logs privés, réglages GA4 et données Search Console restent inconnus. Un refus d'accès ne prouve pas l'absence d'un compte ou de trafic.

Des fichiers de badges ont été ajoutés localement pendant l'audit. Le build et les 341 tests initiaux précèdent ces ajouts ; le lint ciblé relève ensuite quatre erreurs dans ces fichiers. Les résultats sont datés et ne valent pas certification d'un état du dépôt resté immobile.

## 2. Inventaire et état de l'offre

| Ensemble                                                | État publié observé                                                                          | État local ou documenté                                        | Action attendue du visiteur                          |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------- |
| Accueil `/`                                             | Un épisode pilote, repris dans Derniers épisodes                                             | Textes de marque et mise en page en évolution locale           | Comprendre l'intérêt du média et ouvrir un épisode   |
| Bibliothèque `/episodes`                                | Un épisode, recherche, tri, filtres et lien vers la chaîne                                   | Import et administration éditoriale présents                   | Choisir puis regarder                                |
| Épisode `/episodes/1`                                   | Vidéo réelle, 17 chapitres, 14 ressources, partage                                           | Description longue conservée dans l'admin selon DD-0019        | Regarder, rejoindre un passage, retrouver une source |
| Thèmes `/topics`, `/topics/agents`                      | Entrées par sujet ; certains sujets n'ont aucun épisode                                      | Taxonomie plus large que la bibliothèque actuelle              | Trouver un sujet plutôt qu'un numéro d'épisode       |
| Recherche `/search`                                     | Recherche transversale ; Sillage donne un épisode et un projet                               | Sources extraites de la description et collections locales     | Retrouver un contenu connu                           |
| Classements `/charts`, GitHub, Skills, Models           | GitHub et Skills au 10 octobre ; Models jusqu'au 12 octobre                                  | Collecteurs, règles et profils v3 en préparation               | Découvrir puis examiner un outil ou un modèle        |
| Rising                                                  | Pas d'édition ; état explicite, 1 209 dépôts suivis et historique 4/7 jours                  | Baselines et détection intrajournalière                        | Comprendre pourquoi le classement attend             |
| Archives `/charts/history` et éditions                  | Dates et premières places ; archive Skills du 10 octobre en 404                              | Historique figé et routes d'édition                            | Comparer les éditions et citer une date              |
| Méthodes                                                | Pages publiques ; GitHub décrit plusieurs cadences ; Skills/Models décrivent un profil futur | Versions, sources et pondérations dans le domaine              | Comprendre ce que mesure un rang                     |
| Fiches GitHub `/charts/project/...`                     | Fiches issues des classements réels, présentes dans le sitemap                               | Données, historiques et sources en base                        | Examiner les mesures et ouvrir le dépôt              |
| Catalogue `/nos-projets`                                | 34 projets, catégories, créateurs, recherche                                                 | Sources et médias vérifiés, inventaire documenté               | Découvrir une réalisation de l'équipe                |
| Fiches `/nos-projets/sillage` et autres                 | Auteur, disponibilité, plateformes, sources, date, médias                                    | Données structurées validées par Zod                           | Essayer, installer ou consulter le code              |
| À propos `/about`                                       | Photos, noms et liens sociaux                                                                | L'introduction est éditable                                    | Savoir qui produit le contenu                        |
| RSS, sitemap, robots                                    | Services publics accessibles                                                                 | RSS textuel d'épisodes, indexation sélective                   | Suivre les publications ou découvrir les pages       |
| Versions EN, ES, DE                                     | Interfaces accessibles, contenu partiellement français, noindex sur l'échantillon            | Relecture et publication des traductions distinctes            | Lire dans sa langue, quand la traduction est prête   |
| Anciennes fiches `/projects`, `/models`, `/moves`       | Pages de démonstration accessibles ; échantillon noindex                                     | Snapshots Git avec provenance mock                             | Parcours historique à neutraliser ou signaler        |
| Anciens articles `/stories/...`, `/latest`, `/rankings` | Redirections vers les parcours actuels dans les sondes                                       | Articles autonomes retirés selon les décisions                 | Conserver la validité des anciens liens              |
| Administration et API                                   | `/admin` accessible comme écran de connexion ; GET contenu sans session en 401               | Permissions, brouillons, publication et conflits ETag          | Usage interne, pas un produit public                 |
| Badges et récompenses                                   | Présence publique non vérifiée dans cet audit                                                | Nouveaux fichiers et migration 0009 apparus pendant le travail | Fonctionnalité locale en cours, à auditer séparément |

La génération de 213 pages au build n'est pas un inventaire de 213 pages indexables. L'offre publique est beaucoup plus petite et plusieurs routes historiques sont volontairement hors indexation.

## 3. Ce qui fonctionne et mérite d'être conservé

- La lecture est directe. La façade YouTube évite de charger le lecteur avant le clic ; le chapitre Sillage ouvre bien le lecteur à 1 550 secondes. Le lien externe YouTube fournit une alternative. Preuves U03 à U05.
- Les 17 chapitres et 14 ressources donnent une raison de consulter le site même après avoir découvert la vidéo sur YouTube. Leur accès par ancre et les données structurées Clip sont déjà présents.
- La présentation compacte des classements facilite le balayage mobile. Les détails, mesures et sources se déplient à la demande. Le filtre Design conserve le rang officiel 13 : il ne crée pas un faux nouveau classement. Preuves U08 à U11.
- Le catalogue apporte une matière propre à l'équipe. Auteur, état de disponibilité, code source et date de vérification sont visibles. Les filtres croisés, l'état vide et la galerie fonctionnent. Preuves U12 à U17.
- L'état Rising explique l'attente plutôt que de remplir la page avec de faux résultats. Cette règle doit s'appliquer aux autres données manquantes.
- Les fondations sont solides pour ce stade : TypeScript strict, schémas Zod, logique de classement isolée, tests du domaine et des permissions, en-têtes de sécurité, contenus rendus sur le serveur, métadonnées et RSS. Les 341 tests initiaux et le build passent.
- Les routes examinées possèdent des canonical cohérents. Les langues non prêtes restent noindex et ne sont pas annoncées comme alternates indexables. Ce comportement protège les contenus français et doit être conservé jusqu'à la relecture.

## 4. Défauts et améliorations de qualité

Une sévérité élevée signifie ici risque de confusion publique, rupture de parcours ou mesure inutilisable. Une sévérité moyenne signifie gêne d'usage ou coût de maintenance. Elle est indépendante de l'intérêt commercial d'une opportunité. La confiance est élevée quand le comportement et sa source sont vérifiés ; elle est moyenne quand la cause ou l'effet restent à établir.

### F01. Des données de démonstration ressemblent à des données réelles

`/projects/claude-code` répond 200 et montre un Top 10, 16 éditions, une courbe de stars et des avis datés. La page affirme que les données viennent des sources citées. Aucun avertissement de démonstration n'est visible dans le document. Le snapshot local `data/snapshots/github/2026-W41.json` porte pourtant `provenance: mock` et alimente l'ancien écran. Les routes `/models/...` et `/moves/...` sondées appartiennent au même ensemble historique.

Le noindex observé évite de promouvoir ces pages dans l'index, mais ne protège pas une personne qui reçoit un lien. Recommander une désactivation publique ou un avertissement explicite avant toute métrique, en conservant les fixtures pour le développement. Prévoir une redirection seulement lorsqu'une vraie fiche équivalente existe. Confiance élevée, sévérité élevée. Preuves U22, sondes complémentaires, [écran historique](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/apps/site/src/components/entity-screen.tsx) et [route](<https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/apps/site/src/app/%28fr%29/projects/%5Bslug%5D/page.tsx>). Action A01.

### F02. Une archive publiée dans le sitemap est introuvable

`/charts/skills/2026-10-10` figure parmi les 77 URL du sitemap et renvoie 404 lors de deux requêtes HTTP puis dans le navigateur. La page courante Skills et l'archive générale affichent pourtant cette édition. Les autres URL du premier passage répondent comme attendu : 94 réponses 200, un refus 401 et deux 404, dont celle volontairement inexistante.

La cause précise en production n'est pas isolée. Les sources à rapprocher sont le générateur de sitemap, `sandboxChartsData`, `findChart` et `hasChartEdition`. Réparer le contrat entre publication, route et sitemap, puis vérifier toutes les archives par HTTP. Confiance élevée sur le défaut, moyenne sur sa cause. Sévérité élevée. Preuve U21. Action A02.

### F03. La fraîcheur et la méthode sont difficiles à interpréter

Le titre des classements annonce une actualisation toutes les 12 h. GitHub et Skills affichent une seule édition du 10 octobre au relevé du 14 ; Models possède des éditions plus récentes. La méthode GitHub évoque à la fois un gel le lundi et un gel quotidien à 03:00 UTC. Le cron local est quotidien. La méthode publiée annonce `github-momentum-v1+stars`, mais les détails visibles exposent notamment reach et Dynamique ; ils ne permettent pas, à eux seuls, de reproduire le score à sept jours décrit dans le texte. Skills et Models présentent un profil v3 explicitement en préparation, sans donner une explication suffisamment directe de l'édition actuellement affichée.

Cela ne démontre ni panne de collecte ni falsification des scores. Collecte, gel et affichage peuvent avoir des rythmes différents. Le défaut confirmé est leur explication publique. Afficher séparément date du dernier relevé, date de l'édition, version du calcul et état de la prochaine édition. Relier chaque édition à sa méthode conservée ; expliquer le statut de baseline si les variations ne sont pas encore calculables. Une seule ligne de statut et un lien suffisent sur l'interface compacte. Confiance élevée, sévérité élevée. Preuves U08 à U11, extraits de méthodes et [cron](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/apps/site/vercel.json). Action A03.

### F04. Google Analytics est incompatible avec la CSP publiée

Après acceptation, le DOM demande `www.googletagmanager.com/gtag/js`. La CSP HTTP n'autorise que le site, Vercel et YouTube dans script-src ; connect-src n'autorise pas les destinations GA. Le code local reproduit cette incompatibilité. Les journaux de console exposés par l'outil sont vides, mais ne constituent pas une preuve de collecte.

Corriger les origines nécessaires à la configuration GA sans publicité, puis vérifier réellement les requêtes, DebugView, les navigations internes, le refus et le retrait. Ne pas ouvrir la politique à tous les domaines Google ni ajouter des fonctions publicitaires inutiles. La [documentation CSP de Google](https://developers.google.com/tag-platform/security/guides/csp?hl=en) précise les destinations à adapter. Confiance élevée, sévérité élevée. Preuve U06 ; [configuration](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/apps/site/next.config.ts), [composant de consentement](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/apps/site/src/components/analytics-consent.tsx). Action A04.

### F05. L'information sur la mesure reste incomplète pour le visiteur

La préférence Refuser/Accepter et sa réouverture fonctionnent. Aucun lien vers une politique de confidentialité, des informations sur les durées, les destinataires ou l'exercice des droits n'apparaît dans les parcours et le pied de page examinés. La préférence stockée en local n'a pas de date d'expiration dans le code. L'existence et les réglages de la propriété GA4 restent à confirmer.

Faire compléter les informations par le responsable du site et les rendre accessibles depuis la bannière et le pied de page. Définir la durée du choix et sa réévaluation. La CNIL demande une [information accessible et compréhensible](https://www.cnil.fr/fr/conformite-rgpd-information-des-personnes-et-transparence) et un [refus aussi simple que l'acceptation](https://www.cnil.fr/fr/questions-reponses-lignes-directrices-modificatives-et-recommandation-cookies-traceurs). Cet audit constate des manques d'information ; il ne délivre pas une conclusion juridique globale. Confiance élevée sur l'interface, moyenne sur l'ensemble des traitements. Action A05.

### F06. Les contrôles de qualité ne sont pas tous exécutables dans l'état local

`pnpm check` s'arrête au formatage sur 149 fichiers au premier passage. Le lint global dépasse ensuite la mémoire vers 4 Go. Sa configuration n'exclut pas `.local/`, où se trouvent des copies et dépendances de travail ; ce périmètre est une cause probable à corriger, pas une raison de désactiver le lint. Le lint ciblé sur le code actif relève quatre erreurs dans `badge-generator.tsx` et `domain/badges.ts`, ajoutés pendant l'audit.

Rétablir un périmètre explicite pour les fichiers générés et les copies locales, corriger les erreurs du code actif et les écarts de format, puis obtenir un passage complet du gate. Le ciblage exécuté pour diagnostiquer ne remplace pas le contrôle global. Ajouter des parcours navigateur aux contrôles unitaires : une suite de tests du domaine peut passer tout en laissant une URL publiée en 404. Confiance élevée. Sévérité moyenne pour l'usage, élevée pour la fiabilité de livraison. Actions A06 et A07.

### F07. La performance mobile demande un travail ciblé

| Page                      | Performance | Accessibilité | LCP laboratoire | CLS laboratoire |   TBT |
| ------------------------- | ----------: | ------------: | --------------: | --------------: | ----: |
| Accueil mobile            |          89 |           100 |           3,6 s |           0,010 | 30 ms |
| Épisode mobile, passage 1 |          84 |           100 |           2,9 s |           0,205 | 20 ms |
| Épisode mobile, passage 2 |          81 |           100 |           4,0 s |               0 |  0 ms |
| GitHub mobile             |          87 |           100 |           3,8 s |           0,007 |  0 ms |
| Catalogue mobile          |          87 |            97 |           3,8 s |           0,007 | 90 ms |
| Accueil ordinateur        |          97 |           100 |           0,8 s |           0,012 | 60 ms |

Les [seuils de référence](https://web.dev/articles/defining-core-web-vitals-thresholds) sont LCP au plus 2,5 s, INP au plus 200 ms et CLS au plus 0,1, au 75e percentile terrain. Comparer ces passages de laboratoire à ces repères aide à choisir les travaux ; cela ne donne pas un verdict de Core Web Vitals réels. TBT n'est pas INP.

Au premier passage, Lighthouse attribue le déplacement de l'épisode à `main#main`, sans isoler sa cause en amont. Un second passage à 19:21 donne un CLS de 0 et un LCP de 4,0 s, avec un score de 81. Le déplacement n'est donc pas reproduit au second essai ; la variabilité et les conditions de chargement doivent être étudiées avant d'en déduire une correction. Il estime environ 100 Kio de JavaScript inutilisé par page et des économies de 62 à 115 Kio sur les images. Ces estimations ne s'additionnent pas en gain de chargement garanti.

Priorité : vérifier la variabilité du chargement de l'épisode, tracer un déplacement lorsqu'il se reproduit et corriger sa cause démontrée, puis traiter les ressources de rendu et images indiquées par les rapports. Conserver les dimensions réservées et la façade vidéo. Confiance élevée sur les mesures, moyenne sur leur répétabilité et leurs causes. Actions A08 et A09.

### F08. Les pages de classement supportent un coût serveur supérieur au catalogue

Trois requêtes curl par page, connexions fraîches, compression activée, sans limitation de réseau :

| Page      | TTFB médian | HTML transféré, premier relevé | HTML décompressé | JS + CSS référencés dans le HTML, transférés |
| --------- | ----------: | -----------------------------: | ---------------: | -------------------------------------------: |
| Accueil   |      246 ms |                   8 390 octets |    45 170 octets |                               306 962 octets |
| Épisode 1 |      433 ms |                  13 363 octets |    80 644 octets |                               306 099 octets |
| GitHub    |    1 057 ms |                  23 906 octets |   187 678 octets |                               333 231 octets |
| Catalogue |      135 ms |                  15 302 octets |   120 353 octets |                               316 860 octets |
| Sillage   |      147 ms |                  10 722 octets |    65 269 octets |                                   Non relevé |

Le TTFB curl inclut DNS et TLS. Les ressources additionnées ne représentent pas le poids total d'une visite : images, polices, imports tardifs, préchargements et cache navigateur ne sont pas tous comptés. La miniature publique de l'épisode mesure 226 558 octets dans sa version originale.

Les pages média et classements répondent private/no-store ; le catalogue utilise un cache public. Les lectures éditoriales ont un cache de processus de cinq secondes, et les classements assemblent plusieurs lectures de base. Étudier un cache public des éditions immuables et un cache de données invalidé lors de la publication. Garder l'administration privée. Mesurer les requêtes et la région de la base avant de changer l'architecture. Confiance élevée sur les observations, moyenne sur le gain possible. Action A10.

### F09. Les langues ajoutent du poids sans fournir encore une traduction complète

L'accueil anglais transfère 75 928 octets de HTML compressé, contre 8 390 en français. L'épisode anglais garde son titre, résumé et nombreux chapitres en français. Les pages ES/DE de classement mêlent leurs libellés à du français et des descriptions anglaises. Elles restent noindex dans l'échantillon, sans hreflang indexable : ce n'est pas une erreur à corriger en ouvrant l'indexation.

Le layout local transmet le dictionnaire au provider client ; le dictionnaire anglais versionné pèse environ 185 Ko. Cette sérialisation et les composants partagés sont des pistes de réduction, à mesurer séparément. Prioriser le français, terminer une page anglaise utile si la demande est confirmée, puis seulement élargir. Confiance élevée sur l'état, moyenne sur la part exacte de chaque cause de poids. Action A11.

### F10. Quelques détails mobiles et d'accessibilité restent à corriger

À 320 px, le document de l'épisode déborde d'environ 12 px et le lien À propos dépasse sa largeur utile. À 390 px, l'accueil impose neuf lignes de titre. La recherche d'en-tête est cachée sur mobile ; le lien existe dans le pied de page, mais se découvre tard. Dans le catalogue, Lighthouse signale le lien Retrouver l'équipe au milieu de la note de sources : le lien doit être reconnaissable autrement que par sa couleur.

Le lien d'évitement place correctement le focus sur main. La galerie utilise un dialogue modal, place le focus sur la fermeture et se ferme avec Échap. Les contrôles DOM ciblés trouvent un main, un h1 et un label de recherche sur À propos. Les scores automatiques élevés ne prouvent pas une conformité [WCAG 2.2](https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/).

Corriger le débordement, raccourcir la promesse d'épisode, rendre la recherche facilement accessible et souligner le lien de la note. Faire ensuite une revue clavier et lecteur d'écran, du zoom et des préférences de mouvement. Confiance élevée, sévérité moyenne. Actions A12 et A13.

### F11. La promesse du contenu et la suite du parcours sont faibles

Le site utilise encore le titre catalogue de sujets du pilote, alors que le lecteur YouTube présente "Codex, Claude Code, OpenCode : le modèle ne suffit pas". La fiche Sillage ne renvoie pas vers sa démonstration dans l'épisode. La recherche Sillage retrouve l'épisode et le projet, mais pas les ressources, dont les libellés sont génériques. À propos présente des liens personnels sans expliquer les rôles ou la méthode éditoriale.

Cela réduit les occasions de comprendre l'apport de Sandbox et d'approfondir. Réécrire le titre et le résumé autour d'un bénéfice fidèle à la vidéo, nommer les ressources, relier Sillage à 25:50 et à la discussion de 37:17, donner quelques faits vérifiés sur les animateurs. Les corrections de ponctuation et du singulier "1 entrées" peuvent accompagner ce travail. Confiance élevée sur les observations ; effet sur la fréquentation à tester. Actions A13 à A15.

Sur les 13 liens externes d'épisode sondés en HTTP, 12 répondent 200 ; le site du ministère du Travail répond 503 lors de ce passage. Cette indisponibilité ponctuelle ne prouve pas un lien définitivement cassé. Prévoir une vérification des sources avant publication et des contrôles espacés, sans remplacer une source primaire par une affirmation non vérifiée.

### F12. Les raisons de revenir existent, mais les moyens de suivre sont discrets

Le RSS fonctionne, mais contient des liens et descriptions, sans enclosure audio : c'est un flux de publications, pas un flux audio à soumettre tel quel aux plateformes de podcasts. Le lien vers la chaîne existe dans la bibliothèque et la fiche. Aucun formulaire de newsletter n'est visible dans les parcours examinés. Les quatre Shorts privés et le test de miniatures sont documentés dans le rapport YouTube ; leur publication et leur résultat ne sont pas présumés.

Commencer par un appel clair à suivre la chaîne et par le RSS existant. Tester une demande réelle avant d'ajouter une newsletter et son travail régulier. Confiance élevée, opportunité de fidélisation à valider. Actions A16, A18 à A20.

### F13. La sécurité présente des protections et quelques limites connues

Les lectures privées refusent une requête sans session. Le code vérifie l'origine des mutations, les permissions serveur, les mots de passe scrypt et les signatures comparées en temps constant. Les cookies de connexion utilisent HttpOnly, Secure en production et SameSite strict. Le cron vérifie un secret avant d'exécuter un job ; aucun job n'a été déclenché par l'audit.

La limitation des connexions est une Map en mémoire : sa portée ne couvre pas toutes les instances Vercel. La CSP conserve unsafe-inline. Certaines routes lisent le corps entier avant d'en vérifier la taille, alors qu'un utilitaire de lecture bornée existe. Ces limites justifient une revue ciblée ; aucune exploitation n'a été tentée et aucune faille critique n'est déclarée démontrée. Action A21.

L'audit des dépendances trouve un avis modéré sur esbuild 0.18.20, via drizzle-kit et esm-loader, dans l'outillage de développement. Il concerne le serveur de développement esbuild décrit par [GHSA-67mh-4wv8-2f99](https://github.com/advisories/GHSA-67mh-4wv8-2f99). Cela ne prouve pas que le site Next publié utilise ce serveur vulnérable. Étudier la mise à jour du parent et la compatibilité ; aucun audit fix forcé. Action A22.

## 5. Positionnement recommandé et cohérence de l'offre

Le public prioritaire n'est pas validé par des entretiens. La recommandation suivante est une hypothèse fondée sur le pilote, les projets visibles et les requêtes explorées : viser d'abord les développeurs et créateurs qui utilisent les agents IA et veulent comparer des façons de travailler à partir d'exemples concrets.

| Public envisageable                            | Preuve ou indice disponible                                   | Ce qu'il faudrait lui apporter                                   | Priorité proposée                             |
| ---------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------- |
| Développeurs et créateurs utilisant l'IA       | Pilote sur les harnais, Sillage, outils et dépôts de l'équipe | Démonstrations, limites, protocoles, résultats reproductibles    | Première hypothèse à valider                  |
| Curieux de tech déjà familiers du sujet        | Format débat, actualité et jeux accessibles                   | Explications des termes et points d'entrée courts                | Public secondaire, sans multiplier les sujets |
| Équipes qui choisissent un outil en production | Méthodes de classement et outils hébergeables                 | Sécurité, coût, maintenance, travail d'équipe et preuves d'usage | À explorer après collecte de besoins          |

Proposition de formulation à tester : "On construit avec les outils IA, on montre les résultats et on discute de leurs limites." Elle décrit une ligne de travail proposée ; elle ne doit pas servir à prétendre que tous les outils du classement ont été testés.

Les rubriques peuvent jouer des rôles simples :

- Le podcast apporte les démonstrations et les discussions.
- Les classements repèrent des candidats et expliquent des signaux datés.
- Nos projets montre les réalisations de l'équipe, avec leurs états et limites.

Le lien d'intérêt est déjà visible par l'attribution des projets. Le rappeler dans un test ou un épisode consacré à une réalisation interne, et appliquer le même protocole aux alternatives. Séparer clairement auteur d'un projet, auteur d'une analyse et source d'un classement.

À renforcer : la preuve pratique, la méthode, le maillage et la fidélisation. À simplifier : les titres catalogue de marques, les pages et langues incomplètes. À arrêter ou isoler : les anciennes fiches de démonstration publiques et les promesses de fraîcheur non expliquées. À différer : le rôle de média généraliste quotidien, une communauté à animer et une offre payante sans demande observée.

Exemple de présentation de l'épisode, à tester sans l'appliquer pendant cet audit :

- Titre : "Codex, Claude Code, OpenCode : qu'est-ce qui change vraiment ?"
- Résumé : "La démonstration de Sillage ouvre un débat sur les harnais IA, le contexte et les outils. Retrouvez le Build à 25:50 et la discussion à 37:17."
- Actions : regarder l'épisode, choisir un chapitre, suivre les prochaines émissions.

Cette version présente une discussion. Elle ne la transforme pas en benchmark contrôlé que l'équipe n'a pas encore réalisé.

## 6. Contenu : diagnostic et programme proposé

La revue du début de l'émission repose sur les chapitres, le lecteur testé et le fichier local de sous-titres automatiques `transcript-youtube.txt`. Elle ne remplace pas une écoute critique complète. La première minute est un montage de sujets variés ; l'introduction du format commence vers 1:03 et la première actualité vers 1:51. Le chapitre du Build commence à 25:50. Avec le nouveau titre YouTube sur les harnais, l'arrivée au sujet central peut donc paraître tardive.

Le rapport YouTube du 14 octobre consigne 403 impressions, 3,5 % de CTR, une durée moyenne de 5:57 et 30 % de spectateurs présents à 30 secondes au relevé initial. Ces chiffres proviennent de ce rapport, pas d'un nouvel accès Studio pendant cet audit. Ils portent sur une seule émission et de faibles volumes. Ils suggèrent de travailler la correspondance promesse/début, sans démontrer une cause ni désigner un format gagnant.

Pour les prochaines émissions, essayer une ouverture de 20 à 30 secondes sur une question précise et ce que le spectateur va pouvoir juger. Placer tôt une preuve ou un désaccord compréhensible. Le Radar peut rester, mais le titre principal doit correspondre au parcours promis. Ne pas modifier le test de miniatures déjà en cours sur la base de cet audit seul.

Quatre axes éditoriaux proposés :

1. Construire avec les agents : un problème, une réalisation, des limites.
2. Choisir un outil : critères par tâche et protocole reproductible.
3. Comprendre les signaux : classements, données et biais de mesure.
4. Revenir sur un essai : ce qui a tenu, changé ou échoué après utilisation.

Les idées suivantes sont des travaux proposés, pas des contenus ni résultats déjà produits. Les heures sont des estimations de préparation et de déclinaison, hors enregistrement.

| Priorité | Contenu et angle                                        | Public et besoin                                                | Format et apport propre                                                                      | Sources ou preuves à préparer                                               | Effort estimé         | Diffusion                                                |
| -------- | ------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------- | -------------------------------------------------------- |
| 1        | Ce que le harnais change quand le modèle reste le même  | Développeur qui choisit son environnement                       | Démonstration d'une même tâche ; documenter quand les configurations ne sont pas comparables | Dépôt de test, versions, paramètres, journal des essais et docs officielles | 4 à 8 h               | YouTube, ressource d'épisode, LinkedIn                   |
| 1        | Sillage : du problème initial à la démonstration        | Créateur qui veut reprendre une session sur plusieurs appareils | Build accompagné d'un retour sur les choix ; lien d'intérêt déclaré                          | Passage existant à 25:50, code, capture et limites actuelles                | 2 à 3 h               | Extrait horizontal, fiche Sillage, communauté pertinente |
| 1        | Un score GitHub ne dit pas si un outil est bon          | Lecteur des classements                                         | Deux projets comparés sur attention, activité et usages ; pas de confusion avec qualité      | Édition figée, sources des métriques, limites du calcul                     | 2 à 4 h               | Classement, épisode, LinkedIn                            |
| 1        | Installer un skill : comment vérifier ce qu'il va faire | Utilisateur d'agents                                            | Checklist testée sur un exemple ; montrer les permissions et fichiers touchés                | Code du skill, environnement de test isolé, documentation du fournisseur    | 3 à 5 h               | YouTube court, ressource téléchargeable                  |
| 1        | Ce que nous avons corrigé après le pilote               | Auditeur curieux de la fabrication du média                     | Retour court sur une amélioration vérifiée et son résultat                                   | Changements réels, extraits avant/après, limites des statistiques           | 1 à 2 h               | YouTube, LinkedIn                                        |
| 2        | Pourquoi un classement attend sept jours                | Lecteur confronté à Rising vide                                 | Explication visuelle d'une baseline et d'une mesure manquante                                | Règles réellement actives, relevés datés                                    | 1 à 2 h               | Méthode, ressource d'épisode                             |
| 2        | Contexte et mémoire : un essai qui se reproduit         | Développeur confronté aux longues sessions                      | Un cas réel, un résultat observé, des limites ; éviter le discours général                   | Passage de 48:25, scénario et journal d'exécution                           | 3 à 5 h               | YouTube, kit de reproduction                             |
| 2        | Vibe coder un jeu : qu'est-ce qui le rend jouable ?     | Créateur de prototype                                           | Démonstration et erreurs de conception, pas seulement génération de code                     | Passage de 1:11:44, projet choisi, capture et autorisation du créateur      | 2 à 4 h               | Short, épisode, fiche projet                             |
| 2        | Un outil local après deux semaines d'utilisation        | Personne qui veut installer durablement                         | Retour avec incidents et maintenance ; suivi d'un projet déjà couvert                        | Journal d'usage réel de l'équipe, versions et opérations                    | 2 à 3 h après l'usage | YouTube, fiche mise à jour                               |
| 2        | Quel modèle pour quelle tâche ?                         | Lecteur du classement Models                                    | Expliquer capacités, prix et configurations sans meilleur universel                          | Sources de l'édition, variantes exactes, exemples d'usage vérifiés          | 3 à 5 h               | Classement et vidéo pédagogique                          |
| 3        | Une ressource de l'épisode que nous utilisons encore    | Auditeur qui veut agir en moins de dix minutes                  | Présentation d'un usage concret plutôt qu'un nouveau tour d'actualité                        | Usage actuel, source primaire et lien daté                                  | 1 à 2 h               | Extrait, RSS, LinkedIn                                   |
| 3        | Le bilan d'un Build : gardé, modifié ou abandonné       | Créateur qui veut apprendre des choix de l'équipe               | Retour après plusieurs semaines, avec raisons et preuves                                     | Historique du projet, limites et comparaison initiale                       | 2 à 4 h               | Épisode et fiche projet                                  |

Déclinaison possible du pilote, sans nouvelle émission : un extrait centré sur le désaccord harnais officiel/OpenCode ; une ressource décrivant les critères discutés ; un lien de la fiche Sillage vers le chapitre ; une publication LinkedIn présentant une seule question et renvoyant au passage. Les quatre Shorts déjà privés évitent de recommencer leur fabrication. Vérifier leurs sous-titres et leur contexte avant toute décision de publication.

Calendrier de quatre semaines, à valider selon la capacité :

| Semaine | Production proposée                                      | Réutilisation et diffusion                                                          | Charge supplémentaire estimée        |
| ------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------ |
| 1       | Clarifier le titre/résumé du pilote et les liens Sillage | Vérifier un Short existant et préparer une publication sur le même sujet            | 3 à 4 h, hors corrections techniques |
| 2       | Préparer un protocole court sur une même tâche           | Montrer le protocole et ses limites dans un extrait ou le prochain épisode si prévu | 4 à 6 h                              |
| 3       | Expliquer un score réel et sa méthode corrigée           | Une ressource, un visuel simple et une publication, après A03                       | 3 à 4 h                              |
| 4       | Faire le bilan des essais de diffusion et d'usage        | Garder un format, abandonner un autre, préparer le prochain Build                   | 2 à 3 h                              |

Ce calendrier ne suppose ni quatre nouveaux épisodes ni une présence quotidienne. Si l'équipe dispose de moins de trois heures par semaine, garder seulement une déclinaison utile par épisode et un canal de diffusion supplémentaire.

## 7. Découverte, SEO et citation par les moteurs de réponse

Le robots.txt laisse lire les pages et bloque les routes d'administration. Les canonical du premier passage sont cohérents avec le domaine public ; les redirections historiques sondées aboutissent. Le sitemap contient une erreur confirmée, F02. Les méthodes examinées restent noindex et sont exclues du sitemap courant ; leur ouverture éventuelle doit attendre une méthode correcte et suffisamment utile, sans ouvrir les fixtures.

Les données structurées existent dans le HTML brut et ont été parsées en JSON : PodcastSeries et ItemList à l'accueil, PodcastEpisode, VideoObject, 17 Clip et BreadcrumbList sur l'épisode, WebSite et Organization dans le layout. Leur existence est confirmée ; aucune validation Rich Results complète n'a été exécutée. Les fiches de projets personnels disposent d'un fil d'Ariane, sans balisage logiciel spécifique observé. Ajouter du balisage uniquement si les données visibles le justifient.

La [documentation vidéo de Google](https://developers.google.com/search/docs/appearance/video) donne les conditions de découverte et de présentation des vidéos. Vérifier la découvrabilité du lecteur chargé au clic et de sa miniature dans Search Console ; la présence d'un VideoObject ne garantit ni indexation vidéo ni résultat enrichi.

Les variantes linguistiques testées sont noindex, sans alternates indexables. Le manque de hreflang sur ces variantes est cohérent avec leur état. L'enjeu immédiat est de ne pas présenter une traduction partielle comme une expérience achevée. Aucun changement de préfixe d'URL n'est recommandé.

Carte des intentions à travailler :

| Intention                                     | Formulations explorées ou proposées                          | Page à améliorer d'abord                | Condition pour mériter la visite                                              |
| --------------------------------------------- | ------------------------------------------------------------ | --------------------------------------- | ----------------------------------------------------------------------------- |
| Comprendre un harnais et le choisir           | Comparatif Codex Claude Code OpenCode ; rôle d'un harnais IA | Épisode et ressource associée           | Protocole ou discussion honnêtement qualifiée, liens temporels                |
| Choisir un skill utile                        | Meilleurs skills Claude Code ; skill pour un besoin précis   | Classement Skills, puis contenu de test | Compatibilité, sécurité et essai réel ; un rang d'installations ne suffit pas |
| Comprendre un classement de modèles           | Classement modèles IA ; modèle pour une tâche                | Models et sa méthode d'édition          | Variantes, date, couverture et limites compréhensibles                        |
| Trouver un podcast de développement avec l'IA | Podcast IA développeurs ; agents de code podcast             | Accueil, bibliothèque et À propos       | Promesse et public clairs, épisode pertinent, moyen de suivre                 |
| Découvrir une réalisation précise             | Sillage agents de code ; nom d'un projet de l'équipe         | Fiche projet                            | Démonstration, disponibilité, installation et passage d'épisode               |
| Comprendre une tendance open source           | Projets IA GitHub en progression                             | GitHub, édition et analyse associée     | Mesures datées, méthode et interprétation distinctes                          |

Les recherches ont été explorées qualitativement dans le moteur disponible. Ce tableau ne donne ni volumes ni positions Google. Les formulations supplémentaires sont des hypothèses tirées du contenu ; les confirmer dans Search Console et auprès des lecteurs avant de créer des pages.

Pour être citable, Sandbox doit surtout publier des observations originales, datées, attribuées et vérifiables. Exemple : un test avec dépôt, protocole, résultat et limites ; une édition de classement dont la méthode peut être retrouvée. Une compilation de scores sans contexte n'apporte pas cet avantage. Les [recommandations de Google sur les fonctions IA](https://developers.google.com/search/docs/appearance/ai-features) ne demandent pas un fichier ou balisage spécial. `llms.txt`, MCP ou un export Markdown ne sont pas des priorités avant le contenu et les erreurs de données. Aucun taux de citation par ChatGPT, Perplexity ou Google n'a été mesuré.

## 8. Benchmark de six références

Pages officielles consultées le 14 octobre 2026. La comparaison porte sur l'offre et les parcours visibles, sans estimer leur trafic, leur rentabilité ou leurs conversions. Une référence de format n'est pas forcément un concurrent direct.

| Référence et raison du choix                                                  | Pratique visible                                                                            | Application possible à Sandbox                                                  | Limite de la comparaison                                                           |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| [IFTTD](https://www.ifttd.io/), podcast de développeurs en français           | Promesse précise, épisodes par thèmes et invités, transcription, liens d'écoute et extraits | Dire à qui sert le podcast ; relier question, passage et ressource              | Son catalogue ancien ne justifie pas de construire tous ses services dès un pilote |
| [The Changelog](https://changelog.com/podcast), média open source             | Résumés orientés sujet, écoute directe, clips et lettre d'information                       | Faire circuler la même matière entre démonstration, épisode et suivi            | Organisation et volume éditorial différents                                        |
| [TLDR AI](https://tldr.tech/ai), veille par e-mail                            | Promesse de lecture courte, formulaire direct, résumés avec liens vers les sources          | Une éventuelle lettre doit annoncer un bénéfice et une charge de lecture précis | La cadence quotidienne serait coûteuse et peu distincte pour Sandbox               |
| [GitHub Trending](https://github.com/trending), découverte à la source        | Liste de dépôts et choix de période/langue ; le service parle d'intérêt de la communauté    | Rendre chaque signal intelligible et permettre d'ouvrir le dépôt                | Une présence dans Trending n'est pas une évaluation fonctionnelle                  |
| [Skills.sh](https://www.skills.sh/), catalogue proche de Skills               | Définition du format, classement d'installations, accès à une commande d'installation       | Relier découverte, vérification et usage ; choisir quelques skills testés       | Répliquer les installations seules apporte peu de différence                       |
| [Artificial Analysis](https://artificialanalysis.ai/), comparaison de modèles | Évaluations et variantes identifiées, mises à jour datées, plusieurs dimensions             | Expliquer quelle variante et quelle capacité un rang compare                    | Sandbox ne dispose pas d'un laboratoire équivalent démontré                        |

La première tentative de référence Underscore a mené à un studio créatif homonyme ; elle a été exclue. Radio France était inaccessible au robot de recherche. Le rapport YouTube existant contient d'autres références vidéo, mais elles ne remplacent pas ce benchmark directement consulté.

## 9. Diffusion et expériences de croissance

Trois canaux méritent le premier essai : YouTube pour la découverte et la consommation, LinkedIn pour les retours de construction de l'équipe, le site et la recherche pour les preuves durables. RSS sert déjà au retour. Les communautés et invitations croisées peuvent compléter ce dispositif après identification d'un sujet utile et des règles de chaque espace.

| Canal                           | Public et format                                                         | Cadence proposée                                                                   | Destination                                                 | Prérequis et mesure                                                                           |
| ------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| YouTube                         | Développeurs/curieux ; émission, extrait horizontal, Short sur une idée  | Une déclinaison vérifiée par épisode, puis cadence adaptée aux résultats           | Vidéo complète ou chapitre ; ressources dans la description | Respecter le test en cours ; suivre impressions, durée regardée et trafic vers l'émission     |
| LinkedIn                        | Réseau professionnel des animateurs ; problème concret, résultat, limite | Une publication par sujet utile, sans dupliquer artificiellement les trois comptes | Ressource ou passage lié au sujet                           | Un auteur identifié, lien UTM sans donnée personnelle ; clics et visites engagées             |
| Site et recherche               | Personne qui cherche une réponse ou un outil                             | Une amélioration ou ressource durable par épisode                                  | Fiche ou épisode pertinent                                  | A01 à A05 ; suivi d'indexation, requêtes, pages d'entrée et actions utiles                    |
| Communautés/invitations         | Créateurs ou utilisateurs du projet traité                               | Une contribution pertinente ou proposition d'échange, sans cadence forcée          | Démonstration utile et source                               | Identifier les règles, déclarer le lien d'intérêt ; retours qualifiés et visites attribuables |
| RSS, puis éventuellement e-mail | Lecteurs qui souhaitent revenir                                          | RSS à chaque publication ; e-mail à décider après essai d'intérêt                  | Nouveau contenu utile                                       | Le RSS existe ; e-mail exige service, information et charge éditoriale                        |

Ne pas ouvrir tous les réseaux ni automatiser des messages de prospection. Les publications et prises de contact restent des actions proposées au propriétaire.

Quatre expériences sont proposées. Les seuils ci-dessous sont des règles de décision opérationnelles à accepter, pas des prévisions ni des seuils de significativité statistique.

| Expérience                         | Hypothèse et protocole                                                                                                                        | Durée et coût estimé                                                                | Mesure et décision                                                                                                                                                                                                       |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| E1, compréhension du site          | Montrer une proposition d'accueil courte à cinq personnes de la cible ; leur demander de décrire Sandbox et de trouver les sources de Sillage | Une semaine, 2 à 3 h ; aucun outil payant nécessaire                                | Poursuivre si quatre personnes sur cinq comprennent la promesse et trouvent le passage en moins d'une minute ; sinon réécrire. Aucun test utilisateur réalisé ici                                                        |
| E2, extraits déjà préparés         | Vérifier puis proposer au propriétaire la diffusion des quatre Shorts privés avec leur lien natif vers l'émission                             | Trois semaines, 2 à 4 h de vérification/suivi, hors fabrication déjà faite          | Comparer vues engagées, durée et trafic identifiable vers l'émission. Sans trafic suffisant, conclure indéterminé ; si un sujet apporte au moins cinq vues attribuables vers le long, essayer un second lot sur ce sujet |
| E3, contenu pratique différenciant | Publier après validation un essai reproductible sur une tâche, avec résultat et dépôt ; le diffuser sur YouTube et LinkedIn                   | Quatre semaines, 4 à 8 h, consommation éventuelle de modèles à budgéter avant essai | Chercher cinq retours qualifiés ou trois reproductions documentées. En leur absence, revoir le problème ou la diffusion avant de créer une série                                                                         |
| E4, moyen de suivre                | Après A04/A17, tester une action Suivre sur YouTube/RSS placée après un contenu utile, sans interrompre la lecture                            | Trois semaines, 2 à 3 h                                                             | Sur au moins 100 vues éligibles consenties, cinq actions de suivi justifient un deuxième essai ; sinon revoir la proposition. Un clic ne prouve pas l'abonnement externe                                                 |

Avec cette audience de départ, les retours qualitatifs et la répétition d'une observation seront souvent plus utiles qu'un test A/B de petites différences. Le test natif YouTube déjà lancé doit aller à son terme ou être arrêté par une décision explicite, sans lui superposer des modifications non tracées.

## 10. Huit possibilités d'évolution

| Possibilité                                  | Besoin et différence attendue                                   | Version minimale à tester                                                                         | Création/maintenance estimées et dépendances                                                | Décision proposée et signal de poursuite                                                            |
| -------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Kit de reproduction d'un Build               | Passer de la vidéo à une réalisation ; preuve propre à l'équipe | Un dépôt, une fiche de prérequis et un scénario testé                                             | 4 à 8 h, puis vérification à chaque changement de version                                   | À tester maintenant ; reproductions et questions précises                                           |
| Ressource d'épisode centrée sur une question | Retrouver l'idée sans revoir 78 minutes                         | Une section courte ou ressource liée au chapitre, sans réintroduire la description longue retirée | 2 à 4 h par épisode ; décision éditoriale si une nouvelle route autonome est envisagée      | À tester maintenant ; consultation et passage vers la vidéo                                         |
| Analyse courte d'une édition de classement   | Comprendre pourquoi un signal mérite attention                  | Deux ou trois observations signées, liées aux mesures et limites                                  | 1 à 2 h par édition choisie ; A03 indispensable                                             | À tester maintenant après correction des méthodes ; retours utiles et retour des lecteurs           |
| Newsletter sobre                             | Suivre les publications sans dépendre d'une plateforme          | Une lettre toutes les deux semaines sur des contenus déjà produits                                | 2 à 4 h de mise en place, puis 1 à 2 h par numéro ; service, consentement et propriétaire   | Plus tard ; demander et mesurer l'intérêt avant d'ouvrir un canal à entretenir                      |
| Distribution audio                           | Écouter sans garder une vidéo ouverte                           | Un épisode avec fichier audio, enclosure et flux validé                                           | 1 à 3 jours de préparation, puis contrôle à chaque épisode ; droits, qualité et hébergement | Plus tard, si le public le demande ; écoutes et retour après plusieurs épisodes                     |
| Badges datés de classement                   | Donner aux créateurs une citation vérifiable d'un rang          | Un badge lié à une édition et à sa méthode, indiquant rang et date                                | Travail local déjà commencé ; revue des règles et maintenance des routes nécessaires        | Plus tard après F01/F03 ; liens entrants utiles, sans faire passer un rang pour un label de qualité |
| Alertes personnalisées                       | Suivre un projet ou un mouvement précis                         | Commencer par un flux filtré plutôt que des comptes                                               | 1 à 3 jours pour un prototype, davantage pour e-mail/comptes ; fiabilité des données        | Plus tard ; demandes répétées et usages récurrents d'un flux simple                                 |
| Communauté permanente ou offre premium       | Discuter ou obtenir un service plus poussé                      | Recueillir les besoins dans les espaces existants avant tout lancement                            | Animation et support continus ; modèle économique non défini                                | À écarter maintenant ; réexaminer seulement avec un besoin répété et une capacité dédiée            |

## 11. Plan de mesure

La collecte locale en place porte surtout sur les pages vues. La correction de la CSP, la propriété GA4 et les informations de confidentialité sont des prérequis. Vercel Analytics et GA4 peuvent se compléter, mais il faut choisir quelle source répond à quelle question et expliquer les écarts de périmètre.

| Question de décision                              | Événement proposé                                      | Déclenchement et données minimales                                                        | Limite et indicateur                                                                                                                                                      |
| ------------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D'où viennent les visites utiles ?                | page_view et attribution de campagne                   | Page publique après consentement ; chemin et source/campagne autorisés                    | Préserver seulement une liste de paramètres UTM attendus. Le retrait actuel de query avant initialisation peut affecter l'attribution : à vérifier, pas à présumer résolu |
| Un visiteur essaie-t-il de regarder ?             | player_requested                                       | Clic de chargement ; episode_id, emplacement, start_seconds                               | Ce n'est pas une lecture effective ; ratio demandes/vues de fiche                                                                                                         |
| Regarde-t-il réellement ?                         | video_started, video_progress                          | Seulement si une API de lecteur et les choix de confidentialité permettent un état fiable | Sans cette intégration, utiliser YouTube Studio pour la durée et ne pas inventer une mesure site                                                                          |
| Les chapitres et sources sont-ils utiles ?        | chapter_selected, resource_opened                      | Clic ; episode_id, chapitre ou ressource identifiée, domaine de destination               | Un clic ne prouve pas lecture de la source ; comparer par épisode                                                                                                         |
| La recherche aide-t-elle ?                        | search_completed                                       | Soumission ; longueur de requête, nombre de résultats et type de résultat choisi          | Ne pas envoyer la recherche brute, potentiellement personnelle ; taux de recherches sans résultat                                                                         |
| Les classements donnent-ils envie d'approfondir ? | chart_filtered, chart_entry_opened, methodology_opened | Filtre ou détail ; chart_id, edition_id, filtre choisi                                    | Les interactions seules ne prouvent pas une décision d'installation                                                                                                       |
| Les projets trouvent-ils des utilisateurs ?       | project_opened, project_destination_opened             | Fiche puis lien externe ; project_id, type de destination                                 | Installation et usage externe restent inconnus sans retour du créateur                                                                                                    |
| Les visiteurs souhaitent-ils suivre ?             | follow_destination_opened                              | Action chaîne/RSS ; destination et emplacement                                            | Ne pas appeler le clic subscription_completed ; suivre les vrais abonnements dans la plateforme concernée                                                                 |
| Reviennent-ils ?                                  | Cohortes de visites consenties                         | Réutiliser les capacités de l'outil choisi, sans fingerprinting                           | Retour à 7/28 jours uniquement sur le périmètre mesuré ; biais de consentement et petits volumes à indiquer                                                               |

Tableau de bord hebdomadaire limité : sources des visites, fiches consultées, demandes de lecture, ressources ouvertes, actions de suivi et retour des lecteurs consentants. Le compléter par YouTube : impressions, durée de visionnage, rétention au début, abonnements attribués et provenance des vues. Garder séparés les compteurs publics, Studio et temps réel.

Contrôle d'acceptation de la collecte : aucun chargement de mesure avant choix ou après refus ; une vue par navigation prévue après acceptation ; aucun double comptage ; pas de recherche brute, adresse e-mail, identifiant admin ou fragment dans les événements ; arrêt après retrait. Les données des tests de l'audit peuvent avoir créé du trafic de test après acceptation, mais ne sont pas une preuve de fréquentation réelle.

## 12. Tableau unique des actions

P1 : confiance, parcours cassé ou mesure à traiter avant une campagne de diffusion. P2 : qualité et contenu à traiter ensuite. P3 : évolution conditionnée par des usages. Impact fort/moyen décrit l'effet attendu, sans gain chiffré. Efforts : S, moins de 2 h ; M, 2 à 8 h ; L, 1 à 3 jours ; XL, plus de 3 jours. Ce sont des estimations de travail, sans engagement de délai ni de budget.

| ID  | Constat/problème                               | Action concrète                                                                            | Impact attendu                        | Effort                      | Confiance                                        | Dépendances                                                 | Priorité et acceptation vérifiable                                                                         |
| --- | ---------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------- | --------------------------- | ------------------------------------------------ | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| A01 | F01, démonstration ambiguë                     | Neutraliser les fiches historiques ou afficher la provenance avant les métriques           | Fort, confiance                       | M                           | Élevée                                           | Inventaire des routes historiques                           | P1 ; aucune route mock ne ressemble à un relevé réel, noindex conservé                                     |
| A02 | F02, archive 404                               | Réparer publication/route/sitemap ensemble                                                 | Fort, parcours et découverte          | M                           | Élevée                                           | Diagnostic de l'édition Skills en base                      | P1 ; toutes les URL du sitemap répondent 200 et sont indexables                                            |
| A03 | F03, cadence/méthode                           | Afficher dates distinctes et méthode correspondant à chaque édition                        | Fort, confiance                       | L                           | Élevée                                           | Vérification des profils de production                      | P1 ; un lecteur peut retrouver source, date, formule et état d'attente sans contradiction                  |
| A04 | F04, GA bloqué                                 | Adapter CSP et vérifier la collecte avec acceptation, refus et retrait                     | Fort, mesure                          | M                           | Élevée                                           | A05, propriété GA4 confirmée                                | P1 ; requêtes autorisées uniquement selon choix, DebugView vérifié et une vue par navigation               |
| A05 | F05, information incomplète                    | Faire valider les informations de traitement, les lier et définir la durée du choix        | Fort, information                     | M + validation propriétaire | Élevée sur le manque visible                     | Responsable et réglages réels                               | P1 ; informations accessibles depuis chaque page et la bannière                                            |
| A06 | F06, gates incomplets                          | Corriger format, périmètre du lint et erreurs du code actif                                | Fort, livraison                       | L                           | Élevée                                           | Stabilisation des travaux locaux                            | P1 ; pnpm check complet sans règle désactivée ni OOM                                                       |
| A07 | F02/F06, régressions invisibles aux tests purs | Ajouter des parcours navigateur et un contrôle HTTP du sitemap                             | Fort, prévention                      | L                           | Élevée                                           | A02, environnement de test sans données réelles             | P2 ; lecture, chapitre, filtres, langue, noindex et routes publiées vérifiés en CI                         |
| A08 | F07, variabilité de chargement                 | Reproduire le décalage et traiter uniquement sa cause démontrée                            | Moyen, lecture mobile                 | M à L                       | Élevée sur les mesures, moyenne sur la fréquence | Trace et reproduction                                       | P2 ; trois passages comparables documentés, CLS sous 0,1 sans masquer le contenu                           |
| A09 | F07, rendu/images                              | Traiter les ressources identifiées par PageSpeed et réserver les dimensions                | Moyen, chargement                     | M à L                       | Élevée sur les diagnostics                       | A08, budgets par type de page                               | P2 ; mesures avant/après sur quatre pages, aucune régression visuelle ou de partage                        |
| A10 | F08, coût serveur                              | Mesurer lectures et cache ; mettre en cache les éditions publiques immuables               | Moyen, latence et coût                | L                           | Moyenne sur le gain                              | Invalidation et stockage connus                             | P2 ; TTFB comparé sur trois passages et contenu publié toujours visible à temps                            |
| A11 | F09, langues lourdes/incomplètes               | Réduire les dictionnaires transmis et limiter l'effort aux traductions utiles              | Moyen, coût de lecture et maintenance | L                           | Élevée                                           | Publics/langues prioritaires                                | P2 ; page relue avant indexation, poids localisé réduit et alternates valides seulement entre pages prêtes |
| A12 | F10, mobile/a11y                               | Corriger navigation 320 px, accès recherche et lien Retrouver l'équipe                     | Moyen, accès                          | M                           | Élevée                                           | Aucune                                                      | P2 ; pas de débordement document, liens identifiables et revue clavier/zoom réalisée                       |
| A13 | F10/F11, promesse longue et décalée            | Aligner titre, résumé et ouverture des prochains épisodes                                  | Fort potentiel éditorial              | M par épisode               | Moyenne sur l'effet                              | Promesse fidèle à la vidéo ; test YouTube en cours respecté | P2 ; E1 et suivi de rétention documentés, aucune conclusion sur de petits volumes seuls                    |
| A14 | F11, identité limitée aux liens                | Ajouter rôles et faits d'expérience vérifiés, contact éditorial et règles de correction    | Moyen, crédibilité                    | M                           | Élevée                                           | Informations des animateurs                                 | P2 ; lecteur sait qui teste, qui écrit et comment signaler une erreur                                      |
| A15 | F11, contenus peu reliés                       | Relier Sillage/épisode/chapitres et nommer les ressources                                  | Fort, approfondissement               | M                           | Élevée                                           | Sources éditoriales communes                                | P2 ; aller-retour épisode/Sillage en un clic et recherche des ressources Sillage pertinente                |
| A16 | F12, suivi discret                             | Mettre en avant la chaîne et le RSS après un contenu utile                                 | Moyen, retour                         | S à M                       | Moyenne sur l'effet                              | A17 pour mesurer                                            | P2 ; destination fonctionnelle, sans faux abonnement ni interruption                                       |
| A17 | Mesure limitée aux vues                        | Définir événements et attribution minimaux, vérifier leur qualité                          | Fort, décisions                       | M à L                       | Élevée                                           | A04/A05                                                     | P2 ; événements utiles, consentement respecté, UTM testés, pas de donnée personnelle superflue             |
| A18 | Offre générale peu distincte                   | Produire un kit de reproduction et une analyse d'édition plutôt qu'un nouveau catalogue    | Fort potentiel de différence          | M à L par essai             | Hypothèse                                        | A03, protocole et capacité de l'équipe                      | P2 ; preuve originale publiée après validation et retours qualifiés recueillis                             |
| A19 | Diffusion non validée                          | Tester YouTube + LinkedIn avec matière réutilisée et destinations précises                 | Fort potentiel de découverte          | M par cycle                 | Hypothèse                                        | Contenu, A17, autorisation de publication                   | P2 ; calendrier exécuté par le propriétaire et bilan par canal                                             |
| A20 | Demande et fidélisation inconnues              | Exécuter E1 à E4 dans cet ordre, puis décider des formats                                  | Moyen, réduction du travail inutile   | L réparti                   | Hypothèse                                        | A04/A17, participants et moyens                             | P2 ; décisions poursuivre/arrêter/indéterminé consignées avec les volumes                                  |
| A21 | F13, limites sécurité                          | Revoir rate limit distribué, taille des corps et CSP des scripts inline                    | Moyen, exposition                     | L                           | Moyenne sur l'exposition réelle                  | Architecture/auth actuelles                                 | P2 ; tests des limites et permissions, politique documentée sans origine trop large                        |
| A22 | Avis esbuild modéré                            | Mettre à jour le parent compatible ou documenter le traitement de l'outil dev              | Moyen, outillage                      | M                           | Élevée sur l'avis                                | Compatibilité drizzle-kit/migrations                        | P2 ; audit relancé, aucun changement de migration appliquée                                                |
| A23 | Documentation contradictoire                   | Mettre à jour les états courants et distinguer faits historiques et statut actuel          | Moyen, coût de reprise                | M                           | Élevée                                           | Rattachement Vercel et état des sources                     | P2 ; README/questions ouvertes pointent vers des états datés vérifiables                                   |
| A24 | Newsletter/audio/badges envisagés              | Choisir une seule évolution après les premiers retours ; auditer les badges déjà commencés | Moyen, retour ou distribution         | À réestimer par choix       | Hypothèse                                        | A01/A03/A20 et capacité                                     | P3 ; besoin confirmé, version minimale et coût de maintien acceptés avant développement                    |

## 13. Feuille de route à 30, 60 et 90 jours

L'ordre est plus important que le nombre d'actions. La disponibilité de l'équipe n'a pas été confirmée pendant l'audit. Les corrections techniques et les validations du propriétaire sont des charges distinctes de la production du podcast.

| Horizon          | Travail à privilégier                                                                   | Résultat vérifiable                                                                                                 |
| ---------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Jours 1 à 7      | A01 à A05 ; diagnostic et correction de A06                                             | Démonstration signalée ou retirée, archive accessible, dates/méthodes cohérentes, collecte et information vérifiées |
| Jusqu'à 30 jours | A08/A09/A12, puis A13/A15/A17 ; E1 et premier essai de diffusion ; démarrer A07         | Lecture mobile stabilisée, promesse compréhensible, passage épisode/projet direct, premiers événements exploitables |
| Jusqu'à 60 jours | A10/A14/A18/A19 ; répéter un contenu pratique ; E2/E3 ; finir A07/A21/A22               | Deux cycles comparables de production/diffusion, retours documentés, coûts et qualité surveillés                    |
| Jusqu'à 90 jours | E4, A20/A23 ; décision A24 ; langue supplémentaire seulement si elle répond à un besoin | Formats conservés ou arrêtés avec raisons ; une seule évolution choisie, ou aucune si les preuves manquent          |

Un tableau de bord doit commencer par une période de référence après réparation d'Analytics. Aucun objectif de visiteurs ou de classement SEO n'est fixé sans cette base. Pour l'instant, les critères de qualité et les retours qualifiés guident davantage que le volume brut.

## 14. Vérifications exécutées et questions restantes

| Contrôle                                         | Résultat réellement obtenu                                                                                           |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| pnpm check, premier passage                      | Échec : formatage de 149 fichiers ; lint, types et tests non atteints par cette chaîne                               |
| pnpm test, relevé de 18:37                       | 61 fichiers, 341 tests réussis, environ 5,2 secondes ; avant l'apparition des nouveaux fichiers de badges            |
| pnpm build, premier passage                      | Réussi, types vérifiés et 213 pages générées ; avertissement middleware déprécié au profit de proxy                  |
| pnpm typecheck                                   | Génération des routes et TypeScript réussis au passage exécuté                                                       |
| pnpm lint global                                 | Échec par épuisement de mémoire, heap proche de 4 Go                                                                 |
| Lint ciblé src/test/scripts                      | Quatre erreurs dans les fichiers de badges apparus localement ; diagnostic ciblé, pas validation du gate global      |
| pnpm audit --audit-level=high                    | Une vulnérabilité modérée, aucune haute ou critique signalée ; exit 0 au seuil high                                  |
| pnpm audit --json                                | Confirme esbuild 0.18.20 via l'outillage dev, GHSA-67mh-4wv8-2f99 ; exit 1 car un avis est présent                   |
| HTTP, sitemap et ressources                      | 77 URL du sitemap examinées ; une archive Skills en 404 ; contenus privés refusés comme attendu sur la sonde contenu |
| PageSpeed et parcours                            | Quatre pages mobiles, accueil ordinateur ; parcours U01 à U24 documentés                                             |
| Secret scan, E2E CI et logs privés de production | Non exécutés ou non accessibles pendant cet audit ; leur présence dans le workflow ne vaut pas passage réussi        |

Le dernier `pnpm check`, exécuté après création des documents, s'arrête encore au formatage, sur 147 fichiers. Les travaux locaux ont évolué depuis le premier passage à 149 fichiers. Les cinq fichiers de cet audit ont été formatés séparément ; aucune correction des autres fichiers n'a été faite par cet audit.

À décider ou obtenir :

- Public et objectif prioritaires : fidélisation du podcast, référence sur les outils ou découverte des projets. La priorité développeurs/créateurs est proposée, pas validée.
- Temps disponible hors enregistrement et capacité de maintenance ; aucun budget de service n'a été engagé.
- Compte Vercel qui sert réellement le domaine, accès Search Console et propriété GA4 correspondante.
- Profil de calcul et cadence réellement actifs pour chaque édition ; politique publique de correction et droit de réponse.
- Responsable et informations de traitement à publier, durée du choix de mesure et réglages de conservation.
- Statut attendu des anciennes fiches et des nouvelles fonctions de badges, sans confondre travaux locaux et mise en ligne.

Les critères vérifiés sont la réalité des parcours décrits, les défauts HTTP identifiés, la présence des protections étudiées, les résultats de commandes et les mesures de laboratoire. Restent à valider l'usage par le public, les coûts, la collecte réelle de statistiques, les performances terrain, l'accessibilité complète et les hypothèses de croissance.

## Les cinq premières actions à lancer

1. A01 et A02 : traiter les anciennes fiches ambiguës et l'archive Skills. Vérifier ensuite les routes publiques et l'intégralité du sitemap.
2. A03 : relier chaque édition à sa vraie méthode et à ses dates. Faire vérifier qu'un lecteur comprend la différence entre relevé, rang et test éditorial.
3. A05 puis A04 : compléter les informations et réparer Analytics. Contrôler acceptation, refus, retrait et réception des événements avant de lire les statistiques.
4. A06 puis A08/A12 : obtenir des gates exploitables et diagnostiquer la variabilité du chargement de l'épisode et corriger la navigation à 320 px. Refaire des passages comparables et une revue clavier.
5. A13/A15 puis E1/E2 : clarifier la promesse, relier épisode et Sillage, tester les extraits déjà prêts après validation. Mesurer compréhension, visites utiles, lecture et retour, puis décider du prochain effort éditorial.
