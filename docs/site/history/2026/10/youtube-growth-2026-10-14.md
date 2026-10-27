# Première livraison du YouTube Growth Agent

Le 14 octobre 2026, l'accès Studio à Sandbox Podcast a été vérifié sur `UCuATIBXo5uvNLVm-gCgMenA`. OAuth pour le programme reste absent. Les opérations de cette session utilisent l'interface officielle, sans extraction de cookies ni appel privé.

## Relevé initial

L'[émission 1](https://www.youtube.com/watch?v=GgSiPkADCz4), publiée le 12 octobre, dure 1 h 18 min 21 s dans le lecteur public. La copie officielle mesure 4701,553 secondes, en 1280 x 720, 24 images/s. Lou ne détient pas le master; le téléchargement propriétaire a fourni la source autorisée.

La page publique affichait 11 abonnés, 117 vues et 9 likes au premier relevé. Studio affichait ensuite 119 vues dans les contenus, 116 dans Analytics et 130 en temps réel sur 48 h. Ces compteurs ne sont pas fusionnés.

Relevé Studio "Depuis la publication" :

| Mesure                      | Valeur observée                     |
| --------------------------- | ----------------------------------- |
| Impressions de miniatures   | 403                                 |
| CTR de miniature            | 3,5 %                               |
| Durée de visionnage         | 9,6 heures                          |
| Durée moyenne d'une vue     | 5 min 57 s                          |
| Pourcentage moyen regardé   | 7,6 %                               |
| Abonnés attribués           | +4                                  |
| Spectateurs présents à 30 s | 30 %                                |
| Spectateurs uniques         | 17, deux jours encore en traitement |

La carte de conversion des impressions porte sur le 12 et le 13 octobre : 277 impressions, 4,3 % de CTR, 12 vues engagées et 1,23 heure. Sa période diffère des indicateurs principaux.

Trafic depuis la publication : navigation 51,5 %, direct ou inconnu 19,2 %, suggestions 10,8 %, externe 9,2 %, autres fonctionnalités 3,9 %, autres 5,4 %. La recherche YouTube apparaît à 2,3 % sur sa propre carte; ses termes détaillés sont indisponibles faute de trafic suffisant. Aucune conversion Short vers émission n'est mesurée.

La description contient déjà 17 chapitres et des sources. Le site a déjà `/episodes/1`, les ressources et les liens temporels. L'identité existante est conservée. Aucun format gagnant n'est démontré par ces 403 impressions et cette unique émission.

La description publique de la chaîne présente déjà le média, l'IA, le développement et l'open source. Le lien officiel vers le site est présent. La page publique ne présente que l'onglet Vidéos au relevé; les sections d'accueil restent à configurer après la création de la playlist podcast et la publication d'extraits.

## Passages sélectionnés

Huit candidats sont sourcés dans `tools/youtube-growth/episodes/GgSiPkADCz4.json`. Quatre sont retenus :

| Sujet                          | Passage source    | Durée |
| ------------------------------ | ----------------- | ----- |
| Développeurs et Product Owners | 20:33 à 21:02     | 29 s  |
| L'IA utilisée comme Google     | 24:25 à 25:10     | 45 s  |
| Harnais officiel ou OpenCode   | 44:29 à 45:16     | 47 s  |
| Vibe coder un jeu amusant      | 1:12:07 à 1:12:51 | 44 s  |

