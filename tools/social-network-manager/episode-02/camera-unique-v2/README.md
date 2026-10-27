# Sources des trente Shorts E02 corrigés

Ce dossier conserve les compositions `camera-unique-v2` du 18 octobre 2026 : une seule vidéo à l'écran, ses cadrages successifs, ses sous-titres et les bornes des trente passages. Les titres, textes, timecodes et mouvements viennent des compositions locales corrigées. Les MP4, captures, caches HyperFrames, bibliothèques tierces et états des comptes ne sont pas inclus.

`manifest.json` contient les passages et leurs dispositions. `projects/` conserve les trente HTML et leurs storyboards. `pipeline.py` réunit la préparation locale, les contrôles du rendu, la comparaison audio, les planches de revue, les quatre coupes Instagram et la création d'un bundle neuf. Importer ce module ne lance aucune opération.

Le pipeline ne lit ni ne modifie `publication-queue.json`. Un bundle local ne démontre aucune publication ni programmation native. La file et les preuves des réseaux restent sous la responsabilité du processus de distribution existant.

## Contrôle sans médias

Depuis la racine du dépôt, avec Python 3.12 ou supérieur :

```sh
python -m pip install -r tools/social-network-manager/episode-02/camera-unique-v2/requirements-qa.txt
python -m unittest discover -s tools/social-network-manager/episode-02/camera-unique-v2 -p test_pipeline.py -v
python tools/social-network-manager/episode-02/camera-unique-v2/pipeline.py check
```

L'installation télécharge NumPy et Pillow séparément du pipeline. Les deux contrôles suivants vérifient les trente sources, leurs durées, leur unique vidéo et la comparaison audio sur des signaux synthétiques identiques ou dégradés. Ils n'appellent ni FFmpeg, ni HyperFrames, ni un réseau. Le job CI `source-pipelines` installe ces dépendances, exécute ces contrôles et les tests de montage des kits personnels.

## Reproduire un espace de travail

Il faut la source propriétaire complète de l'épisode `7KVqydbGow0`, en **1280 × 720**, FFmpeg et FFprobe dans le PATH, ainsi qu'une copie locale de GSAP **3.14.2**. Pour les rendus, utiliser HyperFrames **0.8.172**, version des projets d'origine. Les scripts ne téléchargent aucun outil. Installer ces dépendances séparément avant leur utilisation. Les contrôles audio demandent NumPy ; les planches de revue demandent Pillow. `requirements-qa.txt` reprend les versions du runtime local utilisé pour ces tests.

Placer les bibliothèques dans un dossier local ignoré, par exemple `.local/e02-runtime/`. Le fichier GSAP et son contrat de licence restent ceux de sa distribution d'origine. Le logo et la police Archivo utilisés par les compositions existent déjà dans les assets du site.

```sh
python tools/social-network-manager/episode-02/camera-unique-v2/pipeline.py prepare --workspace .local/e02-reproduction --episode exports/reseaux-sociaux/episode-02/source/episode-02-studio.mp4 --gsap .local/e02-runtime/gsap.min.js --font apps/site/public/slides/episode-002-bis/assets/archivo.woff2 --logo apps/site/public/sandbox-logo.png
```

Sans `--execute`, cette commande affiche le plan et ne crée rien. Ajouter `--execute` pour préparer les segments et copier les sources dans **un dossier neuf**. Les sorties sont refusées dans ce dossier de sources versionnées. Aucun fichier existant n'est écrasé. Les empreintes de l'épisode et des segments sont enregistrées dans `provenance.json`.

Le fichier de travail complet n'est jamais réencodé ni écrasé. Les segments locaux utilisent `libx264`, disponible sans GPU Nvidia. Ils ne sont donc pas garantis identiques octet par octet aux anciens intermédiaires NVENC ; les timecodes, le cadrage, la voix et les sous-titres restent ceux des sources conservées. Une reproduction doit subir ses propres contrôles.

## Vérifier puis rendre

Ouvrir les projets préparés avec HyperFrames, puis examiner l'aperçu avant d'autoriser un rendu. Les commandes suivantes attendent le chemin de l'exécutable **local déjà installé** ; l'exemple Windows utilise `.cmd`, à remplacer par l'exécutable sans extension sous Linux ou macOS.

```sh
python tools/social-network-manager/episode-02/camera-unique-v2/pipeline.py render --workspace .local/e02-reproduction --cli .local/e02-runtime/node_modules/.bin/hyperframes.cmd --clip E02-007
```

