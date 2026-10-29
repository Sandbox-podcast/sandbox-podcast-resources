# Audit et recette éditoriale du 29 octobre 2026

Demande suivie dans l'[issue #10](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/10). Les outils, tests et guides sont préparés pour une PR dédiée ; les médias et preuves de rendu restent exclusivement sur le poste. L'issue reste ouverte jusqu'à la fusion de la livraison correspondante.

## Audit de départ

| Périmètre examiné | Composants conservés | Écart avec la demande |
| --- | --- | --- |
| Exécution | `store.py`, `runtime.py`, réservations SQLite, reprise, worker Windows | Aucun job de vidéo originale. |
| Analyse | `media.analyze`, transcriptions, couverture par modalité, preuves externes, caches de sonde et décodage | Pas de découverte sémantique en arrière-plan configurée. |
| Éditorial historique | Préparation native, analyse thématique locale ou OpenAI explicite, contrôles des citations et coupes | Familles de sujets et plafonds propres aux anciens parcours ; pas de classement commun multiformat. |
| Extraction | FFmpeg, concaténation, master propre, SRT/ASS, cadrage préservant les pixels, QA et empreintes | Sous-titres sans animation d'entrée ; réorganisation chronologique interdite ; choix du format peu expliqué. |
| Packaging | Packs locaux, trois concepts, références visuelles, revue croisée, verrou d'expérience | Pas de métadonnées de production narrative. |
| Résultats | Observations natives, audits OAuth en lecture seule, expériences, coûts, décisions réversibles | Pas d'import des audits dans les observations persistantes ni de groupes comparables par contenu. |
| Skills et prompts | Sept skills de projet, prompt maître du 28 octobre, consignes de couverture et simulation | Procédures orientées extraction, sans contrat de recherche/scénario/storyboard. |
| Workflows GitHub | Tests de sources et fixtures temporaires | Aucun changement nécessaire : les traitements de production doivent rester locaux. |

La nouvelle voie conserve le moteur Python et FFmpeg. Elle n'ajoute ni Remotion ni dépendance HyperFrames au runtime de la factory. La demande privilégiait la réutilisation des composants opérationnels ; un renderer de schémas avec Pillow, déjà présent dans les dépendances, permet une première chaîne locale sans service supplémentaire. Les projets vidéo existants restent intacts.

## Évolutions exécutables

P1 : `discover` prépare toute la transcription pour un agent ou un modèle local et contrôle les propositions reçues, dont les citations d'accroche. `editorial` et `opportunities` évaluent épisodes et veille avec dix notes motivées, seuil, limites de durée, expiration et dédoublonnage. Un score absent reste absent. Les notes sont des jugements éditoriaux, sans prédiction de vues. Une recommandation retirée ou dépassée bloque les packs concernés et les contrôles avant montage ou envoi simulé.

P2 : le moteur existant conserve les sources, les cartes de coupes et les sous-titres réutilisables. Les sous-titres ASS ont une entrée animée au niveau du segment transcrit. Les coupes peuvent être réorganisées avec une revue explicite du sens ; les recouvrements restent interdits. Les nouvelles recommandations utilisent les plages 15 à 90 secondes et 3 à 15 minutes. Les fonctions historiques qui définissent d'autres limites ne sont pas présentées comme le nouveau parcours.

P3 : `research-fetch` archive les URL documentaires choisies par l'agent. `research` contrôle les copies, citations, natures des affirmations, revues et péremption. `draft-story` prépare ou génère un scénario structuré. `narrative` exécute recherche, scénario, storyboard, voix, rendu et métadonnées avec des reçus distincts. Il prend un sujet provenant d'un épisode ou de la veille. Les étapes peuvent être reprises, la voix partagée entre ratios et les scènes réutilisées. `--queue` utilise le worker existant. Les sauvegardes portables incluent les recherches, sources de scénario, voix et rendus ; la restauration fournit un scénario aux références remappées et remet la revue en attente.

