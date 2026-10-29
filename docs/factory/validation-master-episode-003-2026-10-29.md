# Recette réelle du master de l'épisode 3 — 29 octobre 2026

Suivi : [issue #9](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/9), après la [recette synthétique](validation-autonomie-locale-2026-10-29.md). **Les essais de miniatures sont arrêtés à la demande explicite de Lou**, qui retravaillera cette partie. Les versions et preuves restent conservées, la file est suspendue et le worker arrêté. La recette complète du packaging n'est pas déclarée terminée. Aucun commit, push, PR ou changement social n'a été effectué.

## Source et paramètres du test

- Master terminé : `D:/Videos/Sandbox episode 03.mp4`, export Blackmagic Design DaVinci Resolve daté du 25 octobre 2026.
- Durée sondée : **6 027,242667 secondes**, soit 1 h 40 min 27 s ; vidéo H.264 1920×1080 à 30 i/s, son AAC stéréo 48 kHz.
- Taille : **4 009 037 532 octets** ; SHA-256 : `68a5d68b9ce302f186851dfae15cdfcc3998ea39a516f5c9521e5400c44527eb`.
- Identifiant local : `episode-003-master`. État séparé : `.local/real-master-20261029/state/`. Les données sont exclues de Git.
- Le prochain tournage est fixé par Lou au **1er novembre 2026**. L'heure n'étant pas fournie, la borne locale de test est le début de cette journée, **00:00 Europe/Paris** : hypothèse prudente, sans prétendre connaître l'heure réelle.
- Le départ de la fenêtre de recette est le 29 octobre 2026. Cette entrée de test ne constitue pas une preuve de date de publication ni de disponibilité réelle de l'émission. La destination connue est conservée et le calendrier reste conditionnel.

Le master est environ 92 secondes plus court que la copie YouTube décrite dans l'analyse du 28 octobre. Les sous-titres et bornes de cette copie n'ont donc pas été réutilisés : la transcription est calculée depuis le son du master.

Configuration locale : `.local/real-master-20261029/config.json`, transcription CUDA FP16. Le modèle public [large-v3-turbo converti pour CTranslate2](https://huggingface.co/dropbox-dash/faster-whisper-large-v3-turbo) a été téléchargé explicitement lors de la préparation du poste. Les appels du worker utilisent ensuite les fichiers locaux ; aucun média n'est envoyé à un fournisseur de transcription.

## Défauts effectivement détectés et corrections

### Paroles omises par la première transcription

La première passe small sans VAD produisait **959 unités**. Son traitement supprimait des segments sur la seule probabilité de non-parole ; certains vrais dialogues disparaissaient. Le trou **432,76–460,82 s** a été retranscrit directement depuis le même master : quatre segments de dialogue agent/chatbot y sont reconnus.

Correction : détection locale d'activité vocale, désactivation de la suppression automatique par seuil de non-parole, conservation de cette probabilité dans les preuves plutôt que suppression des mots. L'identité du cache inclut ces paramètres. La passe small révisée produit **1 254 unités** et retrouve ce dialogue. La passe large-v3-turbo produit **2 803 unités**, avec une segmentation plus fine.

Un contrôle séparé compare les intervalles de voix détectée aux bornes des sous-titres. La passe initiale laisse de nombreux trous longs, jusqu'à environ 27 secondes de voix détectée dans un seul intervalle. Les deux nouvelles passes ne présentent plus de trou supérieur à 8 secondes selon ce détecteur. Les écarts plus courts et les erreurs lexicales restent possibles : cette mesure n'est pas une écoute ni une mesure de taux d'erreur des mots.

La lecture indépendante de la nouvelle transcription relève notamment Playwright, seniors, Markdown et UI plus nets que dans le premier brut. D'autres termes restent douteux, dont certains noms d'outils et de boucles d'agents. Ils ne sont pas corrigés par simple déduction.

### Réécriture intempestive de sous-titres

Le correcteur libre complétait des phrases coupées entre deux unités, ajoutait les mots suivants et mélangeait parfois les lignes. Les contrôles l'ont refusé avant toute application.

Correction : opérations liées à l'index d'un mot, avec une seule substitution silencieuse autorisée par position. La ponctuation et les horaires restent identiques. Les propositions sont ciblées autour d'indices d'accord, regroupées avec leur contexte pour éviter des centaines d'appels peu utiles. Le relecteur distinct peut opposer un veto : il rejette alors la **correction proposée**, en conserve la preuve et laisse le texte source intact. Ce veto n'est pas une preuve que la version source était fautive. Les changements lexicaux, chiffres, négations et ajouts de mots restent interdits.

Dans la transcription normalisée examinée, **aucune correction n'a été appliquée** (`changes=[]`). Les améliorations de mots observées proviennent de la nouvelle reconnaissance audio, pas d'une réécriture ultérieure.

### Contexte insuffisant pour l'analyse d'une longue émission

Le service local a explicitement refusé un premier appel de **28 805 tokens** face à une capacité de **16 384**. Il n'a pas fourni d'analyse sur un texte tronqué.

Correction : texte intégral transmis sous forme de lignes compactes, horaires d'entrée arrondis à la milliseconde pour la lecture du modèle, indices toujours liés aux horaires originaux. La capacité d'analyse passe à **32 768 tokens** et entre dans l'identité du cache. Le premier appel corrigé a réellement évalué **19 970 tokens**, avec quatre propositions de passages. Un dépassement de contexte possède désormais un motif distinct d'une indisponibilité temporaire du serveur.

Les variantes se recouvrant fortement avec un passage déjà retenu sont archivées avant une revue visuelle coûteuse, avec leur motif et sans inventer de revue. Cela conserve la règle éditoriale existante et évite de refaire les mêmes contrôles sur les fenêtres de transcription qui se recouvrent.

### Bornes acceptées à tort par la première revue automatique

L'inspection des premières propositions a retrouvé un découpage insuffisamment éditorial : une coupe terminait sur « mais vous pensez pas que c'est différent un agent et un bot », la suivante commençait par « parce que là on est plus sur un bot », et une autre par le fragment « ou alors ». La revue générale avait pourtant donné un avis positif.

Correction : affinage distinct des bornes sur un contexte court, distinction explicite entre **paroles conservées** et **contexte hors montage**, validation séparée du début et de la fin, refus des fragments de réponse ou questions orphelines détectables. Les choix utilisent des identifiants attachés aux paroles, avec les débuts et fins manifestement orphelins exclus des choix autorisés. La revue qui suit utilise un autre modèle. Le contexte fourni au relecteur ne peut plus être pris pour des paroles réellement gardées. Les preuves d'affinage restent liées aux indices et sont revérifiées avant les miniatures et le calendrier.

La présélection éditoriale lit tous les mots du passage et jusqu'à six images représentatives. Les contrôles détaillés à intervalles de cinq secondes restent ceux du **rendu final**, avec ses vrais sous-titres. Le changement de cadence en présélection est explicite et ne supprime pas la revue des images du fichier livré.

## Périmètre de la lecture indépendante des sources

Un autre agent a lu les 959 unités du premier brut puis comparé les zones douteuses dans la nouvelle transcription. Il a examiné la planche source et des images du master à **1 818 s et 4 300 s**. La diapositive Voxtral montre une succession transcription → modèle de langage → TTS ; elle ne prouve pas un modèle audio natif unique. Les réserves sur les commits, la valeur, les statistiques de sécurité, le coût des boucles et la capacité du juge ont été relevées pour la revue des futurs extraits.

Cette lecture n'est pas une écoute humaine, une vérification externe des affirmations des participants ou un visionnage continu. Les rendus et miniatures n'étaient pas encore produits à ce checkpoint et ne sont pas déclarés validés ici.

## Réparations éditoriales sur les vrais extraits

La première analyse complète a lu les **2 803 unités** en **18 fenêtres avec recouvrement** et proposé 73 variantes, dont 35 retenues initialement. Le nombre ne constitue pas un objectif éditorial. Quatre variantes ont ensuite été archivées après lecture indépendante : mauvais titre de goulot humain, explication Voxtral privée de sa clarification, chiffre de sécurité privé de sa comparaison et confusion entre additions aléatoires et boucle critique.

Dix plans de réparation locaux sont conservés sous `.local/real-master-20261029/editorial-corrections-v1.json` à `v10.json`, avec leurs reçus dans `state/editorial-revisions/`. Ils lient les changements aux empreintes du master et de la transcription. Les corrections concernent notamment :

- Voxtral : conserver la clarification de l'architecture transcription → modèle de langage → voix, ainsi que la réserve sur la conversation.
- Anecdote de production : garder l'incertitude exprimée sur la réalité du cas rapporté.
- Boucle critique : garder la limite du juge, le coût et les réserves sur le matériel.
- Interfaces vocales : remplacer la promesse affirmative « en 2035 » par une question, conserver sa contestation et terminer après la conclusion du téléphone trop compliqué.
- Catalogue : reprendre le chiffre de **1 000 jeux** effectivement énoncé, sans en faire un seuil universel mesuré.
- Architecture et classificateurs : rétablir les débuts et conclusions utiles ; ne pas promettre de fonctionnement interne démontré à partir d'un récit d'utilisation.
- Tests : retirer du résumé une simulation de charge et une efficacité qui ne sont pas démontrées. Le projet de simulation d'utilisateurs reste présenté au futur.
- Bords des vrais fichiers : rétablir l'introduction de l'agent comme interface et terminer avant « et l'évolution suivante » ; isoler la proposition de garde-fous avant un autre récit ; conserver les usages qui répondent à la question du catalogue, la condition de structuration des données et la conclusion de l'exemple d'entreprise.
- Seconde lecture des 20 coupes restantes ou révisées : terminer les phrases sur le volume de données et la lecture approfondie ; commencer l'hypothèse visuelle après sa question vocale exclue ; retirer la durée « 5 ans » absente et la promesse de remplacement de mémoire humaine ; présenter les vues 3D comme une prospective.

Un contrôle distinct vérifie les titres sur les seuls mots conservés. La première version exigeait une citation recopiée par le modèle ; celui-ci ajoutait parfois une ponctuation ou un raccord absent, et le contrôle refusait correctement la fausse citation mais bloquait un titre pourtant soutenu. Le choix se fait désormais par indice d'une unité source ; le programme reprend lui-même ses mots exacts. Le modèle ne peut plus réécrire la preuve. Les questions ouvertes et les titres de discussion n'impliquent ni cours exhaustif ni réponse définitive.

## Son et conservation des médias

Certains exports atteignaient 0 dB après encodage AAC malgré la normalisation initiale. Le gate de crête n'a pas été abaissé. Une première atténuation fixe de **−1,5 dB** a suffi pour plusieurs fichiers, mais pas pour un passage : `volumedetect` ramenait son pic à 0 dB alors que la mesure des échantillons flottants AAC donnait **+2,697332 dB** avant correction et **+1,217266 dB** après. Cet export est resté bloqué.

La correction mesure désormais les pics flottants des deux fichiers d'entrée avec `astats`, puis applique une baisse calculée pour viser −1,5 dB, au minimum −1,5 dB. Le traitement reste borné à une correction par version de politique ; le passage de la politique historique à cette version repart de l'export **d'origine**, jamais du fichier déjà réencodé. Le flux vidéo H.264 est copié sans réencodage ; les sous-titres, anciens exports et master restent conservés. La nouvelle version refait les contrôles. Cette opération ne restaure pas un éventuel écrêtage déjà présent dans le master.

Le test média de cette réparation vérifie les empreintes des entrées, l'identité des paquets vidéo, la baisse de niveau, la correspondance temporelle du son, le cache et le refus d'une deuxième réparation automatique. Les vrais extraits disposent aussi d'un décodage technique complet, d'une comparaison de trois fenêtres audio par coupe et d'images sous-titrées examinées toutes les cinq secondes.

La lecture des premiers/derniers sous-titres et de 32 images de bords pour 16 exports a retrouvé des fins interrompues malgré la QA générale. Une vérification supplémentaire lit désormais tout le texte conservé et se concentre uniquement sur ses bords, sans titre ni contexte extérieur susceptible d'être pris pour des paroles gardées. La calibration réelle conservée dans `boundary-regression-real-v6.json` refuse les anciennes fins « et l'évolution suivante » et « dans la session », et accepte la fin révisée sur les questionnaires ainsi que la conclusion sur la factorisation. Cette calibration ne garantit pas une compréhension parfaite de tout passage inédit.

Une image prise à −0,5 seconde semblait montrer une fin sur « hyper » ; le SRT prouve toutefois qu'« utile » était bien présent ensuite, pendant 280 ms. Le défaut portait sur la lisibilité du dernier mot, pas sur sa présence dans la coupe. Le regroupement des fragments fugitifs corrige l'affichage sans changer le texte. Les deux lignes recouvraient aussi le cartouche LOU dans le catalogue. Le profil local réserve maintenant une bande aux sous-titres et y ajuste l'image entière. Le test FFmpeg conserve un marqueur au bas de la source, vérifie qu'il reste au-dessus de cette bande et contrôle le mot final regroupé dans SRT et ASS. Les anciens exports sont conservés et les nouvelles versions refont toute leur QA.

Le bloc **186,68–209,06 s** occupait plus de vingt secondes et un paragraphe entier, trop long pour la bande. L'alignement acoustique local des mots fournis produit **77 unités de mots/ponctuation** puis **sept sous-titres**, sans aucun changement de texte dans le probe observé. Le worker conserve les reçus d'alignement et leurs probabilités. Ce sont des horaires estimés à partir du son, distincts d'une reconnaissance lexicale nouvelle ou d'une écoute humaine.

La seconde revue des **31 nouveaux exports** a ouvert six planches, soit **62 images de bord**, puis **16 captures individuelles à 640 pixels**, et lu les premières/dernières répliques des 31 SRT. Les coupes révisées et la bande sont visibles. Elle n'a pas retrouvé d'autre réserve substantielle de bord, mais a relevé « professionnelle. » isolé pendant **0,320 s** après une pause de **0,740 s**. Le plan v7 le réunit à « à une application » dans un nouvel export, sans déplacer la coupe. Le regroupement autorise désormais une pause d'au plus une seconde lorsque l'ensemble reste court et lisible. Le lecteur distinct a ouvert l'image réelle du nouvel export `asset-765244356b3be9573e0a`, comparé les mots et vérifié le SRT : **« à une application professionnelle. » reste affiché 3,11 s**, entier et lisible dans la bande. Cette réserve d'affichage est levée, sans attestation d'écoute.

Les modèles refusaient aussi des fins orales achevées parce que l'intervenant aurait pu continuer. Le second contrôle reçoit désormais une cible déjà déterminée, uniquement ses mots, sans voir le premier avis : il vérifie les mots indispensables manquants et non l'intention future du locuteur. Les exemples de vraies coupures restent refusés et les premiers avis contradictoires restent dans les reçus. Un résultat incertain continue de bloquer le contenu.

L'interface de cette session ne permet pas l'écoute par l'agent. Des reconnaissances locales ponctuelles et les comparaisons de formes d'onde servent de contrôles complémentaires, sans être présentées comme une écoute humaine. Des mots restent incertains ; aucune correction de noms ou d'expressions n'est inventée pour les masquer.

## Miniatures : défauts réels et faux refus

Checkpoint audiovisuel, après les réparations : **31 rendus courants sur 31** passent les contrôles automatiques liés aux fichiers. Les **93 fenêtres audio** ont une corrélation minimale de **0,9932603634** et un décalage maximal mesuré de **0 ms**. Les modèles ont examiné **1 267 images sous-titrées** échantillonnées ; trois rendus courants ont une correction de marge audio, dont deux avec le calcul adaptatif. L'empreinte complète du master est inchangée. La preuve est `.local/real-master-20261029/av-evidence-28dfc69b88755b0ba542.json`. Ce checkpoint n'inclut pas encore la fin des miniatures ni du calendrier et ne remplace ni écoute humaine ni visionnage continu.

Le second lecteur a ouvert les trois JPEG, les aperçus 160/320 et la planche de **cinq premiers bundles**, soit 15 variantes. Même un bundle accepté automatiquement conservait des visages minuscules, une interface illisible et beaucoup de vide. Le défaut de cadrage était donc réel.

Le premier recadrage libre par modèle a encore produit des visages coupés. Il est remplacé par un consensus de deux détecteurs locaux OpenCV. Le programme construit des portraits carrés conservant le visage entier ; le modèle choisit parmi ces propositions et ne fournit plus de coordonnées. Les pixels proviennent du master à la seconde attestée, sans modification de l'expression ou invention d'intervenant. L'agrandissement éventuel reste déclaré.

La revue révélait aussi des faux refus : mélange du titre général avec le concept évalué, lecture de la mauvaise citation, paraphrase fidèle traitée comme une invention, demande de schéma jamais promis ou exigence d'écoute humaine déduite d'une phrase de limitation. Le critique reçoit désormais uniquement le couple évalué, sa propre citation et les vraies images ; une revue séparée compare les trois hypothèses et le sens du brief. La promesse de contenu et la question du public ne peuvent plus être des instructions de génération ou une promesse de JSON.

Les fragments courts restent avec les paroles voisines quand ils sont à moins de cinq secondes, dans la même coupe et une unité de moins de 80 secondes. Le plan et l'alignement ne peuvent choisir un fragment de moins de douze mots comme preuve isolée. Ce contrôle évite notamment de réduire une condition sur la compréhension de l'agent aux seuls mots « ta confiance… fragile ».

Le pilote final `thumbnails-06bf100c134227d840890097` a passé la revue automatique puis la seconde lecture des trois JPEG, aperçus 160/320 et planche. Le lecteur ne relève plus d'objection bloquante ; il conserve comme réserves la douceur en grand format et quelques répétitions rédactionnelles. Il ne s'agit pas d'un résultat de performance publicitaire.

La recette des nouveaux bundles a encore retrouvé deux variantes en anglais ou en franglais, pourtant acceptées par les critères de fidélité et de lisibilité : « Automating Tests with a Unique Skill » et « Simulating System Pannes for Robust Testing ». La génération demande désormais explicitement du français naturel, avec maintien des noms propres et termes techniques. Un critère indépendant `french_language` examine les couples titre/image et les textes de réseau. Le packaging passe en version 3 : les anciennes approbations et dates sont invalidées, les médias compatibles conservés et les textes/images revérifiés. Un refus de langue bloque le packaging sans rejeter une vidéo techniquement et éditorialement conforme.

La revue distincte des huit bundles alors courants a réellement ouvert **80 images** : 24 JPEG, 24 aperçus 320, 24 aperçus 160 et huit planches. Elle confirme la lisibilité et relève d'autres faux positifs : deux paires reprennent la même phrase avec des titres synonymes ; un titre promet les « limites » d'un audit simplement décrit ; « points d'entrée multiples » inverse un propos sur un point d'entrée unique aux structures disparates. Des métadonnées transforment aussi une anecdote incertaine de classificateur en diagnostic, et une piste d'embeddings « par exemple » en nécessité. Les bundles concernés restent historiques et non approuvés pour la suite. Les nouvelles versions devront être relues sur leurs propres fichiers. Le validateur de rédaction refuse désormais la phrase de miniature reprise d'un concept précédent, même si le titre ou le portrait diffèrent. La revue de fidélité demande une réserve réellement exprimée avant de permettre un titre annonçant des limites ou une critique.

## Packs remis et calendrier

Le passage clavier/chatbot a aussi exposé un faux refus : le contrôle exigeait qu'une question éditoriale soit confirmée ou réfutée alors que le propos la discute ouvertement. La revue rappelle désormais cette distinction. Une reprise avec remarques persistantes peut viser le seul packaging, sans refaire la transcription ou les contrôles vidéo ; elle retire les dates et l'ancienne approbation, conserve les fichiers et refuse une intention distante. Ce parcours est testé avec idempotence et protection des résultats distants.

La première nouvelle version du bundle sur les classificateurs conserve encore des affirmations causales non exprimées dans `hypothesis` et `supports`, malgré des titres interrogatifs et des images acceptables. Le second lecteur a ouvert ses dix images et relu les paroles jusqu'à 5 491,70 s. Le défaut de contrôle est identifié : la revue individuelle recevait le titre et la phrase d'image, mais pas l'hypothèse affichée. Le packaging passe donc en **version 4** : `angle` et `hypothesis` sont aussi des affirmations à confronter à la citation, jamais des preuves. Le plan reçoit la réserve essentielle du passage et doit distinguer succession observée, cause démontrée et supposition. Le rédacteur du couple titre/image ne réécrit plus ces champs du plan ; il reçoit seulement sa citation, son public, sa réserve et les couples déjà utilisés, sans le titre général susceptible d'être recopié.

La seconde lecture de cette version retrouve encore des généralisations et un mauvais référent de « légende urbaine ». Un contrôle textuel séparé, avec raisonnement local, a été calibré sur **deux bundles réellement fautifs** et une version prudente : il accepte les trois. Cette calibration **échoue** ; ses reçus restent dans `claim-regression-receipts/` et `packaging-claims-regression-v1.json`. Ce contrôle n'est pas intégré ni présenté comme une preuve de fidélité.

La **version 5** réduit donc les affirmations laissées à la génération : le modèle choisit des unités de parole, des mots d'ancrage présents dans leur propre citation, les titres/phrases d'image et un choix initial. Les questions complètes sont construites par le programme depuis ces mots. Il construit les autres champs depuis ces questions, le titre de passage déjà contrôlé et les paroles littérales choisies par indice. Les hypothèses affichent une question, les justifications reprennent les mots conservés et les textes de réseau utilisent le titre plus une citation entière. Si celle-ci dépasse la taille autorisée, elle est omise en entier, sans couper sa réserve. Les propositions créatives restent soumises aux revues de fidélité, de langue, d'images et de distinction des trois angles ; cette réduction n'est pas une preuve générale de compréhension du modèle. Une relative ou réserve immédiatement suivante reste attachée à la citation lorsque la proximité et la taille le permettent, notamment « tous les bugs **que ça a détecté** ». Le mode `source_bound_v1` entre dans les preuves et les préalables du calendrier.

La recette a retrouvé un dossier LinkedIn resté sur le titre et le texte initiaux alors que le tableau montrait le packaging révisé. L'export local est maintenant versionné par le contenu contrôlé et sa fenêtre : manifeste, texte, vidéo et couverture doivent correspondre. Les anciennes versions restent intactes. Le calendrier vérifie aussi ces fichiers ; une modification du texte ou d'un média bloque le pack.

Un autre défaut empêchait le pack d'un passage révisé de remplacer son ancien enregistrement local archivé. Le remplacement est désormais permis exclusivement pour cet état local sans intention distante. Le test vérifie la nouvelle empreinte du média et confirme qu'un résultat publié muni d'un identifiant distant reste préservé.

La date conseillée est un champ local `proposed_at`. Elle reste distincte de `scheduled_at`, qui reste vide. L'embargo, la destination, la disponibilité conditionnelle et la fin de validité figurent dans le pack. Le surplus de contenus prêts est conservé sans augmenter la cadence pour le faire entrer avant le tournage.


## État conservé après arrêt des miniatures

Lou a demandé d'abandonner les essais de miniatures pour retravailler cette partie ultérieurement. Le worker et la revue déléguée sont arrêtés ; vingt tâches de miniatures en attente, actives ou bloquées ont été annulées avec leur motif précédent conservé dans l'événement d'arrêt. La file reste suspendue. Aucun média ni reçu n'est supprimé.

Les **31 fichiers vidéo** ont été décodés dans Edge à leurs deux extrémités, avec contrôle des dimensions et durées, sans erreur JavaScript ni requête de mutation. Les empreintes courantes correspondent à ce relevé. Le master est toujours inchangé. Après les dernières corrections de métadonnées, **28 revues automatiques courantes sont validées et trois restent à refaire** ; les fichiers vidéo eux-mêmes n'ont pas changé. Aucune écoute humaine n'est attestée.

La suite complète observée exécute **317 tests : 314 réussis, trois ignorés** pour PostgreSQL non configuré. Les six tests de politique du dépôt ont également réussi. Il n'y a pas eu de nouvelle exécution des essais de miniatures après la demande d'arrêt.

La prévision locale est **partielle** : 15 packs prêts, **huit dates proposées**, sept packs prêts hors capacité restante et 44 packs en attente de revue ou packaging. Ces dates restent conditionnelles et antérieures au prochain tournage ; `valid_for_publication=false`. Aucun envoi, brouillon distant ou programmation sociale : **zéro job dispatch, zéro identifiant distant, zéro scheduled_at**.

Preuves locales : `browser-media-evidence.json`, `full-tests-actual-final.txt` et `stop-evidence-7a5d0062f7bb6eecd48c.json` sous `.local/real-master-20261029/`. La recette navigateur complète des miniatures et d'un calendrier terminé n'a pas été exécutée. À ce point d'arrêt, aucun commit, push ou PR n'avait encore été demandé. Les limites de recette restent ouvertes dans #8 et #9.

Une revue indépendante explicite de deux bundles a été enregistrée avant l'arrêt. Elle conserve les refus du modèle et lie les six critères, les dix fichiers effectivement examinés, le master, le montage, le digest et le rapport à leurs empreintes. Elle ne modifie pas la revue audio ni le droit de publier. Une preuve modifiée, un mauvais montage, une inspection incomplète ou une intention distante bloque cette voie. Cette distinction reste visible entre contrôle automatique et revue indépendante.

## Vérifications pour la livraison Git autorisée

La demande suivante autorise commit, push et une PR regroupée (#34). Le lot a été rebasé sur `main` (`16df906`), en conservant les fonctions éditoriales, narratives et StoryTelling ajoutées depuis son démarrage. La résolution conserve l'animation de sous-titres existante hors bande locale ; la bande locale garde son texte fixe. La version de rendu passe à 3 pour distinguer ces paramètres dans le cache, sans relancer ni modifier les exports de l'épisode.

La suite Python après intégration exécute **427 tests : 424 réussis, trois ignorés** faute de PostgreSQL local, en 166,699 secondes (`full-tests-rebased.txt`). Après ajout du scénario couvrant la coexistence des sous-titres, les **17 tests média** passent aussi. Les **15 tests du dépôt**, dont sept sur le choix de compte GitHub demandé dans #35, et les **trois tests de politique du workflow** passent. La compilation Python, la syntaxe du script navigateur, l'aide CLI et la synchronisation des neuf skills sont contrôlées. Ces vérifications utilisent des fixtures synthétiques et ne reprennent pas les essais de miniatures du master.
