# Préparer un épisode automatiquement sur le poste

La commande `prepare` enchaîne transcription, analyse, sélection, montage, contrôle du rendu, trois miniatures avec revue distincte et calendrier prévisionnel. Le worker existant exécute les étapes et SQLite garde leurs états. Aucun job de diffusion n'est créé, y compris simulé. Les contenus portent `local_only=true` et les barrières sociales restent actives.

La [décision de conception](decision-autonomie-locale-2026-10-29.md) précise la portée des contrôles. Le suivi de cette demande est dans l'[issue #8](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/8).

## Installer les dépendances

Depuis la racine, dans PowerShell :

```powershell
python -m venv .local/autonomy-venv
& ./.local/autonomy-venv/Scripts/python.exe -m pip install -r tools/youtube-growth/requirements-autonomy.txt
$env:PYTHONPATH = 'tools/youtube-growth/src'
```

Prérequis : FFmpeg, FFprobe et un serveur Ollama local déjà installé et démarré. La configuration partagée utilise `qwen3.5:9b` pour l'analyse et la sélection, `gemma3:12b` pour la revue des rendus et la rédaction des miniatures, puis `qwen3.5:9b` pour leur critique. Faster-whisper `dropbox-dash/faster-whisper-large-v3-turbo` fournit la transcription. La base portable reste CPU/int8 ; la recette du master réel utilise une configuration locale CUDA/FP16. La correction orthographique utilise aussi deux rôles distincts. Les noms propres et la fidélité restent soumis aux contrôles : le modèle plus complet améliore plusieurs passages sans garantir une transcription parfaite.

Les poids doivent être présents avant le traitement. La factory ne télécharge pas de modèle et n'utilise ni modèle cloud Ollama, ni service IA payant. Un endpoint autre que la boucle locale, un modèle distant ou un modèle manquant est refusé. Les dépendances comprennent une borne PyAV compatible avec faster-whisper 1.2 ; la recette a révélé une rupture de `metadata_errors` dans une version plus récente.

Le diagnostic indique les modèles configurés ; leur présence et leurs capacités sont vérifiées au début des appels. Changer les modèles ne modifie aucun compte social. Sur un autre poste, adapter les noms aux modèles déjà installés et les paramètres `autonomy` de `config/factory.json`.

Si les poids ASR sont absents, leur installation est une opération explicite préalable, distincte du worker. Cette commande télécharge uniquement les fichiers du modèle public dans le cache local Hugging Face, sans compte :

```powershell
& ./.local/autonomy-venv/Scripts/python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('dropbox-dash/faster-whisper-large-v3-turbo', allow_patterns=['model.bin','config.json','tokenizer.json','preprocessor_config.json','vocabulary.*'], token=False)"
```

## Lancer un épisode

Conserver le master dans son stockage durable, terminer sa copie puis utiliser :

```powershell
& ./.local/autonomy-venv/Scripts/python.exe -m youtube_growth.factory prepare 'D:/medias/master-termine.mp4' `
  --episode-id episode-004 `
  --title 'Titre de cet épisode' `
  --publication-at '2026-11-01T09:00:00+01:00' `
  --next-filming-at '2026-11-06T18:00:00+01:00'
```

Remplacer le chemin et les informations éditoriales. Les dates sont des exemples, jamais déduites d'une habitude de tournage. `--transcript CHEMIN` permet de fournir une transcription existante liée à l'empreinte du master. L'absence de transcription déclenche le moteur local. Les options `--full-episode-url` et `--full-episode-id` complètent une destination connue ; leur absence reste explicite dans les textes et ne bloque pas les exports locaux.

La commande calcule le SHA-256, vérifie que le fichier n'a pas changé, écrit un manifeste terminé et importe l'épisode. Elle fait tourner le worker jusqu'à un état stable, sans commandes manuelles entre les étapes. `--enqueue-only` dépose le travail pour un worker déjà actif. `--limit` borne le nombre de passages de cette commande, pas le nombre éditorial d'extraits. Un épisode sans passage pertinent peut terminer sans vidéo.

