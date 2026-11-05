# Génération native et prompts

Utiliser l'outil natif d'images de l'assistant pour créer et éditer les bitmaps. Aucun script API, clé ou abonnement externe n'est requis par ce dossier. Si l'environnement n'offre pas la génération avec références, le dire ; ne pas prétendre avoir produit trois miniatures avec de simples maquettes.

Pour une image locale à modifier, l'ouvrir avec l'outil de visualisation avant l'édition. Joindre chaque référence à la génération en précisant son rôle. Le nom d'un fichier dans le prompt ne suffit pas à rendre l'image accessible au générateur.

## Références pour un groupe SANDBOX

La génération approuvée utilisait cinq fichiers par variante :

1. La planche d'exemples de Lou, uniquement pour le pattern.
2. Le portrait sélectionné de Lou, à intégrer en préservant la pose, l'expression et le vêtement.
3. Sa photo originale, comme ancre d'identité, sans imposer son vêtement.
4. La photo originale de Nicolas.
5. La photo originale de Loïc.

Cette répartition tient dans la limite de cinq références observée dans l'outil utilisé. Vérifier la capacité de l'outil disponible. Pour un sujet solo, les places libérées peuvent accueillir la preuve réelle du résultat ou une référence de composition supplémentaire. Ne pas sacrifier une identité pour ajouter un autre exemple de style.

## Structure de prompt

Décrire l'image finale, puis les rôles des références, la disposition et le texte exact. Répéter les invariants utiles lors d'une correction. Gabarit à adapter :

```text
Créer une miniature YouTube horizontale 16:9 sur [sujet vérifié].
La vidéo est [discussion, démonstration ou résultat réellement montré].
Image 1 : référence de composition uniquement, aucun visage à recopier.
Image 2 : portrait à intégrer ; préserver expression, pose et tenue.
Images suivantes : ancres photographiques des personnes nommées.
Composition : [grosse accroche, objet ou schéma simple, visages serrés].
Texte littéral : [mots exacts, sans ajout].
Fond et contraste : [selon les références et le sujet].
Préserver les identités, âges apparents, cheveux, barbes et proportions.
Pas de visage supplémentaire, de faux résultat ni de métrique inventée.
Pas de petit texte décoratif ; laisser le coin inférieur droit disponible.
```

Les [prompts réellement employés](../assets/examples/sandbox-equipe-tech-ia/generation-log.json) sont inclus pour les trois variantes approuvées. Les adapter au prochain brief. Ils ne remplacent pas la lecture du contenu et le choix des portraits.

## Correction ciblée

Ouvrir l'image, nommer le défaut visible et limiter le changement à sa zone. Conserver le master initial. Exemple validé : dans B, remplacer seulement le schéma de l'écran par PO puis DEV puis QA, en gardant tous les portraits, le texte, les couleurs et l'ordinateur. Voir [le prompt de correction](../assets/examples/sandbox-equipe-tech-ia/correction-B-v2.json).

Après édition, examiner à nouveau le résultat complet et les aperçus : une correction locale peut faire dériver un visage ou déplacer un mot.
