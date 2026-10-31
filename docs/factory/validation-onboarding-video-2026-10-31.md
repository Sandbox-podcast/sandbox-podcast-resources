# Validation de l'onboarding vidéo, 31 octobre 2026

Suivi : [issue #52](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/52). Le [guide de l'onboarding](onboarding-video.md) décrit le parcours, la [référence voix](../../.agents/skills/sandbox-video-onboarding/references/voix.md) les réglages de Voice Studio.

## Collections installées

| Collection | Commit épinglé | Contenu installé |
| --- | --- | --- |
| `autopunk-media-skills` | `39e119bfef25957223d6c44fccab0329e936d2f6` | 408 skills, 50 variantes localisées, 9 agents, licence et README |
| `screenwriting-skills` | `51115f18d160aa8b2ac5813e4432b6f0b425358f` | 26 skills, 51 références, `LICENSE`, `NOTICE`, README anglais et français |
| `cc-skills` | `123cb155f5ab5751fc13c8027fbfa5eb0d3773c6` | `humaniseur-fr` et sa licence |

L'installation a lu ces commits depuis GitHub, objet par objet, sans extraire l'arbre amont. Le chemin relatif le plus long mesure 117 caractères ; les jeux d'évaluation, dont les noms dépassaient la limite Windows dans un dossier profond, ne sont pas installés. Aucun skill nommé « Spoken Script Editor » n'existe dans ces trois sources ; les autres skills cités par Lou ont été retrouvés et routés (`sw-story-structure`, `commentary-writer`, `documentary-narration-writer`, `narrator-voice-adapter`, `humaniseur-fr`).

## Voice Studio

Le service local répondait sur `127.0.0.1:3900` en version 0.5.7, sur CUDA. Seules des lectures ont été faites : `/health`, `/profiles`, `/engines/tts`, `/engines/effects/presets`, `/openapi.json`. Le contrat en ligne comportait les mêmes 306 routes que la capture locale. Deux profils étaient présents : « Lou », clone français avec consentement attesté, et « Demo Voice », voix de démonstration anglaise. Moteurs disponibles : VoxCPM2 (actif), OmniVoice, OmniVoice isolé et KittenTTS.

Les réglages réellement appliqués viennent de la lecture du code du backend 0.5.7 : VoxCPM2 ne lit ni `speed` ni `duration` et transforme une consigne en préfixe qui remplace la continuation sur la référence ; OmniVoice applique vitesse, durée et étiquettes de timbre ; KittenTTS applique la vitesse et ignore la consigne. Aucune génération n'a été demandée au service : la synthèse, le cache, les sous-titres mesurés et les erreurs sont testés contre un faux service local.

## Contrôles exécutés

| Contrôle | Résultat observé |
| --- | --- |
| Suite Python de la factory, Python 3.14 de l'environnement factory | 453 tests, succès, 11 ignorés selon leurs prérequis ; 435 tests avant ce chantier. |
| Tests du dépôt | 24 tests, succès ; les 8 tests de l'assistant GitHub sont ignorés faute de PowerShell 7 sur ce poste. |
| Clone propre de la branche | `vendor_skills.py check` et `check_repository.py` sans erreur, 555 fichiers de collections suivis. |
| Collections | `vendor_skills.py check` : empreintes, licences et catalogue conformes. |
| Skills SANDBOX | `sync_skills.py` : 10 skills vérifiés, entrée Claude de `sandbox-video-onboarding` générée. |
| Index Git | `check_repository.py` et `git diff --check` sans erreur. |
| Interface | Page `/storytelling` ouverte sur un état de recette : vidéos guidées, étapes et inventaire réel de Voice Studio affichés. |
| CLI | Parcours de recette jusqu'au cadrage StoryTelling avec la voix « Lou » choisie, puis cadrage périmé après une réponse modifiée. |

Une passe d'audit indépendante a corrigé l'invalidation après un changement de voix Windows, ajouté le refus d'une voix fixée sous une autre version de Voice Studio, distingué profils clonés et conçus, et appliqué `delivery.pause_after_seconds` au montage sans modifier les caches existants.

La première CI de la PR a échoué sur `vendor_skills.py check`. Deux causes : la règle `**/analysis/` du `.gitignore` avait écarté six skills Autopunk de `data-journalism/analysis`, et l'empreinte dépendait de l'ordre de tri des chemins, différent sous Windows et Linux. Une exception limitée aux fichiers texte de `.agents/vendor/` et un tri par chemin POSIX corrigent ces deux points ; deux tests les couvrent. La réinstallation depuis les commits épinglés a reproduit les mêmes fichiers et le même catalogue. La CI relancée après ce correctif a réussi ses 8 contrôles.

Les références de `screenwriting-skills` citent des ouvrages que leur licence MIT ne couvre pas (`NOTICE` amont). Lou a choisi de les garder dans le dépôt public ; le [README des collections](../../.agents/vendor/README.md) rappelle qu'elles ne doivent pas être recopiées dans un livrable.

## Ce qui reste à vérifier

Aucune vidéo n'a été produite et aucune voix n'a été générée pendant ce chantier. La qualité de la voix de Lou sur VoxCPM2, l'effet d'une consigne d'interprétation et le rendu d'un commentaire dynamique écrit pour l'oral restent à juger à l'écoute, sur une première vidéo. La découverte du skill par une nouvelle session Codex ou Claude Code doit être constatée dans le harnais utilisé. Les recettes `FACTORY_MEDIA_INTEGRATION=1` n'ont pas été lancées.
