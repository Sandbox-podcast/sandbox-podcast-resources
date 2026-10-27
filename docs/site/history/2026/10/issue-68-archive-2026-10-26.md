# Archive de l’issue GitHub 68

Copie du titre et du corps avant suppression demandée par Lou le 26 octobre 2026. Cette liste date du 21 octobre ; elle ne décrit pas l’état actuel. Voir [le bilan du 26 octobre](issue-68-bilan-2026-10-26.md).

- Ancienne URL : https://github.com/Sandbox-podcast/sandbox-podcast-site/issues/68
- Dernière modification GitHub : 2026-10-21T18:57:01Z

## Reste à faire

Suivi unique des validations qui restent pour le site média. État recoupé le 21 octobre 2026 à 20 h 56 (Paris), avec GitHub Actions, les réponses publiques et la documentation du dépôt.

Les correctifs des issues #81, #82 et #83 sont livrés et ces issues sont closes. #87 et #88 sont également closes. Les routes News en français, anglais, espagnol et allemand répondent HTTP 200. Ces éléments ne restent pas dans la liste.

## Classements et Awards

- [ ] Résoudre les collectes partielles GitHub et Skills, dont les dépôts introuvables et les résultats OpenSSF, puis confirmer deux cycles complets successifs déclenchés par le planning et vérifier les éditions réellement servies. Le lancement manuel [#39606417107](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39606417107) a publié les éditions GitHub, Skills et Models du 21 octobre, 20 positions chacune. Le rafraîchissement planifié [#39570912481](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39570912481) a échoué dans le job refresh. Le contrôle planifié [#39624763575](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39624763575) a vérifié la fraîcheur, mais a ignoré les jobs refresh, discovery et recovery. Les éditions publiques GitHub, Skills et Models sont à jour ; Rising n’a toujours pas d’édition.
- [ ] Examiner les 36 références Models contradictoires, leurs variantes et historiques, puis préparer une correspondance canonique explicite et tester la réparation sur une copie de la base. Constituer les baselines réelles, calibrer et relire les profils avant de renseigner CHARTS_REVIEWED_PROFILE_VERSIONS. Aucune fusion automatique ni mesure inventée.
- [ ] Laisser l’historique Rising atteindre ses critères actuels : 20 projets éligibles sur deux périodes mesurées de sept jours. Publier une édition uniquement quand les données le permettent, sans réduire le seuil ni créer d’historique artificiel.
- [ ] Vérifier que Preview utilise sa propre branche Neon, distincte de Production.
- [ ] Vérifier les premières attributions réelles des Awards, leurs preuves et leur rendu GitHub Camo sur une période éligible.

## News et import YouTube

- [ ] Corriger les traductions News qui restent en attente et confirmer un cycle planifié complet. Le run planifié du 21 octobre à 17:35 UTC [#39645127941](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39645127941) s’est terminé avec quatre articles sans traduction ; le run suivant terminé [#39651794601](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39651794601) en signalait encore cinq. Le run lancé à 18:45 UTC [#39655557327](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39655557327) était toujours en cours lors de ce relevé.
- [ ] Vérifier depuis Vercel l’import d’un épisode YouTube sans clé API, sur un brouillon de test qui ne sera pas publié.

## YouTube et diffusion sociale

- [ ] Avant toute écriture automatique de l’agent de croissance, connecter OAuth YouTube, créer le rôle Postgres limité, initialiser le journal durable et réconcilier l’historique SQLite.
- [ ] Relire la file actuelle des plateformes et terminer les remplacements natifs des Shorts encore signalés en attente. Vérifier chaque résultat sur sa plateforme. Les comptes de l’instantané du 18 octobre ne décrivent plus l’état courant. Confirmer aussi le nouvel horaire dans la plateforme avant de réactiver une routine suspendue.
- [ ] Relever les résultats YouTube d’E2 à 48 heures, sept jours et trois semaines, avec le test natif. Le résultat reste indéterminé tant qu’un sujet n’atteint pas cinq vues longues attribuables.

## Mesure et référencement

- [ ] Retrouver l’accès à la propriété GA4 Sandbox et vérifier après le dernier déploiement la réception de discovery_open, youtube_open et experience_interaction. Une recette antérieure est documentée le 17 octobre ; la propriété n’apparaissait pas dans le compte Analytics consulté le 21 octobre.
- [ ] Obtenir un échantillon mobile hors recette suffisant dans Vercel Speed Insights et rapprocher les clics YouTube des vues attribuées dans Studio.
- [ ] Terminer la validation DNS Search Console avec une session IONOS valide, puis vérifier la réception du sitemap, l’indexation et les requêtes. La validation DNS n’est pas encore confirmée.
