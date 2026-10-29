# Concevoir et vérifier les miniatures SANDBOX

Chaque miniature d'extrait YouTube développé se prépare avec son titre, le passage vidéo et son public. Trois concepts sont proposés avant validation. Chacun doit expliquer ce que le spectateur comprend d'abord, ce que la phrase apporte au titre et pourquoi l'image montre bien le propos.

Le [README de la factory](README.md) décrit le parcours complet. Ce guide précise le travail de conception et les contrôles qui bloquent une préparation insuffisante. Aucun export ni test décrit ici ne téléverse de fichier ou ne modifie une vidéo en ligne.

## Partir du contenu et de références observées

Le [relevé du 28 octobre 2026](references-miniatures-2026-10-28.md) examine treize miniatures de six chaînes : Underscore_, Latent Space, AI Engineer, The Pragmatic Engineer, Silicon Carne et Fireship. La sélection repose sur les sujets et formats proches de SANDBOX. Fireship sert de référence distincte pour un format plus court. Ce relevé ne constitue pas un palmarès des miniatures les plus efficaces.

Avant un nouvel extrait, choisir au moins six exemples sur trois chaînes, dont deux avec des formats comparables. Chercher des cas proches du sujet et quelques contre-exemples sobres. Examiner les images, les titres et leurs dates ; un résultat de recherche textuel ne suffit pas. Conserver les liens des vidéos et des images, la date du relevé, les observations de composition, ce qu'on retient et les limites de la comparaison. Le [relevé structuré](references-miniatures-2026-10-28.json) fournit les observations du premier corpus.

La configuration impose un relevé de moins de 90 jours. Ce délai sert de garde-fou interne ; il ne remplace pas la vérification de références adaptées au sujet de l'épisode. Une nouvelle annonce, un outil ou un public différent peuvent demander une recherche plus récente.

On peut observer un compteur de vues public. On ne peut pas en déduire le CTR, la rétention, un résultat de test ou l'effet causal de la miniature. Ne pas classer les images par vues brutes sans tenir compte de l'âge, du sujet, de l'audience et du format.

## Concevoir les trois couples titre/image

Définir d'abord le public, sa question et l'idée que l'extrait lui apporte. Relever les paroles exactes qui soutiennent la promesse, avec leurs secondes source, le contexte et les réserves à conserver. Le programme vérifie que les citations figurent dans la transcription et que les preuves se trouvent dans les coupes du montage livré.

Si la transcription ne donne qu'une plage large, conserver cette plage ou la préciser après écoute. Ne pas fabriquer un horodatage au mot : les bornes de la preuve doivent englober les segments de transcription cités.

Le relevé suggère plusieurs directions à examiner selon le contenu : une conséquence métier, une règle technique accompagnée d'une preuve, un exemple concret avec une réaction réelle, ou une présentation descriptive sobre. Choisir trois hypothèses pertinentes pour le passage. Changer la couleur ou déplacer le même titre ne crée pas trois concepts.

Pour chaque concept, préciser :

- Le titre de la vidéo et la phrase dans l'image, ou la raison de ne pas mettre de phrase.
- L'hypothèse : ce que cette présentation devrait mieux faire comprendre au public visé.
- Le choix des mots, leur intérêt et ce que l'image ajoute au titre. Lire les deux ensemble pour retirer les répétitions.
- L'image autorisée utilisée, le sujet important à préserver, le recadrage et les zones réservées au texte.
- Les références qui ont nourri la proposition, les preuves du passage et les risques de mauvaise interprétation.

Une phrase peut montrer une conséquence, poser une question ou préciser l'enjeu. Elle ne doit pas annoncer un résultat absent de l'extrait, transformer une réserve en certitude ou attribuer à quelqu'un une phrase qu'il n'a pas dite. Il n'existe pas de nombre de mots gagnant dans tous les cas : la phrase doit être utile et lisible aux tailles de contrôle.

Les images viennent du passage réellement monté ou de photos autorisées. Le moteur extrait lui-même les images vidéo aux secondes choisies et vérifie leur appartenance aux coupes. Pour une photo, conserver son empreinte, le sujet représenté et une preuve d'autorisation. Les visages des chaînes de référence, les faux intervenants et les fausses captures de logiciel n'entrent pas dans les créations SANDBOX.