Ajouter `--execute` après validation de l'aperçu. Le pipeline lance `check` avant chaque rendu et refuse une sortie existante. `--clip` peut être répété ; sans ce filtre, les trente projets sont traités. La présence du fichier ne remplace pas les contrôles. Pour reprendre les contrôles d'un lot existant :

```sh
python tools/social-network-manager/episode-02/camera-unique-v2/pipeline.py qa --workspace .local/e02-reproduction --audio --contact
```

Avec `--execute`, le pipeline décode les fichiers intégralement, contrôle la durée, le format 720 × 1280 à 30 images/s et l'unique piste audio, puis extrait début, milieu et fin. L'audio est comparé à la mezzanine sur trois fenêtres de deux secondes : corrélation supérieure à 0,97 et décalage maximal de 10 ms. Une différence de durée supérieure à 150 ms demande une revue. Ces fenêtres ne constituent pas une écoute intégrale.

Examiner les images et écouter les passages nécessaires. Créer ensuite `visual-review.json` dans le workspace avec exactement une entrée par fichier, attribuée à la personne ayant réellement effectué la revue :

```json
[
  {
    "id": "E02-001",
    "sha256": "empreinte-du-mp4-examiné",
    "status": "reviewed",
    "reviewed_by": "nom-de-la-personne"
  }
]
```

Le pipeline ne remplit pas cette attestation automatiquement. L'exemple doit être complété pour les trente clips. Une modification du MP4 invalide les preuves vidéo, audio et visuelles antérieures.

## Préparer les livrables locaux

```sh
python tools/social-network-manager/episode-02/camera-unique-v2/pipeline.py install --workspace .local/e02-reproduction --destination .local/e02-bundle
python tools/social-network-manager/episode-02/camera-unique-v2/pipeline.py instagram --workspace .local/e02-reproduction
```

La première commande, avec `--execute`, exige les trente contrôles vidéo et audio réussis ainsi que les trente revues visuelles portant sur les mêmes empreintes. Elle copie les MP4 vers un bundle neuf et conserve les preuves. Elle ne remplace aucun média existant et ne change aucun statut natif.

La seconde, avec `--execute`, reconstruit les quatre coupes Instagram sous 90 secondes à partir des intervalles conservés dans le manifeste. La fin d'une coupe peut atteindre la fin de la dernière image à 30 images/s, soit moins d'une image au-delà de la durée logique du clip. Leur audio, leurs coupes et leur contexte doivent être revus séparément ; elles restent marquées `visual_qa: pending`.

## Scripts locaux rapprochés de cette livraison

Les scripts de conversation étaient dans `.local/social-network-manager/`, dossier non versionné. Leur partie utile est conservée ainsi :

| Script local                                  | Source durable                                                                                                                                  |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `recompose-e02-v2.py`                         | Les trente HTML et storyboards figent les cadrages et timelines produits ; leur régénération ne dépend plus de l'ancien montage à deux caméras. |
| `render-e02-v2.py`                            | Commandes `render` et `qa`, contrôles vidéo et images de début, milieu et fin.                                                                  |
| `audio-qa-e02-v2.py`                          | Comparaison audio dans `qa --audio`, avec durées vérifiées avant toute troncature.                                                              |
| `contact-e02-v2.py`, `inspect-e02-sources.py` | Planches de contrôle dans `qa --contact` ; les dispositions retenues sont dans le manifeste.                                                    |
| `install-e02-v2.py`                           | Commande `install`, limitée à un bundle neuf ; les mutations de la file native ne sont pas reprises.                                            |
| `instagram-variants-e02.py`                   | Intervalles et commande `instagram`, sans dépendance NVENC.                                                                                     |

Ne pas relancer les anciens `prepare-e02.py`, `compose-e02.py`, `render-e02.py`, `finalize-e02-projects.py` ou `calendar-e02.py` sur le lot corrigé. Ils visaient le premier montage ou réinitialisaient son suivi. `classify-e02-layouts.py` était une heuristique de sélection : les cadrages effectivement retenus sont conservés dans `manifest.json`, sans prétendre que cette heuristique valide un nouveau décor.

Les scripts `record-*.mjs`, `consolidate-e02.mjs`, `document-e02-v2.py`, `finish-local-e02-v2.py`, `organize-e02-x.py` et les anciens compresseurs X/TikTok restent des archives locales non reprises : ils consignaient une opération native ponctuelle, des preuves propres à la session ou une ancienne variante. Copier leurs affirmations et leurs identifiants dans un pipeline réutilisable pourrait annoncer à tort une programmation ou un remplacement terminé. Leurs résultats historiques ne deviennent pas des opérations automatiques.
