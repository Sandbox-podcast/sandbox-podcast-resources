# Validation de la factory SANDBOX

Relevé du 28 octobre 2026. La recette porte sur les traitements locaux et la diffusion simulée. `mode=simulation`, `live_enabled=false` et les appels externes payants restent désactivés. Aucun compte social réel n'a été validé par cette recette. LinkedIn reste exclusivement manuel.

## Chaîne intégrée exécutée

La recette sous `.local/factory-recette-20261028` a ingéré une source synthétique de 312 secondes deux fois : le premier passage est `ingested`, le second `duplicate_ignored`. Elle a produit un vertical de 12 secondes et un horizontal de 300 secondes, avec master propre, sous-titres, coupes et empreintes. La revue de fixture est signalée `synthetic_fixture` ; elle ne valide aucun propos réel.

Le calendrier simulé couvre le 28 octobre à 07 h jusqu'au 31 octobre à 06 h Europe/Paris, avec dernière heure d'envoi à 05 h 30 et prochain tournage fictif à 07 h. Six sorties ont reçu un créneau : cinq ont terminé en `simulated`, avec identifiant `sim:`, et le pack LinkedIn a expiré lors de la fermeture sans être envoyé. Le bilan conserve cinq observations de test explicitement synthétiques, sans les interpréter comme des performances Sandbox.

Preuves locales : [validation.json](../../.local/factory-recette-20261028/validation.json), base `factory.sqlite3`, sorties dans `episodes/synthetic-demo/`, et [bilan du scénario](../../.local/factory-recette-20261028/reports/synthetic-demo-20261101T060000Z.md). La date du bilan est celle de l'horloge contrôlée du scénario, pas une exécution future réelle.

## Exécution Windows indépendante de Codex

La tâche principale `SANDBOX-Factory-Simulation` est installée avec l'interpréteur `.local/factory-venv/Scripts/pythonw.exe`, un déclenchement chaque minute et un déclenchement à l'ouverture de session. Le relevé Windows à 09 h 55 min 51 s Europe/Paris retourne `LastTaskResult=0`. La base opérationnelle conserve un heartbeat à `2026-10-28T08:55:51.228698+00:00`, avec `clock=wall_clock`, et l'entrée `runtime_service` nomme `factory_worker.py` et le même Python. La tâche est revenue à l'état `Ready` entre passages.

Une seconde tâche, `SANDBOX-Factory-Recette-20261028`, a exécuté le worker sur une base séparée et ingéré un manifeste dans l'inbox. Son reçu Windows porte un dernier passage à 09 h 53 min 48 s Europe/Paris, résultat 0. L'état contient un épisode, deux rendus de 12 et 300 secondes et cinq jobs `completed`. Les médias restent `needs_review`, sans validation éditoriale automatique. Cette tâche temporaire a été retirée après contrôle ; la tâche principale reste installée.

Preuves : [reçu de tâche](../../.local/factory-task-recette/task-receipt.json), [état de la recette Windows](../../.local/factory-task-recette/status.json), état et journal sous `.local/factory/`. Windows a exécuté le worker avec son propre interpréteur et son état, sans appel à une conversation Codex. Le principal Windows est `Interactive` : la machine doit rester active et la session Windows ouverte. L'exécution après déconnexion de session ou extinction n'est pas validée.

## Interface, procédures et contrôles

La vue opérationnelle lit la base et expose filtres, états, aperçus, erreurs, pause et reprise. Les captures de contrôle sont conservées dans [.local/factory-ui-desktop.jpg](../../.local/factory-ui-desktop.jpg) et [.local/factory-ui-mobile.jpg](../../.local/factory-ui-mobile.jpg), cette dernière à 375 pixels de largeur. Les vérifications HTTP portent sur le service local, ses données et ses actions ; elles ne prouvent pas une intégration sociale distante.

Les sept skills passent `quick_validate.py`. Les douze fichiers rédigés de documentation et instructions passent le contrôle de ponctuation ; les liens locaux ont été vérifiés sans référence cassée. Un rafraîchissement du catalogue de l'hôte a exposé les sept noms `sandbox-*` et leurs chemins dans `.agents/skills`. Le fichier `AGENTS.md` du package a été lu par les agents concernés.

