# Jingles Sandbox

Quatre films courts identifient les séquences éditoriales du podcast : Le radar, Le build, Le clash et La bêta. Chaque master est une vidéo 16:9 en 1920 × 1080 à 30 images/s, calée sur la durée de sa musique. La direction reprend le collage typographique coloré et joueur du générique de référence fourni par Lou, avec un motif différent pour chaque séquence.

## Masters

| Séquence | Vidéo                                  |
| -------- | -------------------------------------- |
| Le radar | `le-radar-jingle/renders/le radar.mp4` |
| Le build | `le-build-jingle/renders/le build.mp4` |
| Le clash | `le-clash-jingle/renders/le clash.mp4` |
| La bêta  | `la-beta-jingle/renders/beta.mp4`      |

La page locale [preview.html](preview.html) permet de lire les quatre masters dans le navigateur.

## Rendu local

Le rendu utilise une scène HTML déterministe (`production.html`), Chromium piloté par Playwright et FFmpeg. Les sources audio et les images d’origine restent intactes ; les assets de travail sont copiés dans chaque dossier de séquence.

```powershell
node videos/render-jingles.mjs
```

On peut ne recalculer qu’un film avec `--only=le-radar`, `--only=le-build`, `--only=le-clash` ou `--only=la-beta`. Il faut Chromium, FFmpeg et Playwright ; `CHROME_PATH`, `FFMPEG_PATH` et `CODEX_NODE_MODULES` permettent de préciser leurs chemins.

Les images de contrôle JPEG de chaque master sont rangées dans son dossier `renders/proof/`.
