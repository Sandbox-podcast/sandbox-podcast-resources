# Pilotage pour novices et textes de l'interface

Demandes initialement suivies dans les issues [#6](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/6) et [#7](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/7), regroupées à la demande de Lou dans l'[issue #2](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/2) et la [PR #4](https://github.com/Sandbox-podcast/sandbox-podcast-resources/pull/4). L'issue centrale reste ouverte jusqu'à la fusion.

## Problème

Sur l'épisode 3, la page Publications était vide alors que dix-neuf passages avaient été proposés. Elle invitait à changer les filtres sans expliquer que le montage et la préparation des publications n'avaient pas commencé. Les fiches de passage cachaient leurs raisons et leurs horaires dans du JSON. Les contrôles de file et les chemins occupaient le même niveau que le travail éditorial.

## Changements

Le parcours affiche quatre étapes et la prochaine action à effectuer. Ses indicateurs signalent les éléments disponibles, sans certifier une validation complète de l'analyse. Les passages montrent directement titre, horaires, durée, public et justification. Le lien de lecture ne valide rien ; il ouvre la source YouTube au bon moment. Les restrictions et les données techniques restent consultables dans des détails repliés.

La page Publications distingue l'absence de préparation d'une recherche sans résultat. Elle renvoie vers les passages lorsqu'ils existent. Le réseau ne filtre que les publications ; un filtre laissé dans l'URL ne masque plus des vidéos sur une autre page. Les commandes de suspension et l'emplacement des fichiers sont repliés. Les textes expliquent que les demandes de sélection et de montage se font dans le chat avec Codex.

La relecture No AI Slop remplace notamment "Rendus & sélection" par "Passages et vidéos", "File de traitement" par "Travaux automatiques" et "Revue attendue" par "À regarder et écouter". Le JSON reste réservé aux détails techniques. Les textes des épisodes et les décisions enregistrées ne sont pas réécrits par cette présentation.

## Vérification

Le test navigateur `tools/youtube-growth/scripts/test_factory_novice_dashboard.cjs` utilise l'épisode 3 sur le serveur local. Il vérifie l'accès aux passages depuis la page vide, les horaires et liens source, les détails repliés et conservés après mise à jour, les six vues à 375, 768 et 1440 pixels, ainsi que des états sans épisode et avec passages retenus. Les états supplémentaires sont injectés dans le navigateur, sans modification de SQLite. Les captures restent sous `.local/factory-novice-*.png`.

UI/UX Pro Max a fourni les recommandations sur les états vides avec prochaine action, l'indication de la vue active et les liens conservés dans l'URL. Le contrôle visuel concerne Chrome sur le serveur local ; aucune conformité complète avec lecteur d'écran n'est revendiquée.

Vérifications exécutées : 243 tests Python, dont 240 réussis et 3 tests PostgreSQL ignorés faute de base dédiée, avec `FACTORY_MEDIA_INTEGRATION=1` ; parcours navigateur novice réussi sur l'épisode réel ; parcours de démonstration réussi avec conservation de la lecture vidéo, détails, miniatures, filtres et export ; syntaxe JavaScript, `git diff --check` et contrôle des fichiers partagés réussis. Journal Python local : `.local/factory-novice-tests.txt`. Aucun commit, push ou PR créé.
