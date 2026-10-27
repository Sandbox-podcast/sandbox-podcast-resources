# Retouches des bustes du plateau

16 octobre 2026. Lou demande de compléter l'épaule coupée de Loïc et celle de Nicolas, puis de retirer les micros qui flottent devant les trois personnes. Cette demande complète [DD-0038](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0038-accueil-plein-ecran-portraits-reels-et-vhs.md).

## Correction après revue locale

Lou signale des raccords visibles au cou et des problèmes de proportions selon la largeur. La composition actuelle utilise les trois variantes complètes ci-dessous, chacune en une seule image. Les paragraphes décrivant les deux plans rendent compte de l'essai précédent, remplacé. Les captures et contrôles de cet essai ne valident pas la correction actuelle. Voir le [rapport de correction responsive et biographie](corrections-responsive-bio-2026-10-16.md).

## Retouches

### Décor sans chaises, après la correction des proportions

Le 16 octobre, Lou autorise le retrait des chaises et demande d'espacer les personnes sur mobile. ImageGen intégré produit `exec-04c8a8ce-f5bc-4a97-98cc-872744d4b363.png`, conservé dans le dossier `generated_images/01a14076-a18e-77f1-a4b2-9ee6592e8d66` de Codex. La copie WebP de 1672 x 941 pixels est `apps/site/public/images/home/studio-chairless-v2.webp`. Seule sa bande contenant les anciens dossiers est affichée, derrière les portraits et le bureau d'origine. Les portraits ne sont pas retouchés pour cette correction.

Prompt de l'asset intégré :

> Edit target: supplied podcast studio background. Precise object removal for a website. Remove ONLY the three gray chair backs behind the desk, reconstruct the vertical wooden wall slats and warm lighting hidden behind them. The studio must be completely empty of chairs and people. Preserve exact composition, camera, 1672:941 aspect ratio, the entire desk surface and its back edge at y470, door at upper right, plants, shelves, colors, all other objects. No new objects. Do not move, resize or redesign the table. This is a minimal inpainting edit; all pixels outside the three chair areas should remain visually unchanged.

Un dossier transparent a été généré pendant l'essai intermédiaire, puis retiré du rendu après la demande de Lou. Le fichier `studio-chair-back-v2.webp` reste conservé mais n'est ni référencé ni chargé. Source : `exec-004cd777-8329-41b6-9b9a-54468334704f.png`. Prompt :

> Create a single isolated photorealistic gray upholstered chair BACKREST matching exactly the gray fabric chairs in the supplied studio reference. Asset for compositing behind a seated podcast host. Front view, symmetrical upright tall rounded trapezoidal backrest, broader at bottom, rounded top corners, dark warm gray woven fabric, subtle warm rim light from the studio. Only the complete backrest, no legs, no seat cushion, no armrests, no desk, no room, no person, no floor, no cast shadow beyond the object. Actual transparent background. Backrest fills canvas tightly with a small transparent margin, centered, approximately square aspect ratio. Real photographic fabric texture, not a vector shape or illustration.

### Retouches des personnes précédentes

ImageGen intégré produit trois variantes transparentes à partir des vraies photos. Les vêtements masqués par les micros sont reconstruits. Le buste de Loïc est complété à gauche de l'image ; celui de Nicolas à droite. Les micros, suspensions et bras métalliques disparaissent du plateau. Les photos sources restent intactes, y compris sur les pages de profils.

Chaque personne utilise deux plans : le buste retouché derrière et la tête issue de la photo d'origine devant. Les yeux, le nez, la bouche, l'expression, les cheveux et les casques viennent des photos sources. Le bas de la barbe rejoint progressivement le buste pour éviter une couture au cou. Les masques de tête excluent les anciens micros. Aucun pixel de vêtement retouché ne remplace la partie centrale du visage.

Les variantes générées ne conservant pas exactement le cadrage demandé, les bustes sont recalés avant affichage. Une comparaison de motifs photographiques fournit un premier alignement ; le raccord du cou est ensuite ajusté visuellement. Lou conserve le cadrage de son portrait. Les têtes ne changent ni de position ni de proportions. La table masque toujours le bas des bustes.