La sauvegarde CLI portable v2 de la recette a été restaurée dans `.local/factory-restored-20261028`. Le manifeste indique `portable=true` et 48 fichiers média ; le reçu de restauration indique `restored_paused`. Les dix tests du module de sauvegarde ont réussi, dont un scénario qui supprime le stockage d'origine puis réutilise le cache rendu restauré sans nouvel encodage. Preuves : [manifeste de sauvegarde](../../.local/factory-backups/recette-20261028.manifest.json) et [reçu de restauration](../../.local/factory-restored-20261028/restore-receipt.json).

La passe complète finale a exécuté 162 tests en 118,235 secondes : 159 réussis et trois ignorés. Ces trois cas exigent `YOUTUBE_TEST_DATABASE_URL` vers un Postgres local, absent de cet environnement. Le client Docker est installé, mais le moteur Docker Desktop Linux n'est pas accessible ; aucun service Postgres de recette n'a été lancé. Les trois cas ignorés ne sont donc pas déclarés réussis.

La passe a activé `FACTORY_MEDIA_INTEGRATION=1`. NumPy 2.5.4 est installé ; les deux contrôles de comparaison entre fichiers source et rendu ont été exécutés et réussis. Les recettes utilisent des médias synthétiques, pas un épisode complet de Sandbox. Le journal est conservé dans [.local/factory-final-tests.txt](../../.local/factory-final-tests.txt).

Les dix tests Node du précontrôle de workflow ont aussi réussi. La compilation Python et `git diff --check` n'ont signalé aucune erreur. Les tests couvrent notamment déduplication d'ingestion, copie incomplète, cache et révisions, réservations concurrentes, reprise, envois incertains, disponibilité et fenêtre Europe/Paris, changement d'heure, fermeture indépendante, simulation sans transport social, LinkedIn manuel, métriques manquantes et décisions réversibles. Ces vérifications n'établissent ni les droits d'un compte ni le résultat d'une API réelle.

La décision de recette `e0aefe93b130d96842f06686` a été appliquée puis révoquée dans la base de fixture. Les événements `decision_applied` et `decision_reverted` en conservent la trace ; la configuration opérationnelle est restée intacte.

## Ce que la recette ne certifie pas

Aucun master complet n'étant disponible dans ce clone, l'analyse d'une conversation de 60 à 120 minutes reste à vérifier. Les contrôles de décodage, niveaux, silences et images de la mire ne prouvent ni une écoute humaine, ni la synchronisation labiale, ni la fidélité d'un montage réel. Aucune écoute humaine de propos réels n'est déclarée.

Les connecteurs simulés ne prouvent ni OAuth, ni scope, ni éligibilité, ni capacité d'upload d'un compte. Les contrôles de présence ont confirmé l'absence de `OPENAI_API_KEY`, `YOUTUBE_OAUTH_TOKEN_JSON` et `YOUTUBE_JOURNAL_DATABASE_URL`, ainsi que des fichiers OAuth usuels examinés. Aucune valeur secrète n'a été affichée et aucune connexion n'a été renouvelée. La [matrice des plateformes](capacites.md) distingue documentation officielle, code existant et accès non vérifiés. La source TikTok Direct Post exclut l'utilitaire interne ; Accounts API ou un prestataire compatible restent à examiner. La disponibilité future d'un contenu distant avant l'échéance ne peut pas être garantie par une simulation.

Le manifeste A/B/C du dépôt conserve cinq tests observés en cours dans Studio le 26 octobre. Leur état au 28 octobre n'a pas été recontrôlé. Ils restent conservés sans arrêt ni modification ; l'absence de connexion locale n'autorise pas à les considérer terminés.

La tâche locale persiste après la fermeture de Codex, sous les conditions Windows précisées. Les appels de modèles en arrière-plan ne sont pas configurés ; la sélection utilise des preuves éditoriales explicites. Les contenus, observations et décisions synthétiques restent séparés des performances et de la configuration opérationnelles.
