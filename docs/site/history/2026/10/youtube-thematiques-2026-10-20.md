# Vidéos thématiques : recette sur les deux épisodes

Les cinq MP4 sont générés localement depuis les deux émissions présentes sur YouTube. Aucune vidéo n'est téléversée, publiée ou programmée. Les fichiers et rapports sont sous `.local/youtube-thematic/`. Le [mode d'emploi](../../../../../tools/youtube-growth/THEMATIC.md) donne les commandes et les limites de l'analyse.

## Sources et livrables

L'épisode [01, GgSiPkADCz4](https://www.youtube.com/watch?v=GgSiPkADCz4) dure 4 701,553 s. Sa copie officielle est téléchargée dans YouTube Studio pendant cette recette. Sa transcription YouTube déjà disponible est réutilisée ; ses fins de sous-titres sont inférées depuis le début suivant.

L'épisode [02, 7KVqydbGow0](https://www.youtube.com/watch?v=7KVqydbGow0) dure 7 523,660 s. La copie Studio et la transcription française JSONL existantes servent aussi aux Shorts E02. Les deux sources sont en 1280 × 720 avec audio. Les cinq rendus gardent cette résolution.

| Épisode | Titre                                                      | Durée MP4      | Score éditorial | Timecodes source du corps |
| ------- | ---------------------------------------------------------- | -------------- | --------------- | ------------------------- |
| 01      | Codex, Claude Code, OpenCode : pourquoi le harnais compte  | 10 min 16 s    | 79,4/100        | 38:10 à 48:18             |
| 01      | Sillage : piloter ses agents de code depuis son téléphone  | 11 min 37 s    | 75/100          | 25:55 à 37:17             |
| 02      | Faut-il encore lire les tickets quand on code avec l'IA ?  | 12 min 45,52 s | 79,3/100        | 1:20:43 à 1:33:37         |
| 02      | Faut-il réécrire le code legacy avec l'IA ?                | 8 min 25 s     | 78,4/100        | 1:33:38 à 1:42:07         |
| 02      | Comment utiliser l'IA quand on est artisan ou commerçant ? | 14 min 54,36 s | 77,3/100        | 49:48 à 1:04:34           |

Les durées incluent l'accroche et le retrait des pauses. Les timecodes exacts de chaque coupe et du rejeu de l'accroche figurent dans `montage.json`. Les notes ordonnent des propositions éditoriales ; elles ne sont pas des prédictions de vues.

Chaque vidéo possède un SRT, une piste de sous-titres sélectionnable, une proposition de miniature avec les vraies caméras, un titre, une description avec lien vers l'émission, les motifs de sélection et les citations de la question, du développement et de la conclusion. Les descriptions présentent les estimations et avis comme ceux des intervenants.

## Contrôles exécutés

- Décodage intégral des cinq MP4 : réussi. H.264/AAC, 1280 × 720, 16:9, durée de chaque vidéo comprise entre 300 et 900 s. Écart de durée entre les pistes audio et vidéo : 0 s pour les cinq fichiers au sondage.
- Correspondance avec les sources : 87 fenêtres mesurées, réparties entre les accroches et toutes les plages du corps. Corrélation audio minimale 0,98910, corrélation d'image minimale 0,99493. Décalage audio maximal mesuré : 0 ms, à la résolution de recherche de 1 ms. Ces mesures ne constituent pas une certification image par image ni une écoute intégrale.
- Suite Python YouTube : 77 tests exécutés, dont 74 réussis et trois tests Postgres ignorés faute de base locale configurée. Elle couvre les citations inventées, indices invalides, durées, doublons, SRT après montage, reprise du cache, protection des Shorts, MP4 réels et sous-titres incrustés. Les contrôles de correspondance détectent aussi un son décalé et une image remplacée.
- Shorts E02 : 15 tests réussis et trente compositions source conformes à `pipeline.py check`.
- Shorts E01 : quatre nouveaux rendus produits par `youtube_growth.rendering`, sondés et décodés intégralement sous `.local/youtube-thematic/shorts-regression/`. Les manifestes et médias existants ne sont pas remplacés.
- `pnpm check` : réussi, avec formatage, lint, types, 1 255 tests du site et 35 tests des médias et du conducteur.

Les preuves détaillées restent dans `tests-python.log`, les manifestes, les deux rapports d'émission et les fichiers `correspondance-source.json`. La recette constate une option `filter_complex_script` absente de FFmpeg installé ; le rendu utilise désormais `filter_complex`. Les tests du mode incrusté exécutent aussi ce chemin réellement.

## Décisions et limites

[ADR-0040](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0040-videos-youtube-thematiques.md) consigne le pipeline séparé, la réutilisation des composants et l'absence de publication. Le site, `old/`, les commandes Shorts et les files de distribution ne sont pas modifiés. Les fichiers du site déjà modifiés au début de cette tâche restent hors du lot vidéo. Les modifications sont locales, sans commit, push ni PR.

Aucune clé OpenAI n'est configurée dans cette session. L'analyse appliquée aux deux épisodes est le moteur local, avec cinq familles de discussions reconnues par des marqueurs textuels. Sa couverture est limitée ; elle n'équivaut pas à une analyse sémantique de n'importe quelle émission. L'adaptateur OpenAI est implémenté, validé avec des réponses simulées et optionnel. Son fonctionnement réel avec un modèle du compte reste à vérifier après configuration autorisée.

Les copies 720p ne permettent pas de récupérer des détails 1080p. Les erreurs ASR demeurent dans les sous-titres et les preuves brutes. Le contrôle de correspondance confirme que les fenêtres testées proviennent des bonnes plages, mais ne certifie pas le sens du montage ou la correction de chaque fin de phrase. L'écoute éditoriale intégrale des cinq vidéos reste à faire avant une publication. La génération reste automatique ; cette revue porte sur l'utilisation publique des résultats.
