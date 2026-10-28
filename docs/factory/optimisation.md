# Optimiser la factory et préparer les prochains épisodes

La factory doit réduire le travail répété et aider l'équipe à choisir les sujets, les coupes et les promesses qui servent son public. La vitesse de production ne prouve pas la croissance de la chaîne. Les décisions éditoriales demandent des observations réelles, leur contexte et une revue des passages concernés.

Le suivi initial de cette évolution est dans l'[issue #5](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/5), regroupée à la demande de Lou dans l'[issue #2](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/2) et la [PR #4](https://github.com/Sandbox-podcast/sandbox-podcast-resources/pull/4). Le [prompt maître](sources/prompt-maitre-2026-10-28.txt) conserve la priorité : aucun quota d'extraits, clôture avant le prochain tournage, simulation sociale et LinkedIn manuel.

## Réutilisation des calculs

L'analyse conserve séparément le sondage du master et son décodage technique. Un changement de preuves éditoriales peut les réutiliser quand le SHA-256 de la source reste identique. Le rendu possède aussi un reçu de contrôle technique : une interruption pendant la création des aperçus ne force plus un nouveau décodage complet.

Chaque nouveau cache technique conserve la version, l'empreinte de son entrée et celle du contenu du reçu. Les écritures sont atomiques. La reprise vérifie encore les empreintes des fichiers ; la taille et la date seules ne valident jamais un rendu. Les contrôles techniques ne valent pas une revue du sens, du son ou du cadrage.

Le watcher compare le manifeste et les métadonnées de ses dépendances. Il évite leur réingestion tant qu'elles restent inchangées. Une modification des preuves, l'apparition d'un fichier manquant ou un changement de source relance l'examen. Une vérification intégrale périodique du SHA source reste imposée par `runtime.watch_verify_seconds`, soit 3 600 secondes par défaut. Ce cache de surveillance n'autorise aucune diffusion et ne remplace pas les contrôles avant rendu ou envoi simulé.

Le worker continu enchaîne les travaux disponibles. À vide, son attente augmente de 15 à 30 puis 60 secondes avec les valeurs par défaut, sans dépasser un travail connu à venir ou une borne de clôture. `runtime.idle_max_seconds` règle ce plafond. La détection d'un nouveau fichier peut donc attendre au plus ce délai, hors traitement en cours. La tâche Windows existante conserve son déclenchement à la minute et sa sortie dès que la file est vide.

## Mesurer ce qui coûte

Chaque appel `process` ou `render`, direct ou depuis le worker, inscrit un relevé `resource_run` dans SQLite : début, fin, durée, CPU Python, statut et réutilisation des caches disponibles. Une interruption brutale peut laisser le relevé `running` ; il reste compté comme inachevé. Les anciennes exécutions n'ont pas de mesure rétroactive.

`status`, `diagnostics`, `brief` et le bilan exposent ces relevés agrégés par étape. Le temps écoulé inclut les attentes. Le CPU Python exclut FFmpeg et les autres sous-processus. L'énergie et le coût financier restent inconnus sans relevé distinct ; aucune conversion automatique en euros ou CO₂ n'est faite. Les coûts constatés et estimés conservent leur registre existant. Les services externes payants restent désactivés.

Avant d'accélérer encore un traitement, comparer ses reprises et ses premières exécutions séparément. Mesurer sur les mêmes fichiers, avec la même version des outils et plusieurs passages. Garder les empreintes, le nombre d'appels et les limites de la mesure. Un cache ne doit pas gagner du temps en supprimant un contrôle de fidélité.

## Le brief du prochain cycle

Depuis la racine du dépôt, dans PowerShell :

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
python -m youtube_growth.factory brief
python -m youtube_growth.factory brief --episode-id episode-003
python -m youtube_growth.factory report --episode-id episode-003
```

`brief` lit l'état sans lancer de média, de modèle ou de collecte réseau. Il rassemble le positionnement configuré, les références datées, les blocages, les candidats à relire, les mesures natives disponibles, les expériences et les décisions arrivées à échéance. `report` ajoute ce brief à ses exports locaux JSON et Markdown.

Le brief par épisode filtre ses faits et expériences. Les décisions concernent la configuration globale ; leurs preuves sont vérifiées dans toute la base sans être ajoutées aux faits de l'épisode. Chaque fait conserve son identifiant d'observation, sa période, son unité, son périmètre, sa source et sa version de définition.

Le calcul sépare les variantes d'expérience. Il refuse d'annoncer un gagnant à partir d'une autre publication, de données futures, de mesures incompatibles ou de fenêtres différentes. Une comparaison sans résultat natif ou contrôlé peut rester non concluante. Une proposition issue de fixtures ne peut pas modifier une configuration, quel que soit son chemin. Les décisions ne peuvent pas déplacer le stockage ou l'inbox.

Le [registre des connaissances](youtube-knowledge.json) contient les sources officielles utilisées. Chaque entrée distingue le fait documenté, son application proposée à SANDBOX et la capacité restant à vérifier sur le compte. Le brief signale une échéance dépassée ou une référence postérieure à son horloge. Les délais de revue de 30 ou 90 jours sont des règles internes, pas des recommandations YouTube. Aucun navigateur ni modèle ne tourne en arrière-plan pour les actualiser.

## Donner une direction éditoriale aux mesures

La promesse existante de SANDBOX porte sur les effets concrets de l'IA dans le développement logiciel, le produit et les entreprises. Pour chaque passage retenu, préciser la question traitée, le public principal et ce que le spectateur pourra mieux comprendre ou tester. Garder les réserves, les vrais désaccords et les démonstrations lisibles. Une annonce récente demande une source datée ; un retour d'expérience demande de distinguer ce qui a été observé de ce qui est généralisable.

L'équipe peut préparer une suite autour d'un problème récurrent, puis confronter cette hypothèse aux retours et aux mesures de la chaîne. Un sujet qui attire des vues ponctuelles et un sujet qui donne envie de revenir peuvent servir des usages différents. YouTube propose des segments d'audience pour examiner ces comportements ; sa catégorie de spectateurs réguliers exige plus de six mois de présence mensuelle. Elle convient donc mal comme critère unique au démarrage. [Source officielle](https://support.google.com/youtube/answer/10246996).

| Question à examiner | Preuve à importer ou consulter | Décision possible après revue |
| --- | --- | --- |
| La promesse attire-t-elle les personnes auxquelles le passage est destiné ? | Impressions et CTR avec surface, période, âge de publication et contexte ; commentaires disponibles. | Retravailler le titre et l'image si leur promesse est mal comprise. Aucun seuil CTR universel. |
| Le début tient-il cette promesse ? | Rétention, premières trente secondes et visionnage du passage. | Raccourcir une entrée, avancer la démonstration ou rendre le contexte plus clair, si la revue le justifie. |
| Le passage donne-t-il envie de poursuivre ? | Vidéo associée vérifiée, sources de trafic et visionnage long lorsque accessibles. | Choisir une suite précise ; garder l'attribution inconnue si les données ne relient pas les contenus. |
| Les personnes reviennent-elles ? | Audience active, retours et segments Studio sur des périodes comparables. | Tester une série ou prolonger un problème déjà traité, puis réévaluer. |
| Les trois points de vue apportent-ils quelque chose ? | Commentaires pertinents et examen éditorial des échanges. | Préserver les objections utiles et préparer les démonstrations qui manquent. Les commentaires ne représentent pas toute l'audience. |

Une baisse ou un pic de rétention demande une lecture avec le contenu. Un pic peut aussi signaler une explication difficile à suivre. [Rapport de rétention](https://support.google.com/youtube/answer/9314415?hl=fr). Pour les variantes de packaging, conserver le résultat du test natif, sa population et sa période : YouTube l'évalue sur le temps regardé, avec possibilité de résultat non concluant. [Tests de titres et miniatures](https://support.google.com/youtube/answer/16391400).

Les Shorts et les vidéos longues gardent des mesures distinctes. Les définitions des vues Shorts ont changé en 2025 ; `views` et `engagedViews` ne s'interchangent pas. [Historique des API](https://developers.google.com/youtube/analytics/revision_history). La vidéo associée se vérifie dans Studio, selon l'éligibilité du compte, lors d'une diffusion autorisée. [Vidéo associée](https://support.google.com/youtube/answer/14075157?hl=fr).

Pour chaque changement proposé, conserver l'observation qui le motive, les valeurs avant/après, une date de réévaluation et ce qui ferait revenir à l'état précédent. Le brief prépare cette revue ; il n'applique pas automatiquement une stratégie.

## Mesures du 28 octobre 2026

Comparaison avec la révision `242212a177410e4ea91d250fa35129569be4ced5`, sur ce poste. Les données sont synthétiques.

| Calcul | Scénario | Médiane avant | Médiane après |
| --- | --- | ---: | ---: |
| Reprise d'analyse | 7 passages, cache rempli, fixture de 312 s / 4 102 549 octets | 0,872 s | 0,011 s |
| Reprise de rendu | 7 passages, même fixture, cache rempli | 0,832 s | 0,023 s |
| Recouvrement des observations | 3 passages, 1 500 intervalles disjoints | 0,960 s | 0,014 s |

Dans les deux scénarios média, les sept reprises passent de sept appels FFprobe à aucun. Ces chiffres ne mesurent pas l'encodage initial, la consommation électrique ou l'audience. Les reçus et scripts de reproduction restent localement dans `.local/factory-optimization/` ; les tests de non-régression sont versionnés.

Le brief exécuté sur l'épisode 003 trouve 19 candidats à relire, aucun candidat retenu et aucune observation de performance importée. La date du prochain tournage et la preuve de disponibilité effective restent absentes. Le statut de disponibilité décrit la base ; il ne conclut pas que la vidéo est inaccessible sur YouTube. Ces éléments limitent les décisions de diffusion et de croissance, pas la préparation locale.

## Vérification de cette livraison

La suite Python du package a exécuté 243 tests avec `FACTORY_MEDIA_INTEGRATION=1` : 240 réussis et 3 tests PostgreSQL ignorés, faute de base de test configurée. Les tests supplémentaires couvrent les caches, les mutations de fichiers, la reprise après interruption, les attentes du worker, les mesures de ressources et les décisions d'apprentissage. La recette FFmpeg vérifie des fichiers synthétiques ; elle ne certifie pas la qualité éditoriale d'un épisode réel.

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
$env:FACTORY_MEDIA_INTEGRATION = '1'
python -m unittest discover -s tools/youtube-growth/tests -v
python -m compileall -q tools/youtube-growth/src tools/youtube-growth/tests
node --test tools/youtube-growth/tests/workflow-preflight.test.mjs
python tools/repository/check_repository.py
git diff --check
```

La compilation Python, les trois tests de workflow, le contrôle de dépôt et le contrôle des espaces du diff réussissent. Une revue croisée a vérifié les caches, les délais et les périmètres des preuves ; les défauts trouvés ont été corrigés et retestés. Le lot est intégré à la PR #4 après autorisation de Lou. L'issue centrale #2 reste ouverte jusqu'à la fusion.
