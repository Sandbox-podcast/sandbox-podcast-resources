# Accueil plein écran et VHS photographiques

Le 16 octobre, Lou demande de compléter les épaules coupées de Loïc et Nicolas et de retirer les micros des trois bustes. Cette retouche limitée remplace le montage des corps décrit ici ; les têtes conservent les photos d'origine. Voir la [retouche des bustes](retouches-bustes-2026-10-16.md).

15 octobre 2026. État local après les corrections de Lou, selon [DD-0038](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0038-accueil-plein-ecran-portraits-reels-et-vhs.md). Ce document remplace les validations de cadrage du [rapport précédent](decor-chaleureux-et-porte-animee.md).

## Résultat

Le décor couvre le premier écran. Les trois portraits sont détourés, à leur siège derrière la table. Le titre et le paragraphe sont superposés à l'image. Le dégradé et la mention "Le podcast IA & tech" sont retirés du premier écran. Le titre est "Gardez une longueur d'avance sur la tech." Le paragraphe reprend exactement le texte de Lou.

Le libellé visible "Entrer" et l'indication au survol de la porte sont retirés. Le lien accessible et son animation restent actifs. Les boutons YouTube et Spotify ouvrent les chaînes configurées. "Ce qu'on construit." présente Okodukai pour Lou.

Dans le vidéoclub, les cassettes et leur boîte sont désormais des images photographiques. Les titres et jaquettes restent propres à chaque projet. La boîte ouverte contient une vraie forme de VHS, avec deux fenêtres de bobines alignées sur la longueur de la cassette. L'ouverture dure 1,4 seconde avant la fiche ; elle est immédiate lorsque les mouvements sont réduits.

## Photos et fidélité des visages

Lou : `apps/site/public/team/lou.png`, 1334 x 1179. Loïc : `apps/site/public/team/loic.png`, 1254 x 1254. Ces originaux restent intacts. Le plateau utilise leurs copies WebP sans perte `lou-studio-lossless-v1.webp` et `loic-studio-lossless-v1.webp`, puis Next Image sert les tailles adaptées. Les pixels RGB décodés des copies sont strictement identiques aux originaux, ce que vérifie le test. Ce format corrige le chargement des deux portraits PNG dans le navigateur intégré après navigation.

