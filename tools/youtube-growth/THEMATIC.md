# Vidéos thématiques YouTube

La commande `youtube_growth.thematic` génère des vidéos horizontales de 5 à 15 minutes dans un dossier local. Elle réutilise une transcription existante et ne publie rien. Les commandes Shorts, leurs manifestes et la file des réseaux restent indépendants. Voir [ADR-0040](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0040-videos-youtube-thematiques.md) et [la recette des deux épisodes](../../docs/site/history/2026/10/youtube-thematiques-2026-10-20.md).

## Installation

Python 3.12 ou supérieur, FFmpeg et ffprobe dans le PATH. Depuis la racine du dépôt, avec l'environnement Python existant activé :

```powershell
python -m pip install -r tools/youtube-growth/requirements.txt
$env:PYTHONPATH = 'tools/youtube-growth/src'
python -m youtube_growth.thematic --help
```

Pour la comparaison supplémentaire avec le son et l'image sources :

```powershell
python -m pip install -r tools/youtube-growth/requirements-thematic-qa.txt
```

## Traiter une émission

Fournir un master ou une copie obtenue par le propriétaire dans YouTube Studio. La Data API ne fournit pas le master. L'outil n'ajoute aucun téléchargeur ni accès privé à YouTube.

La transcription peut être un JSON contenant `segments`, un manifeste du pipeline Shorts avec ce champ, un JSONL `start/end/text` ou un export texte YouTube portant le bon `Video ID`. Le programme ne modifie pas ce fichier. Il vérifie les durées et, quand ils sont présents, l'identifiant vidéo et l'empreinte source. Une transcription brute sans identité reste sous la responsabilité de l'opérateur.

Exemple réel pour l'épisode 02, depuis la racine :

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
python -m youtube_growth.thematic `
  --source exports/reseaux-sociaux/episode-02/source/episode-02-studio.mp4 `
  --transcript exports/reseaux-sociaux/episode-02/source/transcript-fr.jsonl `
  --video-id 7KVqydbGow0 `
  --output .local/youtube-thematic/episode-02
```

Pour l'épisode 01, la source téléchargée est référencée dans le manifeste historique :

```powershell
$episodeOne = Get-Content .local/youtube-growth/GgSiPkADCz4/shorts/render-manifest.json -Raw | ConvertFrom-Json
python -m youtube_growth.thematic `
  --source $episodeOne.source_path `
  --transcript .local/youtube-growth/GgSiPkADCz4/transcript-youtube.txt `
  --video-id GgSiPkADCz4 `
  --output .local/youtube-thematic/episode-01
```

Sans configuration d'API, `--analyzer local` applique des règles conservatrices à cinq familles de discussions : Sillage et les agents, les harnais, les artisans/commerçants, les tickets et le legacy. Les règles reconnaissent des formulations dans les paroles, pas des timecodes ou des identifiants d'épisode. Elles sont sensibles aux mots utilisés. Elles peuvent ne retenir aucun sujet d'une émission différente. Les scores locaux reposent sur ces règles ; ils ne mesurent pas une audience ni une rétention observée.

## Analyse sémantique optionnelle

L'analyse OpenAI traite toute la transcription en un appel puis met la réponse validée en cache. Ce choix utilise le compte API configuré et peut être facturé. Il ne se déclenche jamais par défaut.

```powershell
# OPENAI_API_KEY doit déjà être configurée dans l'environnement.
$env:YOUTUBE_THEMATIC_MODEL = 'MODELE_RESPONSES_AUTORISE'
python -m youtube_growth.thematic `
  --source C:/medias/emission.mp4 `
  --transcript C:/medias/transcription.jsonl `
  --video-id IDENTIFIANT_YOUTUBE `
  --analyzer openai `
  --output .local/youtube-thematic/nouvelle-emission
```

Choisir le modèle selon les accès réels du compte. `--model` prend le pas sur la variable. Le programme ne crée pas de compte et ne choisit pas de modèle payant à la place de l'opérateur. Sans clé ou modèle, il échoue avec une explication. Les échecs réseau conservent le travail local ; aucune sélection factice ne remplace une réponse IA manquante.