Le code de sortie est `0` pour une préparation terminée ou une simple mise en file, `3` pour une préparation incomplète/bloquée ou une limite de passages atteinte, et `2` pour une entrée invalide ou une erreur de commande. Lire aussi le résultat JSON et les erreurs d'étape : une fin de processus ne garantit pas qu'un extrait a passé ses contrôles.

Pour un espace de travail distinct, placer les options globales avant la commande :

```powershell
& ./.local/autonomy-venv/Scripts/python.exe -m youtube_growth.factory --state-dir .local/mon-cycle prepare 'D:/medias/master.mp4' --episode-id mon-cycle --title 'Titre' --enqueue-only
& ./.local/autonomy-venv/Scripts/python.exe -m youtube_growth.factory --state-dir .local/mon-cycle worker
```

Le deuxième processus continue sans conversation Codex ouverte. Il dépend du poste et de son mode de lancement. L'installation d'une tâche Windows et le fonctionnement après fermeture de session restent des opérations distinctes ; cette évolution ne modifie pas les réglages système.

## Lire les résultats et reprendre

Les fichiers sont sous `.local/factory/episodes/IDENTIFIANT/` par défaut. Les analyses, reçus des modèles, images examinées, contrôles et miniatures sont dans `autonomy/`. Les réponses refusées sont conservées dans `model-receipts/rejected/`, séparées du cache accepté ; elles ne peuvent autoriser aucune étape. Les rendus gardent le moteur et les chemins existants. Le calendrier JSON et sa version lisible sont dans `.local/factory/reports/` ; leur chemin figure dans la réponse de `prepare`.

`status --episode-id IDENTIFIANT` expose `local_runs` et `local_calendars`. Le tableau local montre le calendrier prévisionnel et les étapes dans Activité. Les états `local_passed` et `local_ready` signifient que les contrôles automatiques prévus ont réussi. Ils ne constituent pas une attestation humaine ni une permission de diffusion.

Une étape en échec bloque son contenu. Les autres extraits poursuivent leur parcours. Une erreur temporaire du serveur local dispose de tentatives bornées. Un contrôle négatif, un modèle absent ou une réponse inexploitable conserve son motif. Après correction, `resume --job-id IDENTIFIANT` reprend le travail admissible, puis `worker` poursuit les étapes.

Pour corriger une sélection déjà rendue, `revise-local PLAN.json` applique un plan éditorial versionné, lié aux empreintes du master et de la transcription. La file doit être suspendue et le traitement actif terminé. Le plan précise son auteur, son périmètre réel, les passages concernés et les motifs : il peut archiver une variante, réviser ses bornes, son titre ou sa nuance. Les anciens médias et reçus restent conservés. Les revues et packs concernés sont invalidés, une étape `local_recheck` relit les mots et images de la nouvelle coupe, puis le worker reprend les contrôles et le packaging. Un changement de métadonnées réutilise le fichier vidéo compatible ; un changement de coupe crée une autre version. Les intentions distantes, résultats publiés et expériences actives interdisent cette correction locale. Un même plan appliqué deux fois n'ajoute pas de nouveau travail.

Le contrat du plan est dans `factory/local_revisions.py`. Il comprend `version`, `episode_id`, `source_sha256`, `transcript_sha256`, `reviewer`, `scope`, `human_listening=false` et `changes`. Chaque changement contient `segment_id`, `action` (`archive` ou `revise`) et `reason`, puis les éventuels `title`, `context`, `rationale`, `essential_nuance`, `start_seconds` et `end_seconds`. Les deux bornes sont nécessaires ensemble ; elles sont élargies aux unités de parole complètes du master. `caption_grouping_version=2` demande un nouvel export d'affichage sans changer la coupe, notamment pour réunir un mot fugitif après une courte pause. Les miniatures de la version remplacée perdent aussi leur statut courant. Après application, `resume` réactive la file. Aucune de ces commandes n'envoie de contenu.

