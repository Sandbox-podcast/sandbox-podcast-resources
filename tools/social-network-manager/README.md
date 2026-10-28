# SANDBOX Social Network Manager

Consigne actuelle, 28 octobre 2026 : utiliser la [factory persistante](../../docs/factory/exploitation.md). Le prompt maître remplace les cadences et quotas ci-dessous par une sélection selon la qualité, dans une fenêtre terminée avant le prochain tournage. La livraison initiale simule tous les envois ; aucun upload privé, brouillon distant, programmation ou modification sociale. LinkedIn reste exclusivement manuel. Les sections historiques conservent le contexte des épisodes précédents.

Pour Nico et Loïc : commence par le [tutoriel pour chaque nouvel épisode](GENERER.md). Il couvre les Shorts adaptés à chaque réseau, les formats YouTube de 5 à 15 minutes, l'installation sur un autre ordinateur et les contrôles. Les vidéos ne font pas partie de cette livraison. Les compositions E02 sont une référence de montage ; leurs timecodes ne doivent pas être réutilisés pour une nouvelle émission.

Agent editorial pour préparer, contrôler et mesurer la distribution de SANDBOX sur YouTube, Instagram, TikTok et X. Le dossier complète l'outil YouTube existant. Il ne remplace pas ses contrôles et ne publie rien par défaut.

Les [sources des trente Shorts E02 caméra unique](episode-02/camera-unique-v2/README.md) conservent les compositions, timecodes et outils locaux de reproduction. Le pipeline reste séparé de la file de publication et des comptes des réseaux.

## Mission

Faire découvrir le talk-show et ses expériences réelles, puis conduire les personnes intéressées vers les émissions complètes et la communauté. Conserver les désaccords tels qu'ils ont eu lieu, vérifier les faits et adapter chaque texte au réseau. Les vues seules ne définissent pas le succès.

## Priorité depuis le 18 octobre : épisode 2 et cadence intensive

