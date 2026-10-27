# Correctifs SEO locaux du 18 octobre 2026

Les problèmes d'images, de traduction et de titres relevés dans l'[audit public](audit.md) sont corrigés localement. Ils restent à publier après revue. Search Console attend toujours une validation DNS ; le code IONOS transmis pendant la reprise a été refusé. Aucun code de connexion n'est conservé dans les fichiers.

## Chargement des images

L'image du vidéoclub mobile est chargée immédiatement avec `fetchPriority="high"`, en qualité 75. Le `picture` sert un pixel embarqué lorsque le plateau desktop masque le vidéoclub. Le media correspond à celui du CSS : largeur minimale 901 pixels et hauteur minimale 541 pixels, ou largeur minimale 1 101 pixels. Un écran horizontal de faible hauteur garde donc l'image visible.

Les portraits illustrés et les couvertures de projets utilisent la qualité 75. Le logo dispose d'un `sizes="252px"` ; le navigateur contrôlé choisit une réponse de 256 pixels, au lieu de la grande variante signalée lors de l'audit. Les fichiers sources ne sont pas réécrits.

| Image                    | Avant, octets | Après, octets |
| ------------------------ | ------------: | ------------: |
| Entrée du vidéoclub      |        24 402 |        11 320 |
| Portrait Lou             |       198 812 |       109 744 |
| Portrait Loïc            |       175 486 |        94 672 |
| Portrait Nicolas         |       190 302 |       103 676 |
| Couverture Okodukai      |        82 452 |        49 320 |
| Couverture Sillage       |        77 568 |        43 924 |
| Couverture Song Maker    |        47 464 |        24 598 |
| Logo                     |        64 542 |         3 308 |
| Total des huit variantes |       861 028 |       440 562 |

Réduction mesurée de 48,8 % sur ces huit réponses de l'optimiseur Next local. Les sept visuels sont comparés à largeur 640, qualité 90 puis 75. Le logo est comparé à qualité 75, largeur 3 840 puis 256. La négociation HTTP est fixée à WebP. Ce total n'est ni le poids complet de la page, ni une mesure de LCP, ni le volume effectivement téléchargé par tous les visiteurs.

Les images chargées tardivement peuvent rester absentes du transfert initial. La collecte mobile réelle et un nouveau rapport PageSpeed production devront être relus après un déploiement autorisé.

## Traductions

Les accroches étaient déjà traduites, mais leur assemblage avec le nom du projet empêchait la traduction du title complet. La couche des pages partagées traduit désormais l'accroche avant assemblage. Le titre Open Graph et le titre de carte sociale reprennent cette même valeur.

Exemple vérifié dans le navigateur : `Sillage : A workspace for your coding agents. · Sandbox`. Les pages espagnole et allemande affichent aussi leur titre localisé. Le nom Sillage, la canonique de chaque langue et les directives robots sont conservés.

Les 132 libellés de fonctionnalités du catalogue manquaient dans les trois langues. Ils sont désormais présents, soit 396 traductions ajoutées. Leurs sources sont inscrites au catalogue et les tests parcourent les 34 projets. Les cinq fonctionnalités de Sillage ont été contrôlées dans le navigateur en anglais, espagnol et allemand. Aucune relecture native n'est revendiquée.

## Titres des classements

Le même H1 `Sandbox Charts` apparaissait sur la collection et les pages de classements. La collection, son archive et les classements GitHub, skills, modèles et progression affichent désormais un titre précis dans chaque langue. Le nom de la collection `CollectionPage` reprend son nouveau H1. Quand le lecteur change de classement, le H1 suit le classement actif ; les pages de collection et d'archive gardent leur titre de page.

Les titres des pages, URL canoniques, règles d'indexation et données publiées restent inchangés. Ce correctif ne rend pas indexable une page qui était en `noindex`. Décision : [DD-0055](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0055-titres-des-pages-de-classement.md).

## Vérification locale

Le serveur utilise le dispositif de fixtures existant : base PGlite éphémère, proxy local, collecteurs et clés externes neutralisés, sortie Next isolée. Son premier lancement depuis la racine du dépôt échouait à trouver le contenu ; la relance depuis `apps/site` corrige ce problème de lancement, sans modification du code de chargement produit.

- `charts-public-language.test.ts` passe ses cinq cas. Le nouveau cas vérifie les six types de page dans les quatre langues, soit 24 combinaisons de H1.
- Un `corepack pnpm check` a passé formatage, lint, types et tests avant l'ajout de cette matrice : 760 tests du site, 7 du générique, 4 des jingles et 24 tests BIS. La suite complète du site passe ensuite à 759/759. Le contrôle de typage du site, le lint ciblé et le formatage des fichiers du lot passent aussi. Aucun test ni contrôle n'est désactivé.
- Le dernier `corepack pnpm check` s'arrête au formatage sur `exports/reseaux-sociaux/episode-02/replanification-proposee.json`, hors de ce lot. Le contrôle ciblé Prettier passe pour tous les fichiers SEO modifiés.
- Le formatage des documents du lot et le vérificateur de texte français passent. `git diff --check` ne signale pas d'erreur.
- La vue mobile demandée à 390 x 844 présente une zone client de 375 pixels, sans débordement horizontal. Le vidéoclub sélectionne la variante 640/75 avec chargement immédiat et priorité élevée.
- La vue desktop demandée à 1 440 x 900 présente une zone client de 1 425 pixels. Le vidéoclub est masqué et son `currentSrc` est le pixel embarqué.
- La vue horizontale demandée à 950 x 500 présente une zone client de 935 pixels. Le vidéoclub reste visible, son image est chargée et aucun débordement n'est observé.
- Les trois portraits se chargent en qualité 75 ; leur rendu est contrôlé dans le navigateur.
- Les fiches Sillage EN/ES/DE répondent 200 et affichent les fonctionnalités traduites.
- La capture mobile du nouveau titre de collection est conservée dans `screenshots/charts-heading-mobile.jpg`.

Les captures et mesures détaillées sont conservées dans `.local/seo-audit-2026-10-18/`, hors Git. Le serveur local est arrêté après vérification. Aucune mesure synthétique n'est présentée comme une visite mobile réelle.

## Périmètre du lot

Composants : `discovery-home.tsx` et son CSS pour le vidéoclub, `shell.tsx` pour le logo, `home-host-card.tsx` et `home-project-spotlight.tsx` pour la compression, `shared-pages.tsx` pour les titres localisés, et `charts-experience.tsx` avec ses routes de collection et d'archive pour les H1. Le lot ajoute les traductions aux dictionnaires et adapte les tests concernés.

Des modifications de Sandbox News et de l'épisode 003 sont présentes dans le même espace de travail. Elles sont conservées. Les ajouts News visibles dans les diffs de composants partagés ne proviennent pas de ce correctif SEO. Décisions : [DD-0054](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0054-correctifs-seo-images-et-traductions.md) et [DD-0055](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0055-titres-des-pages-de-classement.md).

La validation Search Console, sa réception du sitemap et l'inspection Google des huit URL prioritaires restent à terminer avec un code IONOS valide ou une session DNS ouverte par le gestionnaire du domaine. Aucun DNS, contenu public, déploiement, commit, push ou PR n'est effectué par ce lot.