Le parcours natif a créé un [extrait horizontal privé](https://studio.youtube.com/video/0iDaiHjAILk/edit). "Nouveau Short" était désactivé. La copie officielle a ensuite servi aux quatre versions verticales, avec sous-titres et cadrages choisis après inspection. Les rendus ont été sondés et décodés intégralement. Les sous-titres automatiques restent à valider à l'écoute.

Calendrier proposé : 15, 17, 19 et 22 octobre, 17 h à Paris. Une proposition de date ne vaut pas programmation YouTube. Les données, sauvegardes et preuves restent dans `.local/youtube-growth/GgSiPkADCz4/`, ignoré par Git. La source et les photos d'origine ne sont pas écrasées.

## Développement

Les quatre Shorts ont été téléversés et vérifiés dans l'onglet Shorts de Studio, avec le statut privé :

- [Développeurs et Product Owners](https://studio.youtube.com/video/WKrosj0Si5g/edit).
- [L'IA utilisée comme Google](https://studio.youtube.com/video/vi4xR8h1FyQ/edit).
- [Codex ou OpenCode](https://studio.youtube.com/video/jklcnMBP8VU/edit).
- [Vibe coder un jeu](https://studio.youtube.com/video/F2HLJYO6ykQ/edit).

La fonction "Vidéo similaire" relie chacun des quatre Shorts à `GgSiPkADCz4`. Aucun n'est programmé ni public. Les identifiants distants sont conservés dans les manifestes locaux. Le rendu refuse désormais de remplacer un dossier contenant un upload connu ou incertain.

Trois concepts de miniatures sont conservés dans le dossier local `thumbnails/`, en PNG et en JPEG 1280 x 720 de moins de 2 Mo. Ils utilisent les portraits existants comme références. Le premier concept a été corrigé pour retirer un casque ajouté à Lou. La génération native `image_gen` a été utilisée; aucun fournisseur d'images permanent n'est configuré pour l'agent.

Après accord explicite de Lou le 14 octobre, la description est enregistrée et le test natif est en cours : présentation actuelle comme témoin, concept harnais et concept jeux. Studio affiche les trois variantes, leurs parts de durée de visionnage encore indisponibles et un temps restant estimé de treize jours et vingt-trois heures au lancement. Le troisième concept généré, sur l'équipe, reste en réserve. Aucun gagnant n'est désigné.

La [playlist publique SANDBOX : Émissions complètes](https://www.youtube.com/playlist?list=PLdOmyyxmWRJA) est créée avec le statut Podcast, une couverture issue de l'avatar officiel, une description française et uniquement l'émission 1. Ce statut et le contenu sont vérifiés dans Studio et sur la page publique. L'indexation dans YouTube Music n'est pas vérifiée.

Le [commentaire de débat](https://www.youtube.com/watch?v=GgSiPkADCz4&lc=UgwrZzSE-Q4G3qIVJxV4AaABAg) est publié sous `@SandboxFR`, puis épinglé. Il oppose harnais officiel et outil multi-modèles et renvoie au débat à 37:17. Le badge "Épinglé par @SandboxFR" est vérifié. Le commentaire préexistant sur les sujets du prochain épisode est conservé.

Le contrôle d'approbation avait initialement refusé l'enregistrement public. Lou a ensuite validé les quatre changements : description, test, podcast et commentaire. Le journal `public-actions.json` conserve les liens et statuts confirmés, avec les sauvegardes de description et les captures dans `proof/`. Les Shorts restent privés, conformément à cet accord.

Modules d'identité, audit Data/Analytics, journal SQLite, plans/restauration, sélection horodatée sans master, calendrier et rendu. Le pipeline historique reçoit un verrou, une validation liée aux rendus et un blocage après upload incertain. Le polling GitHub reste en lecture seule jusqu'à une persistance distante fiable.

OAuth, la collecte API réelle et les traitements permanents ne sont pas activés. Diarisation automatique, génération récurrente de miniatures et apprentissage statistique ne sont pas implémentés. Aucun résultat A/B n'est fabriqué.

L'environnement virtuel `tools/youtube-growth/.venv` est installé avec les dépendances déclarées. Le diagnostic confirme les bibliothèques Google, Pillow, requests, FFmpeg et ffprobe. `pip check` ne trouve pas de dépendance incohérente. Cinq requêtes sont construites avec les schémas locaux du client Google, sans appel réseau; cela ne valide pas les permissions ni la collecte. Le jeton OAuth reste absent.

Prettier exclut ce dossier de dépendances locales, comme `node_modules`. Les sources, tests et configurations de l'agent restent dans le périmètre des contrôles.

Deux comparaisons publiques ont été relevées dans les suggestions : [DevArt](https://www.youtube.com/watch?v=-fuUWNA8N0Y), test Mistral, 28 minutes, environ 19 k vues, quatre jours après publication; [Le Podcast IA](https://www.youtube.com/watch?v=Qna3BEkub38), entretien avec Le Dev Ultime, 2 h 01, environ 6,2 k vues, quatre jours après publication. Ces deux observations ne constituent pas un benchmark complet ni une preuve de conversion. Hooks, cadence et performances relatives restent à étudier sur plusieurs vidéos par chaîne.

## Benchmark complémentaire

Relevés directs dans YouTube le 14 octobre. Les vues et âges sont arrondis par l'interface; certains titres internationaux sont affichés en traduction française. Les captures et relevés sont conservés dans le dossier local `benchmark/`. Les comptes historiques ont une audience très différente de SANDBOX; leurs vues ne deviennent pas nos objectifs.

| Chaîne                                                               | Échantillon observé                                                                                                                                                                                                                                                                    | Présentation et organisation                                                                                                                                                                           |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Fireship](https://www.youtube.com/@Fireship/videos)                 | Trois dernières vidéos : 5:56, 6:10, 5:46; 2,7 M, 1,4 M, 2,4 M vues; un, six et huit jours. Six publications visibles sur environ deux semaines.                                                                                                                                       | Sujet unique dans le titre; contraste entre quelques mots et une figure reconnaissable. Onglets Shorts, Émissions, Cours et Playlists.                                                                 |
| [Underscore_](https://www.youtube.com/@Underscore_/videos)           | Trois dernières conversations : 33, 32 et 40 minutes; 701 k, 766 k, 607 k vues; deux, trois et quatre semaines. Une [conversation sur le travail des développeurs](https://www.youtube.com/watch?v=AiytemqB_F0) affiche 1,4 M vues pour 39 minutes, environ un mois après publication. | Expérience ou tension concrète dans le titre; peu de mots sur la miniature; personne ou objet central. Onglets Shorts et Podcasts.                                                                     |
| [Lenny's Podcast](https://www.youtube.com/@LennysPodcast/videos)     | Trois dernières vidéos : 1 h 02, 37 et 28 minutes; 45 k, 136 k, 35 k vues; deux jours, neuf jours et deux semaines. Plusieurs conférences courtes publiées dans un même lot.                                                                                                           | Portraits et texte contrasté sur fond clair. Formats longs et conférences coexistent; Podcasts et Playlists séparés des Shorts. Le lot de conférences ne permet pas de déduire une cadence habituelle. |
| [AI Explained](https://www.youtube.com/@aiexplained-official/videos) | Trois dernières analyses : 31, 38 et 32 minutes; 117 k, 280 k, 303 k vues; un jour, douze jours et deux semaines.                                                                                                                                                                      | Un enjeu par vidéo; miniatures blanches, texte noir, personnes liées au sujet. Podcasts et Playlists visibles; aucun onglet Shorts au relevé.                                                          |

Le [Short de Lenny sur les agents et Internet](https://www.youtube.com/shorts/aryWqheMmSI), affiché à 3,1 k vues dans la grille, montre un intervenant en gros plan et des sous-titres. Il possède un lien natif vers son [entretien source](https://www.youtube.com/watch?v=MM-C3JqCXBk). Ce parcours est observé; son taux de conversion reste privé. Les trois premiers Shorts de sa grille affichent 3,1 k, 2,8 k et 8 k vues, loin des compteurs de ses entretiens. Le nombre de vues d'un Short ne prouve donc pas, à lui seul, la réussite de la distribution d'un épisode.

Les hypothèses retenues pour SANDBOX sont une promesse précise par titre, une idée complémentaire par miniature et un lien natif vers la discussion complète. Les quatre Shorts privés appliquent déjà ce dernier point. Le test lancé compare deux angles éditoriaux à la présentation actuelle. Aucun CTR, taux de conversion ou hook gagnant concurrent n'est prétendu connu. La transcription du début de la vidéo Underscore_ sélectionnée n'était pas disponible dans l'export officiel; ses premières phrases ne sont pas analysées.

## Priorités sur trente jours

| Priorité | Action                                                                                                                            | Contrôle du résultat                                                                                                     |
| -------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1        | Corriger à l'écoute les quatre Shorts, valider les limites et le cadrage, puis programmer deux à quatre publications par semaine. | Zéro sous-titre connu comme erroné, zéro doublon, vidéo source associée; relevé à 48 h et sept jours.                    |
| 1        | Suivre le test natif lancé le 14 octobre; la description est enregistrée.                                                         | Résultat Studio et part de temps de visionnage; attendre la conclusion native, sans désigner de gagnant sur le seul CTR. |
| 1        | Commencer la prochaine émission par un passage ou une question qui expose son intérêt.                                            | Comparer la rétention à 30 s au relevé initial de 30 %, en tenant compte du volume et de l'origine du trafic.            |
| 2        | Compléter l'accueil autour de la playlist podcast créée et des extraits lorsqu'ils seront publics.                                | Accès public, contenu réel et liens vérifiés.                                                                            |
| 2        | Configurer OAuth et la persistance avant toute publication automatique.                                                           | Identité correcte, collecte réelle, reprise après interruption et absence de doublon.                                    |
| 2        | Suivre les réponses au commentaire épinglé et finaliser les posts Communauté préparés.                                            | Réponses utiles, questions pour l'émission suivante; aucun engagement artificiel.                                        |

Trois brouillons Communauté, avec leurs sources et visuels existants, sont préparés dans `community-drafts.json` du dossier local. Ils ne sont ni publiés ni planifiés. L'annonce de la prochaine émission attend ses sujets et sa date réelle.

## Suite

Validation exécutée : 47 tests Python réussis, compilation Python réussie, 341 tests du site réussis et contrôle TypeScript réussi. `pnpm check` échoue sur le format de 149 fichiers préexistants; ESLint lancé séparément épuise le heap Node par défaut. Les quatre nouveaux fichiers Markdown/JSON contrôlés passent Prettier; les trois documents rédigés passent le vérificateur de caractères. Les fichiers vidéo ont tous été décodés intégralement après le dernier rendu. Le contrôle global n'est pas déclaré réussi.

Contrôler les quatre brouillons privés, corriger les sous-titres et programmer le lot après validation initiale. Configurer OAuth et un journal distant durable, puis la collecte planifiée. Aucune automatisation permanente nouvelle n'est active; le workflow préexistant ne prouve pas son activation ni sa connexion. Le programme conserve une CLI de contrôle local.

Mise à jour du 14 octobre : quatre nouvelles versions verticales ont été rendues depuis la copie officielle, avec les corrections de transcription évidentes (« cahiers des charges », « IA », « OpenAI », « harnais ») et décodées intégralement. Les corrections s'appuient sur la transcription automatique et le contexte; l'écoute audio n'a pas pu être confirmée. Elles n'ont pas été téléversées. Le calendrier proposé reste le 15, 17, 19 et 22 octobre à 17 h, heure de Paris. La session actuelle ne fournit aucun navigateur pour Studio et le jeton OAuth local est absent : aucune date n'a donc été enregistrée dans YouTube, et les quatre versions déjà téléversées restent privées. Le détail des fichiers, empreintes et créneaux préparés est dans `.local/youtube-growth/GgSiPkADCz4/schedule-plan-2026-10-14.json` et `shorts-revision-20261014/`.