## Composer, cadrer et comparer

La composition utilise la palette bleu nuit et cyan de SANDBOX. Le brief place explicitement l'image et le texte ; le moteur ne choisit pas une mise en page au hasard. Il conserve le sujet déclaré important dans le recadrage, sépare sa zone du texte et garde une réserve dans le coin inférieur droit pour les interfaces. Ces marges sont des choix de production internes.

Le texte s'adapte à sa zone sans coupure de mot ni débordement. Si la phrase ne tient pas dans une composition lisible, le rendu échoue : retravailler la phrase ou la composition. Agrandir un petit fichier source ne crée pas de détails ; l'audit indique l'agrandissement éventuel.

Chaque livraison contient trois JPEG, leurs aperçus à 320 et 160 pixels, une planche de comparaison avec les titres et le brief de conception. Lire aussi cette planche sur fond clair, puis les images sur fond sombre. Vérifier le premier élément identifié, les mots encore lisibles, les détails perdus et les ambiguïtés du couple titre/image.

Le défaut d'export est 3840 x 2160 en JPEG, avec un budget interne de 1,9 Mo par image pour faciliter les usages mobiles. Au 28 octobre, l'[aide YouTube](https://support.google.com/youtube/answer/72431?hl=en-GB) recommande cette définition pour les vidéos, distingue 16:9 vidéo, 9:16 Short et 1:1 playlist podcast, et annonce des limites différentes selon le mode d'envoi. La [Data API](https://developers.google.com/youtube/data/reference/rest/v3/thumbnails/set) indique 50 Mo pour `thumbnails.set`. Le budget de la factory ne constitue donc pas une limite universelle de YouTube. Toutes les variantes d'un test doivent avoir une définition cohérente ; les contrôles locaux refusent une sortie sous 1280 x 720.

## Faire une revue croisée avant de valider

La personne ou l'agent qui a conçu le brief ne valide pas seul ses propositions. Le second lecteur reçoit le passage, la transcription, les preuves, les trois images et les aperçus. Il regarde les fichiers et consigne une revue pour chaque concept, avec ses objections et les corrections nécessaires. Un nom de relecteur dans un JSON ne prouve pas qu'il a fait cet examen.

Les six contrôles sont : fidélité au contenu, complémentarité titre/image, lisibilité mobile, composition, charte et droits, différence des hypothèses. Le choix initial est une proposition éditoriale argumentée. Aucun gagnant de performance n'est déclaré à ce stade.

Le programme exige une attestation distincte liée au contenu exact des images, du brief et du packaging. Il vérifie leurs empreintes avant planification et juste avant envoi simulé. Changer le titre, le texte, le concept choisi ou un fichier invalide la revue. Une revue vidéo réussie ne valide pas les miniatures. Une miniature non conforme bloque sa publication, tout en laissant les autres contenus avancer.

Si une expérience est active, la préparation s'arrête avant d'écrire de nouveaux packs. Les fichiers précédents sont conservés. Après restauration portable, les chemins peuvent changer ; les empreintes, identifiants et contrôles liés au contenu restent vérifiables.

## Adapter les couvertures aux autres formats

Pour un Short ou un extrait vertical, conserver la même exigence de fidélité et de lisibilité, en vérifiant le cadrage dans le lecteur et dans la grille du profil. Une couverture verticale, une première image et une miniature importée restent des objets différents. Le choix dépend de ce que permet réellement la plateforme et le compte.

L'aide YouTube consultée mentionne l'import de miniatures de Shorts depuis Studio sur ordinateur pour les comptes éligibles. Cela ne prouve pas une capacité équivalente de notre API. Les tests A/B de cette aide excluent les Shorts. Instagram, TikTok et X demandent aussi un contrôle de leurs fonctions de couverture avant d'annoncer leur automatisation. Le moteur décrit ici produit et impose les trois concepts pour les extraits YouTube horizontaux ; il ne prétend pas automatiser toutes ces opérations natives.

## Commandes et contrat pour Codex

Le parcours manuel utilise un brief préparé par Codex ou l'équipe. Le parcours d'[autonomie locale](autonomie-locale.md) peut aussi préparer le brief, choisir un cadrage dans le master et relire les vrais rendus avec deux modèles locaux distincts. Le corpus de chaînes reste un relevé daté : le worker ne parcourt pas automatiquement les chaînes pour le renouveler. Une revue automatique porte explicitement cette mention et ne constitue pas une attestation humaine.

Utiliser `$sandbox-packaging` pour préparer le brief. Le JSON attendu par `thumbnails.py` contient :

| Partie | Champs principaux |
| --- | --- |
| Identité | `version=1`, `episode_id`, `segment_id`, `asset_sha256`, `source_sha256`, `created_by` |
| Intention | `audience`, `viewer_question`, `content_promise`, `essential_nuance` |
| Relevé | `benchmark.references`, avec URLs, dates, observations, limites et inspection visuelle attestée |
| Preuves | `content_evidence`, avec identifiant, citation, contexte, promesse soutenue et secondes source |
| Concepts | Trois objets `concepts`, avec titre, phrase, raisons, hypothèse, références et preuves citées |
| Composition | Pour chaque concept : `image`, `image_box`, `text_box` |
| Choix initial | `preferred_concept_id`, `selection_reason` |

`image.kind=episode_frame` prend `source_time_seconds`. `authorized_photo` prend `path`, `sha256`, `rights_evidence` et `subject_identity`. Les deux demandent `crop` et `focus_box`, rectangles `[x,y,largeur,hauteur]` normalisés entre 0 et 1. Les rectangles `image_box` et `text_box` s'expriment sur un canevas de travail de 1280 x 720, indépendamment de la définition d'export.

Les références portent `reference_id`, `channel`, `video_url`, `thumbnail_url`, `observed_at`, `format`, `selection_reason`, `visual_observation`, `title_image_relation`, `takeaway`, `limitations`, `visually_inspected=true` et `comparable_format`. Les concepts citent leurs `reference_ids` et `evidence_ids`. Le relevé JSON fournit les références examinées ; choisir celles qui servent réellement le passage.

Depuis la racine, avec l'environnement Python et `PYTHONPATH` préparés selon [l'exploitation](exploitation.md), remplacer les variables par la publication et le brief réels :