Les limites de cadrage tiennent compte de la largeur des épaules complétées. Sur téléphone, le trio utilise une composition plus compacte.

## Assets et sources

Fichiers servis sous `apps/site/public/images/home/` :

| Fichier                       | Dimensions | Octets  |
| ----------------------------- | ---------- | ------- |
| `lou-body-no-mic-v2.webp`     | 900 x 795  | 112 384 |
| `loic-body-no-mic-v2.webp`    | 900 x 900  | 107 036 |
| `nicolas-body-no-mic-v2.webp` | 900 x 900  | 143 758 |

Les images sont converties en WebP avec Sharp, qualité 92 et alpha conservé. Leur cadrage complet est conservé ; aucun recadrage sur la silhouette n'est appliqué.

Les originaux ImageGen restent sous `C:/Users/Lou/.codex/generated_images/01a14076-a18e-77f1-a4b2-9ee6592e8d66/` :

- Lou : `exec-738f959a-554f-4b69-88f9-a36af3d720c4.png`.
- Loïc : `exec-de5d748a-9f41-4a27-a02c-f0aab6eaac20.png`.
- Nicolas : `exec-6f39550c-8822-4834-80f4-e37001283900.png`.

Références : `public/team/lou.png`, `public/team/loic.png` et `public/team/nicolas-prod-2026-10-15.webp`. La provenance et le contrôle du fichier de production de Nicolas restent consignés dans le [rapport précédent](accueil-plein-ecran-et-vhs.md).

Pour Loïc et Nicolas, une copie de référence ajoute uniquement des marges transparentes autour des pixels d'origine. Ces références de travail restent dans les fichiers de restitution de la conversation, sous `studio-loic-reference-epaules-v2.png` et `studio-nicolas-reference-epaules-v2.png`. Elles servent à donner de la place aux épaules manquantes ; elles ne sont pas utilisées par le site.

## Prompts exacts

Mode utilisé : outil ImageGen intégré, avec une génération par portrait et fond transparent demandé.

### Lou : retrait du micro

```text
Use case: precise-object-edit, identity-preserve, background-extraction.
Asset type: transparent photographic bust for a website studio composition.
Edit target: the original portrait of Lou, full 1334 x1179 canvas. Preserve exact existing head, neck, body scale, pose, crop and pixel registration. Do not recenter, zoom, shift, shrink or redesign the person.
Primary request: remove the foreground microphone completely, including its foam windscreen, metal suspension cage, boom arm and microphone cable. Reconstruct the black sweatshirt and torso that were hidden behind the microphone, with natural continuous black fabric, seams and folds.
Preserve the exact real face, hair, beard, expression, headphones, body proportions, existing sweatshirt shape and lighting. Do not invent new gestures, hands or a new pose. The untouched original head will be overlaid on the website; maintain the neck and shoulders at the original coordinates.
Remove the entire blue studio background and chair, leaving only the person as a complete isolated photoreal cutout on a genuine transparent background. All black clothing remains fully opaque, no holes, transparency or fade-out inside it.
No microphone, stand, boom, suspension hardware, extra objects, new furniture, text, watermark or cast shadow. Keep the full original 1334 x1179 canvas and original registration.
```

### Loïc : épaule et retrait du micro

