# Vidéoclub V12 : cadrage et entrée mobile

16 octobre 2026. Conception décidée par l'agent sur délégation (PD-0003), à la demande de Lou.

## Changements

Le décor occupe presque toute la hauteur sous l'en-tête ivoire. La recherche et les boutons de rayon flottent dans le cadre sur un fond encre translucide. La vue d'ensemble recule pour montrer l'enseigne ; le cadrage des rayons conserve la marge nécessaire pour éviter des bandes vides sur les côtés. Le décor, les objets VHS et les données du catalogue sont conservés.

La cassette ramassée apparaît avec une ombre sur un fond ivoire. Sur ordinateur, l'objet et son titre sont côte à côte. Sur téléphone, la présentation reste verticale. Les aperçus au survol sont masqués sur téléphone pour ne pas couvrir les rayons. Les commandes restent accessibles au clavier et l'ouverture respecte la réduction des mouvements.

La carte de l'accueil mobile utilise désormais une image dédiée de porte entrouverte vers des rayons de VHS. Le titre est ajouté en HTML. Le lien reste après YouTube et Spotify, uniquement lorsque le prototype est activé. Le plateau desktop et sa porte cachée ne sont pas modifiés.

## Image

Outil intégré ImageGen, sans CLI ni dépendance ajoutée. Scène fictive générée, aucun portrait utilisé. Source conservée : `C:/Users/Lou/.codex/generated_images/01a14076-a18e-77f1-a4b2-9ee6592e8d66/exec-31a04b87-e99e-4771-a632-f8188d67040f.png`.

Asset du site : `apps/site/public/video-club/entrance-cinematic-v2.webp`, 1672 x 941 pixels, 172 350 octets. Conversion WebP qualité 92 sans recadrage. Les médias précédents restent disponibles.

Prompt transmis :

```text
Use case: photorealistic-natural. Create a premium cinematic architectural photograph for the mobile homepage of Sandbox, a French tech podcast. Landscape 16:9 composition. A mysterious doorway from a refined contemporary podcast studio into a tiny authentic French video rental shop circa 1998. The image is entirely a fictional physical scene, not a website mockup. Right of center, a deep midnight blue door is halfway open, with a real brushed brass handle, tiny old brass plaque 'VIDÉO CLUB'. Through the opening we see richly textured dark walnut shelves densely filled with real chunky VHS tapes, an amber ceiling lamp and a soft red neon glow deeper in the shop. The visual hook is the extraordinary contrast of warm amber and red light spilling through the doorway onto the cool dark blue studio wall and floor. Left third is atmospheric clean dark slate wall with subtle reflected light, intentionally quiet for a small white HTML caption. A few warm vertical wood slats frame the extreme right. No people, no screens, no studio furniture, no logos, no YouTube logo, no graphic text overlay, no arrows, no watermark. Genuine high-end film still, photographic materials, beautiful controlled chiaroscuro, slight haze only inside the doorway, tactile brass, worn door edges, restrained 35mm film grain, sophisticated color grading, grounded realism, no CGI or cartoon effect. Medium-wide shot, doorway fully visible, elegant straight verticals, immersive sense of discovery.
```

## Vérification

Les 31 tests ciblés de l'accueil et du vidéoclub passent. Ils couvrent notamment la marge du décor dans les vues latérales, le cadrage distinct de la vue d'ensemble, la présence de l'asset et son budget de 200 Ko, ainsi que la réservation du lien au prototype local.

Vérifications navigateur avec Playwright : recherche de Sillage, sélection depuis la liste, ouverture animée, titre de la fiche et transfert du focus, absence de lecteur chargé avant clic, fermeture et lien de la nouvelle carte vers les rayons. À 320 x 740, aucun débordement de page, la navigation tient dans le cadre et l'image couvre le rayon Nicolas.

Le rendu est aussi vérifié à 390 x 844, 844 x 390 et 1440 x 900. Les boutons de rayon visibles sur téléphone mesurent au moins 44 pixels de haut. Captures enregistrées dans les fichiers de la conversation : `accueil-porte-mobile-v12.jpg`, `videoclub-mobile-v12.jpg` et `videoclub-desktop-v12.jpg`.

`pnpm check` : formatage, lint et types réussis ; 635 tests du site passent et un échoue. L'échec préexistant est `test/localization.test.ts`, sur la couverture anglaise du catalogue source, notamment la clé `, histoire mondiale de l'IA</title>`. Aucun nouveau texte traduisible n'est ajouté par cette itération. Les sept tests de l'intro passent ; les tests des jingles ne sont pas atteints par cette commande après l'échec du site.

La route reste réservée au développement et non indexable. Aucun déploiement, commit, push ou PR.
