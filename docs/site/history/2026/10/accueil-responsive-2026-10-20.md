# Accueil : contrôle responsive du 20 octobre 2026

Ce contrôle porte sur les contenus situés après la scène immersive : portraits, projets, blocs illustrés et footer, ainsi que le header et le menu tactile. La recette des six salles est suivie séparément dans [la recette du parcours](six-pieces-recette-2026-10-20.md).

## Périmètre

Playwright avec Edge en mode headless, sur `http://127.0.0.1:3100`. Les mouvements sont réduits pour contrôler la disposition sans animation en cours. Les quatre premiers formats utilisent un contexte tactile :

| Format      | Usage simulé             |
| ----------- | ------------------------ |
| 320 × 568   | Petit téléphone portrait |
| 390 × 844   | Téléphone portrait       |
| 768 × 1024  | Tablette portrait        |
| 844 × 390   | Téléphone paysage        |
| 1366 × 768  | Ordinateur portable      |
| 1920 × 1080 | Ordinateur               |
| 3440 × 1440 | Écran large              |

Le script fait défiler chaque section et attend le décodage des images avant capture. Les liens et boutons visibles sont contrôlés avec les vérifications d'interaction de Playwright, sans ouvrir les destinations externes. Les vignettes latérales du carrousel marquées `aria-hidden` et les enfants des menus `details` fermés sont exclus de ce contrôle. Le menu est testé par appui, fermeture avec Échap, fermeture par appui extérieur et navigation réelle vers `/podcast`. Le carrousel est testé avec les boutons suivant et précédent.

## Résultats

Les sept formats passent les contrôles de disposition et d'interaction : aucun débordement horizontal, aucune cible utile coupée, tous les liens testés accessibles, carrousel suivant/précédent fonctionnel et toutes les images décodées. Le header ne présente aucune cible visible coupée ou inférieure à 44 px. Le menu des quatre contextes tactiles ouvre les liens, se ferme avec Échap et par appui extérieur, puis permet de rejoindre la page podcast. Aucune erreur JavaScript n'a été relevée lors de la passe finale.

Les liens des portraits ont une surface d'au moins 44 × 44 px. Le footer tactile a été revérifié séparément à 320 × 568 et 844 × 390 : `pointer: coarse` confirmé, aucune cible inférieure à 44 px, aucun débordement et aucun lien inaccessible. Les liens de navigation du footer desktop restent à 32 px de haut avec un pointeur fin.

La capture d'une section plus haute que la fenêtre réinitialisait l'émulation du pointeur dans Edge. Les premiers relevés du footer qui suivaient ces captures ne validaient donc pas le tactile. Le contrôle final des deux formats maintient explicitement cette émulation et vérifie le type de pointeur avant la mesure. Les captures servent à la revue visuelle ; les dimensions tactiles proviennent du DOM avant capture.

## Corrections réalisées

Les liens sociaux des portraits avaient une hauteur de 44 px mais une largeur réduite au texte : environ 41 px pour LinkedIn, 35 px pour GitHub et 7,5 px pour X. Leur largeur minimale est maintenant de 44 px. L'espacement mobile passe à 12 px pour conserver les trois liens sur une ligne à 320 px.

En paysage tactile à 844 × 390, les neuf liens de navigation du footer utilisaient la disposition desktop avec une hauteur de 32 px. Une règle `@media (pointer: coarse)` porte leur hauteur minimale à 44 px. Les appareils avec pointeur fin conservent leur disposition.

Les trois illustrations Time Machine, classements et Radar sont désormais livrées directement en WebP, avec `unoptimized` sur leurs seuls composants Image. Le chargement différé est conservé. Les fichiers pèsent respectivement 255 380, 251 486 et 232 618 octets. Ce choix évite une recompression à la volée d'images déjà compressées. Pendant le diagnostic, les URL optimisées ne donnaient pas d'image décodée après cinq secondes dans Edge, alors que les WebP directs chargeaient immédiatement. Le serveur exécutait plusieurs recettes en parallèle : ce relevé ne démontre pas un défaut du navigateur ni une cause unique.

Le test de livraison de l'image du plateau attend maintenant `max(100vw, 178vh)`, conformément au cadrage `cover` retenu par le moteur. Il conserve les contrôles de priorité et de chargement responsive.

## Preuves et tests

Les scripts et captures restent dans le répertoire local ignoré par Git :

- Script : `apps/site/.local/test-home-below-scene.mjs`.
- Rapport JSON : `apps/site/.local/home-below-scene/report.json`.
- Sortie : `apps/site/.local/home-below-scene-run.log`.
- Captures : `apps/site/.local/home-below-scene/`.
- Vérification tactile finale : `apps/site/.local/home-below-scene-final-tactile/report.json`, script `apps/site/.local/test-home-targeted.mjs`.

Captures ouvertes et inspectées : menu et blocs illustrés à 320 × 568, portraits à 390 × 844, blocs illustrés à 768 × 1024, menu et footer à 844 × 390, portraits à 1366 × 768, projets à 1920 × 1080 et blocs illustrés à 3440 × 1440. Les illustrations restent cadrées dans leurs cartes et les légendes lisibles. Les portraits et liens sociaux restent dans leur colonne à 320 px. Le menu paysage tient dans la fenêtre de 390 px de haut.

La commande suivante passe : **54 tests dans quatre fichiers**.

```powershell
pnpm exec vitest run test/discovery-refonte.test.ts test/localization.test.ts test/home-image-delivery.test.ts test/footer-socials.test.ts --reporter=dot
```

Prettier a été exécuté sur les fichiers modifiés. Le contrôle global `pnpm check` est suivi par la recette principale.

## Fichiers modifiés

- `apps/site/src/components/discovery-chapters.module.css` : dimensions des liens sociaux.
- `apps/site/src/components/discovery-story.tsx` : livraison directe des trois WebP.
- `apps/site/src/app/site-polish.css` : hauteur des liens du footer sur écran tactile.
- `apps/site/test/home-image-delivery.test.ts` : assertion de cadrage du plateau.

Cette vérification simule les dimensions et le pointeur dans Edge. Elle ne remplace pas une visite sur téléphone physique, Safari iOS ou Firefox, et ne mesure pas les performances réseau ou GPU.
