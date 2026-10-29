# La factory SANDBOX, côté équipe

La factory prépare les contenus issus d'une émission : extraits, sous-titres, titres, miniatures, textes par réseau, calendrier et bilan. Lou, Nico et Loïc peuvent demander ce travail à Codex, puis consulter les fichiers et leur avancement dans une interface locale.

Aujourd'hui, le programme traite les médias sur l'ordinateur et simule le calendrier. Aucun fichier ni texte ne part vers les réseaux, y compris en privé, en brouillon ou en programmation. LinkedIn reçoit toujours un pack à publier manuellement.

Les [commandes et l'installation](exploitation.md) sont dans le guide technique. Ce README explique le parcours d'une émission et les décisions à prendre en équipe.

Le [guide d'optimisation](optimisation.md) décrit ce que la factory réutilise, ce qu'elle mesure et comment préparer les décisions du prochain épisode. Demande à Codex le `brief` de l'épisode pour retrouver les résultats disponibles, les preuves manquantes et les références à réexaminer.

Le [parcours éditorial multiformat](production-editoriale.md) ajoute la découverte de sujets, leur évaluation justifiée, les dossiers de recherche, les vidéos narratives originales et les comparaisons Analytics. La configuration livrée attend les réponses d'un agent ou un modèle local à configurer ; elle ne lance aucun appel IA payant. La première bibliothèque de schémas animés est décrite dans la [direction artistique narrative](direction-artistique-narrative.md).

## Ce qu'il faut donner pour une émission

Fournis le master vidéo terminé, la transcription horodatée si elle existe, le titre et le numéro de l'épisode. Indique la sortie prévue, l'URL de l'émission complète lorsqu'elle est connue, et la date et l'heure exactes du prochain tournage, en Europe/Paris.

Précise les intervenants identifiés, les sujets à vérifier et les assets autorisés. Un lien YouTube seul ne fournit pas le master au moteur de montage. Si une information manque, les étapes indépendantes continuent : l'analyse locale peut commencer avant la création de l'URL YouTube.

Le calendrier attend une preuve de disponibilité effective de l'émission à la bonne adresse. Toutes les nouvelles publications doivent se terminer avant le prochain tournage, avec une marge de traitement. En cas de sortie tardive, le calendrier se resserre sans déplacer cette borne finale.

## Comment se déroule le travail

| Étape | Ce que tu retrouves | Ce qu'il faut examiner |
| --- | --- | --- |
| Réception du master | Un épisode reconnu, son fichier et son empreinte | La copie est terminée et correspond au bon épisode. |
| Analyse | Transcription disponible, sujets, repères et couverture des images et du son | Les zones non examinées et les affirmations à vérifier restent visibles. |
| Sélection | Passages retenus, à retravailler, rejetés ou archivés, avec leurs motifs | Chaque extrait contient une idée utile et conserve le contexte et les réserves. |
| Montage | Vidéos courtes ou développées, sous-titres et correspondance des coupes | Les paroles, le cadrage, les écrans de démonstration et les sous-titres restent compréhensibles. |
| Présentation | Titres, miniatures, textes et destination par réseau | La promesse correspond au contenu et les variantes ont des hypothèses différentes. |
| Calendrier | Créneaux proposés, contenus bloqués et surplus archivé | L'émission est disponible, les contenus sont contrôlés et la fenêtre reste valable. |
| Bilan | État des sorties, mesures disponibles, expériences et décisions | Les données manquantes et les résultats non concluants restent signalés. |

Le programme découpe les médias, prépare les exports et sous-titres, contrôle les fichiers et mémorise l'avancement. Il reprend les travaux admissibles après interruption et réutilise les médias compatibles quand seul le titre change.

Le choix d'un angle, la fidélité d'une coupe et la lisibilité d'une démonstration demandent un jugement éditorial. Codex peut aider à les examiner et consigner ses preuves. Aucun modèle n'est actuellement configuré en arrière-plan pour comprendre seul une nouvelle émission : le programme attend les éléments d'analyse et de sélection. Un contrôle technique réussi ne prouve pas une écoute ou un visionnage attentif.

Il n'y a pas de nombre d'extraits à atteindre. Un bon passage peut servir un seul réseau ; chaque variante doit apporter quelque chose à son public.

## Lire le tableau de bord

Demande à Codex d'ouvrir l'interface locale, généralement à [127.0.0.1:8765](http://127.0.0.1:8765). Le parcours en haut indique les étapes : analyser, choisir les passages, monter les vidéos et préparer les sorties. Le bloc "Prochaine étape" explique ce qui reste à faire et donne accès à la vue utile. Le dossier de travail reste accessible sous "Emplacement des fichiers" ; les données fictives portent la mention "Démonstration".

Dans "Passages et vidéos", chaque passage proposé affiche ses horaires, sa durée, son intérêt et le public visé. Le lien YouTube ouvre le passage au bon moment dans un nouvel onglet. Les réserves restent sous "À vérifier avant de retenir ce passage". Demande à Codex les décisions de sélection et les montages dans le chat ; consulter une fiche ne valide pas son contenu.

Les vues "Publications", "Miniatures", "Activité" et "Résultats" donnent accès aux autres étapes. Si aucune publication n'est préparée, la page explique ce qui manque et renvoie aux passages proposés. Dans "Publications", filtre par réseau et par état, puis recherche un titre. Les filtres et la vue restent dans l'adresse du navigateur. "Copier le texte" prépare le texte pour une utilisation manuelle.

"Mettre à jour" relit l'avancement. La mise à jour automatique se fait toutes les quinze secondes lorsque l'onglet est visible ; tu peux la désactiver. Une vidéo en lecture et les détails ouverts restent en place. Le journal des traitements montre les événements récents. "Télécharger le diagnostic technique" fournit l'état de l'épisode et du réseau sélectionnés, avec les chemins locaux et les contenus éditoriaux. Cet export ne remplace pas la sauvegarde des médias.

Dans "Options de suivi", "Suspendre les traitements" arrête le démarrage de nouveaux travaux en conservant les fichiers et l'historique. "Reprendre les traitements" relance les travaux prêts. Les traitements en cours continuent. Dans "Activité", "Reprendre ce traitement" cible une erreur isolée. Une tentative au résultat inconnu exige d'abord une vérification de son état.

Le tableau lit un espace de suivi, appelé base, choisi à son lancement. La même adresse peut montrer une recette ou le travail opérationnel selon la session ouverte :

| Base locale | Usage | Comment interpréter ce qu'elle montre |
| --- | --- | --- |
| `.local/factory` | Travail opérationnel, avec le worker Windows installé | Les nouveaux épisodes réels pourront y être préparés. Les envois restent simulés. |
| `.local/factory-recette-20261028` | Recette du 28 octobre | Mire, son, identifiants et résultats synthétiques. Les comptes `simulation:*` ne désignent aucun compte social réel. |
| `.local/factory-miniatures-validation-v2` | Recette des miniatures du 28 octobre | Même type de source synthétique, trois concepts et leurs aperçus. Les images vérifient le moteur ; elles ne sont pas des propositions éditoriales pour un épisode. |
| `.local/factory-demo` | Démonstration créée par la commande `demo` | Exemple synthétique séparé du travail opérationnel. |

Vérifie la base affichée à l'ouverture du tableau et demande à Codex de vérifier les comptes configurés si nécessaire. Un identifiant de chaîne configuré ne prouve pas sa connexion. L'état "Simulation terminée" et un identifiant `sim:` décrivent un scénario local ; les chiffres de recette ne sont pas des performances Sandbox.

## Comprendre les états

Le tableau traduit les états en français. Les codes ci-dessous restent dans les diagnostics et les fichiers pour identifier précisément une situation.

| Code de suivi | Ce qu'il signifie | Suite à donner |
| --- | --- | --- |
| `needs_review` | Le rendu attend sa revue audiovisuelle ou éditoriale. | Regarder, écouter et consigner les contrôles du fichier exact. |
| `ready` | Le média ou son texte est préparé. | Lire aussi la colonne des contrôles : cet état seul ne certifie pas la revue. |
| `scheduled` | Un créneau est enregistré dans le calendrier local. | Il reste soumis à la validité de la fenêtre et des contrôles. Aujourd'hui, l'envoi est simulé. |
| `simulated` | L'opération simulée est terminée. | Aucune publication distante n'en découle. |
| `manual_ready` | Le pack LinkedIn est prêt pour une action manuelle. | Respecter la date conseillée, l'embargo et la fin de validité. |
| `manual_confirmed` | Une publication LinkedIn a été confirmée séparément par son URL et sa preuve. | Suivre les résultats accessibles ; cette confirmation ne déclenche aucun envoi. |
| `blocked` | Une condition manque ou un contrôle interdit l'étape. | Lire le motif, corriger la cause, puis reprendre le travail concerné. |
| `failed` ou `error` | Un traitement a échoué. | Consulter l'erreur et demander une reprise ciblée après correction. |
| `unknown` | Le résultat d'une tentative ne peut pas être établi. | Vérifier et rapprocher l'état avant toute nouvelle tentative. |
| `archived` ou `expired` | Le contenu a été écarté ou sa fenêtre est terminée. | Conserver le motif. Aucun report automatique sur la semaine suivante. |

Dans la partie "Traitements", `queued`, `running` et `completed` décrivent le travail informatique : en attente, en cours ou terminé. Un traitement `completed` ne signifie pas qu'un contenu est publié ou validé éditorialement. Consulte toujours l'état de la vidéo et celui de la publication.

## Préparer des miniatures qui défendent un angle

Pour chaque extrait développé à comparer, Codex doit analyser le sujet et des chaînes qui s'adressent à un public et à des formats comparables. Il relève les vidéos et dates examinées, leur promesse, le texte, le cadrage et le rapport titre/image. Il en tire des hypothèses : une miniature visible ne révèle pas son CTR ni la raison de ses résultats.

La préparation doit ensuite proposer trois hypothèses de titre et d'image distinctes. Chacune change l'angle ou ce que l'image aide à comprendre. Pour chacune, conserver :

- L'idée que le spectateur doit comprendre et les paroles ou timecodes qui la justifient.
- Le rôle du titre et celui du texte dans l'image, avec une raison pour chaque mot conservé.
- La composition : personne ou élément montré, choix de l'image source, expression réelle, cadrage, contraste et ordre de lecture.
- Ce qui doit différencier cette variante des autres et le risque de mauvaise interprétation.

Visages, gestes et écrans viennent des vrais médias autorisés. La composition suit la charte Sandbox et respecte la démonstration. Une image peut demander peu de texte ; il faut expliquer ce que ces mots ajoutent au titre.

Le moteur livre les propositions, une planche avec leurs titres et des aperçus à 320 et 160 pixels de largeur. Vérifier à ces tailles les mots lisibles, le premier élément identifié et les détails perdus. Confier la revue à un autre lecteur ou agent, avec le contenu source et le brief. Il examine fidélité, compréhension, texte, composition et différence entre variantes, puis demande de retravailler ou rejeter les propositions insuffisantes. La revue de la vidéo et celle des miniatures sont deux contrôles séparés.

Un extrait YouTube développé reste bloqué à la planification si ses trois concepts ou sa revue manquent. Changer le titre, le texte ou une image impose une nouvelle vérification. Le tableau présente les couples titre/image et les raisons de leur préparation. Demande à Codex d'appliquer `$sandbox-packaging` pour préparer ou reprendre cette étape.

Cette section fixe la procédure de préparation et de revue. Le [guide des miniatures](miniatures.md) décrit le moteur livré, ses entrées, ses commandes et les contrôles effectivement disponibles. Un test natif dans Studio ne vient qu'ensuite, pour une vidéo et un compte éligibles. Sa disponibilité dans Studio ne prouve pas une API de test. Les expériences déjà actives restent protégées ; on accepte un résultat non concluant et aucune garantie de CTR n'est annoncée.

## Quand une étape bloque

Un master absent ou encore en copie bloque le montage définitif. Une transcription ou une preuve manquante bloque les conclusions concernées. L'URL de l'émission et le prochain tournage sont nécessaires à la diffusion. Les autres étapes et les bons contenus du même épisode peuvent continuer.

Donne à Codex le motif affiché, l'épisode et le contenu concerné pour une correction ciblée. Pour `unknown`, établir ce qui s'est passé avant de réessayer. Pour `expired`, le délai est passé : aucun rattrapage en rafale.

Le worker installé continue sans conversation Codex, tant que la machine est active et la session Windows ouverte. Le tableau indique son dernier passage. S'il paraît arrêté, demande à Codex de vérifier le worker et la file. Le [guide d'exploitation](exploitation.md#pilotage-et-runtime) couvre le redémarrage, la sauvegarde et les reprises.

Un passage de plus de trois minutes invite à vérifier le worker et les traitements en cours. Il ne suffit pas à conclure que le processus est arrêté. Une horloge de recette est affichée séparément : elle ne prouve pas l'activité du worker Windows.

## Où retrouver les sorties

Les vidéos, masters propres, sous-titres, preuves d'analyse et packs sont rangés sous `episodes/IDENTIFIANT/` dans la base locale utilisée. Les bilans sont dans son dossier `reports/`. Le tableau donne les aperçus et chemins utiles ; Codex peut ouvrir le dossier du contenu demandé. Conserve le master original et les sauvegardes dans leur stockage durable.

Le pack LinkedIn contient la vidéo, le texte à copier, le lien et les dates à respecter. "Pack prêt" et "publication confirmée" restent deux étapes différentes. Pour YouTube, les actions natives telles que vidéo associée, écran de fin ou test de titres et miniatures restent indiquées séparément selon les capacités disponibles.

## Un brief à donner à Codex

Remplace les informations entre crochets avant de l'utiliser :

```text
Utilise $sandbox-factory pour préparer notre émission [titre et numéro].
Le master terminé est [chemin]. La transcription disponible est [chemin ou absente].
La sortie est prévue [date et heure Europe/Paris]. L'émission complète est à [URL ou en attente] ; sa disponibilité effective reste à vérifier.
Le prochain tournage est [date et heure Europe/Paris].

Analyse l'émission disponible et signale précisément les zones que tu n'as pas pu examiner. Propose les passages qui apportent quelque chose à notre public, sans quota, puis produis les formats utiles en conservant le sens et les réserves.
Pour les extraits développés, applique la procédure de miniatures : recherche de chaînes pertinentes, trois concepts titre/image, arguments et preuves du contenu, aperçus à 320 et 160 pixels, planche de comparaison et revue croisée.
Prépare les textes, le pack LinkedIn manuel et le calendrier avant le prochain tournage. Garde toute diffusion en simulation.
Ouvre le tableau de la base utilisée, explique les blocages et indique ce qui attend encore une revue humaine ou un accès.
```

La [validation du 28 octobre](validation-2026-10-28.md) détaille les preuves de fonctionnement et leurs limites. La [matrice des plateformes](capacites.md) indique les intégrations et fonctions restant à vérifier avant une activation réelle.

L'[audit et le rework](audit-rework-2026-10-28.md) décrivent les corrections de reprise, de sélection, de sauvegarde et de pilotage apportées après cette première livraison.