Les tâches survivent aux interruptions. Les reçus lient les calculs à la source, aux paramètres, au prompt et à l'identité du modèle. Une correction de titre réutilise la transcription compatible. Une modification de source, de sous-titres, de miniature ou de preuve invalide le contrôle concerné. Le calendrier vérifie les empreintes avant de réutiliser un contenu et réagit aux changements de fichiers et de créneau.

## Ce que les contrôles prouvent

Une objection de packaging peut demander une reprise du seul média concerné via `autonomy.request_packaging_revision(store, config, asset_id, reviewer, notes)`. L'appel conserve la vidéo et sa revue, invalide les anciennes miniatures et dates, puis inscrit les remarques dans un nouveau job persistant. Une demande identique est idempotente. Le brief garde ces remarques ; les nouveaux titres, images et textes refont leurs contrôles. Une intention distante ou une expérience active interdit cette reprise. Cette API locale n'autorise aucun envoi.

- Transcription : l'ASR brut est conservé. Le détecteur local de voix prépare le son ; une probabilité de non-parole élevée reste une incertitude enregistrée et ne supprime plus seule un dialogue. Les corrections d'accords silencieux utilisent des opérations mot par mot autorisées, avec un contexte et une revue distincte. Un veto conserve les mots d'origine et la preuve du refus. Aucun mot, chiffre, nom, négation ou horaire ne peut être réécrit librement. Cette procédure ne remplace pas une reconnaissance audio plus précise.
- Analyse : toute la transcription disponible est parcourue par fenêtres avec recouvrement. Les fenêtres de 20 minutes et leur recouvrement initial de 15 minutes permettent de conserver un sujet développé sans le couper à la frontière d'un petit lot d'images. Le nombre d'images par appel reste borné, avec leurs instants exacts. Les zones entre images ne sont pas déclarées visionnées et l'attribution nominative de tous les intervenants n'est pas certifiée.
- Sélection : un affinage choisit les bornes via des identifiants attachés aux paroles, sans confondre secondes et indices. La question, la réponse et leurs réserves doivent tenir dans le passage. Le contexte hors montage est séparé des mots conservés. Un rôle distinct relit tout le texte choisi et jusqu'à six images représentatives ; les contrôles détaillés à intervalles de cinq secondes portent ensuite sur le vrai rendu. Aucune sélection définitive ne vient d'un simple score ou d'un quota. La capacité d'analyse est configurable (`analysis_context_tokens`, initialement 32768) et un dépassement est signalé explicitement.
- Rendu : décodage, durée, dimensions, pistes et signaux techniques, sous-titres non coupés, comparaison du son source/sortie sur trois fenêtres par coupe et revue des images sous-titrées. Un contrôle distinct confronte le titre aux seuls mots conservés, sans le résumé du rédacteur ; tout avis positif cite les mots d'une unité choisie par indice. Une autre lecture du texte intégral conservé se concentre sur ses deux bords ; elle ne voit ni titre ni contexte hors montage. Le décodage PCM complet évite les erreurs de comparaison liées au seek AAC ; les fenêtres ne constituent pas une écoute humaine continue.
- Miniatures : les fragments ASR conservés sont regroupés en unités de parole horodatées, sans joindre des coupes séparées. Les courtes introductions restent avec leur développement lorsque la proximité le permet. Un plan distingue trois questions, chacune ancrée dans une citation et un terme précis du passage. Chaque couple titre/image est rédigé séparément à partir des paroles pour éviter de confondre le propos avec un texte d'habillage visible. Une vérification distincte contrôle l'association sémantique des citations. Une image réelle est choisie dans le passage, près de la citation retenue ; deux détecteurs OpenCV doivent s'accorder sur un visage. Le programme construit des portraits carrés qui le conservent entier, puis un modèle visuel choisit parmi ces seuls cadrages. Les coordonnées ne sont jamais inventées par le modèle. Le moteur applique ce cadrage à l'image de pleine définition sans modifier le visage ni l'expression. Chaque concept et ses aperçus mobiles sont relus avec leur propre preuve, sans les attestations du rédacteur ni le titre général du candidat. La planche et les trois couples sont ensuite comparés pour vérifier la différence des hypothèses et le sens du brief. Un refus peut déclencher une nouvelle proposition, dans la limite des tentatives configurées. Les reçus de plan, de rédaction, d'association et de cadrage sont revérifiés avant de proposer une date. Une évolution de version du packaging remet les anciens packs en préparation et retire leurs anciennes dates jusqu'au nouveau contrôle. Le corpus de référence reste daté et périssable ; son ancienneté bloque les créations concernées.
- Calendrier : dates proposées en Europe/Paris, espacements, plafonds et fin avant le prochain tournage. Sans disponibilité confirmée de l'émission, il reste conditionnel à la sortie prévue. Il porte toujours `valid_for_publication=false` et ne crée aucun `dispatch`.

