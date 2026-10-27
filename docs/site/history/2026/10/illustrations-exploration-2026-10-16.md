# Illustrations d'Explorer l'IA

16 octobre 2026. Travail local demandé par Lou. Direction décidée par l'agent sur délégation (PD-0003), avec une revue de composition par l'agent de direction artistique.

Lou demande un rendu photoréaliste : une succession d'images du passé, du présent et du futur pour Time Machine, ainsi qu'une illustration plus sobre pour les classements. Les premières propositions de machine et de podium sont écartées à sa demande.

La Time Machine reçoit un assemblage de tirages photographiques : anciens laboratoires, ordinateur à écran cathodique, ordinateur actuel, centre de données, collaboration avec un robot et ville future. Les scènes sont générées ; elles ne sont pas des documents historiques. Les classements reçoivent trois fiches en papier ivoire portant les numéros 01, 02 et 03, photographiées sur un bureau sombre.

Les images sont décoratives. Les titres et descriptions restent du texte HTML ; les liens conservent leur nom accessible, leur description et leur destination. Les trois numéros ne représentent aucune donnée réelle.

## Intégration

- Time Machine : `apps/site/public/images/home/explore/time-machine-photographs-v2.webp`, 1 122 x 1 402 pixels, 198 134 octets.
- Classements : `apps/site/public/images/home/explore/charts-editorial-v2.webp`, 1 122 x 1 402 pixels, 119 408 octets.
- Total des fichiers : 317 542 octets, soit environ 310 Kio. Next Image sert une largeur adaptée à l'écran et charge les illustrations à l'approche de la section.
- Compression WebP à qualité 88, sans retouche de l'image générée. Les PNG originaux sont conservés dans le dossier de génération de cette conversation.
- `DiscoveryStory` utilise les deux images. Les anciennes orbites, graduations, barres et grilles CSS de cette section sont retirées.
- Les deux panneaux ont la même largeur. Les titres sur ordinateur occupent une ligne pour dégager les images. Un voile protège le texte et les libellés ont un fond sombre.
- Au survol, le zoom est limité à 4,5 % et respecte la pause globale ainsi que la préférence système de réduction des mouvements. La pause supprime immédiatement les transitions.
- Le titre des classements s'adapte à la largeur de 320 pixels sans déborder.

## Sources de génération

Mode : génération intégrée, sans référence fournie ni image existante modifiée. Chaque appel produit une illustration indépendante.

Original Time Machine : `C:/Users/Lou/.codex/generated_images/01a14554-0942-7ab0-8912-1f0dc142b989/exec-6b900dfc-c752-4459-bc88-bec8da702bab.png`.

Original Classements : `C:/Users/Lou/.codex/generated_images/01a14554-0942-7ab0-8912-1f0dc142b989/exec-3935302b-26f4-4a19-8a99-c7b42a99d56b.png`.

Les deux images sont inspectées avant intégration. Les premières propositions écartées restent dans les fichiers de cette conversation ; elles ne sont plus servies par le site.

## Prompt final : Time Machine

```text
Create a premium PHOTOREALISTIC editorial photograph for a French technology-history website card. The visual tells a journey through PAST, PRESENT and an imagined FUTURE through many actual photographic images. The photographs themselves are the subject. Absolutely no portal, no time machine prop, no glowing mechanical rings, no holograms, no sci-fi metal sculpture, no illustration, no CGI trophy aesthetic.
A beautiful physical contact-sheet / photo-editing-table composition: six to eight large photographic prints form a flowing chronological ribbon, gently curving across a charcoal photography studio table in shallow perspective. Several prints overlap a little but their main scenes remain visible. This must feel like a real photograph of real photographic paper, with subtle curled edges, silver-gelatin grain, satin print texture and believable soft daylight shadows. The left/back prints show the past in archival black-and-white: an anonymous engineer beside an early room-sized computer with tape reels, a vintage computer laboratory, then a warm faded-color beige CRT desktop and old keyboard. The central larger prints show today's world: close detail of a contemporary laptop with indistinct screen in use by hands, a modern data-center aisle with realistic server equipment. The final larger prints on the right/front show a plausible imagined future in beautiful natural color: a human and a restrained human-scale collaborative robot working in a bright architectural laboratory, and a green sunlit future city with an elegant elevated train. No identifiable real historical person, no recognizable company logos, no readable screen text. Clearly distinct photographic scenes and eras, no repeated pictures. The transition from monochrome to natural warm and cool color is visually clear.
Art direction: cultured editorial photography, contemporary magazine cover quality, sophisticated analog/digital juxtaposition, tactile photographic evidence, very slight depth of field but the major photos are sharp and recognizable even at small sizes. No dramatic neon, no excessive haze, no fantasy museum, no magical floating objects. One small cyan accent along the edge of the dark table is enough; mostly true photographic colors, charcoal and deep navy negative space.
Composition portrait 4:5, the flowing mosaic of photos occupies the upper 65% of the artwork, central 85% of the width. Three important photos are large; smaller supporting photos create the sense of many memories. Photographs at the back recede toward the top, the front row spans the middle of the image. Bottom 30% is a quiet clean deep navy/charcoal tabletop fading into shadow, without essential detail, reserved for an HTML title and description later. Top 8% is calm and dark for a small label. No text, no headings, no dates, no lettering, no watermark in the finished artwork. This should look like a beautifully photographed spread of images, not an interface, not a dashboard, not a 3D-rendered machine.
```

