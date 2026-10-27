# Référencement des recherches sur les skills

20 octobre 2026. Lot local demandé par Lou pour les recherches « meilleurs skill Claude », « meilleurs skill ChatGPT », « meilleurs skill OpenAI » et « meilleurs skill Anthropic ».

## Diagnostic et recherche

Le contrôle HTTP public du 20 octobre relève un statut 200 pour `/charts/skills`, une canonique vers cette même URL sur `https://www.sandboxpodcast.fr` et un titre commençant par `SKILLS TOP 20`. Le fichier `robots.txt` autorise l’exploration publique et annonce le sitemap. Ce contrôle ne démontre pas que Google a indexé la page.

Les routes de plateforme existent dans le code, mais leurs contenus dépendent de collections publiées répondant aux conditions d’ADR-0020. Leur existence dans le routeur ne suffit pas à prouver leur disponibilité publique. L’outil de lecture web n’a pas pu ouvrir les routes publiques interrogées ; aucun statut 404 n’en est déduit.

L’échantillon de recherche consulté renvoie surtout des sélections Claude par usage, avec procédures d’installation : [Make Time](https://www.maketime.fr/articles/meilleurs-skills-claude-2026), [Captain Marketing](https://blog.captainmarketing.io/meilleurs-skills-claude/) et [Fello AI](https://felloai.com/fr/meilleures-competences-claude-code-par-cas-d-usage/). Il renseigne le format des réponses existantes, sans établir une position Google française, un volume mensuel ou une difficulté mesurée. Les faits techniques des nouveaux guides viennent des sources officielles, pas de ces comparateurs.

## Pages ajoutées

| Recherches visées                                                       | URL                                | Réponse proposée                                                                    |
| ----------------------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------- |
| meilleurs skills Claude, meilleurs skills Anthropic, skills Claude Code | `/guides/meilleurs-skills-claude`  | Six ressources Anthropic, choix par livrable, limites et installation               |
| meilleurs skills ChatGPT                                                | `/guides/meilleurs-skills-chatgpt` | Quatre modèles de procédures à configurer, outils nécessaires et essais de contrôle |
| meilleurs skills OpenAI, meilleurs skills Codex                         | `/guides/meilleurs-skills-openai`  | Documentation, CI et revues GitHub ; prérequis et installation                      |
| guides skills IA                                                        | `/guides`                          | Accès aux trois guides et au classement d’adoption                                  |

Claude et Anthropic partagent une page pour éviter deux textes synonymes. ChatGPT et Codex ont des réponses distinctes. Les guides expliquent leur périmètre et la nature documentaire de la sélection. Aucun rang de popularité ne devient une note de qualité.

Le contenu est rendu dans le HTML initial. Chaque guide possède un titre et une description propres, une canonique, un sommaire, des citations visibles, des questions fréquentes et des liens vers les autres guides. Le pied de page et la page Skills assurent leur découverte. Les quatre URL rejoignent le sitemap avec la date de revue du 20 octobre, sans traductions non relues.

Sources vérifiées pour la rédaction : [dépôt Anthropic](https://github.com/anthropics/skills), les fichiers `SKILL.md` liés dans chaque fiche, [documentation Claude Code](https://code.claude.com/docs/en/skills), [documentation OpenAI des skills](https://learn.chatgpt.com/docs/build-skills), [rôle des skills dans les plugins](https://developers.openai.com/plugins/concepts/skills) et [catalogue OpenAI](https://github.com/openai/skills).

La date de revue porte sur cette documentation. Les procédures et tests proposés aux lecteurs n’ont pas été exécutés sur chaque skill. Le guide ChatGPT ne promet pas quatre plugins prêts à installer : il fournit quatre pistes de configuration explicites.

## Vérifications

Les tests dédiés couvrent le rendu serveur, les canoniques, la découverte des guides, les sources, les ancres, les 404, l’absence de fausses traductions et leur présence au sitemap sans édition de classement. Ils passent dans le lot de 94 tests ciblés du [rapport global](seo-global-2026-10-20.md).

Le script `apps/site/scripts/test-skill-guides.mjs` utilise une base PGlite et un serveur local isolés. Sa recette finale couvre quatorze URL indexables, dont les quatre URL des guides, puis dix lectures navigateur sans JavaScript à 390 et 1 440 pixels. Les 24 contrôles passent ; les deux routes inexistantes sont en 404 et le podcast vide reste hors index. Les dix captures et résultats restent dans `apps/site/.local/skill-guides-check/`, hors Git. Lancer depuis `apps/site` : `node --experimental-strip-types scripts/test-skill-guides.mjs`.

## Mise en ligne et mesure

Lou demande ensuite une PR. Le lot SEO est préparé sur une branche isolée depuis `main`, sans déploiement de production. Après mise en ligne autorisée :

1. Contrôler les quatre URL sur le domaine public : 200, canonique, contenu visible, directives robots et sitemap.
2. Terminer la validation de propriété Search Console, encore en attente dans l’audit du 18 octobre ; ne pas considérer cet ancien état comme une vérification actuelle. Soumettre ou relire le sitemap puis inspecter les quatre URL.
3. Relever les requêtes réellement reçues avec filtres France et Web, par page et appareil. Comparer clics, impressions, CTR et position sur des périodes de 28 jours ; conserver les variantes au singulier et au pluriel sans les répéter artificiellement dans le texte.
4. Compléter les guides avec de vrais résultats comparatifs : même tâche, mêmes fichiers, mêmes critères et erreurs publiées. Les essais proposés dans chaque fiche donnent un point de départ, pas un résultat.
5. Préparer un épisode ou un article à partir des essais réellement réalisés, puis relier la démonstration au guide correspondant. Toute publication ou sollicitation externe demande l’accord de Lou.

Les préconisations de [Google pour les fonctionnalités IA](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) maintiennent les fondamentaux SEO et indiquent que `llms.txt` n’améliore pas le classement Google. Aucun fichier ou balisage spécial n’est donc présenté comme un raccourci vers la première place. Les pages doivent encore être explorées, indexées et jugées utiles ; le travail local ne mesure aucun gain de position.