Le montage initial conserve le cadre entier. Le suivi dynamique de locuteur et un recadrage adapté à chaque démonstration restent à développer. Un écran ou des sous-titres illisibles doivent être refusés par la revue. Les erreurs de compréhension d'un modèle peuvent subsister malgré les contrôles : la fidélité sur plusieurs masters réels reste une validation distincte de l'enchaînement technique.

Le profil local `local_caption_band_v1` ajuste l'image horizontale entière au-dessus d'une bande de sous-titres, afin de conserver les noms et les éléments en bas du master. Les fragments ASR très courts peuvent être regroupés avec leur voisin si le groupe reste proche, court et lisible : les mots, leur ordre et les bornes englobantes restent conservés, sans inventer d'alignement au mot. SRT et sous-titres incrustés utilisent le même regroupement. Ce profil entre dans l'identité du rendu. Une migration de profil conserve les anciens fichiers, retire les anciennes dates et refait les exports et leurs contrôles ; elle ne relance pas la transcription ou l'analyse compatible.

Un bloc ASR trop long pour cette bande reçoit un alignement acoustique forcé avec les poids Whisper déjà présents : le modèle reçoit les mots existants, sans nouvelle reconnaissance ni réécriture. Le résultat conserve les mots et leur ordre, contrôle les horaires et forme des sous-titres plus courts. Les horaires et probabilités restent des **estimations du modèle**, pas une certification de mots entendus. Le reçu conserve les poids utilisés, le bloc source, les horaires, les probabilités et les limites ; il est revérifié avec les médias avant le calendrier. Aucun poids n'est téléchargé par cette étape.

Un refus de bord peut être revérifié par l'autre modèle. Le second lecteur voit uniquement les mots du bord ciblé, sans le premier avis, le titre ou le résumé du rédacteur. Il juge si des mots indispensables manquent ; il ne prédit pas l'intention du locuteur de continuer. Les deux avis restent conservés. Un bord initialement refusé reste bloquant si le second lecteur le juge tronqué ou incertain. Cette étape corrige notamment les refus qui exigent tous les détails d'un exemple alors que la phrase ou la liste est déjà terminée. Elle ne remplace pas une revue humaine.

Un export LinkedIn manuel reçoit la vidéo, la couverture et le texte effectivement relus, avec manifeste, destination, embargo, date proposée et fin de validité. Son dossier est versionné ; le calendrier vérifie son contenu. La date proposée reste `proposed_at`, jamais une programmation sociale. Un nouveau rendu peut remplacer le pack local archivé du même passage, en préservant les fichiers précédents. Une intention distante ou un résultat déjà publié n'est pas remplacé par ce parcours local.