Le renderer livre une première bibliothèque de flux, comparaisons, étapes et cartes, avec animations déterministes, logo et composition portrait propre. La voix de recette est une voix Windows standard, avec débit, alias de prononciation et pauses entre phrases. Aucun clonage et aucun appel ElevenLabs ne sont intégrés. `review-narrative` conserve une validation humaine liée aux fichiers, sans créer de publication.

P4 : `import-analytics` réutilise les quatre rapports de l'audit YouTube historique et conserve leurs dimensions. `learn` compare format, durée, ancienneté et impressions avec les définitions et périodes natives. Les synthèses descriptives nourrissent le brief et les requêtes éditoriales. Elles ne changent pas les poids et ne déduisent aucune causalité. Les données synthétiques restent exclues de ces recommandations.

Les commandes, contrats et paramètres sont décrits dans [la production éditoriale](production-editoriale.md). Les nouveaux résultats sont accessibles en CLI dans `status` et `brief` ; aucun nouvel écran de pilotage n'est livré.

La revue finale renforce aussi trois cas de reprise : une commande ciblée revérifie les fichiers des étapes conservées avant de garder leur approbation ; la validation finale revérifie la péremption de la recherche ; un job narratif dont la recherche est bloquée conserve l'état `blocked` dans le worker.

## Recette sur l'épisode 3

La base de recette est `.local/factory-rework-20261029/state`, distincte de la base opérationnelle. La vidéo et la transcription de l'épisode 3 étaient déjà présentes. L'analyse antérieure et ses 19 candidats ont été réutilisés. Cette recette ne constitue pas une nouvelle lecture sémantique intégrale des images et du son de l'émission.

Les jugements préparés par Codex à partir des éléments textuels donnent sept recommandations de Short, une d'extrait et trois de narrative ; huit candidats restent sans format recommandé. Les notes diffèrent selon les opportunités. Le traitement ne marque aucun passage comme retenu et ne prépare aucun calendrier social. La connaissance des publications antérieures reste incomplète : les contrôles de nouveauté conservent cette limite.

| Export local | Durée mesurée | Dimensions | État |
| --- | --- | --- | --- |
| Narrative sur la latence des agents vocaux | 238,642 s | 1280 × 720, 24 images/s | Rendu standard, revue humaine en attente. |
| Même scénario en composition portrait | 238,708 s | 540 × 960, 12 images/s | Prévisualisation, revue humaine en attente. |
| Passage du bot TeamSpeak | 35,333 s | 1080 × 1920 | Prévisualisation technique d'une extraction. |
| Discussion sur la formation des juniors | 183,600 s | 640 × 360 | Prévisualisation technique d'une extraction. |

La narrative part du témoignage dans la transcription, puis distingue les faits documentés des conseils d'ingénierie proposés. Trois documents Microsoft et une copie du passage transcrit sont archivés avec leurs empreintes. Le dossier marque le témoignage `transcript_supported` et conserve son contrôle oral manquant. Les sources officielles sur [les résultats partiels](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/captioning-concepts) et [les délais de synthèse](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-lower-speech-synthesis-latency) soutiennent les précisions techniques citées. La présence de dix secondes dans le texte n'est pas présentée comme un benchmark actuel.

Le renderer a décodé intégralement les nouveaux fichiers, vérifié durée et dimensions et recherché les noirs, silences et crêtes. La narrative ne présente ni noir détecté ni silence supérieur au seuil de deux secondes ; sa crête maximale mesurée est de -1,4 dB. Ces contrôles ne prouvent pas l'intonation, la prononciation ni la fidélité d'un montage au propos source.

Des images des deux ratios ont été inspectées. Une revue croisée par un second agent a examiné le scénario, les copies des sources, trois concepts et six PNG. Elle a conduit à distinguer l'appui ASR de la confirmation orale, ajouter la source sur les résultats intermédiaires, préciser le premier titre, compléter le troisième concept et remplacer les noms de fabrication affichés par des indications françaises. Aucun export de miniature à 320/160 pixels n'a été produit ni validé pendant cette recette.

