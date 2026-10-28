# Audit et reprise de la factory, 28 octobre 2026

La factory reste en simulation. L'audit porte sur le code local, l'état persistant, les reprises, les fichiers de travail et l'écran de pilotage. Il ne certifie aucune intégration sociale réelle ni l'analyse complète d'une émission.

## Défauts retenus pour correction

| Défaut observé | Conséquence | Correction |
| --- | --- | --- |
| Une sélection retirée pouvait conserver ses publications admissibles. | Une ancienne décision éditoriale pouvait encore alimenter le calendrier. | Invalider les publications concernées et revérifier la sélection avant l'envoi. |
| Le plafond journalier était calculé lors de la planification. | Un autre envoi intervenu depuis pouvait rendre le créneau inadmissible. | Revérifier le nombre d'envois du compte pour le jour de Paris juste avant l'envoi. |
| Un changement de source, de transcription, de preuves ou de titre laissait une période où l'ancien pack restait admissible. | Un contenu dépassé pouvait partir avant la fin du retraitement. | Bloquer les anciens packs dès la réingestion ; une QA média seule ne les réactive pas. |
| Un ancien job de rendu conservait ses paramètres après changement de sélection. | Le worker pouvait produire un montage devenu obsolète. | Comparer les révisions et terminer le job remplacé sans produire l'ancien rendu. |
| Un média identique dans deux épisodes pouvait partager un identifiant de candidat ou de rendu. | Le second épisode pouvait remplacer l'association du premier dans SQLite. | Conserver les identifiants historiques et isoler les collisions par épisode. |
| Les miniatures étaient copiées dans les sauvegardes sans toutes les garanties des vidéos enregistrées. | Un fichier modifié ou omis dans l'inventaire pouvait laisser une revue incohérente après restauration. | Vérifier les fichiers de miniature contre les références conservées dans SQLite. |
| L'écran reconstruisait les lecteurs et les détails à chaque actualisation. | Une lecture ou une revue en cours était interrompue. | Réutiliser les éléments inchangés et conserver les états d'ouverture. |
| La base et les données synthétiques étaient peu visibles. | Une recette pouvait être prise pour le suivi opérationnel. | Afficher l'espace de suivi, le périmètre des données et le mode de simulation. |
| La fenêtre affichée ne correspondait pas forcément à l'épisode. | Une vue de plusieurs épisodes pouvait montrer la mauvaise échéance. | Rattacher chaque fenêtre à son épisode enregistré. |
| Une requête JSON de type liste ou une action mal formée pouvait interrompre la réponse HTTP. | Le tableau perdait le retour d'erreur. | Valider la forme des requêtes et répondre explicitement ; refuser les origines et hôtes étrangers. |

## Fonctions de pilotage

Le diagnostic rassemble les contrôles à effectuer, les traitements échoués et les résultats incertains. Chaque entrée conserve son identifiant et propose une suite précise. Il n'accorde aucune validation audiovisuelle ou éditoriale.

Le suivi du worker distingue une horloge de recette, un passage récent, un passage ancien, une date incohérente et l'absence de passage. Le seuil d'ancienneté est de trois minutes. Un passage ancien est un signal de vérification : un long traitement peut être en cours. Les traitements réservés restent visibles à côté de cet indicateur.

Le journal montre les cinquante derniers événements liés aux épisodes sélectionnés, ainsi que les événements globaux de la file. Les événements historiques restent dans SQLite. Le filtre de plateforme concerne les publications ; le journal et les médias gardent le périmètre de l'épisode.

La commande `diagnostics` fournit ces informations en JSON, avec les mêmes filtres d'épisode et de plateforme que `status`. Le téléchargement depuis le tableau utilise les filtres d'épisode et de plateforme. Il produit un état de diagnostic, avec les chemins locaux et les contenus éditoriaux ; il ne remplace pas une sauvegarde portable.

## Ce qui reste à intégrer

| Besoin | État et prochaine preuve attendue |
| --- | --- |
| Analyse d'un véritable épisode | Fournir le master, la transcription et les preuves d'examen des images et du son ; mesurer la couverture et relire les coupes. |
| Compréhension audiovisuelle en arrière-plan | Aucun modèle n'est configuré. Définir le fournisseur, le coût autorisé, les entrées, la reprise et les contrôles avant d'activer des appels. |
| Miniatures d'un épisode réel | Le moteur et le protocole existent. Les images de recette ne prouvent pas la qualité éditoriale : appliquer le benchmark au sujet réel et faire une revue croisée. |
| Connexion des comptes | Vérifier les autorisations et capacités de chaque compte. Les connecteurs restent simulés ; LinkedIn reste manuel. |
| Expériences natives de titres et miniatures | Vérifier l'éligibilité dans Studio et suivre les résultats natifs. Ne pas déduire un gagnant des vues publiques. |
| Mesures réelles | Importer des observations avec leur définition, période et provenance ; aucune performance réelle n'est déduite de la recette. |
| Fonctionnement permanent | Le worker Windows dépend de la machine et de la session utilisateur. Un service sur une machine dédiée demanderait une installation et une exploitation distinctes. |

Ces besoins sont conservés comme des capacités manquantes. L'interface n'affiche aucun bouton qui prétend les exécuter sans moteur ni accès.

## Vérification

Les preuves de cette reprise et les limites des contrôles sont consignées dans [la validation du rework](validation-rework-2026-10-28.md). Le [guide pour l'équipe](README.md) décrit l'usage courant ; [l'exploitation](exploitation.md) décrit les commandes.