```text
Use case: identity-preserve and precise-object-edit.
Asset type: transparent photographic bust for a website studio composition.
Edit target: the provided padded original photograph of Loïc. The full square canvas is 1882 x1882. The original 1254 x1254 photograph occupies the rectangle x314,y314 through x1568,y1568. Keep this EXACT full canvas, crop and subject registration. Do not trim, recenter, zoom, move, enlarge, shrink, rotate or pose the head or body.
Primary request: remove the microphone, pop filter, boom arm, suspension, metal hardware and their cables completely. Reconstruct the black T-shirt and torso that they hide. Complete the cropped shoulder on the VIEWER'S LEFT by extending his existing shoulder, sleeve and upper arm naturally into the transparent left padding. Ensure both shoulders and upper arms have complete rounded natural outer contours, with no vertical cutoff at the old photo boundary. Show a relaxed seated upper body in the exact existing pose and proportions, in the same plain black T-shirt.
Keep the head, hair, headphones, face, beard, neck and expression in their original positions and likeness. No face beautification or redesign. The website will overlay the untouched original head, so the shoulders and neck MUST meet the original neck at its exact source coordinates.
Remove the entire studio background and chair to genuine transparency. Retain the entire shirt as fully opaque black fabric, not holes or a fade-out. Fine real photographic fabric, seams and folds, existing neutral skin lighting, no new blue rim light. Only complete missing clothing/anatomy and remove the microphone.
Output one complete isolated photoreal person cutout on true transparent background. No new furniture, table, microphone, mic stand, hand-held object, text, watermarks or cast shadow. Do not stretch the head or make the shoulders too broad. Preserve the full canvas and exact original pixel registration.
```

### Nicolas : épaule et retrait du micro

```text
Use case: identity-preserve and precise-object-edit.
Asset type: transparent photographic seated bust for a website studio composition.
Edit target: padded original production photograph of Nicolas. Keep the full 1200 x1200 square canvas. The original 800 x800 photo is at x200,y200. Do not trim, recenter, zoom, move, rotate or change the existing head or body scale.
Primary request: remove the entire foreground microphone, pop filter, suspension, boom arm and microphone cables. Reconstruct the black crew-neck sweater and torso hidden behind that microphone. Complete the missing shoulder and upper arm on the VIEWER'S RIGHT, extending the existing black sweater naturally beyond the original photo's right boundary into the transparent padding. Both shoulders must have complete natural rounded contours and balanced realistic body proportions. Extend only the absent clothing/shoulder, retain the exact seated pose and head tilt.
Preserve his real head, face, beard, hair, headphones, expression, neck, and existing lighting. No altered facial features or beautification. The untouched original head will be layered over this image on the website, so the neck and shoulders must stay aligned to the original photo coordinates.
Remove the entire blue studio background and chair. One isolated realistic photographic bust on genuine transparent background. Keep all black clothing fully opaque, no holes and no fading body. Black knitted sweater material with believable folds and seams, no logos. No microphone, mic stand, metal hardware, floating object, hands, new furniture, text, watermark, or cast shadow. Do not make the shoulders excessively wide. Preserve the original image registration and full canvas.
```

## Fichiers modifiés et vérification

Les composants concernés sont `apps/site/src/components/discovery-home.tsx`, sa feuille de style, `src/domain/home-studio.ts`, `test/discovery-refonte.test.ts` et les trois nouveaux WebP.

`pnpm check` passe : formatage, lint, types, 618 tests du site dans 95 fichiers, 7 tests de l'introduction et 4 tests des jingles. Les tests conservent la comparaison des copies de portraits avec les pixels sources et ajoutent le budget, la transparence et l'utilisation des trois bustes retouchés. Aucun contrôle n'est désactivé.

Dans le navigateur, le plateau est inspecté au cadrage courant, à 390 x 844 pixels, à 860 x 1080 pixels et à 1440 x 900 pixels. Les épaules complétées sont visibles, les six plans d'images se chargent et les anciens micros ne sont plus affichés. Les raccords au cou sont corrigés après inspection. La porte reste cliquable sur mobile, rejoint le vidéoclub et permet le retour au plateau. Le cadrage est restauré après les contrôles.

Captures de restitution : `accueil-bustes-sans-micro-mobile-v2.jpg`, `accueil-bustes-sans-micro-etroit-v2.jpg`, `accueil-bustes-sans-micro-large-v2.jpg` et `accueil-bustes-sans-micro-v2.jpg`, dans les fichiers de la conversation.

Cette retouche reste locale. Aucun commit, push, PR ou déploiement n'est effectué. Les épaules et les zones autrefois cachées par les micros sont des reconstitutions générées à la demande de Lou.
