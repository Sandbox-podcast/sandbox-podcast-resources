# Préparer et rendre une opportunité

Conserver le `run_id` du rapport et le rang choisi. Toutes les commandes ci-dessous utilisent `python -m youtube_growth.trend_hunter` depuis la racine, avec `PYTHONPATH=tools/youtube-growth/src`. Le [guide utilisateur](../../../../tools/youtube-growth/TREND-HUNTER.md) détaille les paramètres ; le [contrat éditorial](editorial.md) définit les fichiers de recherche et de scénario.

## Préparation sourcée

1. Lancer `prepare RANG --run IDENTIFIANT`. Lire `production-request.json` et les preuves du dossier `research_required` retourné.
2. Lire les sources primaires avec les outils gratuits disponibles, archiver leurs textes dans `.local/` et vérifier affirmations, dates et chiffres. Préparer le dossier de recherche v1 de la factory et le JSON éditorial avec références par séquence. Utiliser le [contrôle documentaire existant](../../../../tools/youtube-growth/src/youtube_growth/factory/research.py).
3. Rédiger dans Codex ou Claude Code avec l'abonnement existant, sans API OpenAI/Anthropic facturée séparément. Si les sources ne soutiennent pas un script de deux minutes, garder la recherche en attente et expliquer le manque ; ne pas allonger le récit pour atteindre une durée.
4. Lancer `prepare RANG --run IDENTIFIANT --editorial CHEMIN_JSON`. Inspecter le script oral, les titres, les visuels et les attributions de la nouvelle version. Le pack peut passer à `ready_for_voice` ; les schémas SVG/PNG sont originaux et les fichiers ont leurs empreintes.

## Narration

Livrer `script.md` prêt à copier dans ElevenLabs et la commande `voice RANG --run IDENTIFIANT --import CHEMIN_MP3`. Si des repères par caractère sont disponibles, ajouter `--alignment CHEMIN_JSON` ; l'import vérifie leur correspondance au script.

Pour la génération API facultative, lire la section ElevenLabs du guide. Exiger une instruction explicite, une configuration locale activée, des crédits inclus suffisants et un dépassement désactivé côté compte. Une information de coût inconnue bloque la génération, sans bloquer l'import manuel. Une tentative incertaine interdit la reprise automatique ; réconcilier son résultat avant tout nouvel appel.

## Rendu et livraison

Après import de la narration, lancer `render RANG --run IDENTIFIANT`. L'export horizontal 1080p comprend mouvements légers, fondus et sous-titres. Les repères ElevenLabs et les temps estimés par nombre de mots gardent leur nature explicite ; les durées des scènes restent estimées.

Inspecter les images, écouter la voix et relire les sous-titres avant de consigner une revue audiovisuelle. Le décodage intégral ne constitue qu'un contrôle technique. Livrer le chemin de la vidéo, le reçu de provenance, les réserves et les contrôles manquants. Une révision crée une nouvelle version sans écraser les sources.
