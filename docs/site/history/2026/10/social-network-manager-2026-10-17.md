# SANDBOX Social Network Manager

## Mise à jour du 20 octobre 2026

Lou demande le nom public `Sandbox Podcast` et le mot-clé `Talkshow` dans les descriptions. L'état observé et les textes à utiliser sont consignés dans [DD-0065](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0065-nom-public-sandbox-podcast.md) et [la préparation des profils](social-profile-copy-2026-10-20.md). Les informations ci-dessous reflètent le relevé du 17 octobre.

État du 17 octobre 2026. Ce document transforme le brief Head of Social Media en mode opératoire, calendrier et premiers brouillons. Il distingue les faits observés des propositions. Aucun contenu n'est publié ou programmé par ce document.

## Audit de départ

| Surface        | État observé                                                                                                                                                                                                                                                                                                                                                 | Conséquence                                                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| YouTube        | Émission 1, playlist podcast et métadonnées déjà traités. Studio affiche quatre Shorts : deux publics (15 et 16 octobre) et deux programmés (17 et 18 octobre). Les compteurs visibles au relevé sont respectivement 45 et 867 vues pour les Shorts publics. OAuth du programme absent et journal distant non mis en service d'après les documents du dépôt. | Garder `tools/youtube-growth/` comme source du pipeline. Ne pas retéléverser ces quatre Shorts. Vérifier leur statut après les créneaux programmés. |
| Instagram      | `@sandbox.talkshow` (anciennement `@sandbox.podcast.pro`), nom Sandbox TalkShow, bio renseignée, avatar SANDBOX appliqué le 17 octobre 2026, quatre Reels et zéro abonné. Les quatre Reels couvrent Product Owners, IA comme Google, Codex/OpenCode et jeu vidéo.                                                                                            | Le nom et l'identité visuelle sont configurés. Ne pas dupliquer les quatre Reels; développer ensuite les stories à la une et du contenu distinct.   |
| TikTok         | `@sandbox.talkshow`, nom Sandbox TalkShow, bio "IA, dev, open source. Tests & débats sans bruit.", zéro publication, zéro abonné, zéro suivi, zéro mention J'aime au relevé actuel.                                                                                                                                                                          | Premier réseau à alimenter avec les quatre exports après relecture audio/sous-titres.                                                               |
| X              | `@SandboxTalkShow`, nom « Sandbox TalkShow », bio et bannière présents; avatar SANDBOX appliqué le 17 octobre 2026.                                                                                                                                                                                                                                          | Le compte est actif. Les métriques restent à relever depuis les données natives.                                                                    |
| Site et marque | Site média, promesse indépendante IA, développement et open source, charte bleu nuit/cyan et logo existants.                                                                                                                                                                                                                                                 | Réutiliser le symbole et les couleurs existants. Ne pas redessiner la marque.                                                                       |

Les quatre MP4 locaux sont dans `exports/reseaux-sociaux/shorts/`. Les notes d'exploitation indiquent que les sous-titres ont été corrigés au contexte, mais que l'écoute audio n'est pas confirmée. Ils ne sont pas nécessairement identiques aux versions déjà dans Studio. Le relevé YouTube du 14 octobre est limité à une émission et un petit volume; il ne permet pas de fixer une cible de croissance ni un horaire gagnant. Les impressions, clics et métriques sociales doivent être collectés séparément.

## Identité et profils

Le nom public Instagram est « Sandbox TalkShow »; l'identifiant est désormais `@sandbox.talkshow` (anciennement `@sandbox.podcast.pro`). Le compte n'a pas de bannière de profil. L'avatar commun `brand/social/sandbox-social-avatar.png` adapte le logotype source `logov2.png`, selon la palette de DD-0002. Il est appliqué et vérifié sur Instagram, TikTok et X le 17 octobre 2026.

Bio Instagram actuelle :

> IA, dev & open source. Tests et débats sans bruit. 🎙️ Podcast Sandbox TalkShow · sandboxpodcast.fr

Bio TikTok proposée, 77 caractères environ :

> IA, dev, open source. On teste, on débat, on construit. sandboxpodcast.fr

