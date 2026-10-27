# Visuel provisoire du plateau

## Version courante : trio sur un plateau télé

La version présentée après les corrections de Lou est `apps/site/public/images/home/sandbox-trio-tv-v3.png`, générée avec l'outil intégré `image_gen`. Elle utilise les portraits `public/team/lou.png`, `public/team/loic.png` et `public/team/nicolas.jpg` comme références d'identité, sans modifier ces fichiers sources. Le composant d'accueil affiche " Plateau provisoire · photomontage ". Les poses, les corps et le décor sont synthétiques.

Un premier montage a été écarté à la demande de Lou : trio trop serré, décalé à droite et trop grand par rapport à la table. La deuxième version (`sandbox-trio-stage-v2.png`) recentre et espace le trio, réduit la taille relative des personnes et agrandit la table. La troisième conserve ce cadrage et remplace le fond par un studio de télévision : mur LED incurvé, lumières et structure de plateau. Cette image est intégrée à la homepage selon [DD-0033](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0033-accueil-cinematique-et-trio-sur-plateau-tv.md).

Prompt de la dernière retouche, avec la deuxième version et les trois portraits comme références :

```text
Use case: precise-object-edit / background replacement. Edit the supplied corrected SANDBOX trio photomontage. USER REQUEST: the background must look like a genuine television broadcast studio, not a dark interior room. PRESERVE INVARIANTS: preserve the three seated people, their facial identities, relative positions, equal scale, bodies, black clothing, microphones, desk size and frontal camera distance. Lou left, Loïc center, Nicolas right. Keep their head size and the desk-to-person proportions exactly as in the corrected reference. The additional three portraits are identity references only. CHANGE THE ARCHITECTURE BEHIND THEM: replace the dark residential-looking wall, plants and wooden slats with an impressive professional contemporary TV talk-show set. A very wide subtly curved LED video wall spans the full background, showing restrained abstract midnight-blue and cyan broadcast graphics with clean lines, no lettering or data. On both sides, modern architectural broadcast panels and a little visible studio depth. A realistic overhead lighting grid and a few professional soft panels at the top edge make it unmistakably a television studio, but keep the upper central background simple and dark enough for white website text overlay. Bright professional facial key lighting, blue/cyan rim light, polished charcoal studio floor with controlled reflections, big clean semicircular broadcast desk and central platform remain. Premium French evening technology talk show, sophisticated contemporary broadcast design. Balanced symmetrical wide establishing shot with all three seated behind a correctly scaled desk. No new people, no cameras blocking the foreground, no logos, no ticker, no words, no fake news, no watermarks. Output 16:9 widescreen.
```

L'identité visuelle des personnes reste à juger par Lou : une consigne de conservation des visages ne garantit pas leur fidélité exacte. Le logo et les textes de la page restent séparés de l'image. Le cadrage mobile est vérifié à 320 et 390 pixels.

## Première version : décor vide

Le 15 octobre 2026, Lou demande une image d'attente pour composer la landing page pendant la conception du plateau définitif. Ce décor est un support de travail local, pas une proposition de scénographie validée.

Fichier initial : `apps/site/public/images/home/sandbox-stage-placeholder-v1.png`. PNG de 1672 × 941 pixels, généré avec l'outil intégré `image_gen`. Cette version a servi à la première revue et est remplacée sur l'accueil par le trio sur plateau télé. Les images d'accueil sont servies avec `next/image` et une taille responsive.

Le texte et le logo de la page ne sont pas intégrés au bitmap. Remplacer l'image ne nécessite pas de refaire le message. Le cadrage mobile conserve les trois places en rapprochant le décor sous le texte.

## Prompt utilisé

```text
Use case: stylized-concept. Asset type: temporary hero image for the SANDBOX French AI and tech podcast website. Create one exceptionally clean, photorealistic architectural 3D rendering of an empty virtual podcast set for three hosts. Wide panoramic 16:9 image, camera facing the stage straight-on at human eye level with strong but natural depth. A low dark rounded desk with exactly three understated microphones and three empty chairs, on a shallow circular stage. Large architectural curved panels in the background, matte charcoal and midnight navy materials, subtle brushed metal, restrained soft cyan lighting integrated into the set, warm off-white key light. Premium editorial feel, calm and sophisticated, minimal objects, no busy equipment, no sci-fi spaceship, no RGB gamer aesthetic, no neon outlines everywhere, no gratuitous decorative details. Plenty of dark negative space above the set; the scene sits in the central and lower two thirds, wide dark margins. This is a disposable placeholder to help test a homepage composition before the real show set arrives. No people, no faces, no text, no logos, no watermarks. The future hosts' camera feeds will be composited later; do not draw screens or fake camera feeds.
```

## Remplacement

Quand la scène finale arrive, vérifier sa composition derrière le titre, le recadrage à 320 et 390 pixels, son poids et ses droits. Retirer la légende provisoire seulement après remplacement. Si une vidéo ou un maillage est retenu, garder cette interface textuelle et un poster statique. Les mouvements, la caméra et les performances devront faire l'objet d'une prochaine itération locale avec les vraies ressources.
