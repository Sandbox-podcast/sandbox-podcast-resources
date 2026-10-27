# SANDBOX News : V1 locale du 18 octobre 2026

État initial conservé pour la provenance et la recette du décor. L'interface, les sources et les synthèses sont désormais décrites dans le [rapport V2](news-v2-medias-seo-2026-10-18.md).

La V1 se consulte sur <http://localhost:3328/news>. La [DD-0053](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0053-news-liste-minitel-et-radar-local.md) enregistre la direction demandée par Lou. Le périmètre final reste celui de [DD-0052](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0052-sandbox-news-ia-et-developpement.md).

## Lancer

Depuis la racine du dépôt :

```powershell
corepack pnpm --filter @podcast/site dev:news
```

Node 24 collecte les publications puis démarre Next sur `127.0.0.1:3328`. Le cache est dans `apps/site/.local/news-preview/` et le build dans `apps/site/.local/news-next/`, ignorés par Git. Ce build distinct évite de perturber un autre aperçu déjà lancé.

Le script désactive les variables de connexion Postgres et GA4. La page et son API renvoient 404 hors du mode de développement prévu. L'API POST exige une origine locale identique à celle de la requête. Aucun secret n'est requis pour la collecte publique. Aucun cron News n'est activé.

## Fonctionnement et limites

- Une ligne contient la date et l'heure de publication au fuseau Europe/Paris, puis une phrase liée à la publication GitHub d'origine.
- Recherche insensible aux accents et à la casse, quatre catégories, ordre chronologique ou versions stables en premier, quinze lignes puis Afficher la suite.
- Actualiser relance huit appels publics au maximum, avec un délai maximal de quinze secondes par appel, une réponse bornée et un délai minimal d'une minute entre deux relevés.
- Schémas Zod, rejet des brouillons, dates futures et liens incohérents, déduplication par URL, conservation du dernier relevé en cas d'échec. Maximum de deux cents publications en cache local.
- Le relevé initial a reçu 28 publications de sept sources sur huit. Codex n'a pas répondu de manière exploitable ; l'interface indique la collecte partielle. Next.js, Vite, VS Code, Claude Code, Transformers, Ollama et LangChain ont fourni des publications.
- Les quatre langues disposent de libellés et de phrases déterministes. Aucun modèle de traduction ou de résumé n'est déclaré validé. Le contenu actuel annonce les versions ; il ne résume pas leurs nouveautés.

Le flux éditorial IA et développement, ses autres sources, ses contrôles de qualité et sa publication automatique restent à implémenter. Les versions mineures et préversions ne constituent pas en elles-mêmes une sélection d'actualités pertinentes.

## Accueil et images

Une troisième carte rejoint Explorer l'IA. Le radar du décor est un second accès vers `/news`, seulement dans cet aperçu. Les images originales restent présentes.

Deux assets ont été produits avec ImageGen le 18 octobre 2026 puis optimisés en WebP avec Sharp :

- `apps/site/public/images/home/explore/news-editorial-v1.webp` : journal et ordinateur sur une table sombre, dans la lumière et les matières des cartes existantes. Indication de génération : photographie éditoriale réaliste, sans texte lisible ni logo ajouté, espace sombre pour le titre en bas, continuité avec les cartes Time Machine et Classements.
- `apps/site/public/images/home/studio-news-radar-v4.webp` : édition de `studio-easter-eggs-v3.webp`, avec la capture de Lou comme référence. Indication de génération : remplacer uniquement la petite sphère de l'étagère supérieure par une antenne radar parabolique miniature en laiton ; conserver cadrage, étagères, télévision, voiture, porte, éclairage et emplacement des animateurs.

Sorties PNG conservées dans `C:/Users/Lou/.codex/generated_images/01a14ef1-7520-7f42-a757-c3796405ab4c/` : `exec-0d8bb361-4abb-45be-bbc0-c8cd4107fa1f.png` et `exec-a9ff5140-f740-4011-91f8-399ea7801800.png`.

## Recette

Vérifications réelles dans le navigateur : recherche Claude, recherche sans résultat et réinitialisation, filtre Modèles, versions stables en premier, quinze puis vingt-huit lignes, Actualiser avec état de chargement et relevé actualisé, navigation vers News depuis le radar puis la troisième carte. Le clic du radar a nécessité de rendre le libellé décoratif du plateau transparent aux événements de pointeur.

Contrôle mobile : viewport demandé de 390 × 844, document utile de 375 pixels sans dépassement horizontal global ; catégories défilantes dans leur propre bande, date au-dessus de la phrase.

Captures locales : `apps/site/.local/news-preview/qa/news-desktop.jpg`, `news-mobile.jpg`, `home-radar.jpg` et `home-explore.jpg`.

Quatorze tests ciblent le domaine, le collecteur, le rendu, les échecs et les protections de l'API. `corepack pnpm check` termine avec le code 0 : formatage, lint et TypeScript validés ; 740 tests du site, 7 tests de timeline, 4 tests de médias et 24 tests BIS réussis, soit 775 tests au total. `git diff --check` ne relève pas d'erreur. La recette navigateur confirme les interactions et les deux accès depuis l'accueil. Le build de production n'est pas lancé pour cet aperçu de développement.

## OAuth YouTube

La session du navigateur accède à la chaîne SANDBOX avec ses commandes de propriétaire. Lou autorise explicitement le 18 octobre la création du projet Google Cloud « SANDBOX YouTube », sans facturation, et la poursuite d'OAuth.

Après soumission du formulaire de création, la console n'a confirmé aucun projet. Les notifications et l'inventaire Tous renvoient des erreurs de chargement. La création n'est donc pas considérée comme réussie et n'est pas répétée pour éviter un doublon. OAuth n'est pas connecté. Preuve : `apps/site/.local/news-preview/qa/google-cloud-error.jpg`. Aucun essai ni facturation n'a été activé.
