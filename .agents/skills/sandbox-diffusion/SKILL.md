---
name: sandbox-diffusion
description: Planifier, suspendre, reprendre ou simuler le calendrier de diffusion SANDBOX après contrôle des médias et du packaging. Respecter disponibilité réelle, prochain tournage et tentatives incertaines ; LinkedIn manuel et aucune mutation sociale réelle.
---

# Préparer la diffusion

Réunir `episode_id`, disponibilité vérifiée de l'émission complète, rendus et packaging contrôlés, comptes configurés et prochain tournage explicite. Utiliser `status`, `plan`, `simulate`, `pause` et `resume` sur le bon état persistant ; consulter [l'exploitation](../../../docs/factory/exploitation.md) pour leurs paramètres.

1. Calculer la fenêtre en Europe/Paris entre disponibilité effective et prochain tournage, avec marge de traitement. Une date prévue ne prouve pas la disponibilité. Stocker des instants avec décalage UTC ; faire préciser une heure ambiguë lors d'un changement d'heure.
2. Après retard, recalculer dans la fenêtre restante sans déplacer la borne finale. Éviter les sujets trop rapprochés et archiver le surplus justifié. Appliquer la fermeture même sans nouvel épisode ; aucun rattrapage en rafale d'échéances expirées.
3. Laisser le runtime réserver atomiquement le travail. Revérifier cycle, disponibilité, compte, empreintes et validité immédiatement avant chaque envoi simulé. Lire l'état durable avant de reprendre ; ne pas effacer une intention pour forcer une tentative.
4. Pour une tentative au résultat inconnu, conserver le blocage jusqu'à réconciliation. Borner les reprises selon le runtime ; continuer les contenus indépendants encore admissibles.

Maintenir les connecteurs simulés, même avec des credentials. Les uploads privés, ébauches distantes, programmations et modifications sont des mutations sociales interdites dans ce parcours. Préparer uniquement le pack manuel pour LinkedIn.

Livrer calendrier persistant, statuts, journal de tentatives, identifiants `sim:`, blocages par contenu et actions humaines. Le succès de simulation ne prouve pas une intégration réelle. Consulter [les capacités](../../../docs/factory/capacites.md) si une activation réelle est demandée ; ce skill ne l'active pas.
