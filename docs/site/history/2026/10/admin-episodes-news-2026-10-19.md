# Épisodes admin et fil News, 19 octobre 2026

Mise à jour de suivi : la PR 94 est fusionnée et son déploiement Vercel est déclaré réussi. Le contrôle CI News était en échec sur un sélecteur masqué ; la correction et les vérifications complémentaires figurent dans l'audit de stabilisation du même jour. La file est absente du schéma de production consulté. Voir [le rapport](audit-stabilisation-2026-10-19.md).

Lot préparé pour la PR demandée par Lou dans un checkout isolé de main. Les autres travaux du répertoire d'origine restent hors du lot. Aucune migration distante, variable de production ni description YouTube n'est modifiée par cette livraison.

## Épisodes

La création affiche une miniature compacte, un titre modifiable et une description facultative. Le double aperçu et le bloc qui ressemblait à une deuxième étape sont retirés. La durée ne bloque plus la sauvegarde et reste omise quand elle manque. Sans date YouTube, le site utilise l'instant d'ajout de la vidéo au formulaire ; une republication avec une date vide conserve la date enregistrée. Les chapitres présents dans la description restent utilisables sans durée.

La recette navigateur publie un épisode avec un import oEmbed simulé, sans date ni durée, puis contrôle l'iframe et le lien vers un chapitre. Le cache éditorial public existant peut retarder sa lecture de cinq secondes ; la recette attend sa disponibilité dans un délai borné. Le compte, le contenu et la base sont éphémères. Aucune erreur JavaScript n'est remontée.

L'épisode 2, 7KVqydbGow0, possède une description publique sans chapitres lors du contrôle. Une proposition conservant le texte existant est préparée dans le dossier local ignoré par Git du répertoire d'origine : .local/episode-admin-2026-10-19/description-youtube-episode-2.txt. Ses repères viennent d'une transcription locale et attendent une validation d'écoute. Elle n'a pas été enregistrée sur YouTube : aucun jeton OAuth ni session Studio exploitable n'est disponible.

Décision : [DD-0060](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0060-publication-episode-sans-duree.md).

## News

Le cron existant reste programmé toutes les heures, à la minute 23. Il consulte désormais 105 adresses : dix sources précédentes et 95 adresses uniques ajoutées depuis la liste de Lou. Les doublons MiniMax Audio et The Rundown AI sont regroupés. Les URL de référence ne gardent aucun UTM.

La collecte enregistre les candidats dans Postgres avant l'installation des modèles. Le traitement réserve ensuite les plus anciens par lots de cinq et enchaîne les lots dans un budget de 22 minutes. Une réservation de vingt minutes évite les traitements concurrents et permet une reprise après interruption. Les contrôles de rédaction et de traduction restent obligatoires. Un rejet attend 24 heures avant un nouvel essai ; après trois tentatives, la ligne reste enregistrée pour examen. Une publication déjà confirmée en base ne repart pas en génération, même si l'accusé de fin a été perdu.

Le passage réel en lecture seule obtient 97 réponses HTTP 200 sur les 105 index. Le parseur trouve des données datées sur 77 sources et des données partielles sur huit autres. Il produit 263 candidats récents venant de 62 sources ; tous passent le schéma de source. Huit adresses refusent l'accès en HTTP 403 ou 429 ; douze autres ont encore des formats sans lien, date ou ancre exploitable. Le [relevé CSV](news-sources-2026-10-19.csv) distingue chaque cas. Les HTML et extraits de travail restent locaux, hors de Git. Ce contrôle ne lance pas de modèle et ne publie aucun article.

Les articles publiés s'accumulent sans doublon d'URL dans news_items. La lecture publique retire le plafond de 200 et la limite des quatorze derniers jours. Elle charge 30 fiches, puis les suivantes avec un curseur date et identifiant. La fenêtre de quatorze jours concerne seulement l'admission des nouveaux candidats. Les filtres portent sur les articles déjà chargés.

La page, les menus, le pied de page, la carte d'accueil et le radar restent fermés quand le fil est vide ou illisible. Les candidats en attente ne les ouvrent pas. Le premier article publié ouvre la rubrique et sélectionne le décor avec radar. La publication invalide aussi les layouts pour actualiser la navigation. Les règles couvrent FR, EN, ES et DE.

Décisions : [DD-0061](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0061-news-fil-cumulatif-et-ouverture.md) et [DD-0062](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0062-sources-news-et-file-de-traitement.md).

## Vérifications du lot isolé

- corepack pnpm check : formatage, lint, types et tests réussis ; 923 tests du site, 7 tests de l'introduction, 4 tests d'assets et 24 tests BIS.
- corepack pnpm build : build Next.js réussi, 204 pages statiques générées et routes API News présentes.
- corepack pnpm --filter @podcast/site test:episode:e2e : création, publication et republication sans durée ni date imposées ; iframe, chapitre et fermeture News vérifiés ; aucune erreur JavaScript.
- corepack pnpm --filter @podcast/site test:news:e2e : dix groupes réussis ; authentification, file privée et réservation, stockage idempotent, états vide et panne, quatre langues à 1440 et 390 px, filtres et pagination de 30 à 36 articles avec historique de trente jours ; aucune erreur JavaScript.
- Les tests Postgres parcourent 215 articles de même date sans perte ni doublon et vident une file de 45 candidats par réservations successives. Ils vérifient aussi les réservations concurrentes, la reprise après crash, les accusés périmés, les trois tentatives et les entrées trop anciennes.
- corepack pnpm audit --audit-level=high : aucune vulnérabilité connue signalée.
- git diff --check : aucun défaut d'espacement signalé.

Les recettes utilisent PGlite, des comptes et des fichiers éphémères sur loopback. Rapports et captures restent dans apps/site/.local/news-e2e/ et apps/site/.local/episode-publication-e2e/. Les premiers passages ont permis de corriger le menu Actualité inconditionnel et d'aligner la recette sur les réservations. Le test de recherche attend une interaction après hydratation avant de saisir son filtre.

## Mise en service et limites

Appliquer les migrations additives 0017 et 0018 sur la base cible après sauvegarde et accord, puis livrer l'application et le workflow correspondants. Le contrôle de version du protocole empêche le nouveau collecteur de démarrer contre une ancienne API. La migration 0016 est un prérequis déjà présent ; aucune migration existante n'est modifiée.

Avant d'activer ce volume en production, contrôler les minutes GitHub disponibles, le temps CPU, la capacité Postgres et la rétention des extraits dans la file. Aucun forfait payant ni quota supplémentaire n'est engagé. GitHub peut retarder le démarrage horaire et l'arriéré peut retarder la publication : le cron ne promet pas une fiche publique sous 60 minutes. Les lignes ne sont pas supprimées automatiquement.

Le modèle de résumé n'est pas installé sur ce poste. La génération réelle complète avec les nouvelles sources reste à vérifier sur le runner configuré, après livraison autorisée. La description YouTube attend l'accès à la chaîne et la validation d'écoute de ses repères.
