# Affiche de l’épisode 3 et navigation de l’accueil

26 octobre 2026. Demande de Lou : reprendre les affiches cinéma des deux premières émissions pour la troisième et rendre les pages accessibles depuis le header de l’accueil. Choix consignés dans [DD-0074](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0074-navigation-accueil-et-affiche-episode-003.md).

## Affiche

Image produite avec Imagegen intégré, sans appel à une API facturée par le dépôt. Références de style : `episode-001-cinema-v2.webp` et `episode-002-cinema-v2.webp`. Références d’identité inspectées : `team/lou-studio-lossless-v1.webp`, `team/loic-studio-lossless-v1.webp`, `team/nicolas-prod-2026-10-15.webp`.

Source conservée : `C:/Users/Lou/.codex/generated_images/01a17725-d3ba-7f13-a3dd-462629a9450a/exec-76e329a4-f0ed-4db9-a506-8a63afbc4191.png`. Sortie du site : `apps/site/public/images/home/replays/episode-003-cinema-v1.webp`, 1024 × 1536, 192 184 octets. Sharp effectue uniquement l’encodage WebP qualité 88, sans recadrage ni redimensionnement.

Prompt utilisé :

> Create a new portrait 2:3 photographic cinema poster artwork for SANDBOX episode 3 about 'Vibe coding en production'. First two references are STYLE / SERIES references only: preserve their premium cinematic photographic quality, recognizable ensemble faces and rich dark navy shadows. References 3,4,5 are IDENTITY references: respectively Lou, Loïc, Nicolas. EXACTLY these three men, recognizable likeness and natural proportions, no extra person. Compose a new suspenseful near-future technology thriller: the three real hosts as a serious film ensemble in a dramatic dark glass production control room overlooking a luminous city. Lou foreground center, Loïc slightly behind to left, Nicolas slightly behind to right, black everyday clothes, no microphones, no headphones. A thin molten amber-red fault line runs through reflective architectural glass behind them while restrained cyan code-like light reflections hint at AI-generated software going into real production. Abstract reflections only, NO legible code or text. Visually distinctive from episode1's cyan monolith and episode2's amber cafe; use midnight navy, restrained crimson, cyan rimlight, cinematic soft photographic skin lighting, film grain, atmospheric depth, elegant original movie poster composition. Faces occupy upper middle area ~18-51% height, complete shoulders blend into architecture around 60%; keep BOTTOM 40% dark near-black navy with only faint atmospheric reflection and plentiful negative space so HTML title will later overlay there. Full-bleed flat artwork, 1024x1536 portrait aspect. IMPORTANT NO TEXT AT ALL: no title, no SANDBOX wordmark, no letters, no credits, no episode number, no typography, no watermarks, no fake film laurels. This is the art layer; website adds all typography. Not a thumbnail, no shocked expressions, no sticker collage. Match the craftsmanship and photographic coherence of the two existing posters.

## Navigation et contrôles

- L’accueil réutilise le header commun, avec un fond sombre, une bordure et des liens visibles. Guides et À propos rejoignent les rubriques principales. Les Guides restent une page française ; le lien annonce `hreflang="fr"`.
- La recette navigateur contrôle l’accueil à 1440, 1100 et 375 pixels : navigation visible sur ordinateur, menu mobile ouvert avec les rubriques et la recherche, fermeture par Échap, aucun débordement horizontal.
- Le cinéma de l’aperçu local montre les trois affiches dédiées chargées, dont celle de l’épisode 3 avec son titre court.
- Les 80 tests ciblés passent : navigation publique, localisation des affiches, correspondance vidéo/affiche, intégration et pagination du cinéma. TypeScript et lint ciblé passent.
- `pnpm check` échoue au formatage sur les 100 fichiers déjà présents dans le lot, notamment les exports de l’épisode 3. Les contrôles ne sont pas désactivés et les exports ne sont pas reformatés dans ce changement.

Captures dans `.local/` : `home-navbar-desktop-2026-10-26.png`, `home-navbar-mobile-2026-10-26.png`, `cinema-poster-003-2026-10-26.png`.

L’aperçu `/cinema-local-qa#room-cinema` utilise trois épisodes de présentation et reste réservé au développement. Le contenu publié n’a pas été modifié. Aucun déploiement effectué.

## Préparation de la PR

À la demande de Lou, le lot est repris sur `main` à jour (`6c647ab7`) dans une branche isolée. Les correctifs de jaquettes et le pipeline vidéo thématique sont déjà livrés dans cette base ; ils ne sont pas réintroduits. La PR rassemble la navigation de l’accueil, les six emplacements du cinéma, l’affiche du troisième épisode, les tests et la documentation, ainsi que les quinze miniatures A/B/C et leurs preuves Studio. Les vidéos sources et les rendus volumineux restent dans le dossier local d’origine.

Dans ce checkout, `pnpm check` réussit : formatage, lint, TypeScript, 155 fichiers et 1 307 tests du site, sept tests d’introduction, quatre tests de jingles et 24 tests du conducteur. Le build de production réussit avec 207 pages statiques générées. Un changement de retour à la ligne demandé par Prettier dans `slides/episode-003/show.js` est inclus. Gitleaks ne détecte aucun secret dans le diff préparé.

`pnpm audit --audit-level=high` échoue : dix vulnérabilités signalées, dont deux critiques, trois élevées, trois modérées et deux faibles. Elles concernent les versions déjà présentes dans `main`, notamment Next.js, Zod et Undici. Les manifestes de dépendances et le lockfile restent identiques à cette base. Ce résultat est signalé dans la PR ; la validation locale du code ne vaut pas validation de l’audit.
