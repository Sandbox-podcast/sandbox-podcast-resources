# Générique SANDBOX

Projet Remotion éditable du générique demandé le 14 octobre 2026. Les sorties sont enregistrées dans `.local/videos/sandbox-intro/` à la racine du dépôt :

- `sandbox-intro-final.mp4` : master H.264, 1920 x 1080, 50 images/s, AAC stéréo 320 kbit/s.
- `sandbox-intro-preview.mp4` : copie légère en 1280 x 720.

Durée cible : 63,56 secondes, soit 3 178 images à 50 images/s. Le M4A original est conservé intact dans `public/original.m4a`. À la demande de Lou, les dialogues sont refaits avec quatre voix ElevenLabs v4 : Stephane pour Lou, Nova pour Loïc, Fabien pour Nico et Fred pour l'annonceur. Il s'agit de voix du catalogue, pas de clones des animateurs. La composition utilise désormais `public/voices/sandbox-elevenlabs-mix.wav`.

## Ouvrir et modifier

Prérequis : Node 24, npm, Chrome et FFmpeg. Les dépendances Remotion sont verrouillées dans `package-lock.json`.

```powershell
cd projects/videos/sandbox-intro
npm ci
npm run studio
```

Dans Remotion Studio, ouvrir la composition `SandboxIntro`. Déplacer la tête de lecture pour vérifier les animations et écouter la piste. Le code de chaque scène est dans `src/sandbox-intro.tsx`. Les animations dépendent uniquement du numéro d'image : elles se recalculent correctement en revenant en arrière.

Les horaires de scènes, annonces et punchlines sont dans `timeline.json`. Les constantes de couleur sont au début du fichier TSX. Les neuf composants portent les noms `Intro`, `Lou`, `Loic`, `Nico`, `Radar`, `Build`, `Clash`, `Beta` et `Finale`.

Les masques SVG des portraits et les photos originales sont dans `public/`. Pour refaire un détourage, modifier le chemin correspondant dans `scripts/prepare-assets.mjs`, puis exécuter le script. Sharp est inclus dans les dépendances du projet. Les chemins des images source sont indiqués dans ce script ; sur une autre machine, il utilise les copies de `public/originals/`. Aucun visage n'est généré. Les nouvelles photos de Loïc fournies pendant la réalisation remplacent le portrait flou initial : `loic 2.png` avec casque pour sa présentation, l'introduction et le final ; `loic 3.png` sans casque pour le ring et le laboratoire. À la demande de Lou, toutes ses apparitions utilisent la photo studio avec casque `Downloads/Lou sandbox.png` (1334 x 1179 pixels). Le masque SVG conserve le visage et le casque, avec un détourage court sous le menton. La photo de Nico reste celle du premier envoi.

La police Anton est fournie avec sa licence OFL. Le logo `public/logo.png` est identique à `logov2.png`.

## Recalculer

```powershell
npm run typecheck
npm test
node scripts/render.mjs stills
node scripts/render.mjs preview
node scripts/render.mjs final
```

`CHROME_PATH`, `FFMPEG_PATH` et `RENDER_CONCURRENCY` permettent d'adapter le moteur au poste. La commande `stills` produit 22 captures réparties sur toutes les scènes. Les fichiers `*-silent.mp4` sont les intermédiaires vidéo avant ajout du son.

## Synchronisation

La transcription locale Parakeet TDT v3, ses tokens et leurs timestamps sont conservés dans `analysis/transcript-raw.json`. Les noms et termes techniques mal reconnus ont été corrigés dans la timeline à partir du brief. La résolution native des timestamps est de 80 ms : ce repérage automatique ne constitue pas une validation phonétique manuelle.

`analysis/audio-analysis.json` conserve l'enveloppe RMS par pas de 10 ms et les impacts détectés. L'explosion de Nico se cale sur l'impact mesuré à 28,90 s ; celle du laboratoire sur 50,94 s. La bande-son réelle contient deux annonces SANDBOX avant l'introduction parlée, un passage instrumental après Nico et une fin sonore après la dernière phrase. Tous sont conservés.

Le conteneur source annonce 63,56 s. Le décodage Opus inclut environ 13,5 ms de padding supplémentaire ; le master respecte la durée de présentation du conteneur. Le silence final original est conservé. Aucun effet sonore supplémentaire n'est ajouté. Les cris SANDBOX et les plages instrumentales viennent du mix original. Les autres fenêtres utilisent l'instrumental séparé localement avec Demucs htdemucs et les dialogues ElevenLabs. La séparation peut laisser de légers artefacts musicaux.

## Contrôles

`npm test` vérifie les paramètres et la timeline sans demander les médias de l'utilisateur. Pour inclure les contrôles des pistes, portraits et empreintes locales, définir `$env:SANDBOX_MEDIA_INTEGRATION = '1'` avant la commande. Les fichiers de `public/` et `analysis/` restent ignorés par Git.

Les tests vérifient la continuité des neuf scènes, les repères des annonces, la durée exacte en images et l'identité SHA-256 de l'audio et du logo copiés. Le rapport final est enregistré dans `analysis/validation.json` après vérification des MP4. Les captures de contrôle sont dans `analysis/proof/`.

Le projet est inclus dans l'espace de travail pnpm. Le contrôle global `pnpm check` du 14 octobre 2026 réussit : formatage, lint, types, 414 tests du site, sept tests du générique et quatre tests des assets de jingles. Le build du site réussit avec 213 pages statiques. Les exports final et aperçu passent le décodage complet et le contrôle de concordance audio.

Les liens du site et de la référence YouTube n'étaient pas accessibles depuis l'outil web pendant cette réalisation. La direction s'appuie sur le brief fourni, la charte locale et les décisions SANDBOX, sans prétendre avoir visionné cette référence.

## Refaire le mix ElevenLabs

`voice-edit.json` associe chaque réplique à une voix, au texte, à son extrait source et à sa fenêtre vidéo. Les quatre voix et la prise corrigée de la chute finale sont dans `public/voices/`, les 23 extraits calés dans `public/voices/aligned/`. Les répliques sont normalisées à -17 LUFS et accélérées seulement si nécessaire, sans changement de hauteur, au maximum 1,3 fois. La musique baisse de 55 % sous les dialogues ; des fondus courts évitent les clics.

Exécuter `python scripts/mix-elevenlabs.py` avec Python et NumPy, puis exporter avec `node scripts/render.mjs final`. Le mix utilise l'instrumental FLAC fourni ; Demucs n'est pas nécessaire pour le refaire. `analysis/voice-mix-report.json` garde les vitesses, durées et niveaux. `scripts/verify.py` compare désormais l'audio des MP4 au nouveau mix, et non au Suno rejeté. Les sorties précédentes sont sauvegardées localement dans `analysis/revisions/suno-voices/` (hors ZIP).

La chute finale utilise une prise séparée ; le mot écrit `prode` dans la consigne de synthèse force la prononciation de « prod », vérifiée par transcription. Le texte éditorial reste « prod ». Cinq demandes de génération ont été effectuées dans ElevenLabs ; les variantes automatiques non retenues ne sont pas incorporées.
