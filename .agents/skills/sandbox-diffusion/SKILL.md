---
name: sandbox-diffusion
description: Préparer le calendrier SANDBOX et exécuter sa simulation en respectant disponibilité réelle, échéance, comptes et reprises incertaines. Utiliser pour planifier, suspendre ou reprendre un cycle ; aucune mutation sociale réelle.
---

# Préparer la diffusion

Entrées : épisodes, disponibilité vérifiée de l'émission complète, rendus contrôlés, packaging, comptes configurés et prochain tournage explicite. Paramètres : `episode_id`, plateforme, instant avec décalage UTC et état persistant. Outils : commandes `plan`, `simulate`, `status`, `pause`, `resume` de la factory. Vérifie leur aide dans [le parcours d'exploitation](../../../docs/factory/exploitation.md).

Calcule la fenêtre en Europe/Paris entre disponibilité effective et prochain tournage, avec marge de traitement. Une date prévue ne prouve pas la disponibilité. Stocke des instants non ambigus ; ne devine pas une heure lors d'un changement d'heure. Après retard, recalcule dans la fenêtre restante sans déplacer la borne finale. Évite les sujets trop rapprochés et archive le surplus justifié.

Consulte le vrai état, réserve atomiquement le travail, puis revérifie cycle, disponibilité et validité immédiatement avant l'envoi simulé. Une fermeture doit s'appliquer même sans nouvel épisode. Ne rattrape pas les échéances expirées en rafale.

Le connecteur doit rester simulé, même si des credentials existent. Aucune publication, upload privé, ébauche distante, programmation ou modification distante n'est autorisée. LinkedIn produit uniquement son pack manuel. Les nouvelles tentatives sont bornées ; un résultat inconnu exige une réconciliation avant toute reprise. Ne supprime pas une intention pour forcer un nouvel envoi.

Sorties : calendrier persistant, statuts et journal de tentatives, identifiants `sim:` reconnaissables, blocages par contenu et actions humaines. Le succès de simulation ne prouve pas une intégration réelle. Toute activation future exige le périmètre explicite de Lou et les prérequis de [la matrice](../../../docs/factory/capacites.md).
