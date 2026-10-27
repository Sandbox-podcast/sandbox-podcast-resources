# Référencement global de Sandbox

20 octobre 2026. L’optimisation demandée par Lou porte sur tout le site : accueil, podcast, épisodes, actualités, classements, archives, fiches projet et traductions. Les recherches sur les skills Claude, ChatGPT, OpenAI et Anthropic constituent une priorité éditoriale dans cet ensemble.

## Audit public

Le contrôle lit les 569 URL du sitemap public avec deux requêtes simultanées au maximum, sans session et sans suivre les redirections. Il réutilise le contrôle du dépôt pour les statuts HTTP, directives robots et canoniques, puis relève les titres, descriptions, H1, textes principaux et liens de langue. Les scripts Next sont exclus du comptage de texte et des H1. Les données structurées observées dans le HTML sont conservées ; leur absence éventuelle ne permettrait pas de conclure à l’absence de données injectées côté client.

| Contrôle                                                    | Résultat    |
| ----------------------------------------------------------- | ----------- |
| URL annoncées au début du crawl                             | 569         |
| HTTP 200, HTML, indexabilité déclarée et canonique conforme | 569 sur 569 |
| Description manquante                                       | 0           |
| H1 absent ou multiple                                       | 0           |
| Groupes de titres identiques entre plusieurs URL            | 88          |
| Groupes de descriptions identiques entre plusieurs URL      | 73          |

Les doublons relevés concernent notamment les variantes de langue d’une même page. Un nom de projet ou une marque peut rester identique ; le chiffre de 88 n’est donc pas un nombre d’erreurs établi. Les titres génériques `GITHUB TOP 20`, `SKILLS TOP 20` et `MODELS TOP 20` sont néanmoins répétés sans désignation propre à la langue. Les descriptions dynamiques d’archives et de fiches GitHub échappent aussi à certaines traductions.

L’accueil public a un titre descriptif, tandis que le H1 conserve l’accueil éditorial « Bienvenue dans l’univers de Sandbox ». Ce titre visible n’est pas remplacé dans ce lot. La page À propos expose environ 149 mots dans le contenu principal au relevé ; les biographies déjà publiées sur l’accueil permettent de mieux présenter les auteurs sans inventer de contenu.

Les fiches GitHub les plus courtes de l’échantillon comptent environ 99 à 104 mots selon la langue. Ce comptage repère des pages à enrichir, sans constituer un seuil Google ni justifier une désindexation automatique. Les rangs et dates disponibles restent utiles ; une analyse fonctionnelle demanderait des essais propres au projet.

Preuve détaillée locale : `apps/site/.local/seo-global-2026-10-20/report.json`. Le rapport inclut les réponses normalisées, textes et groupes de doublons. Il ne contient pas de session privée. Le crawl a lieu pendant un site vivant : le nombre d’éditions peut évoluer après sa lecture du sitemap.

## Correctifs implémentés

### Titres et descriptions

Les quatre familles de classement ont désormais une désignation SEO descriptive en français, anglais, espagnol et allemand. Leurs archives mentionnent la famille et l’édition. Les archives globales et les fiches de projets GitHub utilisent également des textes propres à la langue. Les noms de dépôt et les identifiants d’édition restent exacts.

Le modèle ne reprend plus automatiquement une description de dépôt dans une autre langue pour la couper à 160 caractères. Il présente les informations réellement disponibles sur la fiche : rangs, mesures, historique, sources et dates. Les détails du dépôt restent dans le contenu de la fiche.

### Identité, auteurs et fiches projet

Les layouts français et localisés partagent les mêmes identités structurées `WebSite` et `Organization`, reliées par un identifiant stable. Les profils sociaux sont ceux déjà visibles dans le footer. Le nom du publisher suit les réglages éditoriaux en cours, plutôt qu’une valeur capturée avant leur chargement.

À propos affiche les biographies et rôles existants, avec leurs traductions. Chaque animateur dispose d’une ancre réelle. Les épisodes citent ces animateurs dans leurs données structurées et partagent l’identité de la série podcast. Les fiches de projets personnels décrivent l’œuvre, son créateur, ses sources et la date de vérification, avec une URL de page adaptée à la langue. Aucun tarif, avis ou lancement n’est inventé.

### Sitemap et indexation

Les liens de langue du sitemap et ceux des métadonnées HTML passent par la même fonction. Ils incluent `x-default` lorsque la variante française est disponible. Les directives `noindex` des pages non publiables restent conservées ; la langue courante doit aussi être autorisée.

Les dates des pages courantes de classement suivent les publications réelles, celles des archives leur propre édition. Les pages de méthode ne sont pas rajeunies à chaque collecte. Le hub podcast reprend la date du dernier épisode publié. Une date absente n’est pas remplacée par celle du build ou de la visite.

### Maillage et guides

Les trois guides de skills et leur hub sont liés au pied de page, à la page Skills et entre eux. Leur contenu documentaire est indépendant des éditions d’adoption. Le [rapport des guides](seo-skills-2026-10-20.md) précise les sources, limites et essais proposés. Ils restent un complément à l’optimisation globale.

## Vérification locale

