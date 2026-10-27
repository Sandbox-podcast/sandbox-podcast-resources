# Générer les formats d'un nouvel épisode Sandbox

Nico et Loïc peuvent utiliser ce système pour chaque prochaine émission : produire des Shorts adaptés à YouTube, TikTok, Instagram et X, ainsi que des vidéos YouTube thématiques de 5 à 15 minutes. Le master, les transcriptions et les rendus restent locaux. Les sources E02 servent uniquement de référence de montage.

## Sommaire

- [Installer le système](#installer-le-système)
- [Préparer un nouvel épisode](#préparer-un-nouvel-épisode)
- [Choisir les passages et les variantes par réseau](#choisir-les-passages-et-les-variantes-par-réseau)
- [Générer les Shorts](#générer-les-shorts)
- [Générer les vidéos de 5 à 15 minutes](#générer-les-vidéos-de-5-à-15-minutes)
- [Contrôler et comparer](#contrôler-et-comparer)
- [Demande à copier dans Codex](#demande-à-copier-dans-codex)

## Installer le système

Clone le dépôt, récupère la branche de cette livraison, puis ouvre-le dans Codex. Toutes les commandes ci-dessous partent de la racine, dans PowerShell. Prérequis : Python 3.12 ou supérieur, FFmpeg et FFprobe dans le PATH. FFmpeg doit disposer du filtre ASS pour les sous-titres incrustés. Aucun compte social ni OAuth n'est requis pour générer les fichiers.

```powershell
python -m venv .local/social-venv
& ./.local/social-venv/Scripts/python.exe -m pip install -r tools/youtube-growth/requirements-thematic-qa.txt
$env:PYTHONPATH = 'tools/youtube-growth/src'
& ./.local/social-venv/Scripts/python.exe -m youtube_growth.social --help
& ./.local/social-venv/Scripts/python.exe -m youtube_growth.thematic --help
```

L'installation télécharge les dépendances. Le parcours local n'appelle aucun service IA payant. L'analyse OpenAI des formats thématiques est une option explicite, facturée au compte API configuré ; elle n'est jamais activée par défaut.

| Élément                                     | Emplacement                                                               |
| ------------------------------------------- | ------------------------------------------------------------------------- |
| Générateur de variantes courtes             | `tools/youtube-growth/src/youtube_growth/social.py`                       |
| Moteur de rendu vertical et sous-titres     | `tools/youtube-growth/src/youtube_growth/rendering.py`                    |
| Générateur 5–15 min                         | `tools/youtube-growth/src/youtube_growth/thematic.py` et modules associés |
| Guide détaillé des formats 5–15 min         | [THEMATIC.md](../youtube-growth/THEMATIC.md)                              |
| Référence E02 avec compositions HyperFrames | [camera-unique-v2](episode-02/camera-unique-v2/README.md)                 |

## Préparer un nouvel épisode

Crée un dossier neuf, par exemple `.local/episode-suivant/`. Fournis :

1. `source.mp4` : master autorisé ou copie téléchargée par le propriétaire dans YouTube Studio. Un lien YouTube seul ne fournit pas les images au moteur local.
2. `transcript.txt` : transcription horodatée relue, portant le bon identifiant vidéo.
3. `social-plan.json` : sélection des passages et variantes, préparée après lecture et examen des scènes.

Format de transcription accepté par le moteur court :

```text
Video ID: IDENTIFIANT_YOUTUBE
[00:00] Paroles réellement prononcées au début.
[00:04] Intervention suivante avec son véritable horodatage.
```

Remplace l'identifiant et les paroles par ceux du nouvel épisode. Une fin de segment est déduite du début suivant : vérifie les limites à l'écoute. Les SRT et les JSON ASR ne peuvent pas être renommés en TXT sans conversion. Le moteur thématique accepte aussi les segments JSON/JSONL, selon son guide.

Le moteur vertical actuel exige une source **1280 × 720 avec audio**. Pour une autre résolution, prépare une copie de travail compatible et conserve le master. Vérifie que la copie et la transcription gardent les mêmes temps. Le cadrage `fit` conserve toute l'image horizontale dans le cadre vertical. Les cadrages historiques `speaker`, `panel` et `slide` supposent des positions de caméra : utilise-les seulement après inspection de la nouvelle émission. Le programme ne détecte pas automatiquement l'intervenant.

## Choisir les passages et les variantes par réseau

Demande à l'agent de lire la transcription et de proposer des passages sourcés : question, démonstration ou désaccord complet, début, fin, contexte indispensable et réserves. Examine aussi les images. Une transcription seule ne permet pas de vérifier qu'une démonstration reste lisible.

Pour chaque passage retenu, décide sur quels réseaux il apporte quelque chose. Un passage peut avoir une, deux, trois ou quatre variantes. Chaque variante possède ses propres bornes source, son titre, sa légende et son cadrage. Un même thème peut donc commencer plus tôt sur YouTube, aller directement au résultat sur TikTok et conserver une explication pratique sur Instagram. Ce sont des choix éditoriaux à tester sur les comptes Sandbox, pas des règles universelles.

| Réseau          | Hypothèse de montage à tester                                                                                                  | Mesures à relever après publication autorisée                                         |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| YouTube Shorts  | Une question explicite, une réponse complète et un prolongement vers une vidéo thématique ou l'épisode                         | Vues engagées, choix de regarder plutôt que balayer, rétention, abonnements attribués |
| TikTok          | Montrer immédiatement l'usage ou l'enjeu ; garder la réaction et la conclusion ; reprendre les mots employés par le public     | Temps regardé, complétion, partages, visites du profil, abonnements                   |
| Instagram Reels | Un cas utile et compréhensible sans contexte, une couverture lisible et une conclusion qui mérite d'être conservée ou partagée | Portée hors abonnés, durée regardée, enregistrements, partages, abonnements           |
| X               | Une idée ou un désaccord précis, accompagné d'un texte qui apporte le contexte                                                 | Impressions, lectures disponibles, interactions, clics et abonnements mesurables      |

Commence avec des hypothèses de durée adaptées au propos, par exemple 20–40 secondes pour une démonstration très directe et 40–60 secondes pour une explication. Allonge uniquement si le contexte l'exige. Ces plages ne sont ni des limites des plateformes ni une durée optimale démontrée. Le générateur accepte 5 à 180 secondes par variante ; vérifie l'éligibilité réelle dans la plateforme avant diffusion.

Les sources officielles justifient de mesurer séparément : [YouTube distingue les vues engagées des démarrages de Shorts](https://support.google.com/youtube/answer/10059070?hl=en), [TikTok tient compte du temps regardé et des interactions](https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content), et [Instagram propose les Reels d'essai auprès de non-abonnés](https://about.fb.com/news/2024/12/trial-reels-try-content-non-followers-first-see-what-perfoms-best/). Vérification documentaire : 24 octobre 2026. Les fonctions disponibles peuvent varier selon le compte.

## Générer les Shorts

Prépare `social-plan.json`. Cet exemple illustre le schéma ; son identifiant, sa durée, ses timecodes et ses textes sont fictifs et doivent être remplacés après sélection réelle :

```json
{
  "version": 1,
  "video_id": "AbCdEfGhI12",
  "source_duration": 7200,
  "clips": [
    {
      "id": "assistant-restaurant",
      "variants": [
        {
          "platform": "youtube",
          "start": 120,
          "end": 175,
          "title": "Comment un assistant traite une réservation",
          "caption": "Le raisonnement complet, extrait de notre nouvelle émission.",
          "layout": "fit"
        },
        {
          "platform": "tiktok",
          "start": 132,
          "end": 165,
          "title": "Répondre pendant le service",
          "caption": "Quel appel te fait perdre le plus de temps pendant le service ?",
          "layout": "fit"
        },
        {
          "platform": "instagram",
          "start": 126,
          "end": 170,
          "title": "Un cas concret pour les restaurateurs",
          "caption": "La piste présentée dans cet extrait, avec ses limites.",
          "layout": "fit"
        }
      ]
    }
  ]
}
```

Ajoute autant de passages utiles que l'émission en contient, jusqu'à 100 par plan. Trente passages avec trois variantes produisent jusqu'à 90 fichiers ; l'outil n'invente aucun passage pour atteindre ce nombre. Chaque variante est un **extrait continu** : le moteur applique ses bornes et son cadrage, incruste les sous-titres et le titre, puis normalise l'audio. Il ne réécrit pas les propos et ne réalise pas encore de montage interne complexe. Pour des coupes successives ou des mouvements de caméra, crée une nouvelle composition HyperFrames sur le modèle de la référence E02, avec les nouveaux sous-titres et timecodes.

Simulation sans écriture ni rendu :

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
& ./.local/social-venv/Scripts/python.exe -m youtube_growth.social --plan .local/episode-suivant/social-plan.json --source .local/episode-suivant/source.mp4 --transcript .local/episode-suivant/transcript.txt --output .local/episode-suivant/shorts-v1
```

Après relecture du plan, relance avec `--execute` pour créer les fichiers. Le dossier de sortie contient un sous-dossier par réseau puis par passage, avec le MP4, les sous-titres ASS, `caption.txt` et le reçu de rendu. `social-manifest.json` regroupe les résultats avec le statut `needs_review`.

Le programme vérifie tous les candidats avant le rendu. Il refuse un plan ou une source modifiés dans un ancien dossier. Une reprise avec le même plan réutilise uniquement les fichiers correspondant aux empreintes enregistrées. Un rendu interrompu sans reçu doit être conservé pour diagnostic ; utilise un nouveau dossier. Ne retire un verrou qu'après avoir vérifié l'absence de processus actif.

## Générer les vidéos de 5 à 15 minutes

Ce parcours produit des vidéos horizontales avec une question, un développement et une conclusion. Il fournit aussi les sous-titres, une proposition de miniature, le titre, la description et la carte des coupes.

```powershell
& ./.local/social-venv/Scripts/python.exe -m youtube_growth.thematic --source .local/episode-suivant/source.mp4 --transcript .local/episode-suivant/transcript.txt --video-id IDENTIFIANT_YOUTUBE --output .local/episode-suivant/thematiques-v1 --analyze-only
```

Remplace `IDENTIFIANT_YOUTUBE`. Examine `selection.json` et `rapport.md`, puis relance sans `--analyze-only` pour rendre. Le programme retient au plus cinq vidéos, chacune de 300 à 900 secondes, et peut n'en retenir aucune. Il préserve les sources et vérifie chaque export.

L'analyse locale reconnaît un vocabulaire limité, issu des premiers sujets Sandbox. Une nouvelle émission peut nécessiter une analyse sémantique ou une sélection externe vérifiée, via `--analysis`. Le [guide thématique](../youtube-growth/THEMATIC.md) décrit le schéma et l'option OpenAI explicite. Le programme ne garantit pas de reconnaître tous les sujets d'une prochaine émission.

La miniature proposée suppose une caméra à droite. Adapte-la si le nouveau plateau diffère. L'analyse d'un sujet et les notes éditoriales ne prédisent pas les vues.

## Contrôler et comparer

Avant livraison, écoute les coupes, corrige les sous-titres, vérifie le cadrage et le contexte de chaque variante. Les contrôles techniques décodent les exports ; ils ne certifient pas le sens du montage.

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
& ./.local/social-venv/Scripts/python.exe -m unittest discover -s tools/youtube-growth/tests -p test_social.py -v
& ./.local/social-venv/Scripts/python.exe -m unittest discover -s tools/youtube-growth/tests -p test_thematic.py -v
& ./.local/social-venv/Scripts/python.exe -m youtube_growth.thematic_qa --output .local/episode-suivant/thematiques-v1
```

La dernière commande exige des rendus thématiques terminés. Elle compare des fenêtres d'image et de son au master. Un doute reste à relire.

Après publication explicitement autorisée, relève les métriques natives à 48 heures puis à sept jours. Compare les variantes au sein de leur réseau, à âge comparable, avec source et période. Tester une seule différence à la fois facilite l'interprétation ; les variantes concurrentes sur des audiences différentes ne constituent pas un A/B aléatoire. Un gagnant TikTok n'est pas automatiquement un gagnant Instagram ou YouTube. Avec peu de données, conserve la conclusion « insuffisant ».

Ne mets aucun MP4, master, mot de passe ou jeton sur GitHub. Les routines Codex de Lou sont en pause depuis le 24 octobre 2026. Le clone et les commandes de génération ne créent aucune programmation native ni publication.

## Demande à copier dans Codex

```text
Lis AGENTS.md, tools/social-network-manager/GENERER.md et tools/youtube-growth/THEMATIC.md.
Nous traitons un NOUVEL épisode. Demande le fichier source, la transcription horodatée
et l'identifiant YouTube s'ils manquent. N'utilise aucun ancien timecode.
Propose des Shorts et des sujets de 5 à 15 minutes à partir des propos réels.
Pour chaque Short, choisis les réseaux pertinents et propose des variantes de bornes,
d'accroche, de titre, de cadrage et de légende, avec une justification à tester.
Fais relire les sélections puis génère les fichiers localement dans un dossier neuf.
Préserve la voix, le contexte, le master et les anciens rendus ; vérifie les sous-titres.
Distingue contrôles techniques, revue humaine et performance observée.
Ne publie ni ne programme rien et n'ajoute aucun fichier vidéo dans Git.
```
