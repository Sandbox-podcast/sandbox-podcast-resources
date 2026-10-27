# Kit de chaîne YouTube Sandbox

## Identité actuelle (9 octobre 2026)

Les fichiers `*-v2.png` sont les visuels à utiliser sur la chaîne [@SandboxFR](https://www.youtube.com/@SandboxFR). Leurs sources SVG homonymes reprennent le logotype officiel `logov2.png`, la palette bleu nuit/cyan et le triangle de l'icône du site. L'identité évite les cubes en 3D du premier kit. La bannière affiche uniquement le logo SANDBOX, centré sur un fond uni.

- `channel-banner-v2.png` : bannière 2560 × 1440 px. Le logo seul reste dans la zone centrale de 1544 × 423 px, visible sur mobile.
- `channel-avatar-v2.png` : avatar 800 × 800 px, triangle cyan centré optiquement dans le recadrage circulaire YouTube, avec des espaces équilibrés en haut et sur les côtés.
- `video-watermark-v2.png` : filigrane transparent 150 × 150 px, prévu pour l'intégralité des vidéos.
- `episode-thumbnail-template-v2.png` : base 1280 × 720 px à personnaliser par épisode. Le titre et le numéro sont des exemples, pas une miniature publiable telle quelle.

La [décision graphique](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0011-identite-youtube-sandbox.md) explique l'alignement avec le site. Le [texte de chaîne](channel-copy.md) contient le nom, le lien et la description en vigueur. Les fichiers sans suffixe `-v2` sont conservés comme première version du kit.

## Première version conservée

- channel-banner.jpg : bannière 2560 x 1440 px.
- channel-avatar.png : avatar carré 800 x 800 px, composé à partir de l'emblème Sandbox fourni.
- video-watermark.png : filigrane carré transparent 150 x 150 px.
- episode-thumbnail-template.jpg : gabarit de miniature 1280 x 720 px. Remplacer le texte de démonstration pour chaque épisode.
- banner-background-source.png et watermark-emblem-source.png : sources générées utilisées dans les compositions.
- channel-copy.md : description et paramètres publiés.

La bannière reprend le logo existant et la signature "La tech mérite mieux que du bruit." sur le fond bleu nuit et cyan défini dans docs/design-decisions/DD-0002-charte-sandbox-bleu-nuit-cyan.md.

Fonds générés avec l'outil image_gen. Prompts :

- Bannière : fond de studio podcast en 16:9, bleu nuit et cyan, cubes translucides sur les bords, bande centrale sombre sans texte ni logo.
- Filigrane : découpe transparente de l'emblème central microphone et cubes du logo existant, sans mot-symbole ni texte.

Les dimensions de la bannière et du filigrane suivent les recommandations YouTube. Le gabarit de miniature est une base visuelle, pas une miniature finalisée pour un épisode.
