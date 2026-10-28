# Consignes de la factory SANDBOX

Ce module étend le package Python existant. Lire [l'exploitation](../../../../../docs/factory/exploitation.md) et les README des moteurs utilisés avant modification. Les sources, reçus et décisions historiques restent conservés. Le prompt du 28 octobre, référencé dans [l'audit](../../../../../docs/factory/audit.md), prime sur les anciennes cadences.

## Analyse et médias

Pour `media.py` et ses appels : conserver l'empreinte source, les secondes explicites et la correspondance des coupes source / sortie. Ne jamais écraser le master. Distinguer transcription, décodage, échantillonnage visuel et compréhension des propos ; les lacunes restent visibles. Aucun quota ni sélection définitive par simple score. Un changement de source ou montage invalide ses contrôles, une correction de titre réutilise les calculs compatibles. Une revue technique ne certifie pas la fidélité éditoriale.

## Packaging

Pour `packaging.py` : chaque texte vient des propos et preuves disponibles. Employer les vrais assets de `brand/`, les apostrophes simples et guillemets droits. Une miniature importée, une première image et une fonction Studio restent distinctes. Préserver le verrou d'une expérience active. LinkedIn reçoit exclusivement un pack local avec destination, embargo, date conseillée et fin de validité.

Pour `thumbnails.py`, suivre la [procédure](../../../../../docs/factory/miniatures.md) : références visuelles pertinentes et datées, preuves du passage, trois concepts titre/image distincts, mots et cadrage justifiés, aperçus 320/160 et revue croisée. Aucun gagnant de performance déduit des vues publiques. La QA média ne valide pas le packaging. Toute révision invalide sa revue ; vérifier les empreintes avant planification et envoi simulé. Ne pas utiliser un gabarit historique comme preuve de conception.

## Diffusion et persistance

Pour `scheduler.py`, `runtime.py`, `store.py`, `connectors.py` et les commandes : la base porte l'état d'exécution. Réserver atomiquement avant traitement ; revérifier disponibilité, fenêtre, compte et empreinte juste avant envoi. Une date prévue ne prouve pas la disponibilité. La fermeture s'applique sans nouvel épisode et interdit les rattrapages tardifs. Un résultat inconnu bloque le renvoi jusqu'à réconciliation. Ne pas effacer l'intention pour forcer la reprise.

La simulation doit empêcher tous les chemins de mutation sociale, y compris les anciens outils, même avec des credentials. Aucun upload privé, brouillon distant, programmation ni modification distante. Les identifiants simulés sont reconnaissables. LinkedIn ne possède aucun chemin d'envoi. Ne pas confondre succès du mock et intégration vérifiée ; consulter [les capacités datées](../../../../../docs/factory/capacites.md).

## Résultats et coûts

Pour `analytics.py` : garder définitions natives, périmètres, périodes, unités et provenance. Une mesure manquante reste absente. Ne pas sommer relevés cumulés, fenêtres recouvrantes ou médias partagés. Séparer les observations réelles des fixtures. Un test peut rester non concluant ; une comparaison séquentielle n'est pas randomisée. Les mesures, rapports et expériences continuent après clôture des posts. Toute décision conserve justification, valeurs avant / après et date de réévaluation, avec retour possible. Les dépenses externes restent désactivées.

## Vérification

Exécuter les tests adaptés aux risques modifiés, puis la suite Python du package. Utiliser une horloge contrôlée pour délais, fermeture et changements d'heure, et des adaptateurs simulés pour les pannes. Vérifier les vrais fichiers rendus en plus des tests. Signaler séparément contrôle réussi, contrôle manquant, intégration non vérifiée et accès bloqué. Aucun commit, push ou PR sans demande de Lou.