`--analysis CHEMIN` réutilise une analyse externe au format JSON du champ `raw` de `analysis.json`. Le prompt et le schéma attendu sont dans `thematic_analysis.py`. Les indices désignent les unités de `units.json`, pas les mots ni les segments d'origine. Les citations sont contrôlées contre ces unités.

## Options et reprise

- `--count 1..5` limite le nombre de vidéos ; il n'impose aucun minimum.
- `--minimum-score 72` est le seuil éditorial par défaut. L'autonomie doit aussi atteindre 70/100.
- `--analyze-only` prépare une sélection sans rendu. Relancer la même commande sans cette option reprend le lot.
- `--burn-subtitles` incruste les sous-titres. Par défaut, le SRT est livré séparément et ajouté au MP4 comme piste sélectionnable.

La commande complète fonctionne sans validation intermédiaire. L'écoute précède uniquement une éventuelle publication, qui reste hors de cet outil.

Le verrou et les JSON atomiques réutilisent `storage.py`. Un cache est lié au master, à la transcription, au modèle, au prompt et aux paramètres. Changer l'un de ces éléments exige un autre dossier. La reprise vérifie les empreintes des MP4 terminés et réutilise les parties de rendu dont les reçus correspondent. Une vidéo finale modifiée n'est pas écrasée. Après un arrêt forcé, contrôler qu'aucun processus ne travaille encore avant de retirer `run.lock`.

## Sorties

Le dossier de l'émission contient `thematic-manifest.json`, la transcription normalisée, les unités de parole, l'analyse en cache, `selection.json` et `rapport.md`. Les refus sont justifiés dans la sélection.

Chaque sous-dossier de vidéo contient :

- `video.mp4`, en H.264/AAC, 16:9, avec normalisation audio ;
- `subtitles.srt`, synchronisé sur les plages conservées et le rejeu de l'accroche ;
- `thumbnail.png`, proposition 1280 × 720 avec trois à cinq mots et la colonne caméra réelle ;
- `titre.txt`, `description.txt` et `metadata.json`, avec notes, motifs et preuves citées ;
- `montage.json`, avec tous les timecodes source et destination, ainsi que le contrôle technique.

Les miniatures supposent une colonne caméra à droite, comme les deux épisodes de la recette. Un autre décor demande d'adapter ce cadrage dans `thumbnail`. Le dossier `parts/` contient les intermédiaires de reprise. Le master n'est jamais remplacé. Les sources et rendus restent dans les dossiers locaux ignorés par Git.

## Vérifications

Chaque MP4 final passe un décodage intégral, un contrôle de durée, de format et d'horloges audio/vidéo. La comparaison suivante ajoute trois fenêtres d'image et de son pour chaque plage de montage :

```powershell
python -m youtube_growth.thematic_qa --output .local/youtube-thematic/episode-01
python -m youtube_growth.thematic_qa --output .local/youtube-thematic/episode-02
python -m unittest discover -s tools/youtube-growth/tests -v
```

Les fichiers `correspondance-source.json` conservent les empreintes, corrélations et décalages mesurés. Un doute donne `needs_review` et un code de sortie 2. Une absence de son exploitable n'est jamais déclarée conforme. La comparaison ne vaut pas écoute complète ou avis éditorial.

L'analyse locale ne supprime pas les hésitations et répétitions à l'intérieur des paroles. Elle raccourcit seulement les pauses sans texte de plus de 1,8 seconde, avec 180 ms de respiration de chaque côté. Le mode IA peut proposer des coupes supplémentaires de passages complets. Les fins de segments ASR et les sous-titres restent à écouter avant publication ; leurs erreurs ne sont pas corrigées en inventant les propos.

Les copies disponibles sont en 720p. Elles restent en 720p ; les miniatures sont en 1280 × 720. Une source 1080p ou supérieure conserve une définition horizontale adaptée. La normalisation du mix ne remplace pas des pistes séparées pour chaque intervenant.