Une reprise de la narrative complète retrouve les six reçus en cache. L'empreinte du master source reste `e47075031bc13141ae22f9f1482e19cbc1709a28681cd22d52882284f9053c89`. Aucun master n'a été écrasé. Les vidéos, SRT, données de recherche, scripts de recette et preuves sont uniquement dans `.local/factory-rework-20261029/`. `validation.json` y regroupe les chemins, durées, empreintes, caches et blocages.

## Vérifications

La suite Python a été exécutée avec la recette média explicite :

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
$env:FACTORY_MEDIA_INTEGRATION = '1'
python -m unittest discover -s tools/youtube-growth/tests -v
python tools/repository/check_repository.py
python -m unittest discover -s tools/repository -v
node --test tools/youtube-growth/tests/workflow-preflight.test.mjs
git diff --check
```

Résultat de la suite après finalisation : 272 tests, dont trois ignorés car la base Postgres de test n'est pas configurée. Les 29 nouveaux tests couvrent les jugements, citations inventées, durées de formats, répétitions, modèle local, reprise, réutilisation de voix, restauration portable, refus de validation d'un témoignage seulement transcrit, dimensions Analytics et un véritable encodage/décodage de scène synthétique. Ils vérifient aussi les fichiers conservés après approbation, la péremption avant validation et le statut des jobs narratifs bloqués. Les six tests de politique du dépôt et les trois contrôles Node de workflow passent. Le contrôle du dépôt confirme que l'index ne contient pas les livrables locaux. Les fichiers de recette restent ignorés.

## Dépendances et fonctions restantes

| Besoin | État constaté | Suite nécessaire |
| --- | --- | --- |
| Agent sémantique autonome dans le worker | `generation.local_command=null`, `auto_editorial=false` ; les commandes `--generate` produisent un blocage et une requête exploitable. | Installer/configurer un modèle local et sa révision, puis éprouver ses réponses. Les jugements et scénarios de cette recette viennent de Codex dans la conversation. |
| Recherche autonome d'actualités | La collecte de documents depuis des URL fournies fonctionne ; le choix et le croisement des sources sont préparés par l'agent. | Connecter le flux de veille réel et éprouver la recherche du modèle choisi. |
| Qualité audiovisuelle et fidélité orale | Contrôles techniques et images ponctuelles disponibles ; pas d'écoute intégrale certifiée. | Écouter les voix et coupes, confirmer les paroles, revoir le rythme, le cadrage et les sous-titres. |
| Variété artistique | Première bibliothèque de schémas opérationnelle. | Ajouter illustrations, démonstrations et composants selon les sujets ; aucun documentaire illustré complet n'est revendiqué. |
| Miniatures narratives | Trois concepts et trois titres dans le pack JSON. | Produire les images, leurs aperçus et leur revue croisée selon la procédure. |
| Voix ElevenLabs | Aucun client ni appel facturé activé. | Choisir une voix et un budget autorisés, puis intégrer et tester le fournisseur ; l'import de WAV autorisés est disponible. |
| Analytics réelles | Le diagnostic du venv trouve les bibliothèques Google, mais aucun OAuth à l'emplacement attendu ; aucune mesure réelle importée dans la recette. | Fournir l'accès en lecture ou un audit/export réel ; compléter impressions, CTR et nouveaux spectateurs avec leurs définitions. |
| Expérimentation native et publication | Registre existant conservé, aucun test Studio ni envoi distant effectué. | Vérifier l'éligibilité et les résultats natifs séparément ; toute publication reste soumise à une autorisation explicite. |

La recette démontre les traitements locaux avec un épisode existant. Elle ne démontre ni une autonomie éditoriale de fond sans modèle configuré, ni une validation audiovisuelle finale, ni une amélioration des performances de la chaîne.
