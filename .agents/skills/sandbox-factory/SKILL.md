---
name: sandbox-factory
description: Lancer ou reprendre un cycle local SANDBOX, du master aux rendus et au bilan, ou produire une histoire avec StoryTelling Generator. Diffusion simulée uniquement.
---

# Factory SANDBOX

Travaille dans `tools/youtube-growth`, avec le module `youtube_growth.factory`. Lis [l'exploitation](../../../docs/factory/exploitation.md), puis les consignes du périmètre modifié. Le [prompt source](../../../docs/factory/sources/prompt-maitre-2026-10-28.txt) décrit les exigences ; la configuration et l'état persistant renseignent leur exécution.

Entrées : manifeste d'épisode, master autorisé terminé, transcription éventuelle, preuves d'analyse et configuration. Paramètres utiles : `episode_id`, emplacement de l'état, fuseau Europe/Paris et borne du prochain tournage. Outils : Python, FFmpeg et FFprobe. Aucun compte social n'est nécessaire pour la recette locale.

1. Exécute `python -m youtube_growth.factory --help`, puis `doctor` et `status` avec le bon état. Ne déduis pas l'état courant d'un ancien rapport.
2. Importe l'épisode seulement après signal de copie terminée. Traite ensuite les étapes disponibles. Une URL absente bloque la préparation de diffusion qui en dépend, sans empêcher l'analyse locale.
3. Applique les skills spécialisés pour l'analyse, la sélection, la production, le packaging, la diffusion simulée et les résultats. Réutilise les commandes et fonctions métier existantes.
4. Vérifie les fichiers produits et leur provenance. Garde les contrôles visuels et d'écoute manquants comme manquants. Un rendu ne certifie pas le sens du montage.
5. Consulte le calendrier, simule les échéances, relève les erreurs puis produis le bilan. La clôture interdit les nouveaux posts, tout en laissant continuer mesures et expériences existantes.

Pour le parcours multiformat, lis [la production éditoriale](../../../docs/factory/production-editoriale.md). `discover` prépare les sujets depuis toute la transcription ; `editorial` et `opportunities` enregistrent des notes motivées, sans quota ni validation audiovisuelle implicite. Les vidéos originales utilisent `research`, `draft-story` puis `narrative`, avec les mêmes réservations de worker via `--queue`. Un modèle local absent reste un blocage explicite ; ses requêtes sont utilisables dans la conversation. Ne transforme pas une réponse d'agent en revue humaine ni en autorisation sociale.

Sorties : état durable du cycle, reçus d'étape, rendus, packs manuels, calendrier simulé et bilan. Qualité attendue : coupes traçables, reprise sans doublon, sources intactes, aucune performance synthétique présentée comme réelle.

Les uploads privés, brouillons distants et programmations sont des mutations sociales. Ils restent interdits. LinkedIn reste exclusivement manuel. Si le runtime est arrêté, redémarre-le selon le guide ; un SKILL.md ne remplace pas le worker. Si une donnée ou un accès manque, bloque seulement l'étape concernée et indique le besoin exact.

Pour StoryTelling Generator, lis [le parcours et ses reprises](references/storytelling.md), puis [son tutoriel](../../../docs/factory/storytelling-generator.md). Le sujet vient du brief de Lou ; le corpus narratif fournit une méthode d'écriture.