Nicolas : portrait récupéré depuis [À propos en production](https://www.sandboxpodcast.fr/about), puis copié sans conversion dans `apps/site/public/team/nicolas-prod-2026-10-15.webp`, 800 x 800. L'URL source est `/api/host-photos/aea75f5d4a0c46079e5464a94bc5338a19a720c61063001e23e0e5e6b06b7fe7.webp`. Son SHA-256 est identique au nom du fichier source : `aea75f5d4a0c46079e5464a94bc5338a19a720c61063001e23e0e5e6b06b7fe7`.

Les masques servent uniquement à retirer les fonds. Le rendu utilise les pixels des photos sources, pas les pixels RGB d'une image de personnes générées. L'échelle s'applique à chaque photo entière ; le visage et le buste gardent leurs proportions. Aucun bras, main ou corps supplémentaire n'est inventé. La table occulte le bord inférieur des portraits. Les essais de trio généré et les cadres photo ont été écartés.

## Assets servis

| Asset sous `apps/site/public/`            | Dimensions | Octets  | Usage                               |
| ----------------------------------------- | ---------- | ------- | ----------------------------------- |
| `images/home/lou-cutout-mask-v1.webp`     | 640 x 566  | 39 962  | Masque alpha de Lou                 |
| `images/home/loic-cutout-matte-v1.webp`   | 640 x 640  | 10 578  | Masque par luminance de Loïc        |
| `images/home/nicolas-cutout-mask-v1.webp` | 640 x 640  | 27 266  | Masque alpha de Nicolas             |
| `video-club/vhs-case-closed-v1.webp`      | 640 x 1051 | 77 198  | Boîtier VHS avec jaquette du projet |
| `video-club/vhs-case-open-v1.webp`        | 1000 x 685 | 200 796 | Boîtier ouvert et cassette VHS      |

Les masques gardent le cadrage complet et le rapport de la source ; ils ne sont pas rognés. Leur réduction à 640 pixels et leur conversion WebP passent par Sharp. Le masque de Loïc utilise la luminance pour conserver son T-shirt opaque : les premiers masques alpha retiraient une partie du vêtement.

Les originaux générés restent dans le dossier de génération de la conversation `C:/Users/Lou/.codex/generated_images/01a14076-a18e-77f1-a4b2-9ee6592e8d66/` :

- Lou : `exec-eb505fdb-0e6a-4a23-804e-c0ce301ae0c3.png`.
- Loïc retenu : `exec-84d1d0c3-b599-4273-a148-d30553cb1846.png`. Les variantes `exec-7ea47f46-7290-4e9b-ba5b-241421c40f3a.png` et `exec-d6f1b38d-ed95-4361-837f-0a3faae6b958.png` ne sont pas utilisées.
- Nicolas : `exec-9e75ab31-1908-4fc8-bc25-9a544fd0cacc.png`.
- VHS fermée : `exec-356de1ee-21e5-4089-bcb1-0d8e25cce6cb.png`.
- VHS ouverte : `exec-f829991b-f47d-489d-b26a-0ab00a1abce8.png`.

Les VHS ont été recadrées sur leur contenu transparent, réduites et converties en WebP avec alpha conservé. Le boîtier fermé porte une jaquette HTML personnalisée sous sa texture photographique. Le boîtier ouvert remplace les anciennes bobines dessinées en CSS. Les assets référencés sont copiés dans le dépôt, sans dépendance au dossier de génération.

## Prompts exacts

Génération avec l'outil ImageGen intégré. Chaque masque reçoit uniquement la photo originale de la personne concernée. La VHS ouverte reçoit la VHS fermée comme référence.

### Détourage de Lou

```text
Use case: background-extraction.
Asset type: exact registration alpha matte for a real photographic person cutout, to be used as a CSS mask over the UNCHANGED original photo.
Input image is the source photo of Lou. Output ONLY an OPAQUE WHITE SILHOUETTE of the foreground subject on a genuinely TRANSPARENT background. Include Lou's complete visible head, fine hair, headphones, face outline, neck, black-clothed shoulders and torso, and the foreground microphone and attached microphone hardware. Remove the entire blue studio background and chair.
Critical registration: keep every silhouette edge in exactly the original pixel coordinates. Keep the SAME FULL ORIGINAL CANVAS dimensions and aspect ratio, 1334 x 1179, no trimming, no recentering, no zoom, no padding changes. Retain original cropping at the image boundaries. Do not draw additional body parts or invent arms or hands beyond the original photograph. Do not move, reshape or resize the person or microphone.
The original photograph's RGB pixels will be displayed through this mask, so precise alignment is essential. WHITE interior for the retained foreground, soft anti-aliased transparent edge for hair and silhouette, completely transparent removed background. No face texture, no colors, no labels, no new scene, no shadow, no checkerboard drawn into the image.
```

### Détourage de Nicolas

```text
Use case: background-extraction.
Asset type: exact registration alpha matte for a real photographic person cutout, to be used as a CSS mask over the UNCHANGED original photo.
Input image is the source photograph of Nicolas. Output ONLY a SOLID OPAQUE WHITE SILHOUETTE of the foreground subject on a genuinely TRANSPARENT background. Include Nicolas's complete visible head, fine hair, headphones, face outline, neck, full black-clothed shoulders and torso down to the source image bottom edge, and the foreground microphone and attached microphone hardware. Remove the entire blue studio background and chair. His BLACK SHIRT must be retained inside the opaque silhouette, not confused with transparent background.
Critical registration: keep every silhouette edge in exactly the original pixel coordinates. Keep the SAME FULL ORIGINAL CANVAS dimensions and aspect ratio, 800 x 800, no trimming, no recentering, no zoom, no padding changes. Retain original cropping at the image boundaries. Do not draw additional body parts or invent arms or hands beyond the original photograph. Do not move, reshape or resize the person or microphone.
The original photograph's RGB pixels will be displayed through this mask, so precise alignment is essential. Flat SOLID OPAQUE WHITE interior for ALL retained foreground, including the black clothing. Only a narrow anti-aliased transparent edge for hair and silhouette, completely transparent removed background. No face texture, no colors, no labels, no new scene, no shadow, no fade-out on the torso, no checkerboard drawn into the image.
```

### Masque de Loïc

```text
Create a flat, untextured black and white segmentation matte of the attached portrait of Loïc, with EXACT pixel registration to the source. FULL CANVAS 1254 x 1254, same scale and crop. Do not move the subject. The person AND his entire black T-shirt and shoulders and foreground microphone boom must be SOLID PURE WHITE (#FFFFFF), ALL background and chair must be SOLID PURE BLACK (#000000). The entire central lower torso region is WHITE, with NO hole, NO gradients, NO fade-out. Clothing counts as person. Convert the complete person's silhouette into one connected flat filled white shape, including his clothing continuing to the bottom edge. No details whatsoever inside the silhouette: no face, no clothing texture, no gray, no black areas within the head or T-shirt. Preserve the original outer edges and fine hair silhouette without recentering. This is an opaque grayscale technical segmentation mask, not a transparent cutout. The background must be solid black, not transparent.
```

### VHS fermée

```text
Use case: product-mockup.
Asset type: photorealistic product cutout of a 1990s VHS video rental clamshell case for an interactive website.
Subject: ONE genuine vintage VHS tape storage case, CLOSED, standing vertically, straight-on front view with a very slight right edge visible. Physical dimensions about 230 mm tall, 135 mm wide, 32 mm thick. This is the chunky large VHS rental box from the 1990s, with thick molded black polypropylene edges, rounded corners, snap closure seam, visible hinge spine, aged clear plastic cover sleeve, fine scuffs, fingerprints and realistic specular reflections. It must look like a real photographed object, not a 3D game icon or a DVD case.
Front: a large plain warm off-white EMPTY paper cover insert under the transparent sleeve, filling the main front face with a thick black plastic border around it. The insert must be blank so project artwork can be printed onto it later. No text, no logo, no fake movie cover, no brand name.
Camera and framing: studio product photograph, 85 mm lens, sharp material microtexture, soft upper-left lighting, gentle natural highlights. Object vertical and centered, complete unclipped silhouette, minimal transparent padding. No ground plane, no cast shadow outside the object, no environment. Output with genuine transparent background.
Avoid: thin DVD jewel case, Blu-ray case, disc, CD, 2D vector art, flat illustration, cartoon, fake CGI shine, heavy perspective distortion, additional objects, hands, labels, lettering, watermarks.
```

### VHS ouverte

```text
Use case: product-mockup.
Asset type: photorealistic cutout of an OPEN 1990s VHS rental clamshell box containing a real VHS cassette.
Reference image 1: the CLOSED box design reference. Use the same thick black molded polypropylene case, aged clear sleeve, scuffed plastic and rounded physical edges.
Primary request: photograph that case open flat like a book, both covers visible. The hinge is vertical between a blank empty left lid and the right molded tray. One authentic FULL SIZE VHS videotape sits securely in the right tray. Full size VHS shell dimensions are 187 mm long by 103 mm tall by 25 mm thick. To fit the vertically standing box, the complete cassette is rotated 90 degrees into PORTRAIT orientation: its TWO TRANSPARENT REEL WINDOWS and white reel hubs are one ABOVE the other, aligned along the long vertical dimension. Its rectangular paper label and horizontal VHS tape features are rotated with the cassette. Do NOT draw a vertical cassette with side-by-side circular reels. The two clear windows show wound brown magnetic tape, real white toothed hubs, molded ridges, screws, locking tabs and the thick top dust flap. No disc, no DVD.
Composition: left lid to the left, right tray to the right, open approximately 180 degrees, shot from nearly perpendicular above with a small realistic angle that reveals the depth of the thick box and tape. Both leaves fully visible with minimal transparent margins. High resolution studio product photography, detailed matte black plastic microtexture, soft upper-left lighting and natural highlights. A plain small aged cream label on the VHS may read only "SANDBOX" and "VHS"; no other text. Background must be genuinely TRANSPARENT, no dark backdrop, no gray gradient, no floor, no shadow outside the product silhouette.
Avoid: DVD case proportions, Blu-ray, CD, optical discs, thin jewel case, vector illustration, CSS-looking graphic, cartoon, fake 3D render, extra reels, wrong reel alignment, tape floating above its tray, hands, extra objects, watermark.
```

## Fichiers concernés

Sous `apps/site/` : `content/hosts.json`, `src/domain/home-studio.ts`, `src/domain/home-story.ts`, `src/domain/video-club.ts`, les composants `discovery-home`, `cinematic-stage`, `studio-door`, `video-club` et leurs feuilles de style, les dictionnaires anglais, espagnol et allemand, les tests `discovery-refonte`, `hosts`, `host-photos` et `video-club`, ainsi que les nouveaux assets ci-dessus.

## Validation et limites

`pnpm check` passe : formatage, lint, types, 618 tests du site dans 95 fichiers, 7 tests de l'introduction et 4 tests des jingles. Aucun contrôle n'est désactivé. Les attentes de trois tests sur l'ancien portrait JPEG de Nicolas ont été mises à jour. Son nouveau fichier est vérifié par son SHA-256. Les copies WebP de Lou et Loïc sont comparées aux pixels RGB des originaux.

Le navigateur confirme le décor sur toute la hauteur du premier écran, sans pseudo-élément de dégradé. À 390 x 844 pixels, le décor et le bloc principal mesurent tous deux 375 x 844 pixels, hors barre de défilement. Les trois portraits se chargent et restent visibles. Les cadrages 893 x 875 et 860 x 1080 ont aussi été inspectés. La taille et la position des personnes sont bornées pour ne pas couper les visages sur un écran étroit. Le cadrage d'ordinateur est restauré après les contrôles mobiles.

Le clic sur la porte en mobile, puis son activation au clavier sur ordinateur, rejoignent le vidéoclub. Sillage peut être ramassé, sa boîte s'ouvre avec la photographie de VHS, puis sa fiche affiche les descriptions, sources et aperçus du catalogue. Aucun lecteur vidéo n'est présent avant le clic sur "Lire la vidéo". Après ce clic, la lecture avance à 14 secondes, avec `readyState` 4 et aucune erreur du lecteur. Échap ferme la fiche et retire le lecteur. Le lien "Retour au plateau" revient à l'accueil. Le lien de la carte de Lou pointe sur `/nos-projets/okodukai`.

Captures réelles du navigateur, conservées dans les fichiers de restitution de la conversation : `accueil-plein-ecran-actuel.jpg`, `accueil-plein-ecran-mobile.jpg`, `vhs-photo-fermee.jpg`, `vhs-photo-ouverte.jpg` et `vhs-fiche-sillage.jpg`.

Le travail reste local, sans publication ni PR. Les détourages ont été inspectés dans le navigateur ; leurs contours ne constituent pas une retouche photographique professionnelle. Le cadrage étroit rapproche les personnes pour les garder visibles. Les masques devront être refaits si les photos sources changent de cadrage. Aucun système de déplacement libre dans le studio n'est ajouté. La réduction des mouvements conserve son comportement prévu par DD-0037 ; la préférence système n'a pas été émulée dans cette itération.