Texte X proposé si le compte est confirmé :

> Talk-show francophone sur l'IA, le développement et l'open source. On teste les outils, on débat et on construit. Épisodes et sources : sandboxpodcast.fr

La bio Instagram et le nom sont déjà affichés sur le profil. Instagram et TikTok n'ont pas de bannière de profil; utiliser l'avatar officiel et, plus tard, des couvertures de stories à la une cohérentes plutôt que la bannière X.

## Épingles proposées

- Instagram : une présentation courte de SANDBOX; un extrait de désaccord authentique; une démonstration ou un retour d'expérience de l'équipe. Les quatre Reels existants peuvent fournir le deuxième choix après écoute et relecture des sous-titres. Le troisième nécessite un contenu dédié sur Sillage ou une démonstration vérifiée.
- TikTok : commencer par le débat Codex/OpenCode, puis le passage Product Owners et le retour sur le jeu. Épingler seulement après publication et comparaison initiale de la compréhension et de la rétention.
- YouTube : conserver la playlist des émissions complètes et l'émission source associée aux Shorts. Revoir la page d'accueil dans Studio après avoir confirmé les statuts publics.
- X : pas de recommandation d'épinglage avant vérification du compte et de son historique.

## Cadence de départ sur 30 jours

**Remplacée le 18 octobre pour les nouveaux contenus par le [plan intensif à six mois](social-growth-six-months-2026-10-18.md).** Le tableau ci-dessous conserve la proposition historique; ne pas le rejouer, notamment pour les quatre extraits d'E1 déjà publiés ou programmés.

Période proposée : du 19 octobre au 17 novembre 2026. Heure de test : 18 h, heure de Paris. Ce créneau est un point de départ pratique, pas une heure optimisée par des données. Viser trois sorties éditoriales par semaine au total; adapter le texte au réseau et ne pas publier mécaniquement partout. Les jours sans source fiable restent vides.

| Date proposée | Contenu et réseau                                                              | Dépendance ou statut                                              |
| ------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| 19 oct.       | TikTok, désaccord Codex/OpenCode                                               | Brouillon 1; validation audio et sous-titres                      |
| 21 oct.       | Instagram Story, question sur les usages de l'IA                               | Brouillon 2; modèle de story simple avec logo                     |
| 23 oct.       | TikTok, Product Owners et IA                                                   | Brouillon 3; validation audio et contexte                         |
| 26 oct.       | Instagram carrousel, IA chez les artisans                                      | Brouillon 4; sources France Num, DGE et CMA France                |
| 28 oct.       | TikTok, jeu et game design                                                     | Brouillon 5; conserver la chute et le contexte                    |
| 30 oct.       | X, point de vue sur le travail produit                                         | Brouillon 6; compte à confirmer                                   |
| 2 nov.        | Instagram carrousel, mesurer un essai IA en TPE                                | Brouillon 7; sources de l'épisode 2                               |
| 4 nov.        | TikTok, usages de l'IA comme moteur de recherche                               | Brouillon 8; ne pas transformer le "99 %" oral en statistique     |
| 6 nov.        | X, extrait de méthode sur les relances de devis                                | Brouillon 9; compte à confirmer, source dans le dossier épisode 2 |
| 9 nov.        | YouTube Communauté, question préparatoire sur la prochaine émission            | Brouillon 10; ne pas annoncer de date ou de sujet non confirmé    |
| 11 nov.       | TikTok, second passage d'E1 seulement si l'écoute et les métriques l'indiquent | À sélectionner après mesures; pas de nouveau montage présumé      |
| 13 nov.       | Instagram Story, coulisse d'une préparation réelle                             | En attente d'un visuel réel fourni ou autorisé                    |
| 16 nov.       | X ou Instagram, retour de semaine avec données vérifiées                       | En attente du relevé natif; aucun chiffre à inventer              |

Si la revue audio n'est pas terminée, remplacer le créneau par un contenu texte vérifié ou le laisser vide. Ne pas créer de contenu pour respecter le quota.

## Dix premiers brouillons

