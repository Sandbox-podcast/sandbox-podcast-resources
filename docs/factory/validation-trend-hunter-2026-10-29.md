# Validation du YouTube Trend Hunter, 29 octobre 2026

Suivi : [issue #15](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/15). Le [guide d'utilisation](../../tools/youtube-growth/TREND-HUNTER.md) décrit les commandes et leurs limites.

Le skill `sandbox-youtube-trend-hunter` utilise le package Python existant. Les sept autres skills avaient déjà le préfixe `sandbox-` ; leurs noms sont conservés. Les huit points d'entrée Claude Code renvoient aux sources de `.agents/skills/`. Le contrôle des noms et de la synchronisation est ajouté à la CI.

## Contrôles exécutés

| Contrôle | Résultat observé |
| --- | --- |
| Suite Python du package, checkout isolé de PR | 289 tests, succès, 5 ignorés selon leurs prérequis. |
| Tests ciblés après les dernières modifications | 17 tests Trend Hunter, succès. |
| Tests du dépôt | 8 tests, succès, dont les deux contrôles de noms et de points d'entrée. |
| Validation des skills | Les huit sources et les huit points d'entrée passent `quick_validate.py`. |
| Dépendances déclarées | Tests ciblés avec Pillow 12.3.0 et tzdata dans un environnement local séparé. |
| Structure | `sync_skills.py`, `check_repository.py`, compilation Python et `git diff --check` exécutés avec succès. |
| Documentation | Liens locaux du guide, du nouveau skill et des points d'entrée vérifiés. |

Les fixtures couvrent les budgets séparés de YouTube, le jour Pacifique, le cache sans nouvelle observation, la réservation d'une tentative échouée, les lectures groupées, les recherches FR/EN, l'historique de chaîne, les statistiques cachées, les formats courts inconnus, la médiane à âge comparable, les vitesses et accélérations, les alias, les titres syndiqués, les pannes et la préparation documentaire. La génération ElevenLabs est testée avec un transport fictif ; les cas de dépassement activé et de résultat incertain empêchent le POST ou sa répétition.

## Collectes réelles sans clé

Les modes `ai-tech` et `general` ont été exécutés avec le réseau disponible. Trends retourne vingt éléments, News deux cents éléments en IA/tech et soixante-douze en général, Reddit vingt-cinq éléments avec un autre flux refusé en HTTP 429, et Hacker News cinquante éléments. Ces nombres décrivent les réponses observées, pas une audience ni un historique complet.

La recette a révélé que plusieurs éléments Trends partageaient l'URL du flux et que des titres News syndiqués pouvaient gonfler la confirmation. Les identifiants Trends incluent désormais le sujet et la région ; les copies d'un même titre ne comptent pas comme des confirmations indépendantes. Ces deux cas ont leurs tests de régression.

Aucune clé YouTube n'a été utilisée. Les vues, la surperformance et la concurrence restent donc non mesurées dans les rapports réels. Après déduplication et application des critères, aucun sujet n'atteint le niveau de preuve nécessaire au classement. Les pistes et motifs de rejet restent consultables. Le moteur ne complète pas le TOP avec des sujets inventés.

Les fichiers de recette restent sous `.local/youtube-trend-hunter/` et `.local/trend-hunter-work/`. Les rapports contiennent les dates de collecte et la provenance de chaque élément. Aucun résultat synthétique n'est présenté comme une tendance réelle.

## Préparation et rendu

Un dossier de recherche synthétique a servi à préparer le script, quatre séquences, les titres, la description, les crédits et les cartes SVG/PNG originales. Une piste audio de test a ensuite été importée et assemblée en vidéo H.264/AAC 1920 × 1080. La recette courte utilise explicitement l'exception réservée aux démonstrations synthétiques. Le rendu a passé les contrôles de résolution, piste audio, durée et décodage complet ; une image extraite a été inspectée.

Ce test vérifie le montage local. Il ne valide ni une narration ElevenLabs réelle, ni la fidélité d'un sujet d'actualité, ni la synchronisation à l'écoute d'une vidéo de production. Le reçu garde `audiovisual_review=pending` et identifie les temps estimés des sous-titres. Les sources, le script, le storyboard, les visuels et la narration ont des empreintes vérifiées avant réutilisation.

L'API ElevenLabs n'a pas été appelée avec un compte réel. La recherche n'en consomme jamais les crédits. L'import manuel du MP3 reste le parcours par défaut ; la génération facultative exige un dépassement désactivé côté compte et des limites vérifiables.

La découverte du nouveau nom dans les catalogues d'une nouvelle session Codex ou Claude Code n'est pas attestée par la seule validation des fichiers. Les points d'entrée existent et sont valides ; leur chargement doit être constaté dans le harnais utilisé.

## Entrée StoryTelling, issue #20

Le [contrat de cadrage de la PR #19](https://github.com/Sandbox-podcast/sandbox-podcast-resources/pull/19) a été lu à la révision `2e0266f522530174f618641425a8f10b63722c7c`. Après une sélection explicite du sujet, `storytelling RANG --run IDENTIFIANT` exporte `storytelling-brief.json`, les documents archivés, leurs métadonnées, les citations et la provenance des observations. Ce transfert ne produit ni scénario ni voix.

Sept tests couvrent le transfert, le choix lié à l'analyse d'origine, les sources absentes ou modifiées, les versions et les reprises identiques. Le test de compatibilité exécute les vrais `frame`, `import_sources` et `build_request` de cette révision de la PR #19, dans un autre interpréteur. Le cadrage est accepté, les documents sont importés sans accès réseau, leurs citations restent reliées aux bons identifiants et la requête de scénario reçoit les sources. L'original documentaire est supprimé avant cet import pour vérifier que le dossier transféré suffit.

La recette utilise un sujet et des textes synthétiques. Elle ne confirme aucune tendance réelle ni aucun droit sur une voix. Le budget monétaire et les crédits navigateur restent à zéro par défaut, le mode documentaire attend une validation éditoriale et les choix de voix restent visibles. Une sélection de tendance ne constitue pas une approbation du scénario. Le test de compatibilité peut utiliser `STORYTELLING_CONTRACT_ROOT` pour pointer vers le checkout cible ; sans ce checkout ni le module installé, ce seul test est ignoré.

Après ajout du transfert, la suite complète exécute 296 tests avec succès, dont 5 ignorés selon leurs prérequis ; le checkout de la PR #19 est fourni pour que le test de compatibilité soit effectivement exécuté. Les sept tests ciblés passent aussi après les derniers contrôles de voix et de crédits transmis. Les huit tests du dépôt, les seize validations de skills, les liens locaux, la compilation et le contrôle de l'index sont vérifiés séparément.
