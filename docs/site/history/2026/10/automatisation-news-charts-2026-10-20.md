# Comment News et les classements se mettent à jour

Relevé du 20 octobre 2026. Les horaires ci-dessous sont en UTC ; Paris a deux heures d'avance à cette date. Les workflows s'exécutent sur GitHub Actions depuis `main`. Ils appellent le site Vercel, qui lit et écrit dans Postgres/Neon. Ouvrir une page du site ne lance pas une collecte.

Mise à jour locale du 26 octobre : News et le contrôle Charts partagent un seul workflow quotidien à 03:37 UTC et le contrôleur externe à 05:37 UTC. Voir [ADR-0041](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0041-controles-quotidiens-news-et-classements.md). Les constats et horaires du 20 octobre conservés ci-dessous précèdent ce changement ; sa livraison distante reste à effectuer.

## Horaires prévus

| Traitement                               | Planification                                               | Action                                                                                                                         |
| ---------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| News                                     | Chaque heure, minute 37                                     | Collecter les sources, réserver des candidats, résumer et traduire un lot, publier les fiches acceptées, vérifier la fraîcheur |
| Découverte GitHub                        | 01:17 UTC                                                   | Consulter Trending puis rechercher des candidats                                                                               |
| Classements                              | 03:17 et 15:17 UTC                                          | Collecter GitHub, Skills et Models, calculer puis publier les éditions admissibles                                             |
| Contrôle des classements                 | Chaque heure, minute 23                                     | Lire les quatre éditions publiques et signaler les éditions absentes ou anciennes                                              |
| Reprise des classements, correctif local | Après un contrôle horaire qui trouve un créneau dû manquant | Relire les publications sous le verrou partagé, puis reprendre uniquement les chaînes manquantes                               |

Les identifiants d'édition 00:00 et 12:00 UTC désignent les créneaux de données. Ils ne donnent pas l'heure de publication. Les deux collectes prévues correspondent à 05:17 et 17:17 à Paris le 20 octobre ; ces heures locales changent au passage à l'heure d'hiver.

Les poussées GitHub constituent un signal distinct. Elles demandent `SANDBOX_CHARTS_BURSTS_ENABLED=true` dans GitHub Actions et leur activation côté application. La variable GitHub est absente du relevé du 20 octobre : aucune collecte horaire de poussées n'est donc déclenchée par ce workflow.

## News

Le workflow `news-refresh.yml` collecte les sources et conserve les candidats dans la file Postgres. Les résumés utilisent un modèle Qwen sur le CPU du runner GitHub ; Argos traduit les fiches en anglais, espagnol et allemand. Les modèles restent dans le cache Actions après leur téléchargement initial. Le worker réserve un lot, applique les contrôles puis appelle les routes protégées du site. Une fiche rejetée n'apparaît pas dans le fil et un nouveau passage ne republie pas la même URL.

Les lots bornés ne vident pas nécessairement la file à chaque passage. Une collecte récente ne prouve donc pas que tous les candidats récents ont déjà leur résumé. La dernière collecte et la dernière publication ont des dates distinctes. La date d'un article reste celle de sa source.

La variable GitHub `SANDBOX_NEWS_PUBLIC=true` autorise le job sur `main`. Le secret `SANDBOX_CHARTS_CRON_SECRET` authentifie les écritures et doit correspondre au `CRON_SECRET` de Vercel. Les dates, erreurs de source et statuts de la file permettent de distinguer un ordonnanceur absent, une source inaccessible et un article écarté.

## Classements

Le workflow `charts-refresh.yml` appelle trois chaînes indépendantes : GitHub, Skills et Models. Un collecteur peut réussir alors qu'un autre échoue. Les gels contrôlent ensuite les mesures disponibles ; le pilote relit les éditions réellement servies par `/api/charts/<classement>/current`. Une réponse réussie du cron ne suffit pas à déclarer une publication réussie.

Rising utilise les mesures GitHub mais exige son propre historique et ses critères d'admissibilité. Son absence reste visible même si GitHub, Skills et Models ont publié. Les seuils n'ont pas été abaissés et aucune donnée de démonstration ne remplace des mesures absentes.

Le contrôle horaire signale une édition de plus de dix-huit heures. Le correctif local de reprise n'attend pas ce seuil : après 03:17 ou 15:17 UTC, une édition manquante du créneau dû suffit. Une édition déjà publiée ne déclenche aucune nouvelle collecte. Le seul manque de Rising ne déclenche pas une reprise.

Le job de reprise partage le verrou du rafraîchissement et relit les publications après l'attente. Ses trente minutes sont distinctes des dix minutes du contrôle public. Si les API publiques sont indisponibles ou si le secret requis manque, le script échoue sans appeler les collecteurs. Voir [ADR-0038](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0038-reprise-horaire-des-classements.md).

La reprise vérifie aussi le créneau avant chaque nouvel appel. Si un traitement dépasse 00:00 ou 12:00 UTC, elle arrête ses nouveaux appels de collecte et de gel, puis contrôle les publications. Elle ne démarre pas le travail du créneau suivant avant son horaire prévu.

## Ce que les journaux montrent

Le relevé des quinze derniers runs des classements contient un contrôle à 06:06:39 UTC le 20 octobre, mais aucun lancement du job de collecte de 03:17 UTC ce jour-là. Le [contrôle à 06:07 UTC](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39378523156) trouve GitHub, Skills et Models au créneau `2026-10-19T12:00Z`, devenu ancien, et Rising sans édition valide. Son échec correspond aux données publiques ; ce run ne collectait rien.

La [découverte du 20 octobre](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39377815371), planifiée à 01:17 UTC, démarre à 05:59:12 UTC. Les logs montrent trois réponses 503 de Trending, puis deux de la découverte. Le troisième appel de découverte s'interrompt à la limite de dix minutes. Le correctif local conserve les deux sources indépendantes, retire ces répétitions curl et donne quinze minutes à leurs deux appels bornés à six minutes.

Les [runs News du 19 octobre à 23:01 UTC](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39338877846) et du [20 octobre à 02:00 UTC](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39356595304) réussissent. Ils sont séparés d'environ trois heures malgré un cron horaire. Ce relevé confirme des déclenchements irréguliers, sans établir la cause de tous les créneaux absents. Le [rapport backend et qualité](audit-automatisation-2026-10-20.md) détaille les générations, les rejets et la santé du fil.

## Activation et limites

Les changements de reprise restent locaux jusqu'à leur livraison autorisée. Ce travail ne relance aucun workflow distant et ne modifie ni variable, secret, plan, compte ou base de production.

Après livraison, vérifier un événement `schedule` réel, la sortie `recovery-needed`, la présence des nouvelles éditions publiques et la durée des jobs. Un lancement manuel valide un traitement, sans prouver le fonctionnement du planning. Le contrôle horaire peut rattraper une collecte omise seulement si GitHub le lance lui-même. Il ne fournit pas de garantie de délai lorsque les événements Actions sont absents.
