# Guides skills : reprise de la lecture

26 octobre 2026. Lou demande de rendre les guides lisibles et utiles. Cette reprise locale complète DD-0072 sans ajouter de rubrique ni changer les URL.

La page d’accueil définit le mot « skill » et propose un choix entre Claude, ChatGPT et Codex. Les titres visibles décrivent le besoin du lecteur ; les titres SEO et les adresses existantes sont conservés. Chaque fiche commence par une tâche, explique le skill en français courant et propose une demande à essayer. Les précautions utiles restent visibles ; les contrôles détaillés et les questions fréquentes s’ouvrent à la demande, même sans JavaScript.

Le guide ChatGPT annonce dès le début qu’il s’agit de quatre recettes à créer. Il décrit la création avec `@skill-creator` dans ChatGPT Work, sous réserve d’accès. Les fiches Claude et Codex conservent leurs liens vers les skills officiels. La procédure Claude Code comprend maintenant l’installation du plugin, après l’ajout du catalogue.

La lecture se fait sur une colonne, avec une largeur limitée et des exemples distincts du texte explicatif. Les couleurs et les polices restent celles du site. Aucun composant client ni dépendance n’est ajouté.

## Sources relues

- [Catalogue Anthropic et installation](https://github.com/anthropics/skills), avec les fichiers `SKILL.md` de docx, xlsx, pptx, pdf, frontend-design et skill-creator.
- [Catalogue OpenAI](https://github.com/openai/skills), avec openai-docs, gh-fix-ci et gh-address-comments.
- [Création des skills](https://learn.chatgpt.com/docs/build-skills) et [skills dans les plugins](https://developers.openai.com/plugins/concepts/skills).

La date de revue documentaire passe au 26 octobre 2026. Les demandes d’exemple sont proposées par Sandbox ; elles ne constituent pas des tests effectués sur chaque skill. Aucun résultat comparatif n’est annoncé.

## Vérification

- Tests ciblés : 7 tests réussis dans `skill-guides.test.ts` et `skill-guide-sitemap.test.ts`.
- `pnpm test` réussit : 1 284 tests du site dans 155 fichiers, sept tests de l’introduction, quatre tests des jingles et 24 tests BIS.
- `pnpm typecheck` réussit pour les deux applications concernées.
- Recette `pnpm --filter @podcast/site test:seo:e2e` : 24 contrôles réussis. Lecture des guides sans JavaScript à 390 et 1 440 pixels, liens, ancres, volets de vérification au clavier et questions dépliables. Douze captures enregistrées dans `apps/site/.local/skill-guides-check/`, hors Git.
- ESLint et Prettier passent sur les fichiers de ce lot. `git diff --check` ne relève pas d’erreur sur ces fichiers.

Le contrôle global `pnpm check` s’arrête au formatage : 105 fichiers d’autres travaux locaux ne respectent pas Prettier, notamment les exports vidéo et deux documents déjà présents. Le lancement séparé de `pnpm lint` a aussi relevé les fichiers GSAP minifiés dans ces exports ; l’assertion non nulle ajoutée dans notre test a été corrigée, puis le lint ciblé a été relancé avec succès. Aucun gate n’a été désactivé et les fichiers des autres lots n’ont pas été reformattés.

Les captures du hub mobile et du guide Claude sur mobile et ordinateur ont été relues. La recette finale sur l’aperçu local vérifie aussi les quatre pages après les dernières retouches rédactionnelles.

Aucun commit, push ni déploiement dans ce lot.
