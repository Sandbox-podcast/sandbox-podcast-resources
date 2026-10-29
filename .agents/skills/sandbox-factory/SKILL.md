---
name: sandbox-factory
description: Lancer, reprendre ou diagnostiquer un cycle complet SANDBOX, du master aux rendus et au bilan. Utiliser pour coordonner plusieurs étapes ; pour une histoire originale, appliquer sandbox-storytelling-generator et pour une seule étape, son skill spécialisé. Diffusion simulée uniquement.
---

# Factory SANDBOX

Depuis la racine du dépôt, définir `PYTHONPATH=tools/youtube-growth/src` et utiliser `python -m youtube_growth.factory`. Lire [l'exploitation](../../../docs/factory/exploitation.md) pour installer ou redémarrer le runtime, choisir la base ou vérifier les paramètres. La configuration et SQLite portent l'état courant ; le [prompt maître](../../../docs/factory/sources/prompt-maitre-2026-10-28.txt) porte les exigences.

## Reprendre le travail

1. Exécuter `doctor` et `status` sur l'état choisi. Pour un épisode, recueillir `episode_id`, manifeste, master autorisé terminé, transcription disponible, preuves et prochain tournage en Europe/Paris ; importer seulement après confirmation de copie terminée. Pour une histoire originale, partir de son brief sans exiger un master d'épisode.
2. Choisir l'étape utile dans le tableau ci-dessous. Continuer les étapes indépendantes si une entrée manque : une URL absente bloque la diffusion concernée, pas l'analyse locale.
3. Vérifier les sorties, empreintes et reçus. Conserver comme manquants les examens impossibles. Une réponse d'agent ne constitue ni une revue humaine ni une autorisation sociale.
4. Terminer par le calendrier simulé et le bilan si le périmètre le demande. Après fermeture, interdire les nouveaux posts tout en poursuivant mesures et expériences existantes.

| Besoin | Skill à appliquer |
| --- | --- |
| Examiner le master et documenter sa couverture | [sandbox-analyse](../sandbox-analyse/SKILL.md) |
| Choisir les passages et leurs coupes | [sandbox-selection](../sandbox-selection/SKILL.md) |
| Rendre ou contrôler un montage | [sandbox-production](../sandbox-production/SKILL.md) |
| Préparer titres, miniatures et pack LinkedIn | [sandbox-packaging](../sandbox-packaging/SKILL.md) |
| Planifier ou reprendre la simulation | [sandbox-diffusion](../sandbox-diffusion/SKILL.md) |
| Examiner mesures, expériences et prochain brief | [sandbox-resultats](../sandbox-resultats/SKILL.md) |
| Chercher de nouveaux sujets sur Internet | [sandbox-youtube-trend-hunter](../sandbox-youtube-trend-hunter/SKILL.md) |
| Créer, reprendre ou corriger une histoire originale | [sandbox-storytelling-generator](../sandbox-storytelling-generator/SKILL.md) |

Pour la découverte multiformat et le parcours `research` / `draft-story` / `narrative`, lire [la production éditoriale](../../../docs/factory/production-editoriale.md). `discover` utilise toute la transcription ; les notes d'`editorial` et d'`opportunities` restent motivées et sans quota. Utiliser `--queue` pour les réservations de worker. Sans modèle local, traiter dans la conversation la requête exportée plutôt que prétendre à une génération exécutée en arrière-plan.

Pour StoryTelling Generator, appliquer [son skill dédié](../sandbox-storytelling-generator/SKILL.md). Si le Trend Hunter a préparé `storytelling-brief.json`, reprendre ce dossier et ses sources pour le cadrage.

Livrer l'état durable, les reçus, les fichiers locaux et le prochain besoin exact. Préserver sources, traçabilité des coupes et reprise sans doublon. Maintenir la simulation sociale, y compris pour uploads privés et brouillons distants ; LinkedIn reste manuel. Distinguer performances réelles et fixtures, contrôle technique et fidélité du montage. Un SKILL.md ne remplace pas le worker.