Lire le [plan à six mois et l'audit Silicon Carne](../../docs/site/history/2026/10/social-growth-six-months-2026-10-18.md) avant l'ancien calendrier de lancement. Lou vise 10 000 abonnés par compte dans six mois et annonce un épisode hebdomadaire de deux heures, avec environ trente extraits possibles. L'épisode 2 est en cours d'upload; attendre son signal et vérifier la source avant de sélectionner des timecodes.

Cadence éditoriale retenue pour un essai de 14 jours : **4 Shorts YouTube/jour, 4 TikTok/jour, 3 Reels Instagram/jour, 2 vidéos X et 1 texte original X/jour**. Les créneaux Europe/Paris et les critères de révision sont dans le plan. Cette consigne remplace la faible cadence initiale pour les nouveaux lots validés; elle ne constitue pas une programmation native déjà effectuée. Réconcilier les sorties existantes avant tout ajout.

Préparer environ 40 candidats et retenir jusqu'à 30 extraits distincts : cas d'usage par métier, désaccords complets et actualités sourcées. Le nombre dépend du contenu réel. Utiliser les outils et le journal existants, sans nouvelle base ni deuxième ordonnanceur. Les routines doivent lire ce plan lors de leur prochaine reprise; leur restriction actuelle aux contrôles locaux reste en vigueur.

## Sources et limites actuelles

- Le 20 octobre, Lou demande le nom d'affichage `Sandbox Podcast` sur YouTube, Instagram, TikTok, X, LinkedIn et Spotify, avec le mot-clé `Talkshow` dans les descriptions. Les profils observés et les textes préparés sont dans [DD-0065](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0065-nom-public-sandbox-podcast.md) et [ce relevé](../../docs/site/history/2026/10/social-profile-copy-2026-10-20.md). TikTok bloque le changement de nom jusqu'au 24 octobre; sa bio de 80 caractères est déjà occupée par trois liens.

- Le positionnement et la charte existants sont dans `brand/youtube/` et `docs/design-decisions/DD-0001-direction-artistique-du-site.md`.
- La chaîne YouTube est déjà équipée d'un agent d'audit, de métadonnées, de sélection de passages, de rendu et de suivi. Son guide est `tools/youtube-growth/README.md`.
- Les quatre Shorts de l'émission 1 sont maintenant visibles dans Studio : deux publics (15 et 16 octobre), deux programmés (17 et 18 octobre). Le relevé Studio actuel prime sur les notes plus anciennes de `docs/open-questions.md`.
- Les quatre exports verticaux du dossier `exports/reseaux-sociaux/shorts/` sont des fichiers locaux. Leur audio et leurs sous-titres doivent être relus avant toute nouvelle diffusion. Les exports du dossier ne sont pas à confondre avec les quatre vidéos déjà présentes dans Studio.
- Le profil Instagram `@sandbox.talkshow` s'affiche sous le nom « Sandbox TalkShow », avec la bio renseignée et quatre Reels. L'identifiant a été modifié depuis `@sandbox.podcast.pro` le 17 octobre 2026. Le même avatar officiel `brand/social/sandbox-social-avatar.png`, dérivé de `logov2.png`, est appliqué sur Instagram, TikTok et X; les trois profils ont été vérifiés le 17 octobre 2026. Les quatre Reels Instagram reprennent déjà les exports et ne doivent pas être repostés tels quels.
- Le profil TikTok `@sandbox.talkshow` a quatre vidéos listées dans TikTok Studio avec l'audience « Tout le monde » au contrôle du 17 octobre. Le compteur du profil public n'était pas cohérent avec Studio; vérifier l'état de chaque vidéo avant de la considérer comme effectivement publiée. Aucun résultat de performance n'est déduit.
- Le 17 octobre, X indiquait quatre vidéos dans la file « Scheduled » pour les 18, 20, 22 et 24 octobre 2026 à 18 h. Au contrôle du profil le 18 octobre, seul le post de présentation du 17 octobre est visible; la file programmée n'a pas été revérifiée. Ne pas présumer que les quatre vidéos sont encore en attente ou déjà publiées.
- Les données natives Instagram/TikTok/X et un flux d'analytique unifié ne sont pas établis par les accès examinés. Ne pas en déduire des performances.
- Au contrôle des profils le 18 octobre, Instagram affiche quatre publications, zéro abonné et zéro suivi; TikTok affiche quatre vidéos publiques, zéro abonné et zéro j'aime. TikTok Studio, période des sept derniers jours, affiche zéro vue vidéo, visite de profil, j'aime, commentaire et partage, sans ventilation des sources faute de données suffisantes. Sur X, le profil affiche un post (9 vues, 1 j'aime, 1 repost), un abonné et trois comptes suivis. Ces compteurs sont un instantané, pas des métriques comparables par âge de publication. Le contrôle natif Instagram Insights et la file X n'ont pas été terminés.
- Le jeton OAuth du programme YouTube et la mise en service de son journal durable restent à traiter. Le workflow GitHub existant ne prouve pas que les opérations sont connectées ni publiées.

## Règle d'exploitation

L'agent peut rechercher, analyser les données accessibles, proposer des extraits, rédiger, préparer les médias, tenir le calendrier et produire un rapport. Toute publication, programmation publique, modification de profil, réponse publique, dépense, création de compte ou suppression attend un accord explicite du propriétaire tant qu'un processus d'approbation n'a pas été défini.

Un brouillon n'est pas une publication. Une date proposée n'est pas une programmation. Après chaque action autorisée, vérifier l'état réellement affiché dans la plateforme et enregistrer le lien, l'heure, le statut et la preuve disponible.

## Cycle hebdomadaire

1. Relever les nouveaux épisodes, les statuts de publication et les métriques disponibles. Noter la période et la source de chaque mesure.
2. Analyser la transcription et signaler les passages candidats avec début, fin, idée, contexte indispensable, formulation risquée et source.
3. Prioriser les passages compréhensibles sans l'émission complète. Préserver la question, la réponse et la nuance. Écarter toute coupe qui inverse une position ou transforme une plaisanterie en fait.
4. Générer des variantes natives par plateforme. TikTok ouvre directement sur l'idée. Instagram travaille la reconnaissance de l'équipe et le lien avec la communauté. YouTube Shorts relie le passage à l'émission source. X ajoute un point de vue ou une question précise, sans agrégateur de nouvelles.
5. Contrôler audio, sous-titres, noms propres, cadrage, droits, description, lien et statut de doublon. Les outils de rendu existants vérifient les fichiers, mais leur succès technique ne vaut pas validation éditoriale.
6. Préparer le calendrier, puis demander l'accord avant chaque écriture publique ou programmation.
7. À 48 heures et 7 jours, relever les chiffres natifs disponibles. Comparer des périodes équivalentes; signaler les données absentes et les échantillons trop faibles.
8. Produire un rapport qui sépare faits observés, hypothèses, décisions proposées et blocages.

### Contrôle de distribution et d'acquisition

Avant d'augmenter la cadence, contrôler que le contenu est effectivement visible et éligible à la recommandation, puis diagnostiquer les comptes qui n'ont aucune portée mesurable. Ne pas confondre compteur public, statistiques de Studio et données en cours de traitement.

- **TikTok** : vérifier dans TikTok Studio le statut, la visibilité, la date et les statistiques de chaque vidéo; consulter l'état du compte et l'éligibilité si les vues restent à zéro. Quand les fonctions sont disponibles, utiliser Creator Search Insights, les tendances Creative Center et les thèmes des commentaires pour choisir une question réelle. Une nouvelle publication doit apporter un angle ou une réponse distincte; ne pas retéléverser les mêmes quatre exports.
- **Instagram** : vérifier l'état du compte et l'accès aux Insights professionnels. Si la fonction est disponible, les Reels d'essai permettent de tester un angle d'abord auprès de non-abonnés; relever portée, rétention, partages, enregistrements, visites de profil et abonnements avant de décider de le partager plus largement. Les Stories servent surtout à écouter la communauté, pas à mesurer la découverte.
- **X** : contrôler la file programmée avant d'ajouter un post. Utiliser les statistiques natives ou X Analytics pour les impressions, interactions, clics et abonnements; utiliser l'outil Inspiration comme veille, sans recopier un post. Une réponse à un autre compte doit être spécifique au propos et apporter une information ou une expérience pertinente.
- Si les statistiques restent à zéro ou indisponibles, consigner la source, la période et les statuts vérifiés, puis investiguer l'éligibilité et la distribution. Ne pas augmenter les follows, publier en boucle ou annoncer un format gagnant sur la seule base d'un compteur nul.

## Acquisition organique et gratuite

Le plan d'exécution détaillé se trouve dans [la stratégie de croissance du 18 octobre](../../docs/site/history/2026/10/social-network-growth-2026-10-18.md). L'objectif de 10 000 abonnés est une ambition, pas une promesse ni une échéance prévisible avec les données actuelles.

- Ne pas faire de campagne follow-for-follow, de suivi/désabonnement massif, de copie automatisée des abonnés de concurrents, de pods d'engagement, d'achat d'abonnés ou de commentaires copiés-collés. Ces tactiques gonflent un chiffre sans construire une audience intéressée et exposent les comptes aux restrictions des plateformes.
- Un suivi manuel sert à organiser le fil autour de créateurs réellement pertinents, jamais à provoquer un retour de follow. Ne pas fixer de quota ni chercher à contourner les limites de fréquence propres à chaque plateforme.
- Consacrer une courte session quotidienne à lire les échanges et répondre aux commentaires reçus avec une réponse utile et personnelle. Participer aux discussions d'autres créateurs uniquement si SANDBOX apporte un point précis, sans déposer mécaniquement un lien ou une autopromotion.
- Chaque vidéo doit donner une raison de rester et une prochaine étape claire : accroche compréhensible dès la première phrase, idée ou désaccord complet, question précise à la communauté, puis lien vers l'épisode complet quand la plateforme le permet.
- Chercher des collaborations pertinentes (invitation, réponse croisée, co-publication ou extrait autorisé). Préparer une proposition personnalisée et obtenir l'accord de l'équipe avant tout contact externe.
- Réutiliser chaque épisode en angles distincts plutôt que republier en boucle le même fichier. Tester une seule variable à la fois (accroche, angle, couverture ou CTA) et garder un journal des variantes.
- À chaque bilan, comparer séparément portée/impressions, rétention ou complétion, partages/enregistrements, visites de profil, nouveaux abonnés et clics sortants. Utiliser les statistiques natives et la même fenêtre de mesure; si une donnée manque, l'indiquer comme indisponible.

## Automatisation Codex

Depuis le 24 octobre 2026, toutes les routines Sandbox de cette conversation sont en pause à la demande de Lou. Le contrôle quotidien à 09 h et le bilan du lundi à 09 h 30 ne se déclenchent plus. Leurs anciennes observations restent sous `.local/social-network-manager/`. Les associés peuvent lancer les contrôles manuellement dans leur session. Toute nouvelle routine nécessite une demande explicite ; le clone du dépôt n'en crée aucune.

## Mesure

YouTube : impressions, CTR, rétention à 30 secondes, durée moyenne, abonnés attribués, vues des Shorts et clics vers la vidéo associée. Instagram : portée, vues, durée de lecture ou rétention disponible, partages, enregistrements, visites de profil et abonnements. TikTok : vues, temps moyen, complétion, partages, commentaires, visites de profil et abonnements. X : impressions, interactions, clics et abonnements si le compte et les métriques sont accessibles.

Chaque ligne doit inclure plateforme, identifiant ou URL, date de publication, fenêtre de mesure, source de la donnée et valeur. Ne jamais fusionner les métriques de plateformes différentes ou présenter une valeur manquante comme zéro. Aucun seuil de performance n'est fixé avant plusieurs semaines de données comparables.

## Mise en service

Le plan d'audit, les profils proposés, le calendrier de 30 jours et dix brouillons se trouvent dans [le dossier de lancement social](../../docs/site/history/2026/10/social-network-manager-2026-10-17.md). La mise en service automatique exige encore une collecte autorisée et durable par réseau, des accès OAuth/API adaptés, une procédure d'approbation, ainsi qu'une preuve de programmation et de reprise après incident. Les outils de publication web ne doivent pas contourner les API officielles.
