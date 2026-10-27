# Porte du vidéoclub sur l'accueil

Le décor décrit ici est remplacé par l'image chaleureuse fournie par Lou et sa porte animée : [version suivante](decor-chaleureux-et-porte-animee.md) et [DD-0037](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0037-decor-chaleureux-et-ouverture-de-la-porte.md).

15 octobre 2026. Demandes de Lou : intégrer une porte au décor complet, la rendre plus discrète, ajouter deux petits boutons vers YouTube et Spotify. Décision : [DD-0036](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0036-porte-du-videoclub-et-liens-des-chaines.md).

## Image

Image finale : `apps/site/public/images/home/sandbox-trio-tv-video-club-v5.webp`, 1672 x 941 pixels, 193 134 octets. Générée avec l'outil ImageGen intégré, puis convertie en WebP avec Sharp (qualité 92). Le fichier original `sandbox-trio-tv-v3.png` reste intact et sert toujours hors développement.

Source d'édition : `apps/site/public/images/home/sandbox-trio-tv-v3.png`. Sortie originale conservée dans les fichiers de génération de la conversation : `exec-2579a9a4-d993-49b4-8d88-145306d5da7c.png`.

La porte est intégrée aux pixels du décor. Aucun fichier de porte séparé n'est chargé dans la page. Le lien occupe la zone de la porte dans un cadre aux mêmes proportions que l'image. Le cadre et le lien partagent les déplacements du plateau. Sur mobile, l'image entière reste visible.

Prompt final exact :

```text
Use case: precise-object-edit.
Asset type: complete photographic TV studio backdrop for homepage, landscape 16:9.
Input image 1 is the EDIT TARGET: preserve this studio photo with its three podcast hosts.
Primary request: integrate a SMALL, DISCREET access door into the far-right rear wall of this studio, leading to a 1990s video rental shop. It is an understated detail to discover in the scenery, not a prominent feature.
Placement and scale: within the wall panel to the right of the desk and trio, just left of the right illuminated column, at approximately x=83.5%-89.5% of the full image, from y=32% down to y=58%. Total door width about 6% of the image and height about 26%. Align the threshold with the rear wall floor, naturally recessed, realistic perspective and human scale further back.
Design: flush panel door in the same dark blue as the wall, understated narrow seams, minimal small metal handle. No bulky jamb. One small narrow vertical glass slit with a very faint warm glow and barely suggested VHS shelves. A tiny non-illuminated brushed metal plaque at eye level says exactly "VIDÉO CLUB" in small understated lettering. No large sign above the door, no bright amber lightbox, no glowing threshold, no halo, no conspicuous warm lighting. The door must blend into the blue wall.
Invariants: preserve all three people's identities, faces, hair, clothing, hands, expressions, headphones, microphones, chairs and positions EXACTLY. Preserve the desk, curved platform, floor, ceiling truss, studio lighting, blue wall design and all other objects unchanged. Preserve original framing and camera. Edit ONLY the small far-right wall region necessary for the integrated door. Single flattened complete photographic image.
Avoid: large entrance, big door, storefront, illuminated signage, bright amber accents, extra people, changed faces, changed poses, new furniture, pasted-on appearance, extra text, logos, watermarks, UI buttons, borders.
```

## Parcours et fichiers

`DiscoveryHome` reçoit l'activation depuis la page serveur d'accueil, uniquement en développement. Son lien ouvre `/nos-projets/video-club?from=studio`. La route attend les paramètres de recherche Next.js et transmet un état d'entrée initial au vidéoclub. Les accès directs gardent l'écran d'accueil du magasin. La route refuse toujours les environnements de production et de test.

Les boutons de plateformes lisent `siteConfig.platforms`. YouTube utilise `https://www.youtube.com/@SandboxFR`. Lou transmet le lien de l'épisode Spotify `4Dq1kMkrvdHlsp8gYfO1vJ`. Sa page associe l'épisode à [Sandbox Podcast](https://open.spotify.com/show/2Wp6S4qgRqQaV01AjkDcMH), confirmé dans le navigateur par le lien "Voir tous les épisodes" et le titre de la page. Le réglage `content/site.json` utilise cette adresse d'émission, sans paramètres de partage. Le bouton reste désactivé si un réglage ultérieur ne contient que l'accueil de Spotify.

Fichiers d'interface modifiés : `src/app/(fr)/page.tsx`, `src/app/(fr)/nos-projets/video-club/page.tsx`, `src/components/discovery-home.tsx`, `src/components/discovery-home.module.css`, `src/components/video-club.tsx`. Tests adaptés : `test/discovery-refonte.test.ts` et `test/video-club.test.ts`, sous `apps/site`.

## Validation

La génération finale conserve le trio, la table et le plateau à la lecture visuelle. Le navigateur charge l'image optimisée et confirme le clic vers les 34 cassettes avec l'état d'entrée actif et le lien de retour à `/`.

À 390 x 844 pixels, l'image entière et la porte restent visibles, sans débordement horizontal. La zone de porte mesure 44 x 55 pixels. L'activation au clavier ouvre directement la salle, sans second bouton d'entrée. La légende et les boutons sont espacés. Le cadrage d'ordinateur est restauré après les contrôles. Le rechargement final ne produit aucune erreur ni aucun avertissement dans la console.

`pnpm check` passe : formatage, lint, types, 615 tests du site dans 95 fichiers et 11 tests média. Les tests ajoutés couvrent l'image intégrée, les liens de chaînes et l'absence de fausse destination Spotify, l'entrée directe depuis le plateau et le maintien du refus en production. Une erreur de lint dans le nettoyage du test a été corrigée avant cette exécution complète.

Captures réelles conservées dans les fichiers de restitution de la conversation, hors Git : `accueil-porte-discrete-boutons.jpg`, `accueil-porte-discrete-mobile.jpg` et `video-club-depuis-plateau.jpg`.

Les premiers tests ciblés échouent avant leur exécution sur des fichiers temporaires absents du bac à sable Windows. Une relance hors bac à sable est nécessaire, sans modifier les tests.

Limites : essai local, sans déploiement. L'image reste un photomontage provisoire.