Si le seul défaut technique est un pic audio de l'export trop proche de 0 dB, une seule réparation locale par version de politique est permise. Elle mesure les pics flottants AAC des deux entrées, puis applique une baisse calculée pour viser −1,5 dB, au minimum −1,5 dB. Un ancien échec avec une baisse fixe peut être repris depuis son export d'origine, jamais en enchaînant les réencodages sur la correction précédente. La réparation crée de nouveaux fichiers, copie le flux vidéo sans le réencoder et refait les contrôles audio et vidéo. Le master et les anciens exports restent intacts. Cette marge de sortie ne répare pas un éventuel écrêtage déjà présent dans la source. Un autre défaut ou un échec avec la politique courante reste bloquant.

Les modèles restent chargés uniquement dans la durée d'une étape ; un changement de rôle décharge le précédent, et la fin d'étape décharge le dernier. La rétention de secours est bornée à 60 secondes. Cela évite les rechargements à chaque lot d'images sans modifier les réglages globaux du poste.

Le public SANDBOX est francophone : titres, phrases de miniature, questions, promesses et textes de réseau sont rédigés en français naturel. Les noms d'outils et termes techniques utiles restent permis. La revue vérifie la langue séparément de la fidélité ; une phrase anglaise ou artificiellement mêlée au français bloque le packaging. Trois angles n'autorisent pas à inventer une critique ou une limite absente des paroles.

Les champs `angle` et `hypothesis` du brief sont aussi des affirmations à contrôler : un titre prudent ne valide pas une causalité inventée dans ces champs. Le critique les reçoit avec le couple titre/image et sa citation. La réserve essentielle contraint le plan, notamment lorsqu'un participant dit ignorer le mécanisme d'un comportement rapporté. Le rédacteur ne recopie plus le titre général et ne réécrit pas les hypothèses déjà planifiées.

Le mode courant `source_bound_v1` limite la génération au choix d'unités de parole, de mots d'ancrage dans leur propre citation, de titres/phrases d'image et du choix initial. Le programme construit des questions complètes depuis les mots retenus ; les autres textes sont construits depuis ces questions, le titre de passage contrôlé et des paroles littérales choisies par indice. Une hypothèse devient une question de présentation, sans diagnostic technique ajouté. Une citation trop longue pour un texte de réseau est omise entièrement ; elle n'est pas raccourcie en supprimant une condition. Les relatives et réserves proches sont regroupées dans la preuve quand les bornes de taille et de temps le permettent. Ce choix conserve une rédaction plus prudente : les modèles inspectés ont laissé passer des affirmations fautives même lors d'un essai de contrôle textuel séparé. Les champs créatifs et leur adéquation à la preuve gardent leurs contrôles et leurs limites.

## Vérifier

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
$env:FACTORY_MEDIA_INTEGRATION = '1'
& ./.local/autonomy-venv/Scripts/python.exe -m unittest discover -s tools/youtube-growth/tests -v
python tools/repository/check_repository.py
```

Les tests de machine d'états utilisent des doubles explicitement identifiés. La recette média vérifie aussi les vrais exports FFmpeg, dont l'amorce AAC au début et après une coupe non entière. La [recette avec de vrais modèles locaux et une vidéo parlée synthétique](validation-autonomie-locale-2026-10-29.md) précise les fichiers examinés et les résultats ; elle ne vaut pas une validation d'une émission réelle de 60 à 120 minutes.


Une revue indépendante explicite des miniatures peut être enregistrée par `local_review.adopt_packaging(store, config, bundle_id, report_path)`. Le rapport doit nommer un lecteur distinct, lier les empreintes courantes, déclarer les six critères et les dix images examinées, et ne contenir aucun blocage. Le refus automatique reste conservé. Cette revue porte sur images et textes ; elle n'atteste aucune écoute humaine et ne permet aucune publication. Le calendrier revérifie ses preuves ; le pack est versionné par la nouvelle preuve de revue. Cette action est explicite et ne constitue pas un contournement automatique d'un avis négatif.
