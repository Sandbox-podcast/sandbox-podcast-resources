# Production et provenance

Ce dossier partage les scripts et la composition. Les anciens kits complets de ce poste sont conservés dans `.local/legacy/kits-relais/2026-10-18/`. Le moteur de montage écrit désormais dans `.local/relay-kits/2026-10-18/` ; ses vidéos, sous-titres et preuves restent hors de Git.

Les fichiers prêts à utiliser sont dans les dossiers personnels et `../videos/`. Ce dossier conserve la sélection, le script de montage et la composition de la fin commune.

## Règles de montage

Début directement sur le sujet, ordre des échanges conservé, cadre horizontal complet et son d'origine. Une fin commune de trois secondes invite à retrouver la discussion. Aucun intervenant n'est isolé pour transformer une objection en position définitive.

`selection.json` donne les bornes dans chaque source. Les fichiers `montage.json` conservent les empreintes, les bornes, la durée et le contrôle de décodage. Les sources complètes restent hors de Git. Les sous-titres viennent des transcriptions automatiques locales ; les noms et les formulations doivent être relus à l'écoute avant diffusion.

Les extraits courts des kits personnels contiennent déjà leurs sous-titres dans l'image. Leurs fichiers SRT restent dans `production/captions/`, en dehors des dossiers personnels et des ZIP. Placer un SRT à côté du MP4 peut déclencher son chargement automatique par le lecteur et afficher les sous-titres deux fois. Les montages longs gardent leur SRT séparé, car leur vidéo ne contient pas de sous-titres incrustés.

## Reproduire

Prérequis : Python 3.12 ou plus, FFmpeg et ffprobe. Depuis ce dossier :

```powershell
npm run check
npm run render -- --fps 25 --crf 23 --output assets/fin.mp4
ffmpeg -i assets/fin.mp4 -f lavfi -i anullsrc=r=48000:cl=stereo -c:v copy -c:a aac -t 3 assets/fin-avec-audio.mp4
```

Depuis la racine du dépôt, avec vos propres copies Studio :

```powershell
python projects/relay-kits/2026-10-18/production/monter.py --episode 1 --source CHEMIN_SOURCE_EPISODE_1 --transcript CHEMIN_TRANSCRIPTION_EPISODE_1
python projects/relay-kits/2026-10-18/production/monter.py --episode 2 --source CHEMIN_SOURCE_EPISODE_2 --transcript CHEMIN_TRANSCRIPTION_EPISODE_2
```

Les noms `CHEMIN_SOURCE` indiquent un argument à fournir à la commande, pas un lien de publication. La transcription d'E1 est l'export YouTube horodaté ; celle d'E2 est le JSONL français avec `start`, `end` et `text`.

HyperFrames rend la fin commune. FFmpeg assemble les longs passages sans capturer une heure d'images dans le navigateur. Les exports H.264/AAC 720p gardent le cadre complet, avec démarrage rapide pour la lecture web. E1 est réduit depuis sa copie 1080p préparée pour Spotify ; E2 conserve la définition de sa copie Studio 720p. Les exports restent sur le poste, quelle que soit leur taille. Avant le montage, placer la fin avec audio dans `.local/relay-kits/2026-10-18/production/assets/fin-avec-audio.mp4`.

## Réutiliser

Ouvrir directement les fichiers `video.mp4` pour lire les montages. La fin commune est modifiable dans `index.html` avec HyperFrames. Les dossiers du kit n'exigent aucun accès aux comptes personnels pour être consultés.
