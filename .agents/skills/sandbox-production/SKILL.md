---
name: sandbox-production
description: Rendre et contrôler les montages locaux SANDBOX depuis des coupes validées, avec provenance, sous-titres et reprise par empreinte. Utiliser pour produire ou réviser un média, sans téléverser de fichier.
---

# Produire les médias

Entrées : source autorisée, sélection sourcée, coupes en secondes, transcription et disposition choisie. Paramètres : `episode_id`, `segment_id`, format et version. Outils : Python, FFmpeg et FFprobe, en conservant les moteurs du dépôt. Lis [le guide](../../../docs/factory/exploitation.md) et l'aide de `render` / `qa` avant exécution.

Conserve le master intact et écris dans un dossier de sortie lié aux empreintes. Une correction du titre ne justifie pas de retranscription ni de réencodage. Un changement de source, de coupes ou de paramètres invalide les sorties et contrôles qui en dépendent. Ne remplace pas une ancienne version associée à une publication.

Choisis le 9:16 ou le 16:9 selon le contenu. Vérifie la lisibilité de la démonstration avant recadrage ; garde le cadre complet ou une composition adaptée si le vertical cache l'information. Utilise les vrais visages et assets autorisés de `assets/brand/`. Garde un master propre et des sous-titres réutilisables. Corrige les noms propres, modèles et acronymes en comparant avec le son.

Contrôle lecture intégrale, durée, pistes, codec, dimensions, synchronisation et signaux de silence, saturation ou noir. Inspecte les images et écoute les rendus avec les moyens disponibles. Sépare contrôles techniques et revue de fidélité, cadrage et sous-titres ; une vérification impossible reste manquante.

Sorties : fichiers, SRT éventuel, carte des coupes source / sortie, empreintes et contrôles liés à la version. Un fichier défectueux bloque sa propre déclinaison. Une source manquante ou copiée partiellement empêche le rendu définitif. Aucun quota et aucun média tiers sans droits établis.
