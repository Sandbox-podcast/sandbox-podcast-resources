# Livraison du lot local du 20 octobre 2026

Lou demande une seule PR contenant tout le travail local non encore livré. Le lot est intégré sur `main` à partir de `b8dd73d`, après les PR 99 et 100. Le checkout utilisé pour la démonstration locale reste intact.

## Contenu

- Accueil immersif composé de six salles, avec ouverture sous le curseur sur toute la surface et traversée vers la salle suivante. Le décor repose sur des images projetées et des éléments interactifs ; il ne constitue pas un monde 3D librement navigable.
- Projets intégrés au vidéoclub, quatre accès aux classements avec préchargement et statut au clic, chronologie complète et salle cinéma avec les deux derniers replays disponibles.
- Affiches de cinéma propres aux épisodes 001 et 002, titrage HTML traduit et pagination prévue pour accueillir les prochains replays.
- Choix initial de langue selon le navigateur, priorité au choix manuel mémorisé et maintien des routes explicites dans leur langue.
- Supports LinkedIn, historique et planification des clips de l’épisode 02, documentation de conception et suivi du quota demandé dans AGENTS.md. Aucune publication sociale n’est exécutée par cette livraison.

Les corrections déjà livrées sur `main`, notamment la reprise persistante de découverte et les alias des anciens textes publiés, sont conservées. Les historiques sociaux gardent les publications existantes et ajoutent les réservations locales plus récentes.

## Corrections issues de la recette d’intégration

La frontière `charts/loading.tsx` ajoutée au lot a été retirée : elle déclenchait le streaming avant la détection des archives absentes, qui renvoyaient alors HTTP 200. Le test conserve son exigence de statut 404. Le retour visuel au clic reste porté par les liens du terminal.

Le nettoyage du renderer libère ses ressources sans forcer la perte du contexte du canvas. Le canvas peut ainsi être réutilisé après un retour navigateur, une préférence de mouvement ou un changement de format. Une création de renderer réinitialise également l’état de traversée.

## Validation

- `pnpm check` : format, lint, types, 148 fichiers et 1 225 tests du site, plus les autres suites du dépôt.
- `pnpm --filter @podcast/site build` : compilation réussie.
- Python : 3 tests du résumé News, 4 tests des kits relais et 15 tests du pipeline vidéo réussis. Le contrôle des sources valide 30 clips.
- Audit des dépendances : aucune vulnérabilité connue signalée.
- Gitleaks sur les fichiers préparés : aucune fuite détectée.
- Routes publiques : recette HTTP réussie, dont archives et méthodologies absentes en 404.
- News : 11 groupes de vérification réussis, dont publication locale, langues, pagination, clic du terminal radar et panne SQL ; aucune erreur JavaScript. Le test utilise désormais le sélecteur des salles et le mode mouvement réduit pour isoler le parcours éditorial.
- Analytics : consentement bloqué puis prêt vérifié. Publication d’épisode : parcours admin, lecteur et chapitre vérifiés sur des fixtures locales, sans écriture distante.
- OpenGraph : les 13 routes contrôlées incluent leurs cinq polices. Sécurité admin HTTP : contrôle réussi sans accès à une base distante.
- Playwright responsive : 128 contrôles réussis, de 320 à 3440 pixels, six salles, texte agrandi à 200 %, interaction tactile et navigation sans JavaScript ; aucun problème relevé.
- Playwright sur la copie consolidée : six salles, ouverture globale, traversées, clavier, Escape, retour navigateur, hash direct et redimensionnements WebGL de 901 à 3440 pixels ; repli portrait puis restauration du moteur vérifiés sans erreur JavaScript.

Les journaux d’intégration sont conservés hors Git dans `.local/pr-*.log` du checkout principal. Les recettes antérieures et leurs limites restent documentées dans les rapports de salles, d’affiches et de performance. Les mesures de navigation en développement ne sont pas des garanties de temps en production. Les contrôles CI distants sont à consulter sur la PR.