## Prompt final : Classements

```text
Create a restrained, sophisticated PHOTOREALISTIC editorial still-life photograph for the rankings section of a French technology-culture website. No futuristic podium, no trophy, no crown, no metallic monoliths, no neon light trails, no bar chart, no 3D CGI illustration, no UI screenshot.
On a beautiful dark charcoal desk, three thick ivory uncoated paper index cards are arranged in a simple, carefully composed diagonal stagger. The front card is clearly most prominent, with a large beautifully printed black "01"; behind it to the right a second card shows "02", and a third slightly further back shows "03". All three rank numbers are clearly readable, each appears only once. The front card occupies about one third of the image width; real heavy paper, a barely curled corner, fine visible paper fibers, realistic soft contact shadows and thickness at the edges. The numbers use elegant bold classic typography, precisely printed in matte black ink, not embossing, no gold. One short very fine muted cyan rule beneath each number is the only color accent. Otherwise each card is blank, no names or scores or invented data or logos. It reads instantly as an editorial selection and an ordered ranking.
Natural raking daylight from upper left, a soft shadow falls to the right, subtle warm ivory against deep navy and charcoal. Photograph with a high-end full-frame camera and a normal macro lens; restrained depth of field, keep all three numbers sharp. Realistic studio photography, tangible everyday material, sober, tasteful, modern editorial design. Minimal but striking because of composition, texture and beautiful light. Not a flat graphic, not vector art, not an artificial object in a science-fiction gallery.
Composition portrait 4:5: all three paper cards are in the central 75% of the width and upper 65% of the image, viewed from a subtle three-quarter top angle. Foremost "01" card starts around x=20%, y=24%, the others step toward x=48%, y=14% and x=64%, y=9%. Leave comfortable margins so cropping a small website card does not cut any number. Bottom 30% is quiet empty deep charcoal tabletop fading to near-navy black for an HTML title later. Top 8% also dark and calm. Generate only the photograph. The only lettering in the image is exactly the three rank numbers "01", "02", "03".
```

## Vérification

Contrôles exécutés sur la copie locale :

- `pnpm check` : réussi. Formatage, lint et types valides ; 686 tests du site et 33 tests des autres projets, soit 719 tests réussis. Les derniers ajustements de cadrage ont aussi été vérifiés par Prettier et par le build.
- `pnpm --filter @podcast/site exec next build --webpack` : réussi après les derniers ajustements, 203 pages statiques générées.
- Navigateur Codex : sept largeurs contrôlées, 320, 390, 700, 701, 900, 1 280 et 1 920 pixels. Aucun débordement de page, de titre ou de description. Les trois rangs restent visibles à 320 pixels.
- Les deux images finales sont chargées sur ordinateur et téléphone. Les captures montrent la version intégrée en 1 280 x 720 et 390 x 844.
- Navigation au clavier depuis Time Machine vers les classements : focus visible et contenu immédiatement révélé. Les deux destinations ont été ouvertes depuis les panneaux.
- Pause globale : les transformations des deux images deviennent nulles et leurs transitions passent à zéro. La préférence système de réduction des mouvements est traitée dans les styles, sans émulation du réglage système pendant cette recette.
- Aucun message d'erreur dans la console du navigateur lors de la vérification finale.
- `git diff --check` et vérification rédactionnelle : réussis.

Les captures sont jointes directement à la conversation et conservées dans son dossier local : `sandbox-exploration-photo-v2-desktop.jpg`, `sandbox-time-machine-photo-v2-mobile.jpg` et `sandbox-classements-photo-v2-mobile.jpg`.

Les changements concernent `DiscoveryStory`, `discovery-chapters.module.css`, les deux WebP et les documents de conception. Aucun nouveau test unitaire n'est ajouté pour ces illustrations ; les contrôles existants et la vérification réelle du rendu couvrent cette modification visuelle. Les essais de dimensions ne remplacent pas une mesure de performance sur un téléphone physique.

Aucun commit, push, PR ou déploiement n'est réalisé. Aucune question fonctionnelle ne reste ouverte pour ce lot ; l'appréciation visuelle appartient à Lou.
