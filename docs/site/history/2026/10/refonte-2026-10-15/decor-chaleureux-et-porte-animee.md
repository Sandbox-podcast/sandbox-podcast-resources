# Décor chaleureux et porte animée

La composition décrite ici est remplacée par l'[accueil plein écran avec les trois vrais portraits](accueil-plein-ecran-et-vhs.md), selon DD-0038. La provenance du décor et le mécanisme de porte ci-dessous restent valables ; les captures et le cadrage correspondent à l'itération précédente.

15 octobre 2026. Lou demande d'utiliser [son image partagée](https://chatgpt.com/s/m_6ad126abd10881918935aa7673c1f5eb) comme fond de l'accueil, avec une petite porte vers le vidéoclub et une animation d'ouverture. Décision : [DD-0037](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0037-decor-chaleureux-et-ouverture-de-la-porte.md).

## Médias

La page partagée est intitulée "Studio podcast élégant aux lumières chaleureuses". L'image est téléchargée depuis son bouton de média dans le navigateur. L'original est conservé dans `apps/site/public/images/home/studio-warm-source-v1.png`, sans modification. Elle montre trois sièges vides ; aucun animateur n'est ajouté.

Deux fichiers de 1672 x 941 pixels sont servis :

- `studio-warm-v1.webp` : image fournie, optimisée avec Sharp (qualité 92), 241 720 octets.
- `studio-warm-video-club-v1.webp` : variante complète avec porte intégrée, produite par ImageGen intégré, puis optimisée avec Sharp (qualité 92), 210 206 octets.

Les deux fichiers sont dans `apps/site/public/images/home/`. Le PNG original de l'édition est conservé dans les fichiers de génération de la conversation, sous `exec-56aaab83-d968-45a4-8aff-003a705ca617.png`. Les images précédentes restent intactes.

Prompt exact envoyé à ImageGen :

```text
Use case: precise-object-edit.
Asset type: complete photographic website homepage studio backdrop.
Edit target: the provided warm podcast studio image, 1672 x 941 landscape. Preserve this exact room, composition, lens, table, three EMPTY chairs, shelves, plants, wood slats, warm lighting and blue accents.
Primary request: integrate ONE small understated physical access door into the narrow dark blue wall panel immediately to the RIGHT of the central bookshelves and immediately LEFT of the right wooden slat panel and right-hand chair. The door is an architectural detail of the set, not a prominent entrance.
Door position: approximately x=67%-72.2% of the full frame, top at y=15%, lower part naturally hidden by the foreground chair and desk. Respect the foreground occlusion from the chair. The door has a plain FLAT rectangular dark navy leaf in the same shade as the wall, a very thin frame, hinges at its LEFT edge, small handle at right edge, a tiny metal plaque reading exactly "VIDÉO CLUB". No glass, no bright sign, no halo. Make the visible upper leaf clearly rectangular with straight vertical sides, so it could realistically swing inward on its left hinge. Recessed human-scale access to a back room, matching original perspective.
Invariants: change only the small wall region needed for the door. Keep all existing furniture, the desk silhouette and its slat pattern, chair shapes and positions, plants, shelves, decorative objects, colors, lighting and camera crop exactly unchanged. Keep the three seats EMPTY. Preserve the whole landscape composition and 16:9 ratio. Single complete flattened studio image with door integrated.
Avoid: people, microphones, oversized door, storefront, illuminated signage, extra furniture, rearranged room, floating or pasted-on door, extra text, UI elements, watermarks.
```

## Intégration

L'image fournie devient le fond commun de l'accueil. La variante avec porte est utilisée en développement. Le texte est légèrement décalé pour dégager l'entrée. La légende "Décor provisoire" remplace les références à des personnes absentes de l'image, avec traductions anglaise, espagnole et allemande.

`StudioDoor` garde un lien vers `/nos-projets/video-club?from=studio`. Au clic normal, il affiche le magasin derrière le battant, ouvre ce dernier par une rotation CSS sur sa charnière gauche, puis rapproche le décor. La navigation intervient après 1100 ms. Un verrou empêche les activations répétées et le minuteur est nettoyé au démontage. L'événement `pageshow` restaure l'état fermé au retour navigateur.

Le battant est un extrait CSS de la même image complète, cadré sur ses pixels. Il ne s'agit pas d'un second visuel de porte généré puis collé sur le décor. Le plan se partage entre la photo et la cible cliquable afin de conserver l'alignement au défilement.

Le contexte du plateau transmet la réduction des mouvements à la porte. Cette réduction et `prefers-reduced-motion` gardent la navigation native immédiate. Les clics avec Ctrl, Cmd, Maj ou Alt gardent également leur comportement natif. Sans JavaScript, le lien ouvre directement le magasin. La route du vidéoclub conserve son refus en production.

Fichiers concernés sous `apps/site` : `src/domain/home-studio.ts`, `src/components/studio-door.tsx`, `src/components/discovery-home.tsx`, `src/components/cinematic-stage.tsx`, `src/components/discovery-home.module.css`, les trois dictionnaires et `test/discovery-refonte.test.ts`.

## Validation

`pnpm check` passe après intégration : formatage, lint, types, 616 tests du site dans 95 fichiers et 11 tests média. Les tests vérifient les deux WebP, leurs dimensions et budgets, le lien natif de la porte, l'absence de chargement du magasin avant le clic et la nouvelle légende.

Dans le navigateur, le clic affiche la porte ouverte et l'intérieur du magasin, puis arrive dans le vidéoclub avec les 34 cassettes et l'état d'entrée actif. Après activation de "Réduire les mouvements", Entrée sur le lien rejoint directement le magasin. Le navigateur a nécessité le redémarrage du serveur de développement hors du bac à sable Windows pour y accéder.

À 390 x 844 pixels, le décor entier et la porte restent visibles sans débordement horizontal. La cible mesure 44 x 57 pixels. Le clic déclenche l'ouverture, puis arrive dans le magasin avec l'état d'entrée actif. Le cadrage d'ordinateur est ensuite restauré.

L'ouverture au clavier et le retour arrière du navigateur sont vérifiés : la porte revient fermée avec `data-opening="false"`. La console ne remonte aucune erreur ni aucun avertissement depuis le dernier rechargement. La préférence système de réduction des mouvements est prise en compte dans le code, mais n'a pas été émulée ; le bouton de réduction du plateau a été testé.

Captures de restitution, hors Git : `accueil-decor-chaleureux.jpg`, `porte-ouverture-1.jpg`, `porte-ouverture-2.jpg`, `accueil-decor-chaleureux-mobile.jpg` et `porte-ouverture-mobile.jpg`. L'aperçu `porte-video-club-apercu.gif` assemble avec FFmpeg les captures réelles de l'ouverture et de l'arrivée, avec un temps de lecture ajouté au début et à la fin.

Limites : prototype local, sans déploiement. L'ouverture est une transition entre une image photographique et le vidéoclub, pas une simulation complète de l'espace du studio.