```powershell
& $python -m youtube_growth.factory thumbnails $publicationId --brief $briefPath
& $python -m youtube_growth.factory review-thumbnails $publicationId --reviewer $reviewer --evidence $reviewEvidence --checks content_fidelity title_image_complementarity mobile_readability composition brand_rights distinct_hypotheses
& $python -m youtube_growth.factory plan $episodeId
```

Les commandes de revue enregistrent l'examen effectué ; elles ne doivent pas servir à passer une revue manquante. Les sorties restent sous `episodes/EPISODE/thumbnails/` dans la base choisie. Le tableau montre les trois couples titre/image, leurs aperçus et les raisons du choix.

## Mesurer ensuite sur les contenus autorisés

Selon l'[aide officielle des tests YouTube](https://support.google.com/youtube/answer/16391400?hl=en-GB), Studio permet de comparer jusqu'à trois titres, miniatures ou combinaisons sur des vidéos éligibles. Le résultat se fonde sur le temps regardé et peut rester non concluant. Modifier le titre ou la miniature pendant le test l'arrête. Préserver les tests existants ; leur fin ne dépend pas de la fermeture du calendrier de nouveaux posts.

Si titre et miniature changent ensemble, le résultat porte sur la combinaison. Ne pas attribuer séparément le gain à une phrase ou à un portrait. Le CTR peut compléter l'analyse lorsqu'il est accessible, avec la durée regardée, la fidélité de la promesse et l'intérêt du public visé. Une rotation à des dates différentes reste une comparaison observationnelle.

La simulation actuelle ne lance aucun test Studio et ne produit aucune mesure réelle. Le brief, les images, leurs hypothèses, la revue et les résultats ultérieurs restent reliés pour que le cycle suivant puisse reprendre une décision documentée.