Ces textes ne sont pas publiés. Les quatre premiers extraits sont déjà présents sur Instagram; les textes ci-dessous sont des versions destinées à TikTok, afin de tester le réseau où aucune publication n'apparaît au relevé. Avant publication, regarder chaque export avec le son et corriger les sous-titres directement à partir de l'audio.

### 1. TikTok - Codex ou OpenCode

Fichier : `exports/reseaux-sociaux/shorts/03-Codex-ou-OpenCode.mp4`.

Texte : "Codex ou OpenCode ? Le choix d'un outil ne répond pas à tout : le harnais et les cas d'usage comptent aussi. On en débat dans SANDBOX #1."

Légende : "Deux approches, des besoins différents. Extrait de SANDBOX #1. Épisode complet et sources sur sandboxpodcast.fr."

Contrôle : conserver la réserve sur les cas d'usage. Ne pas présenter l'échange comme une opposition absolue.

### 2. Instagram Story - question à la communauté

Visuel : fond bleu nuit, logo officiel, texte blanc, accent cyan. Pas de photo synthétique.

Texte : "Dans ton travail, l'IA t'aide surtout à chercher, écrire, coder ou vérifier ?" Ajouter un sticker de sondage avec ces quatre choix en deux stories si l'interface limite les réponses.

Contrôle : relever les réponses sans prétendre qu'elles représentent tous les professionnels.

### 3. TikTok - Product Owners et IA

Fichier : `exports/reseaux-sociaux/shorts/01-IA-et-Product-Owners.mp4`.

Texte : "Quand les développeurs accélèrent avec l'IA, le goulot peut se déplacer vers la définition du besoin et les décisions produit. C'est le point de départ de ce débat."

Légende : "L'IA change aussi le rythme du travail produit. Extrait de SANDBOX #1, épisode complet sur sandboxpodcast.fr."

Contrôle : garder la condition exprimée dans l'échange. Ne pas annoncer le remplacement des Product Owners.

### 4. Instagram carrousel - IA chez les artisans

Source : `docs/site/episode-002-beta-artisans-commercants.md` et ses sources France Num, DGE, CMA France.

Slides :

1. "Où l'IA peut aider un artisan ?"
2. "Un devis commence par une visite. Une dictée peut préparer un dossier structuré."
3. "Les quantités, les prix et les engagements restent à vérifier par le professionnel."
4. "Une relance peut être préparée à partir d'une échéance, puis validée avant envoi."
5. "Mesure le temps gagné après relecture et corrections."
6. "Commence par une tâche répétée. Vérifie d'abord les fonctions de ton logiciel métier."

Légende : "L'IA ne fait pas disparaître la vérification. Pour un artisan, un premier essai peut porter sur les devis ou leur suivi. Le gain se mesure après corrections, pas au nombre de textes générés. Sources : France Num, DGE et CMA France."

### 5. TikTok - jeu et game design

Fichier : `exports/reseaux-sociaux/shorts/04-vibe-coding-et-jeux.mp4`.

Texte : "On peut créer un jeu plus vite avec l'IA. Ça ne décide pas à ta place ce qui le rend amusant."

Légende : "Vibe coder un jeu ne remplace pas le game design. Retour d'expérience dans SANDBOX #1."

Contrôle : garder la conclusion humoristique et le propos complet.

### 6. X - le rythme du travail produit

Texte : "Quand le code accélère, le prochain goulot n'est pas forcément le code. Il peut être dans le besoin, les arbitrages ou les retours. C'est une hypothèse à tester dans l'équipe, pas une loi générale."

Visuel : extrait 01, uniquement si le compte X est confirmé et si la vidéo a été revue.

### 7. Instagram carrousel - évaluer un essai IA

Source : `docs/site/episode-002-beta-artisans-commercants.md`.

Slides :

1. "Un essai IA a-t-il vraiment fait gagner du temps ?"
2. "Chronomètre la tâche avant l'essai."
3. "Compte la préparation, la relecture et les corrections."
4. "Note les erreurs qui restent et le coût des outils."
5. "Compare des volumes et des périodes comparables."
6. "Si les corrections effacent le gain, simplifie ou arrête l'essai."

