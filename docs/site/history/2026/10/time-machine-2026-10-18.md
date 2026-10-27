# Time Machine, mise à jour du 18 octobre 2026

À la demande de Lou, la Time Machine ouvre désormais la fiche la plus récente du corpus, en 2026. Le réglage suit les mises à jour du contenu sans année ni identifiant imposé dans le composant. Les liens vers un événement précis gardent leur priorité et toutes les années restent consultables.

Le corpus passe de 151 à 162 événements, dont 52 en 2026. La date de vérification passe au 18 octobre ; le dernier événement retenu date du 17. La revue des annonces OpenAI, Anthropic, Google, Meta, xAI, Mistral, Ai2 et des publications récentes repérées via Hugging Face distingue les dates de sortie des dates de reprise dans la presse. Aucun événement du 18 suffisamment documenté n'a été retenu dans cette passe. La sélection reste non exhaustive.

## Ajouts

- 2026-10-15 : Google utilise Antigravity pour chercher des peptides antimicrobiens. [Source](https://deepmind.google/blog/accelerating-antimicrobial-discovery/).
- 2026-10-15 : OpenAI ouvre les candidatures au Rosalind Academic Plan. [Source](https://openai.com/index/introducing-the-rosalind-academic-plan/).
- 2026-10-15 : Meta publie les poids de Muse Spark Open. [Source](https://research.meta.ai/blog/muse-spark-open).
- 2026-10-15 : Jais 3 publie six modèles pour l'arabe et ses dialectes. [Source](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai).
- 2026-10-15 : Le DOE publie Genesis Agent Skills pour la recherche. [Source](https://www.energy.gov/science/articles/genesis-agent-skills-release-support-innovation-across-genesis-mission).
- 2026-10-15 : IBM réunit conversation, décisions et transcription dans Granite Switch 4.1. [Source](https://huggingface.co/blog/ibm-granite/granite-switch-4-1).
- 2026-10-15 : FLUX.3 Image Klein arrive dans Diffusers. [Source](https://huggingface.co/blog/flux-3).
- 2026-10-16 : Reflection publie les poids de Beam sous Apache 2.0. [Source](https://reflection.ai/blog/beam-is-available).
- 2026-10-16 : Claude conçoit des circuits quantiques moins coûteux. [Source](https://www.anthropic.com/research/designing-efficient-quantum-circuits).
- 2026-10-16 : Claude retrouve l'origine des paramètres de courbes ECDSA. [Source](https://www.anthropic.com/research/ecdsa-curve-origins).
- 2026-10-17 : DeepSeek met à jour V4.1 Flash et ouvre Search et Fetch. [Source](https://api-docs.deepseek.com/news/news261017/).

Chaque ajout reçoit une affiche distincte, générée par le script du projet. Le manifeste conserve la source et l'empreinte de chaque affiche. Les fiches scientifiques distinguent prédiction, conception et validation expérimentale.

## Vérifications

- `pnpm test` passe : 125 fichiers et 883 tests du site, 7 tests de l'introduction, 4 tests des jingles et 24 tests du lecteur BIS.
- `pnpm lint` et `pnpm typecheck` passent. Le formatage des fichiers de ce lot passe.
- `pnpm check` a été lancé. Il s'arrête au formatage de `exports/reseaux-sociaux/episode-02/remplacements-tiktok-v2.md`, extérieur à ce lot. Le lint, le typage et les tests ont donc été exécutés séparément.
- Le générateur vérifie 162 compositions distinctes, pour 1 665 140 octets de SVG. Les tests contrôlent les sources, les dates, la recherche, le récapitulatif, les exports et le sitemap actualisé au 18 octobre.
- Dans le navigateur, la page locale ouvre DeepSeek V4.1 Flash 1017 au 17 octobre 2026, y compris après rechargement. Le lien `#ia-chatgpt` ouvre la fiche du 30 novembre 2022. Le lien `#wrapped-2026` affiche 52 événements et la revue au 18 octobre. Aucune erreur de console relevée sur ce parcours.
- Le vérificateur Human Quality et `git diff --check` passent.

Le lot reste local dans `C:/github/sandbox-podcast`. Aperçu : [Time Machine](http://127.0.0.1:3038/time-machine). La publication reste à faire sur demande de Lou.