Préparation de la PR à la demande de Lou : le lot SEO est repris dans une branche isolée depuis `main` (`9b0b670`). Les autres changements du dossier principal ne sont pas embarqués. Les adaptations des anciennes fixtures et le formatage des slides sont déjà intégrés dans cette base ; ils ne sont donc pas réintroduits par la PR. La recette HTTP et navigateur est ajoutée à la CI sous `test:seo:e2e`.

Validation dans le dossier principal avant préparation de la PR : `pnpm check` passe intégralement (formatage, ESLint, TypeScript, **1 178 tests du site dans 148 fichiers**, sept tests de l’introduction vidéo, quatre tests des jingles et 24 tests du support BIS). Le build `pnpm --filter @podcast/site build` réussit : compilation, types et génération de 208 pages statiques. Les nouveaux guides figurent dans le résultat du build. Aucun déploiement ne fait partie de ces commandes.

Sur la branche de PR repartie du `main` à jour : `pnpm check` passe avec **1 249 tests du site dans 152 fichiers**, en plus des suites vidéo et BIS. La recette `test:seo:e2e` passe ses 24 contrôles. L’audit des dépendances ne trouve aucune vulnérabilité connue et Gitleaks ne détecte aucun secret dans les changements préparés. Les tests supplémentaires proviennent des correctifs déjà intégrés dans `main` depuis la version du dossier principal.

Les tests ciblés des métadonnées, auteurs, projets, langues et archives donnent **94 tests réussis sur 12 fichiers**. La recette finale donne **24 contrôles HTTP et navigateur réussis** : quatorze URL indexables conformes, dix lectures navigateur sans JavaScript à 390 et 1 440 pixels, sans débordement horizontal. Elle vérifie aussi deux 404 attendues et le maintien du podcast vide hors index et hors sitemap dans la base de test. Les dix captures et le rapport sont conservés dans `apps/site/.local/skill-guides-check/` ; les captures du guide Claude mobile, d’À propos sur ordinateur et de Sillage en anglais sur mobile ont été relues visuellement.

Le contrôle global initial a également relevé des problèmes dans l’espace de travail antérieurs à ce lot. Les trois appels de test dans `news-preview.test.ts` ne passent plus la prop retirée. Le test de l’accueil contrôle maintenant le lien vers le catalogue, puis les projets dans leur salle dédiée ; les assertions sur les projets sont conservées. Le CSS des slides de l’épisode 003 et `suivi-issue-68-2026-10-20.md` ont reçu le formatage demandé par Prettier. Aucun gate n’est désactivé.

## Fichiers du lot

- Métadonnées et identité : `src/lib/seo.ts`, `src/lib/site-identity.ts`, `src/domain/chart-seo.ts`, `src/domain/chart-seo-copy.ts`, les layouts français et localisé, le routeur localisé et `src/app/sitemap.ts`.
- Pages et attribution : routes de classement courant, éditions, Rising, archives globales et fiches GitHub ; routes À propos, épisode et projet personnel ; composants `shared-pages.tsx` et `podcast-replays.tsx` ; styles des biographies dans `site-polish.css`.
- Guides et maillage : `src/domain/skill-guides.ts`, routes `/guides`, composant et feuille de style `skill-guide`, page Skills et pied de page. Voir DD-0072.
- Vérification : quatre nouveaux fichiers de tests (`chart-seo-copy`, `global-seo`, `skill-guides`, `skill-guide-sitemap`), complément à `chart-seo.test.ts`, adaptation des fixtures News et accueil et script `scripts/test-skill-guides.mjs`.
- Documentation : cet audit, le rapport des guides, DD-0072, DD-0073 et l’index `docs/README.md`. Les chemins de code sont relatifs à `apps/site`.

## Travail restant après livraison autorisée

1. Vérifier les nouvelles métadonnées et le sitemap sur le domaine public. Contrôler les données structurées avec les validateurs Google et Schema.org, sans confondre présence du balisage et obtention d’un résultat enrichi.
2. Confirmer l’accès Search Console et l’état de validation du domaine. L’audit du 18 octobre indiquait une validation DNS en attente ; aucun accès ni résultat Search Console actuel n’est déduit de ce document ancien.
3. Lire l’indexation, les impressions, clics et positions par page, pays et appareil. Le crawl HTTP ne remplace pas l’inspection Google. Comparer des périodes de 28 jours lorsque des données existent.
4. Mesurer de nouveau les Core Web Vitals mobiles. Les durées HTTP du crawl ne sont pas le LCP ou l’INP. L’audit du 18 octobre relevait un LCP de laboratoire à 3,8 secondes, sans données mobiles réelles suffisantes ; les correctifs d’images préparés depuis doivent être mesurés après publication.
5. Enrichir les fiches et les guides avec les essais effectivement réalisés dans le podcast : cas d’usage, résultat obtenu, défauts et passage vidéo correspondant. Ne pas multiplier les pages synonymes pour augmenter le nombre d’URL.

Les recommandations de [Google sur les titres](https://developers.google.com/search/docs/appearance/title-link), les [sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap) et l’[identité des organisations](https://developers.google.com/search/docs/appearance/structured-data/organization) motivent ces corrections. Elles ne garantissent aucune position. La publication, la mesure d’audience et les actions externes restent soumises aux autorisations du dépôt.