Légende : "Générer plus vite ne suffit pas. Pour savoir si l'essai aide vraiment, compte le temps de relecture, les erreurs restantes et les coûts. Cette méthode est une proposition de mesure, pas un résultat observé."

### 8. TikTok - l'IA comme Google

Fichier : `exports/reseaux-sociaux/shorts/02-IA-comme-Google.mp4`.

Texte : "On pose souvent une question à l'IA comme à un moteur de recherche. Mais les réponses ne se vérifient pas de la même façon."

Légende : "Un débat sur nos usages de l'IA, extrait de SANDBOX #1. L'épisode complet est sur sandboxpodcast.fr."

Contrôle : ne pas reprendre le "99 %" de l'intervenant comme statistique.

### 9. X - relances de devis

Texte : "Une relance de devis assistée par IA peut préparer un message. Le test utile porte sur le temps total, les corrections et les devis signés, pas sur le nombre de messages produits."

Visuel : carte texte dans la charte existante. Compte et publication à confirmer.

### 10. YouTube Communauté - question pour le prochain épisode

Texte : "Pour la prochaine émission, quel usage de l'IA aimeriez-vous voir testé en conditions réelles : préparer un devis, suivre une relance, traiter une demande client ou autre chose ?"

Contrôle : publier seulement si l'équipe a confirmé le thème de la prochaine émission et souhaite utiliser les réponses pour préparer le conducteur.

## Automatisations en service et à établir

Deux tâches récurrentes Codex sont actives dans la conversation de Lou : un contrôle quotidien à 09 h et un bilan hebdomadaire le lundi à 09 h 30, heure de Paris. Elles examinent les sources et exports locaux, écrivent des notes dans `.local/social-network-manager/` uniquement si de nouvelles informations le justifient, et restent silencieuses quand rien n'a changé. Elles préparent des brouillons et des bilans; elles ne publient pas, ne programment pas et ne modifient aucun compte. Ce réglage appartient à la tâche de Lou et ne se copie pas automatiquement aux comptes Codex de Nico et Loïc. Comme ces routines lisent le dépôt local, l'ordinateur, Codex et le projet doivent rester disponibles au moment prévu.

1. Réutiliser l'audit YouTube déjà implémenté et compléter son OAuth/journal après autorisation et vérifications listées dans `tools/youtube-growth/README.md`.
2. Étendre les notes quotidiennes et le rapport hebdomadaire en paquet de préparation local : nouveaux épisodes, transcription, propositions d'extraits, textes de plateformes, calendrier, liste de contrôles et métriques disponibles. Enregistrer les sorties dans `.local/social-network-manager/`, ignoré par Git.
3. Ajouter Instagram, TikTok et X seulement avec des API officielles et permissions documentées. Vérifier les capacités réelles de publication, programmation et métriques pour chaque réseau; prévoir une voie manuelle tant qu'une API n'est pas configurée.
4. Centraliser le statut éditorial dans un journal durable : `idea`, `draft`, `needs_review`, `approved`, `scheduled`, `published`, `blocked`. Une transition vers `approved` ou `scheduled` doit porter l'identité du valideur, l'horodatage, les empreintes du média et du texte, la plateforme et le créneau.
5. Relancer après erreur uniquement après réconciliation de l'état distant. Une réponse réseau ambiguë ne doit pas générer un doublon.
6. Importer chaque semaine les métriques natives et produire un bilan. Ne pas entraîner un choix automatique sur un échantillon trop faible.

### Bloqueurs de mise en service

- Aucun OAuth/API Instagram, TikTok ou X n'est documenté dans le dépôt.
- OAuth YouTube pour le programme et base durable du journal ne sont pas confirmés comme actifs.
- Réécoute audio et revue des sous-titres des exports restantes.
- Accès natifs aux statistiques par plateforme non collectés dans ce dossier.
- Le compte X et la prochaine date/sujets d'émission ne sont pas confirmés.

Le compte Gmail connecté et les pages sociales ne remplacent pas les permissions API. Ne pas enregistrer un mot de passe ou un jeton dans le dépôt.
